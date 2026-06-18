# signal-engine

An automated, AI-driven data pipeline that scrapes top tech headlines from the Hacker News API and uses state-of-the-art Large Language Models (LLMs) to separate critical technical breakthroughs ("High Signal") from general media chatter ("Noise").

## Features
- **Live Data Ingestion**: Programmatically queries the official Hacker News API to fetch real-time trending engineering discussions.
- **Intelligent Classification**: Utilizes the high-speed Groq API running `llama-3.3-70b-versatile` to extract structured analysis from raw titles.
- **Zero-Dependency Leakage Safety**: Built around system environment variables to handle sensitive developer API keys cleanly without hardcoding credentials into source code.

## Tech Stack
- **Language**: Python 3.13
- **Inference Runtime**: Groq Cloud API
- **Model Layer**: Llama 3.3 70B Versatile
- **Networking**: Python Requests library

## Quick Start

### 1. Installation
Install the project dependencies using the requirements file:
```bash
pip3 install -r requirements.txt --user