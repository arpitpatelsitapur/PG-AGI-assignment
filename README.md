[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://talentscout7.streamlit.app/)

# TalentScout Hiring Assistant

## Project Overview
TalentScout is an AI-powered hiring assistant chatbot that streamlines the technical interview process. Built with **Streamlit** and **Kimi-K2** (via OpenRouter), it collects candidate information, generates tailored technical questions for each declared tech stack, and simulates safe, anonymized data storage. The assistant adapts question difficulty based on candidate experience and provides a conversational UI for a smooth interview flow.

## Installation Instructions
1. **Clone the repository:**
	```bash
	git clone https://github.com/arpitpatelsitapur/PG-AGI-assignment
	cd "PG-AGI-assignment"
	```
2. **Install dependencies:**
	```bash
	pip install -r requirements.txt
	```
3. **Configure API Key:**
	- Create a file at `.streamlit/secrets.toml` with the following content:
	  ```
	  API_KEY = "your_api_key_here"
	  ```
4. **Run the app:**
	```bash
	streamlit run app.py
	```

## Usage Guide
- Launch the app and fill in candidate details (name, email, phone, experience, role, location, tech stack) in the sidebar.
- Select the number of technical questions per technology.
- The chatbot will ask one question at a time, collect answers, and provide feedback.
- All candidate data is simulated and stored in-memory for privacy.

## Technical Details
- **Languages & Frameworks:** Python, Streamlit
- **AI Model:** Kimi-K2 by MoonShot (free, accessed via OpenRouter), use any as u wish.
- **Architecture:**
  - Modular codebase (prompt generation, storage, UI)
  - Prompts adapt to candidate experience and tech stack
  - Simulated (in-memory) data storage for privacy compliance
- **Libraries Used:**
  - streamlit, openai, httpx, pandas, numpy, dotenv, tqdm, etc.

## Prompt Design
Prompts are dynamically crafted to:
- Gather candidate information clearly and concisely
- Generate relevant, open-ended technical questions for each technology in the candidate's stack
- Adjust question difficulty based on years of experience (fresher, junior, mid-level)
- Use template prompts as fallback to ensure reliability and consistency
This approach ensures the chatbot can handle a wide range of tech stacks and candidate profiles, maintaining high-quality, relevant questions throughout the interview.

## Challenges & Solutions
- **Prompt Engineering:** Ensuring prompts were clear and adaptable for various tech stacks and experience levels. *Solution:* Used dynamic and template-based prompt generation.
- **Data Privacy:** Avoiding storage of sensitive candidate data. *Solution:* All data is simulated and stored only in memory, with no persistent storage or external transmission.
- **LLM Output Consistency:** Handling cases where the LLM output was inconsistent or incomplete. *Solution:* Implemented fallback templates and robust parsing logic.
- **User Experience:** Creating a smooth, conversational UI. *Solution:* Leveraged Streamlit's session state and UI components for seamless interaction.

---
