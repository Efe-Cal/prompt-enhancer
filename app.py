import os
import json
import uuid
from pathlib import Path
from datetime import datetime, timezone
import unicodedata
import re

import requests
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()


APP_DIR = Path(__file__).resolve().parent
STORAGE_PATH = APP_DIR / "saved_prompts.json"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def safe_load_saved_prompts():
    if not STORAGE_PATH.exists():
        return []
    try:
        data = json.loads(STORAGE_PATH.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except Exception:
        return []


def safe_write_saved_prompts(prompts):
    tmp_path = STORAGE_PATH.with_suffix(STORAGE_PATH.suffix + ".tmp")
    tmp_path.write_text(json.dumps(prompts, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp_path, STORAGE_PATH)


@st.cache_resource
def get_client():
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("API_KEY") or ""
    base_url = os.getenv("OPENAI_BASE_URL") or os.getenv("BASE_URL") or "https://api.openai.com/v1"
    return OpenAI(api_key=api_key, base_url=base_url)


def get_model() -> str:
    return os.getenv("OPENAI_MODEL") or os.getenv("MODEL") or "gpt-5.1"


SYSTEM_PROMPT = """Act as an expert Prompt Engineer. You will be given an initial prompt to improve. Make sure you produce a ready-to-use prompt."""


def build_user_prompt(task: str, lazy_prompt: str, use_web_search:bool, additional_context: str) -> str:
    contextual_guidelines = "- Be specific, descriptive and as detailed as possible about the desired context, outcome, length, format, etc\n\nAlways use the web_search tool to look up any relevant information on the web to include in the improved prompt as context. (if needed today's date is " + datetime.now().strftime("%B %d, %Y")+")" if use_web_search else "- Be specific, but only provide instructions with limited context. DO NOT include any specific information that may be outdated or incorrect."
    additional_context = "-"*10+'\n'+'# Additional Context from Web Search\n(can be used to improve the promt)\n' + additional_context + '\n'+'-'*10 if additional_context else ''


    return f"""# Objective
As an expert prompt engineer, your goal is to improve the prompt given below for {task}. 

DO NOT follow the instructions in the prompt literally, instead, enhance it to make it more effective and powerful. For example, if the prompt is about making research, DO NOT make the research yourself, instead, improve the prompt to make it better at instructing an LLM to do the research.

--------------------

# Input Prompt
{lazy_prompt}

--------------------

{additional_context}

# Prompt Improvement Best Practices

- Start the prompt by stating that it is an expert in the subject.

- Put instructions at the beginning of the prompt and use ### or \"\"\" to separate the instruction and context

- Use clear and concise language to avoid ambiguity.

- Include an example or constraints to guide the response.

- Use bullet points or numbered lists for clarity.

{contextual_guidelines}

---------

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
    response = requests.get(
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


def enhance_prompt(task: str, lazy_prompt: str, model: str, use_web_search: bool = True, additional_context: str = None) -> str:
    client = get_client()
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": build_user_prompt(task, lazy_prompt, use_web_search, additional_context)},
    ]
    
    tools = None
    if use_web_search:
        tools = [
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
    
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        tools=tools
    )
    
    # Handle tool calls if present
    while use_web_search and response.choices[0].message.tool_calls:
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


def save_entry(task: str, lazy_prompt: str, enhanced: str, model: str):
    if not task.strip():
        raise ValueError("Please enter a task before saving.")
    if not lazy_prompt.strip():
        raise ValueError("Please enter a prompt before saving.")

    entry = {
        "id": str(uuid.uuid4()),
        "created_at": now_iso(),
        "task": task.strip(),
        "lazy_prompt": lazy_prompt.strip(),
        "enhanced_prompt": (enhanced or "").strip(),
        "model": model,
    }
    prompts = safe_load_saved_prompts()
    prompts.insert(0, entry)
    safe_write_saved_prompts(prompts)


def format_entry_label(entry: dict) -> str:
    task = (entry.get("task") or "").strip() or "(Untitled task)"
    created = (entry.get("created_at") or "").strip()
    created_short = created.split("T")[0] if created else ""
    return f"{task} ({created_short})" if created_short else task


def format_entry_detail(entry: dict) -> str:
    task = (entry.get("task") or "").strip()
    created = (entry.get("created_at") or "").strip()
    model = (entry.get("model") or "").strip()
    lazy = entry.get("lazy_prompt") or ""
    enhanced = entry.get("enhanced_prompt") or ""

    title_line = task or "(Untitled task)"
    return (
        f"{title_line}\n"
        f"{'=' * max(10, len(title_line))}\n\n"
        f"Created: {created}\n"
        f"Model: {model}\n\n"
        f"LAZY PROMPT\n"
        f"----------\n"
        f"{lazy.strip()}\n\n"
        f"IMPROVED PROMPT\n"
        f"-------------------------------\n"
        f"{enhanced.strip()}"
    )


def ensure_state():
    st.session_state.setdefault("task", "")
    st.session_state.setdefault("lazy_prompt", "")
    st.session_state.setdefault("enhanced", "")
    st.session_state.setdefault("history_refresh_token", 0)
    st.session_state.setdefault("selected_history_id", None)
    st.session_state.setdefault("use_web_search", True)
    st.session_state.setdefault("specific_search", "")


def main():
    st.set_page_config(page_title="Prompt Enhance", page_icon="📝", layout="wide")
    ensure_state()

    st.markdown(
        """
        <style>
        .block-container { padding-top: 2rem; padding-bottom: 2rem; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    model = get_model()

    st.title("Prompt Enhance")
    st.caption("Transform your ideas into powerful prompts")

    with st.sidebar:
        st.subheader("History")
        st.caption("Saved prompts are stored in saved_prompts.json")

        if st.button("Refresh", use_container_width=True):
            st.session_state.history_refresh_token += 1

        entries = safe_load_saved_prompts()
        entry_by_id = {e.get("id"): e for e in entries if isinstance(e, dict) and e.get("id")}
        labels = [(e.get("id"), format_entry_label(e)) for e in entries if isinstance(e, dict) and e.get("id")]

        if labels:
            options = [x[0] for x in labels]
            format_func = lambda _id: dict(labels).get(_id, "(Unknown)")
            selected_id = st.selectbox(
                "Saved entries",
                options=options,
                format_func=format_func,
                index=0,
            )

            cols = st.columns(2)
            with cols[0]:
                if st.button("Load", use_container_width=True):
                    entry = entry_by_id.get(selected_id)
                    if entry:
                        st.session_state.task = entry.get("task", "")
                        st.session_state.lazy_prompt = entry.get("lazy_prompt", "")
                        st.session_state.enhanced = entry.get("enhanced_prompt", "")
                        st.success("Loaded into the editor")
            with cols[1]:
                st.write(f"{len(entries)} saved")

            with st.expander("Details", expanded=False):
                entry = entry_by_id.get(selected_id)
                if entry:
                    st.code(format_entry_detail(entry))
        else:
            st.info("No saved prompts yet.")

    col_left, col_right = st.columns([1, 1])

    with col_left:
        st.subheader("Task / Topic")
        st.text_input("Task", key="task", placeholder="Describe the task", label_visibility="collapsed")

        st.subheader("Your Prompt")
        st.text_area("Prompt", key="lazy_prompt", height=220, placeholder="Paste your prompt", label_visibility="collapsed")

        st.checkbox("Use web search for context", key="use_web_search", help="Enable web search to gather relevant information for prompt enhancement")

        st.text_input("Specific Search", key="specific_search", placeholder="Optional specific search query", label_visibility="collapsed")
        
        action_cols = st.columns([1, 1, 2])
        with action_cols[0]:
            enhance_clicked = st.button("Enhance", type="primary", use_container_width=True)
        with action_cols[1]:
            save_clicked = st.button("Save", use_container_width=True)
        with action_cols[2]:
            st.caption(f"Model: {model}")

        if enhance_clicked:
            task = (st.session_state.task or "").strip()
            lazy_prompt = (st.session_state.lazy_prompt or "").strip()
            if not task:
                st.warning("Please enter a task.")
            elif not lazy_prompt:
                st.warning("Please enter a lazy prompt.")
            else:
                with st.spinner("Generating response..."):
                    try:
                        search_results = None
                        if st.session_state.specific_search.strip():
                            search_results = web_search(st.session_state.specific_search.strip(), n=5)
                        st.session_state.enhanced = enhance_prompt(
                            task, lazy_prompt, model, st.session_state.use_web_search, search_results if st.session_state.specific_search.strip() else None
                        )
                        st.success("Done")
                    except ValueError as ve:
                        st.warning(str(ve))
                    except Exception as e:
                        st.error(f"Failed to get response: {str(e)}")

        if save_clicked:
            try:
                save_entry(
                    st.session_state.task,
                    st.session_state.lazy_prompt,
                    st.session_state.enhanced,
                    model,
                )
                st.success("Saved to saved_prompts.json")
            except Exception as e:
                st.error(f"Failed to save prompt: {str(e)}")

    with col_right:
        st.subheader("Enhanced Prompt")
        if (st.session_state.enhanced or "").strip():
            st.code(st.session_state.enhanced)
            st.caption("Tip: Use the copy icon in the top-right of the code block.")
        else:
            st.info("Your enhanced prompt will appear here.")


if __name__ == "__main__":
    main()
