import os
import json
import unicodedata
import re
from typing import Callable, Awaitable, Optional

import openai
import httpx
from dotenv import load_dotenv
from openai import OpenAI, AsyncOpenAI

from .prompt import build_prompts

load_dotenv()

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

def web_search(query: str, n=10) -> str:
    print(f"Performing web search for query: {query}")
    response = httpx.get(
        'https://search.hackclub.com/res/v1/web/search',
        params={'q': query},
        headers={'Authorization': f'Bearer {os.getenv("HACKCLUB_SEARCH_API_KEY", "")}'},
    )
    response.raise_for_status()
    data = response.json()
    
    # Extract titles and snippets
    data = [(item["title"], "\n".join(item["extra_snippets"]) if "extra_snippets" in item else item["description"]) for item in data["web"]["results"][:n]]

    # Clean text for LLM compatibility
    data = [(clean_text_for_llm(title), clean_text_for_llm(snippets)) for title, snippets in data]

    data_str = "\n".join([f"- {title}\n{snippets}\n----------" for title, snippets in data])
    
    return data_str

async def web_search_async(query: str, n=10) -> str:
    print(f"Performing async web search for query: {query}")
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


# Deprecated
def enhance_prompt(task: str, lazy_prompt: str, model: str, use_web_search: bool = True, additional_context_query: str = None, falling_back=False, task_id: str = None) -> str:
    if not falling_back:
        client = get_client()
    else:
        client = OpenAI(api_key=os.getenv("FALLBACK_API_KEY", ""))

    additional_context = web_search(additional_context_query, 3) if additional_context_query else ""  
    
    system_prompt, user_prompt = build_prompts(
            task=task,
            lazy_prompt=lazy_prompt,
            use_web_search=True,
            additional_context=additional_context
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
                "description": "Ask the user for input to clarify or enhance the prompt. Include only the question, do not include any additional text.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "question": {
                            "type": "string",
                            "description": "The question to ask the user",
                        },
                    },
                    "required": ["question"],
                },
            }
        }
    ]
    if use_web_search:
        tools += [
            {
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
            }
        ]
    
    
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=tools
        )
        print(f"[DEBUG] Initial LLM Response: {response.choices[0].message}")
        
        # Handle tool calls if present
        while response.choices[0].message.tool_calls:
            messages.append(response.choices[0].message)
            for tool_call in response.choices[0].message.tool_calls:
                print(f"[DEBUG] Processing Tool Call: {tool_call.function.name} with args: {tool_call.function.arguments}")
                if tool_call.function.name == "web_search":
                    args = json.loads(tool_call.function.arguments)
                    search_result = web_search(args["query"])
                    print(f"[DEBUG] Tool Result ({tool_call.function.name}): {search_result[:100]}...")
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": search_result
                    })
                if tool_call.function.name == "get_user_input":
                    # Local import to avoid circular dependency
                    from .tasks import ask_user_question
                    
                    args = json.loads(tool_call.function.arguments)
                    print("Asking user question via WebSocket...")
                    user_input = ask_user_question(
                        task_id=task_id,
                        question=args["question"]
                    )
                    print(f"[DEBUG] Tool Result ({tool_call.function.name}): {user_input}")
                    
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": user_input
                    })
            
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                tools=tools
            )
            print(f"[DEBUG] Next LLM Response: {response.choices[0].message}")

        result = (response.choices[0].message.content or "").strip()
        start_index = result.find("IMPROVED PROMPT:")
        if start_index != -1:
            result = result[start_index + len("IMPROVED PROMPT:"):].strip()
        
        return result
    except openai.APIStatusError as e:
        print(f"APIStatusError: {e}")
        print("Falling back to alternative model...")
        # return enhance_prompt(task, lazy_prompt, "gpt-5.1", use_web_search, additional_context_query, falling_back=True)

def format_answers_for_llm(questions:list[str],answers: list[str]) -> str:
    if len(answers) == 1:
        return answers[0]
    else:
        return "\n".join([f"Q: {q}\nA: {answer}" for q, answer in zip(questions, answers)])

def parse_llm_response(response: str) -> None:
    improved_prompt_match = re.search(r"<improved_prompt>(.*?)</improved_prompt>", response, re.DOTALL)
    if improved_prompt_match:
        improved_prompt = improved_prompt_match.group(1).strip()
        print(f"[DEBUG] Parsed Improved Prompt: {improved_prompt[:50]}...")
        return improved_prompt
    else:
        print("[DEBUG] No <improved_prompt> tag found in LLM response.")
        return None

async def enhance_prompt_async(
    task: str,
    lazy_prompt: str,
    model: str,
    use_web_search: bool = True,
    additional_context_query: Optional[str] = None,
    target_model: str = "gpt-5.1",
    ask_user_func: Optional[Callable[[str], Awaitable[str]]] = None,
    falling_back: bool = False
) -> str:
    """Async version of enhance_prompt that runs in the WebSocket consumer."""
    client = get_async_client(fallback=falling_back)

    additional_context = ""
    if additional_context_query:
        additional_context = await web_search_async(additional_context_query, 3)
    
    system_prompt, user_prompt = build_prompts(
            task=task,
            lazy_prompt=lazy_prompt,
            use_web_search=use_web_search,
            additional_context=additional_context,
            target_model=target_model
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
        print(f"[DEBUG] Initial LLM Response (Async): {response.choices[0].message}")
        
        while response.choices[0].message.tool_calls:
            messages.append(response.choices[0].message)
            for tool_call in response.choices[0].message.tool_calls:
                print(f"[DEBUG] Processing Tool Call (Async): {tool_call.function.name} with args: {tool_call.function.arguments}")
                if tool_call.function.name == "web_search":
                    args = json.loads(tool_call.function.arguments)
                    search_result = await web_search_async(args["query"])
                    print(f"[DEBUG] Tool Result ({tool_call.function.name}): {search_result[:100]}...")
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": search_result
                    })
                elif tool_call.function.name == "get_user_input":
                    args = json.loads(tool_call.function.arguments)
                    print("Asking user question via WebSocket...")
                    if ask_user_func:
                        user_input = await ask_user_func(args["questions"])
                    else:
                        user_input = "(No user input handler available)"
                    
                    user_input = format_answers_for_llm(args["questions"], user_input)
                    
                    print(f"[DEBUG] Tool Result ({tool_call.function.name}): {user_input}")

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
            print(f"[DEBUG] Next LLM Response (Async): {response.choices[0].message}")

        result = (response.choices[0].message.content or "").strip()
        
        result = parse_llm_response(result)
        
        return result
    except openai.APIStatusError as e:
        print(f"APIStatusError: {e}")
        print("Falling back to alternative model...")
        return await enhance_prompt_async(
            task, lazy_prompt, "gpt-5.1", use_web_search, 
            additional_context_query, ask_user_func, falling_back=True
        )