import os
import sqlite3
import requests
import json
from groq import Groq

DB_NAME = "signals.db"


def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS news_signals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT UNIQUE,
            score INTEGER,
            signal_score INTEGER,
            category TEXT,
            reason TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def is_already_processed(title):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM news_signals WHERE title = ?", (title,))
    exists = cursor.fetchone() is not None
    conn.close()
    return exists

def save_signal(title, score, signal_score, category, reason):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO news_signals (title, score, signal_score, category, reason)
            VALUES (?, ?, ?, ?, ?)
        """, (title, score, signal_score, category, reason))
        conn.commit()
    except sqlite3.IntegrityError:
        pass
    finally:
        conn.close()



def fetch_hacker_news_signals(limit=15):  # Pulling more stories to feed the filters
    print("📥 Fetching raw data from Hacker News API...")
    top_stories_url = "https://hacker-news.firebaseio.com/v0/topstories.json"
    response = requests.get(top_stories_url)
    if response.status_code != 200:
        return []
        
    story_ids = response.json()[:limit]
    scraped_stories = []
    
    for story_id in story_ids:
        item_url = f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json"
        item_response = requests.get(item_url)
        if item_response.status_code == 200:
            story_data = item_response.json()
            scraped_stories.append({
                "title": story_data.get("title", ""),
                "score": story_data.get("score", 0)
            })
    return scraped_stories


def passes_heuristic_filter(article):
    """
    Tier 1 Filter: Drops items with zero engagement or irrelevant topics
    before wasting money on AI API calls.
    """
    title_lower = article["title"].lower()
    
    
    keywords = ["ai", "llama", "llm", "vllm", "vulnerability", "exploit", "security", "open-source", "framework", "git", "python", "bug", "release", "model"]
    
   
    has_keyword = any(keyword in title_lower for keyword in keywords)
    has_high_engagement = article["score"] >= 50 
    
    if has_keyword or has_high_engagement:
        return True
    return False



def ai_analyze_headline(title):
    """
    Tier 2 Filter: Uses LLM to score the signal from 1-10 and outputs strict JSON.
    """
    api_key = os.environ.get("GROQ_API_KEY") 
    if not api_key:
        raise ValueError("GROQ_API_KEY environment variable missing.")
        
    client = Groq(api_key=api_key)
    
    system_prompt = (
        "You are an expert AI Engineer. Analyze the given headline. "
        "Rate its engineering/technical value as a signal from 1 to 10 (10 being a major open-source breakthrough, 1 being drama/noise). "
        "You must respond with a raw JSON object matching this exact schema:\n"
        "{\n"
        '  "signal_score": 8,\n'
        '  "category": "AI Infrastructure",\n'
        '  "reason": "Explains why this is or isn\'t high-signal in one short sentence."\n'
        "}"
    )
    
    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Headline: {title}"}
        ],
        temperature=0.1,
        response_format={"type": "json_object"}  # Forces Groq to output valid JSON
    )
    return json.loads(completion.choices[0].message.content)



if __name__ == "__main__":
    init_db()
    raw_articles = fetch_hacker_news_signals(limit=15)
    
    print(f"\n⚡ Ingested {len(raw_articles)} raw headlines. Starting production pipeline...")
    
    for article in raw_articles:
        title = article['title']
        score = article['score']
        
        print(f"\nProcessing: '{title}'")
        
        
        if is_already_processed(title):
            print("Skipping: Already handled in database.")
            continue
            
      
        if not passes_heuristic_filter(article):
            print(" Dropped by Heuristic Filter (Low engagement / irrelevant keywords).")
            continue
            
        
        print(" Heuristics passed. Running Structured LLM Evaluation...")
        try:
            analysis = ai_analyze_headline(title)
            
            signal_score = analysis.get("signal_score", 1)
            category = analysis.get("category", "General")
            reason = analysis.get("reason", "")
            
            print(f"   [Score: {signal_score}/10] | [Category: {category}]")
            print(f"   Reason: {reason}")
            
           
            if signal_score >= 6:
                save_signal(title, score, signal_score, category, reason)
                print("High Signal confirmed. Saved to database checkpoint.")
            else:
                print("Dropped: LLM signal score below target threshold (6).")
                
        except Exception as e:
            print(f" Pipeline evaluation error: {e}")