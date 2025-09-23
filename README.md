# TalentScout Hiring Assistant 

AI-powered hiring chatbot built with **Streamlit** + **DeepSeek**.  
Developed as part of the AI/ML Intern Assignment.

## Features
- Collects candidate info (name, email, phone, experience, position, location, tech stack)
- Generates **subjective, open-ended technical questions** per tech stack item
- Conversation flow with context + exit command
- Simulated data storage (safe, anonymized)
- Streamlit UI

## Setup
```bash
git clone https://github.com/arpitpatelsitapur/PG-AGI-assignment
cd "PG-AGI-ASSIGNMENT"
pip install -r requirements.txt
```

## Configure Secrets
Create .streamlit/secrets.toml:
```
DEEPSEEKR1_API_KEY = "your_api_key_here"
```
### Run
```
streamlit run app.py
```

### Tech
- Python
- Streamlit
- DeepSeek (via OpenRouter)
- Modular code (prompts, storage, utils)
---
