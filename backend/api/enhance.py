import os
import json_repair as json

import openai
from dotenv import load_dotenv

from .prompt import build_enhancement_prompts
from . import log

from .shared_utils import (
    FALLBACK_MODEL,
    EnhancedPromptResponse,
    PromptConfig,
    get_async_client,
    parse_llm_response_XML,
    parse_llm_response_markdown,
    web_search_async,
    check_hcai_status,
    format_answers_for_llm,
    get_tools
)

load_dotenv()


async def enhance_prompt_async(
    task: str,
    lazy_prompt: str,
    config: PromptConfig,
    falling_back: bool = False,
) -> tuple[str, bool, list[dict]]:
    """Async version of enhance_prompt that runs in the WebSocket consumer."""
    if not check_hcai_status() and not falling_back:
        log("HCAI service is down, falling back to alternative model...")
        if os.getenv("FALLBACK_API_KEY") and os.getenv("FALLBACK_API_KEY") != "":
            fallback_config = PromptConfig(
                model=FALLBACK_MODEL,
                use_web_search=config.use_web_search,
                additional_context_query=config.additional_context_query,
                target_model=config.target_model,
                ask_user_func=config.ask_user_func,
                prompt_style=config.prompt_style,
                is_reasoning_native=config.is_reasoning_native,
            )
            result, _, msgs = await enhance_prompt_async(
                task, lazy_prompt, fallback_config, falling_back=True
            )
            return result, True, msgs
        else:
            raise Exception("We are out of money! Please try again later.")    
    
    client = get_async_client(fallback=falling_back)

    additional_context = ""
    if config.additional_context_query:
        additional_context = await web_search_async(config.additional_context_query, 3)
    
    system_prompt, user_prompt = build_enhancement_prompts(
            task=task,
            lazy_prompt=lazy_prompt,
            use_web_search=config.use_web_search,
            additional_context=additional_context,
            target_model=config.target_model,
            prompt_style=config.prompt_style,
            is_reasoning_native=config.is_reasoning_native
        ).values()

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
    
    tools = get_tools(config.use_web_search)
    
    try:
        response = await client.chat.completions.create(
            model=config.model,
            messages=messages,
            tools=tools,
            reasoning_effort="medium",
        )
        log(f"[DEBUG] Initial LLM Response (Async): {response.choices[0].message}")
        
        count = 1
        while (response.choices[0].message.tool_calls
               or (response.choices[0].message.content.strip() == "" and
                    not response.choices[0].message.tool_calls)) and count <= 6:
            messages.append(response.choices[0].message)
            if not response.choices[0].message.tool_calls:
                log(f"[DEBUG] LLM response has no tool calls but content is empty.")
                break
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
                    if config.ask_user_func:
                        user_input = await config.ask_user_func(args["questions"])
                    else:
                        user_input = "(No user input handler available)"
                    
                    user_input = format_answers_for_llm(args["questions"], user_input)
                    
                    log(f"[DEBUG] Tool Result ({tool_call.function.name}): {user_input}")

                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": user_input
                    })

            response = await client.chat.completions.parse(
                model=config.model,
                messages=messages,
                tools=tools,
                reasoning_effort="medium",
                response_format=EnhancedPromptResponse,
            )
            log(f"[DEBUG] Next LLM Response (Async): {response.choices[0].message}")
            count += 1

        messages.append({"role": "assistant", "content": response.choices[0].message.content})
        
        if hasattr(response.choices[0].message, "parsed") and response.choices[0].message.parsed:
            result = (response.choices[0].message.parsed or None)
            result = result.improved_prompt if result else None
        else:
            log(f"[DEBUG] No parsed content in LLM response")
            try:
                result = json.loads(response.choices[0].message.content)
                if "improved_prompt" in result:
                    result = result["improved_prompt"]
                else: raise ValueError("No 'improved_prompt' key in JSON response")
            except Exception as e:
                log(f"[ERROR] Failed to repair JSON in LLM response. Trying XML. Error: {e}")
                result = parse_llm_response_XML(response.choices[0].message.content)
                if not result:
                    log(f"[ERROR] Failed to parse XML in LLM response. Using markdown parsing")
                    result = parse_llm_response_markdown(response.choices[0].message.content)
                    
                    
        return result, False, messages


    except openai.APIStatusError as e:
        log(f"APIStatusError: {e}")
        log("Falling back to alternative model...")
        if os.getenv("FALLBACK_API_KEY") and os.getenv("FALLBACK_API_KEY") != "" and not falling_back:
            fallback_config = PromptConfig(
                model=FALLBACK_MODEL,
                use_web_search=config.use_web_search,
                additional_context_query=config.additional_context_query,
                target_model=config.target_model,
                ask_user_func=config.ask_user_func,
                prompt_style=config.prompt_style,
                is_reasoning_native=config.is_reasoning_native,
            )
            result, _, msgs = await enhance_prompt_async(
                task, lazy_prompt, fallback_config, falling_back=True
            )
            return result, True, msgs
        else:
            raise Exception("We are out of money! Please try again later.") from e