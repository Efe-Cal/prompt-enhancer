from functools import cache
import os
import json
from datetime import datetime
import unicodedata
import re
from typing import Callable, Awaitable, Optional

import openai
import httpx
from dotenv import load_dotenv
from openai import OpenAI, AsyncOpenAI


load_dotenv()

@cache
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


SYSTEM_PROMPT = """Act as an expert Prompt Engineer. You will be given an initial prompt to improve. Make sure you produce a ready-to-use prompt."""


def build_user_prompt(task: str, lazy_prompt: str, use_web_search:bool, additional_context: str) -> str:
    contextual_guidelines = "- Be specific, descriptive and as detailed as possible about the desired context, outcome, length, format, etc\n\n- Always use the web_search tool to look up any relevant information on the web to include in the improved prompt as context. (if needed today's date is " + datetime.now().strftime("%B %d, %Y")+")" if use_web_search else "- Be specific, but only provide instructions with limited context. DO NOT include any specific information that may be outdated or incorrect."
    additional_context = "\n----------\n"+'# Additional Context from Web Search\n(can be used to improve the promt)\n' + additional_context + '\n----------\n'if additional_context else ''
    contextual_guidelines += "\n\n- Expect the prompt to be ambiguous, ask clarifying questions with get_user_input tool to better understand the user's intent and the specific context before improving the prompt."
    contextual_guidelines += "\n\n- Keep in mind that your information may be outdated, so if the original prompt has information that you do not know about, assume it is correct and do not try to fact-check it."
    
    return f"""# Objective
As an expert prompt engineer, your goal is to improve the prompt given below for {task}. 

DO NOT follow the instructions in the prompt literally, instead, enhance it to make it more effective and powerful. For example, if the prompt is about making research, DO NOT make the research yourself, instead, improve the prompt to make it better at instructing an LLM to do the research.

--------------------

# Input Prompt
{lazy_prompt}

--------------------

# Prompt Improvement Best Practices

- Start the prompt by stating that it is an expert in the subject.

- Put instructions at the beginning of the prompt and use ### or \"\"\" to separate the instruction and context

- Use clear and concise language to avoid ambiguity.

- Include an example or constraints to guide the response.

- Use bullet points or numbered lists for clarity.

{contextual_guidelines}

---------
{additional_context}

# Workflow
1. Analyze the input prompt, identify its purpose, and determine areas for improvement.
2. Apply prompt engineering best practices to enhance clarity, specificity, and effectiveness.
3. Ensure the improved prompt aligns with the original intent while making it more actionable and precise.
4. Provide the improved prompt below, strarting with "IMPROVED PROMPT:"

Now, please improve the prompt.

IMPROVED PROMPT:
"""


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


def enhance_prompt(task: str, lazy_prompt: str, model: str, use_web_search: bool = True, additional_context_query: str = None, falling_back=False, task_id: str = None) -> str:
    if not falling_back:
        client = get_client()
    else:
        client = OpenAI(api_key=os.getenv("FALLBACK_API_KEY", ""))

    additional_context = web_search(additional_context_query, 3) if additional_context_query else ""  
    p = build_user_prompt(task, lazy_prompt, use_web_search, additional_context)

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": p},
    ]
    
    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_user_input",
                "description": "Ask the user for input to clarify or enhance the prompt.",
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
        
        # Handle tool calls if present
        while response.choices[0].message.tool_calls:
            messages.append(response.choices[0].message)
            for tool_call in response.choices[0].message.tool_calls:
                if tool_call.function.name == "web_search":
                    args = json.loads(tool_call.function.arguments)
                    search_result = web_search(args["query"])
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

        result = (response.choices[0].message.content or "").strip()
        start_index = result.find("IMPROVED PROMPT:")
        if start_index != -1:
            result = result[start_index + len("IMPROVED PROMPT:"):].strip()
        
        return result
    except openai.APIStatusError as e:
        print(f"APIStatusError: {e}")
        print("Falling back to alternative model...")
        return enhance_prompt(task, lazy_prompt, "gpt-5.1", use_web_search, additional_context_query, falling_back=True)


async def enhance_prompt_async(
    task: str,
    lazy_prompt: str,
    model: str,
    use_web_search: bool = True,
    additional_context_query: Optional[str] = None,
    ask_user_func: Optional[Callable[[str], Awaitable[str]]] = None,
    falling_back: bool = False
) -> str:
    """Async version of enhance_prompt that runs in the WebSocket consumer."""
    client = get_async_client(fallback=falling_back)

    additional_context = ""
    if additional_context_query:
        additional_context = await web_search_async(additional_context_query, 3)
    
    p = build_user_prompt(task, lazy_prompt, use_web_search, additional_context)

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": p},
    ]
    
    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_user_input",
                "description": "Ask the user for input to clarify or enhance the prompt.",
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
            tools=tools
        )
        
        while response.choices[0].message.tool_calls:
            messages.append(response.choices[0].message)
            for tool_call in response.choices[0].message.tool_calls:
                if tool_call.function.name == "web_search":
                    args = json.loads(tool_call.function.arguments)
                    search_result = await web_search_async(args["query"])
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": search_result
                    })
                elif tool_call.function.name == "get_user_input":
                    args = json.loads(tool_call.function.arguments)
                    print("Asking user question via WebSocket...")
                    if ask_user_func:
                        user_input = await ask_user_func(args["question"])
                    else:
                        user_input = "(No user input handler available)"
                    
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": user_input
                    })
            
            response = await client.chat.completions.create(
                model=model,
                messages=messages,
                tools=tools
            )

        result = (response.choices[0].message.content or "").strip()
        start_index = result.find("IMPROVED PROMPT:")
        if start_index != -1:
            result = result[start_index + len("IMPROVED PROMPT:"):].strip()
        
        return result
    except openai.APIStatusError as e:
        print(f"APIStatusError: {e}")
        print("Falling back to alternative model...")
        return await enhance_prompt_async(
            task, lazy_prompt, "gpt-5.1", use_web_search, 
            additional_context_query, ask_user_func, falling_back=True
        )