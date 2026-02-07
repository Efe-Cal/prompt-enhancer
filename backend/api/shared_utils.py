import os
import unicodedata
import re

import httpx
from dotenv import load_dotenv
from openai import OpenAI, AsyncOpenAI

from . import log

load_dotenv()

FALLBACK_MODEL = "gpt-5-mini"

def get_client():
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("API_KEY") or ""
    base_url = os.getenv("OPENAI_BASE_URL") or os.getenv("BASE_URL") or "https://api.openai.com/v1"
    return OpenAI(api_key=api_key, base_url=base_url)

def get_async_client(fallback: bool = False):
    if fallback:
        return AsyncOpenAI(api_key=os.getenv("FALLBACK_API_KEY", ""))
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("API_KEY") or ""
    base_url = os.getenv("OPENAI_BASE_URL") or os.getenv("BASE_URL") or "https://api.openai.com/v1"
    return AsyncOpenAI(api_key=api_key, base_url=base_url)

def get_model() -> str:
    return os.getenv("OPENAI_MODEL") or os.getenv("MODEL") or "gpt-5.1"

def clean_text_for_llm(text):
    # Normalize Unicode
    text = unicodedata.normalize('NFKC', text)
    
    # Remove control characters except newlines/tabs
    text = ''.join(c for c in text if unicodedata.category(c)[0] != 'C' or c in '\n\r\t')
    
    # Remove zero-width characters
    text = re.sub(r'[\u200b-\u200d\ufeff]', '', text)
    
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()

async def web_search_async(query: str, n=3) -> str:
    log(f"Performing async web search for query: {query}")
    async with httpx.AsyncClient() as client:
        response = await client.get(
            'https://search.hackclub.com/res/v1/web/search',
            params={'q': query},
            headers={'Authorization': f'Bearer {os.getenv("HACKCLUB_SEARCH_API_KEY", "")}'},
        )
    response.raise_for_status()
    data = response.json()
    
    data = [(item["title"], "\n".join(item["extra_snippets"]) if "extra_snippets" in item else item["description"]) for item in data["web"]["results"][:n]]
    data = [(clean_text_for_llm(title), clean_text_for_llm(snippets)) for title, snippets in data]
    data_str = "\n".join([f"- {title}\n{snippets}\n----------" for title, snippets in data])
    
    return data_str

def format_answers_for_llm(questions:list[str],answers: list[str] | str) -> str:
    if answers == "CANCEL":
        return "User refused to answer the questions."
    if len(answers) == 1:
        return answers[0]
    else:
        return "\n".join([f"Q: {q}\nA: {answer if answer else 'User did not provide an answer for this question.'}" for q, answer in zip(questions, answers)])

def parse_llm_response(response: str) -> None:
    improved_prompt_match = re.search(r"<improved-prompt>(.*?)</improved-prompt>", response, re.DOTALL)
    if improved_prompt_match:
        improved_prompt = improved_prompt_match.group(1).strip()
        log(f"[DEBUG] Parsed Improved Prompt: {improved_prompt[:50]}...")
        return improved_prompt
    else:
        log("[DEBUG] No <improved-prompt> tag found in LLM response.")
        return None

def check_hcai_status() -> bool:
    res = httpx.get("https://ai.hackclub.com/up").json()
    return res.get("status", "down") == "up"
