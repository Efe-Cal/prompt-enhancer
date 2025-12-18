import os
import json
import uuid
from pathlib import Path
from datetime import datetime, timezone

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


SYSTEM_PROMPT = """Act as an expert Prompt Engineer.
You will be given an initial prompt.
Reason step by step to improve it.
Make sure you produce a ready-to-use prompt."""


def build_user_prompt(task: str, lazy_prompt: str) -> str:
    return f"""# Objective
Your task is to enhance the quality and effectiveness of the prompt provided for the following task: `{task}`.
---

# Prompt to Improve
`{lazy_prompt}`

---

## Best Practices for Prompt Engineering
- Start the prompt by stating that it is an expert in the subject.
- Place all instructions at the very beginning, using clear dividers (e.g., ###) to separate instruction sections from the context.
- Specify the desired context, outcome, length, format, or style with as much detail as can be supported by the source prompt, without adding extra information.


## Workflow
1. Begin with a concise 3-7 bullet checklist summarizing the key conceptual steps you will take to improve the prompt, without delving into specific content.
2. Generate the improved prompt, applying the best practices above.
3. After generating the improved prompt, perform a 1-2 line validation to ensure the revised prompt follows all best practices and constraints. Revise if the validation fails before final output.

---

## Output Instructions
- Output the improved prompt below.
- Place curly braces around sections that need user input.
- Always start your answer with "Improved Prompt:" followed immediately by the improved prompt and no extra commentary.

---

## Output Verbosity
- For all responses, use at most 2 short paragraphs or, if using a bulleted format, no more than 6 concise bullets (1 line each).
- Prioritize providing complete, actionable answers within this length cap.
- If giving updates or supervision on your process, make these updates no longer than 1-2 sentences unless explicitly instructed otherwise.
"""


def enhance_prompt(task: str, lazy_prompt: str, model: str) -> str:
    client = get_client()
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_user_prompt(task, lazy_prompt)},
        ],
        temperature=0.7,
    )

    result = (response.choices[0].message.content or "").strip()
    start_index = result.find("Improved Prompt:")
    if start_index != -1:
        result = result[start_index + len("Improved Prompt:"):].strip()
    
    validation_index = result.find("Validation:")
    if validation_index != -1:
        result = result[:validation_index].strip()
        
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


def main():
    st.set_page_config(page_title="Prompt Enhance", page_icon="🤍", layout="wide")
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
        st.text_input("", key="task", placeholder="Describe the task")

        st.subheader("Your Prompt")
        st.text_area("", key="lazy_prompt", height=220, placeholder="Paste your prompt")

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
                        st.session_state.enhanced = enhance_prompt(task, lazy_prompt, model)
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
