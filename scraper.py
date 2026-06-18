import os
import requests
from groq import Groq

# 1. Fetch data from Hacker News Open API
def fetch_hacker_news_signals(limit=3):
    print("Connecting to Hacker News API...")
    top_stories_url = "https://hacker-news.firebaseio.com/v0/topstories.json"
    response = requests.get(top_stories_url)
    
    if response.status_code != 200:
        print(f"Failed to fetch top stories IDs. Error code: {response.status_code}")
        return []
        
    story_ids = response.json()[:limit]
    scraped_stories = []
    
    for story_id in story_ids:
        item_url = f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json"
        item_response = requests.get(item_url)
        
        if item_response.status_code == 200:
            story_data = item_response.json()
            scraped_stories.append({
                "title": story_data.get("title"),
                "score": story_data.get("score")
            })
    return scraped_stories

# 2. Feed the headlines to the AI model
def ai_analyze_headline(title):
    # Reads the key securely from your terminal session variable
    api_key = os.environ.get("GROQ_API_KEY") 
    
    if not api_key:
        return "SIGNAL: Error\nREASON: Environment variable GROQ_API_KEY is not set."
        
    client = Groq(api_key=api_key)
    
    system_prompt = (
        "You are an expert AI Engineer screening tech news. Analyze the given headline. "
        "Determine if it is 'High Signal' (involves new AI models, developer tools, open-source tech, infrastructure) "
        "or 'Noise' (general news, politics, drama). "
        "Reply in exactly this format:\n"
        "SIGNAL: [High Signal / Noise]\n"
        "REASON: [One sentence why]"
    )
    
    # Using the updated, active Llama 3.3 model string
    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Headline: {title}"}
        ],
        temperature=0.1
    )
    
    return completion.choices[0].message.content

# 3. Main execution script
if __name__ == "__main__":
    articles = fetch_hacker_news_signals(limit=3)
    print("\n--- RUNNING AI INTELLIGENCE EVALUATION ---")
    
    for article in articles:
        print(f"\nEvaluating Headline: {article['title']}")
        try:
            ai_verdict = ai_analyze_headline(article['title'])
            print(ai_verdict)
        except Exception as e:
            print(f"AI Evaluation failed: {e}")
        print("-" * 40)