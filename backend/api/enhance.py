import os
import json_repair as json
import unicodedata
import re
from typing import Callable, Awaitable, Optional

import openai
import httpx
from dotenv import load_dotenv
from openai import OpenAI, AsyncOpenAI

from .prompt import build_prompts
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

async def enhance_prompt_async(
    task: str,
    lazy_prompt: str,
    model: str,
    use_web_search: bool = True,
    additional_context_query: Optional[str] = None,
    target_model: str = "gpt-5.1",
    ask_user_func: Optional[Callable[[str], Awaitable[str]]] = None,
    falling_back: bool = False,
    prompt_style: dict | None = None
) -> str:
    """Async version of enhance_prompt that runs in the WebSocket consumer."""
    if not check_hcai_status() and not falling_back:
        log("HCAI service is down, falling back to alternative model...")
        if os.getenv("FALLBACK_API_KEY") and os.getenv("FALLBACK_API_KEY") != "":
            return await enhance_prompt_async(
                task, lazy_prompt, FALLBACK_MODEL, use_web_search, 
                additional_context_query, ask_user_func, falling_back=True,
                target_model=target_model, prompt_style=prompt_style
            ), True
        else:
            raise Exception("We are out of money! Please try again later.")    
    
    client = get_async_client(fallback=falling_back)

    additional_context = ""
    if additional_context_query:
        additional_context = await web_search_async(additional_context_query, 3)
    
    system_prompt, user_prompt = build_prompts(
            task=task,
            lazy_prompt=lazy_prompt,
            use_web_search=use_web_search,
            additional_context=additional_context,
            target_model=target_model,
            prompt_style=prompt_style
        ).values()

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
    
    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_user_input",
                "description": "Ask the user for input to clarify the prompt.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "questions": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "The question(s) to ask the user",
                        },
                    },
                    "required": ["questions"],
                },
            }
        }
    ]
    
    if use_web_search:
        tools.append({
            "type": "function",
            "function": {
                "name": "web_search",
                "description": "Useful for when you need to look up information on the web to enhance the prompt.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The search query to look up.",
                        },
                    },
                    "required": ["query"],
                },
            }
        })
    
    try:
        response = await client.chat.completions.create(
            model=model,
            messages=messages,
            tools=tools,
            reasoning_effort="medium"
        )
        log(f"[DEBUG] Initial LLM Response (Async): {response.choices[0].message}")
        
        while response.choices[0].message.tool_calls:
            messages.append(response.choices[0].message)
            for tool_call in response.choices[0].message.tool_calls:
                log(f"[DEBUG] Processing Tool Call (Async): {tool_call.function.name} with args: {tool_call.function.arguments}")
                if tool_call.function.name == "web_search":
                    args = json.loads(tool_call.function.arguments)
                    search_result = await web_search_async(args["query"])
                    log(f"[DEBUG] Tool Result ({tool_call.function.name}): {search_result[:100]}...")
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": search_result
                    })
                elif tool_call.function.name == "get_user_input":
                    args = json.loads(tool_call.function.arguments)
                    log("Asking user question via WebSocket...")
                    if ask_user_func:
                        user_input = await ask_user_func(args["questions"])
                    else:
                        user_input = "(No user input handler available)"
                    
                    user_input = format_answers_for_llm(args["questions"], user_input)
                    
                    log(f"[DEBUG] Tool Result ({tool_call.function.name}): {user_input}")

                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": user_input
                    })

            response = await client.chat.completions.create(
                model=model,
                messages=messages,
                tools=tools,
                reasoning_effort="medium"
            )
            log(f"[DEBUG] Next LLM Response (Async): {response.choices[0].message}")

        result = (response.choices[0].message.content or "").strip()
        
        result = parse_llm_response(result)
        
        return result, False
    except openai.APIStatusError as e:
        log(f"APIStatusError: {e}")
        log("Falling back to alternative model...")
        if os.getenv("FALLBACK_API_KEY") and os.getenv("FALLBACK_API_KEY") != "" and not falling_back:
            return await enhance_prompt_async(
                task, lazy_prompt, FALLBACK_MODEL, use_web_search, 
                additional_context_query, ask_user_func, falling_back=True,
                target_model=target_model, prompt_style=prompt_style
            ), True
        else:
            raise Exception("We are out of money! Please try again later.") from e