import os
import json_repair as json
from dotenv import load_dotenv

from .prompt import _build_edit_user_prompt, _build_system_prompt
from . import log
import openai

from .shared_utils import (
    PromptConfig,
    get_async_client,
    web_search_async,
    check_hcai_status,
    format_answers_for_llm,
    get_tools,
    FALLBACK_MODEL,
    EnhancedPromptResponse
)

load_dotenv()

async def edit_prompt_async(
    edit_instructions: str,
    current_prompt: str,
    config: PromptConfig,
    enhancement_messages: list[dict],
    falling_back: bool = False,
) -> str | None:
    
    # Check HCAI status before proceeding
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
            result = await edit_prompt_async(
                edit_instructions, current_prompt, fallback_config, enhancement_messages, falling_back=True
            )
            return result
        else:
            raise Exception("We are out of money! Please try again later.")
    
    client = get_async_client(fallback=falling_back)
    
    tools = get_tools(config.use_web_search)
    
    # Best case scenario - we have the messages from the enhancement phase and can just continue the conversation
    if enhancement_messages:
        user_prompt = _build_edit_user_prompt(
            edit_instructions=edit_instructions,
            current_prompt=current_prompt
        )
        messages = enhancement_messages + [{"role": "user", "content": user_prompt}]

    # If we don't have enhancement messages, we need to reconstruct the conversation from scratch
    else:
        system_prompt = _build_system_prompt(use_web_search=config.use_web_search, is_reasoning_native=config.is_reasoning_native, additional_context=None)
        user_prompt = _build_edit_user_prompt(
            edit_instructions=edit_instructions,
            current_prompt=current_prompt
        )
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
    try:
        response = await client.chat.completions.create(
            model=config.model,
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

        messages.append({"role": "assistant", "content": response.choices[0].message.content})
        
        result = (response.choices[0].message.parsed or None)
        
        result = result.improved_prompt if result else None

        return result

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
            result = await edit_prompt_async(
                edit_instructions, current_prompt, fallback_config, messages, falling_back=True
            )
            return result
        else:
            raise Exception("We are out of money! Please try again later.") from e

