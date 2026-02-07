import os
import json_repair as json
from typing import Callable, Awaitable, Optional

import openai
from dotenv import load_dotenv

from .prompt import build_prompts
from . import log

from .shared_utils import (
    FALLBACK_MODEL,
    get_async_client,
    web_search_async,
    check_hcai_status,
    format_answers_for_llm,
    parse_llm_response
)

load_dotenv()


async def enhance_prompt_async(
    task: str,
    lazy_prompt: str,
    model: str,
    use_web_search: bool = True,
    additional_context_query: Optional[str] = None,
    target_model: str = "gpt-5.1",
    ask_user_func: Optional[Callable[[str], Awaitable[str]]] = None,
    falling_back: bool = False,
    prompt_style: dict | None = None,
    is_reasoning_native: bool = False
) -> tuple[str, bool, list[dict]]:
    """Async version of enhance_prompt that runs in the WebSocket consumer."""
    if not check_hcai_status() and not falling_back:
        log("HCAI service is down, falling back to alternative model...")
        if os.getenv("FALLBACK_API_KEY") and os.getenv("FALLBACK_API_KEY") != "":
            result, _, msgs = await enhance_prompt_async(
                task, lazy_prompt, FALLBACK_MODEL, use_web_search, 
                additional_context_query, target_model, ask_user_func,
                falling_back=True, prompt_style=prompt_style,
                is_reasoning_native=is_reasoning_native
            )
            return result, True, msgs
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
            prompt_style=prompt_style,
            is_reasoning_native=is_reasoning_native
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

        messages.append({"role": "assistant", "content": response.choices[0].message.content})
        
        result = (response.choices[0].message.content or "").strip()
        
        result = parse_llm_response(result)
        
        return result, False, messages
    except openai.APIStatusError as e:
        log(f"APIStatusError: {e}")
        log("Falling back to alternative model...")
        if os.getenv("FALLBACK_API_KEY") and os.getenv("FALLBACK_API_KEY") != "" and not falling_back:
            result, _, msgs = await enhance_prompt_async(
                task, lazy_prompt, FALLBACK_MODEL, use_web_search, 
                additional_context_query, target_model, ask_user_func,
                falling_back=True, prompt_style=prompt_style,
                is_reasoning_native=is_reasoning_native
            )
            return result, True, msgs
        else:
            raise Exception("We are out of money! Please try again later.") from e