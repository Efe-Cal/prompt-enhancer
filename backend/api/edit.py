import os
import time
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
    
    t_start = time.perf_counter()
    timings: list[tuple[str, float]] = []

    def _mark(label: str):
        timings.append((label, time.perf_counter() - t_start))
        log(f"[TIMING] {label}: {timings[-1][1]:.3f}s elapsed")

    _mark("edit_start")

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

    _mark("hcai_check_done")
    
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

    _mark("messages_built")
        
    try:
        _mark("llm_call_1_start")
        response = await client.chat.completions.parse(
            model=config.model,
            messages=messages,
            tools=tools,
            reasoning_effort="low",
            response_format=EnhancedPromptResponse,
        )
        _mark("llm_call_1_done")
        log(f"[DEBUG] Initial LLM Response (Async): {response.choices[0].message}")
        
        count = 1
        while response.choices[0].message.tool_calls:
            messages.append(response.choices[0].message)
            for tool_call in response.choices[0].message.tool_calls:
                log(f"[DEBUG] Processing Tool Call (Async): {tool_call.function.name} with args: {tool_call.function.arguments}")
                if tool_call.function.name == "web_search":
                    _mark(f"tool_web_search_{count}_start")
                    args = json.loads(tool_call.function.arguments)
                    search_result = await web_search_async(args["query"])
                    _mark(f"tool_web_search_{count}_done")
                    log(f"[DEBUG] Tool Result ({tool_call.function.name}): {search_result[:100]}...")
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": search_result
                    })
                elif tool_call.function.name == "get_user_input":
                    _mark(f"tool_get_user_input_{count}_start")
                    args = json.loads(tool_call.function.arguments)
                    log("Asking user question via WebSocket...")
                    if config.ask_user_func:
                        user_input = await config.ask_user_func(args["questions"])
                    else:
                        user_input = "(No user input handler available)"
                    
                    user_input = format_answers_for_llm(args["questions"], user_input)
                    _mark(f"tool_get_user_input_{count}_done")
                    
                    log(f"[DEBUG] Tool Result ({tool_call.function.name}): {user_input}")

                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": user_input
                    })

            _mark(f"llm_call_{count + 1}_start")
            response = await client.chat.completions.parse(
                model=config.model,
                messages=messages,
                tools=tools,
                reasoning_effort="medium",
                response_format=EnhancedPromptResponse,
            )
            _mark(f"llm_call_{count + 1}_done")
            log(f"[DEBUG] Next LLM Response (Async): {response.choices[0].message}")
            count += 1

        messages.append({"role": "assistant", "content": response.choices[0].message.content})
        
        _mark("parsing_response_start")
        result = (response.choices[0].message.parsed or None)
        
        result = result.improved_prompt if result else None

        _mark("edit_complete")
        log(f"[TIMING] === Edit Timing Summary ===")
        prev = 0.0
        for label, elapsed in timings:
            delta = elapsed - prev
            log(f"[TIMING]   {label}: {elapsed:.3f}s total, +{delta:.3f}s step")
            prev = elapsed
        log(f"[TIMING] === Total: {timings[-1][1]:.3f}s ===")

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

