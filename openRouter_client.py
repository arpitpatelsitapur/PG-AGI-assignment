import streamlit as st
from openai import OpenAI

API_KEY = st.secrets["API_KEY"]
BASE_URL = "https://openrouter.ai/api/v1"

class OpenRouterClient:
    def __init__(self):
        self.client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

    def generate(self, prompt: str) -> str:
        chat = self.client.chat.completions.create(
            model="moonshotai/kimi-k2:free",
            messages=[{"role": "user", "content": prompt}],
        )
        return chat.choices[0].message.content.strip()