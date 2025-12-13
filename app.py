import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import os
import json
import uuid
from datetime import datetime, timezone
from openai import OpenAI
from dotenv import load_dotenv
from langdetect import detect, LangDetectException

# Load environment variables
load_dotenv()

class PromptEnhanceApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Prompt Enhance")
        self.root.geometry("900x800")
        self.root.configure(bg="#f5f5f5")
        
        # Initialize OpenAI client with custom base URL
        api_key = os.getenv("OPENAI_API_KEY") or os.getenv("API_KEY") or "your-api-key"
        base_url = os.getenv("OPENAI_BASE_URL") or os.getenv("BASE_URL") or "https://api.openai.com/v1"
        self.model = os.getenv("OPENAI_MODEL") or os.getenv("MODEL") or "gpt-5.1"

        self.storage_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "saved_prompts.json")
        self._saved_prompts_cache = None
        
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url
        )
        
        self.setup_ui()

    def _now_iso(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _safe_load_saved_prompts(self):
        if not os.path.exists(self.storage_path):
            return []
        try:
            with open(self.storage_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                return data
            return []
        except Exception:
            return []

    def _safe_write_saved_prompts(self, prompts):
        tmp_path = self.storage_path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(prompts, f, ensure_ascii=False, indent=2)
        os.replace(tmp_path, self.storage_path)

    def _get_current_output_text(self) -> str:
        # `ScrolledText` is disabled; reading is fine.
        return self.output_text.get("1.0", tk.END).strip()

    def save_current_prompt(self):
        task = self.topic_entry.get().strip()
        lazy_prompt = self.prompt_text.get("1.0", tk.END).strip()
        enhanced = self._get_current_output_text()

        if not task:
            messagebox.showwarning("Missing Input", "Please enter a task before saving.")
            return
        if not lazy_prompt:
            messagebox.showwarning("Missing Input", "Please enter a prompt before saving.")
            return
        if not enhanced or enhanced == "Generating response...":
            if not messagebox.askyesno(
                "No Output",
                "The enhanced prompt output is empty. Save anyway?"
            ):
                return

        entry = {
            "id": str(uuid.uuid4()),
            "created_at": self._now_iso(),
            "task": task,
            "lazy_prompt": lazy_prompt,
            "enhanced_prompt": enhanced,
            "model": self.model,
        }

        prompts = self._safe_load_saved_prompts()
        prompts.insert(0, entry)
        try:
            self._safe_write_saved_prompts(prompts)
            self._saved_prompts_cache = prompts
            messagebox.showinfo("Saved", "Prompt saved to saved_prompts.json")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save prompt: {str(e)}")

    def open_saved_prompts_window(self):
        SavedPromptsWindow(self)
    
    def setup_ui(self):
        # Modern gradient background
        self.root.configure(bg="#0f0f1e")
        
        # Main container with padding
        main_frame = tk.Frame(self.root, bg="#0f0f1e", padx=30, pady=30)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Header with title and subtitle
        header_frame = tk.Frame(main_frame, bg="#0f0f1e")
        header_frame.pack(fill=tk.X, pady=(0, 25))
        
        title_label = tk.Label(
            header_frame,
            text="✨ Prompt Enhance",
            font=("Segoe UI", 28, "bold"),
            bg="#0f0f1e",
            fg="#ffffff"
        )
        title_label.pack(anchor="w")
        
        subtitle_label = tk.Label(
            header_frame,
            text="Transform your ideas into powerful prompts",
            font=("Segoe UI", 11),
            bg="#0f0f1e",
            fg="#8b8b9f"
        )
        subtitle_label.pack(anchor="w", pady=(5, 0))
        
        # Topic Input Section with elegant card design
        topic_card = tk.Frame(main_frame, bg="#1a1a2e", highlightthickness=0)
        topic_card.pack(fill=tk.X, pady=(0, 20))
        
        topic_inner = tk.Frame(topic_card, bg="#1a1a2e")
        topic_inner.pack(fill=tk.X, padx=20, pady=20)
        
        topic_label = tk.Label(
            topic_inner, 
            text="Task / Topic", 
            font=("Segoe UI", 11, "bold"),
            bg="#1a1a2e",
            fg="#a8a8ff",
            anchor="w"
        )
        topic_label.pack(fill=tk.X, pady=(0, 10))
        
        # Custom styled entry with inner frame for rounded effect
        topic_entry_frame = tk.Frame(topic_inner, bg="#252540", highlightthickness=1, highlightbackground="#3d3d5c")
        topic_entry_frame.pack(fill=tk.X)
        
        self.topic_entry = tk.Entry(
            topic_entry_frame,
            font=("Segoe UI", 12),
            relief=tk.FLAT,
            bg="#252540",
            fg="#ffffff",
            insertbackground="#a8a8ff",
            borderwidth=0
        )
        self.topic_entry.pack(fill=tk.X, padx=15, pady=12)
        
        # Prompt Input Section with gradient accent
        prompt_card = tk.Frame(main_frame, bg="#1a1a2e", highlightthickness=0)
        prompt_card.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        prompt_inner = tk.Frame(prompt_card, bg="#1a1a2e")
        prompt_inner.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        prompt_header = tk.Frame(prompt_inner, bg="#1a1a2e")
        prompt_header.pack(fill=tk.X, pady=(0, 10))
        
        prompt_label = tk.Label(
            prompt_header,
            text="Your Prompt",
            font=("Segoe UI", 11, "bold"),
            bg="#1a1a2e",
            fg="#a8a8ff",
            anchor="w"
        )
        prompt_label.pack(side=tk.LEFT)
        
        # Frame for prompt input and send button
        prompt_container = tk.Frame(prompt_inner, bg="#252540", highlightthickness=1, highlightbackground="#3d3d5c")
        prompt_container.pack(fill=tk.BOTH, expand=True)
        
        self.prompt_text = tk.Text(
            prompt_container,
            font=("Segoe UI", 11),
            wrap=tk.WORD,
            relief=tk.FLAT,
            bg="#252540",
            fg="#ffffff",
            insertbackground="#a8a8ff",
            borderwidth=0,
            height=6,
            selectbackground="#3d3d5c",
            selectforeground="#ffffff"
        )
        self.prompt_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=15, pady=12)
        
        # Modern send button with gradient effect
        self.send_button = tk.Button(
            prompt_container,
            text="▶",
            font=("Segoe UI", 18, "bold"),
            bg="#6366f1",
            fg="white",
            relief=tk.FLAT,
            cursor="hand2",
            command=self.send_request,
            width=4,
            height=2,
            activebackground="#4f46e5",
            activeforeground="white",
            borderwidth=0
        )
        self.send_button.pack(side=tk.RIGHT, padx=15, pady=12)
        
        # Add hover effect
        self.send_button.bind("<Enter>", lambda e: self.send_button.config(bg="#4f46e5"))
        self.send_button.bind("<Leave>", lambda e: self.send_button.config(bg="#6366f1"))
        
        # Output Section with elegant styling
        output_card = tk.Frame(main_frame, bg="#1a1a2e", highlightthickness=0)
        output_card.pack(fill=tk.BOTH, expand=True)
        
        output_inner = tk.Frame(output_card, bg="#1a1a2e")
        output_inner.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        output_header = tk.Frame(output_inner, bg="#1a1a2e")
        output_header.pack(fill=tk.X, pady=(0, 10))
        
        output_label = tk.Label(
            output_header,
            text="Enhanced Prompt",
            font=("Segoe UI", 11, "bold"),
            bg="#1a1a2e",
            fg="#a8a8ff",
            anchor="w"
        )
        output_label.pack(side=tk.LEFT)

        # Buttons in header
        self.history_button = tk.Button(
            output_header,
            text="🗂 History",
            font=("Segoe UI", 9, "bold"),
            bg="#0ea5e9",
            fg="white",
            relief=tk.FLAT,
            cursor="hand2",
            command=self.open_saved_prompts_window,
            padx=12,
            pady=6,
            activebackground="#0284c7",
            activeforeground="white",
            borderwidth=0
        )
        self.history_button.pack(side=tk.RIGHT, padx=(10, 0))

        self.save_button = tk.Button(
            output_header,
            text="💾 Save",
            font=("Segoe UI", 9, "bold"),
            bg="#f59e0b",
            fg="white",
            relief=tk.FLAT,
            cursor="hand2",
            command=self.save_current_prompt,
            padx=12,
            pady=6,
            activebackground="#d97706",
            activeforeground="white",
            borderwidth=0
        )
        self.save_button.pack(side=tk.RIGHT, padx=(10, 0))

        self.copy_button = tk.Button(
            output_header,
            text="📋 Copy",
            font=("Segoe UI", 9, "bold"),
            bg="#10b981",
            fg="white",
            relief=tk.FLAT,
            cursor="hand2",
            command=self.copy_output,
            padx=15,
            pady=6,
            activebackground="#059669",
            activeforeground="white",
            borderwidth=0
        )
        self.copy_button.pack(side=tk.RIGHT)
        
        # Add hover effects
        self.copy_button.bind("<Enter>", lambda e: self.copy_button.config(bg="#059669"))
        self.copy_button.bind("<Leave>", lambda e: self.copy_button.config(bg="#10b981"))

        self.save_button.bind("<Enter>", lambda e: self.save_button.config(bg="#d97706"))
        self.save_button.bind("<Leave>", lambda e: self.save_button.config(bg="#f59e0b"))

        self.history_button.bind("<Enter>", lambda e: self.history_button.config(bg="#0284c7"))
        self.history_button.bind("<Leave>", lambda e: self.history_button.config(bg="#0ea5e9"))
        
        output_frame = tk.Frame(output_inner, bg="#252540", highlightthickness=1, highlightbackground="#3d3d5c")
        output_frame.pack(fill=tk.BOTH, expand=True)
        
        self.output_text = scrolledtext.ScrolledText(
            output_frame,
            font=("Segoe UI", 11),
            wrap=tk.WORD,
            relief=tk.FLAT,
            bg="#252540",
            fg="#ffffff",
            state=tk.DISABLED,
            borderwidth=0,
            height=10,
            selectbackground="#3d3d5c",
            selectforeground="#ffffff"
        )
        self.output_text.pack(fill=tk.BOTH, expand=True, padx=15, pady=12)
    
    def send_request(self):
        task = self.topic_entry.get().strip()
        lazy_prompt = self.prompt_text.get("1.0", tk.END).strip()
        
        if not task:
            messagebox.showwarning("Missing Input", "Please enter a task.")
            return
        
        if not lazy_prompt:
            messagebox.showwarning("Missing Input", "Please enter a lazy prompt.")
            return
        
        # Check if inputs are in English
        try:
            task_lang = detect(task)
            if task_lang != 'en':
                messagebox.showwarning("Language Error", "Please enter the task in English.")
                return
        except LangDetectException:
            messagebox.showwarning("Language Error", "Could not detect language for task. Please ensure it's in English.")
            return
        
        try:
            prompt_lang = detect(lazy_prompt)
            if prompt_lang != 'en':
                messagebox.showwarning("Language Error", "Please enter the prompt in English.")
                return
        except LangDetectException:
            messagebox.showwarning("Language Error", "Could not detect language for prompt. Please ensure it's in English.")
            return
        
        # Clear previous output
        self.output_text.config(state=tk.NORMAL)
        self.output_text.delete("1.0", tk.END)
        self.output_text.insert("1.0", "Generating response...\n")
        self.output_text.config(state=tk.DISABLED)
        
        # Update UI
        self.root.update()
        
        try:
            # Make API call to OpenAI
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": f"You are an expert Prompt Writer for Large Language Models."},
                    {"role": "user", "content": f"""Your goal is to improve the prompt given below for {task} :
--------------------

Prompt: {lazy_prompt}

--------------------

Here are several tips on writing great prompts:

-------

Start the prompt by stating that it is an expert in the subject.

Put instructions at the beginning of the prompt and use ### or to separate the instruction and context 

Be specific, descriptive and as detailed as possible about the desired context, outcome, length, format, style, etc 

---------

Here's an example of a great prompt:

As a master YouTube content creator, develop an engaging script that revolves around the theme of "Exploring Ancient Ruins."

Your script should encompass exciting discoveries, historical insights, and a sense of adventure.

Include a mix of on-screen narration, engaging visuals, and possibly interactions with co-hosts or experts.

The script should ideally result in a video of around 10-15 minutes, providing viewers with a captivating journey through the secrets of the past.

Example:

"Welcome back, fellow history enthusiasts, to our channel! Today, we embark on a thrilling expedition..."

-----

Now, improve the prompt.

IMPROVED PROMPT:"""}
                ],
                temperature=0.7
            )
            
            # Extract the response
            result = response.choices[0].message.content
            
            # Display the result
            self.output_text.config(state=tk.NORMAL)
            self.output_text.delete("1.0", tk.END)
            self.output_text.insert("1.0", result)
            self.output_text.config(state=tk.DISABLED)
            
        except Exception as e:
            self.output_text.config(state=tk.NORMAL)
            self.output_text.delete("1.0", tk.END)
            self.output_text.insert("1.0", f"Error: {str(e)}")
            self.output_text.config(state=tk.DISABLED)
            messagebox.showerror("Error", f"Failed to get response: {str(e)}")
    
    def copy_output(self):
        output = self.output_text.get("1.0", tk.END).strip()
        
        if not output:
            messagebox.showinfo("Nothing to Copy", "The output is empty.")
            return
        
        self.root.clipboard_clear()
        self.root.clipboard_append(output)
        messagebox.showinfo("Copied", "Output copied to clipboard!")


class SavedPromptsWindow:
    def __init__(self, app: PromptEnhanceApp):
        self.app = app
        self.window = tk.Toplevel(app.root)
        self.window.title("Saved Prompts")
        self.window.geometry("980x700")
        self.window.configure(bg="#0f0f1e")

        container = tk.Frame(self.window, bg="#0f0f1e", padx=20, pady=20)
        container.pack(fill=tk.BOTH, expand=True)

        header = tk.Frame(container, bg="#0f0f1e")
        header.pack(fill=tk.X)

        title = tk.Label(
            header,
            text="🗂 Saved Prompts",
            font=("Segoe UI", 18, "bold"),
            bg="#0f0f1e",
            fg="#ffffff"
        )
        title.pack(side=tk.LEFT)

        btns = tk.Frame(header, bg="#0f0f1e")
        btns.pack(side=tk.RIGHT)

        self.refresh_btn = tk.Button(
            btns,
            text="⟳ Refresh",
            font=("Segoe UI", 9, "bold"),
            bg="#334155",
            fg="white",
            relief=tk.FLAT,
            cursor="hand2",
            command=self.refresh,
            padx=12,
            pady=6,
            activebackground="#1f2937",
            activeforeground="white",
            borderwidth=0
        )
        self.refresh_btn.pack(side=tk.LEFT, padx=(0, 10))

        self.load_btn = tk.Button(
            btns,
            text="↩ Load",
            font=("Segoe UI", 9, "bold"),
            bg="#10b981",
            fg="white",
            relief=tk.FLAT,
            cursor="hand2",
            command=self.load_selected,
            padx=12,
            pady=6,
            activebackground="#059669",
            activeforeground="white",
            borderwidth=0
        )
        self.load_btn.pack(side=tk.LEFT)

        split = tk.PanedWindow(container, orient=tk.HORIZONTAL, sashwidth=6, bg="#0f0f1e", bd=0, relief=tk.FLAT)
        split.pack(fill=tk.BOTH, expand=True, pady=(15, 0))

        left = tk.Frame(split, bg="#1a1a2e")
        right = tk.Frame(split, bg="#1a1a2e")
        split.add(left, stretch="always")
        split.add(right, stretch="always")

        # List
        list_header = tk.Frame(left, bg="#1a1a2e")
        list_header.pack(fill=tk.X, padx=15, pady=(15, 10))

        tk.Label(
            list_header,
            text="Entries",
            font=("Segoe UI", 11, "bold"),
            bg="#1a1a2e",
            fg="#a8a8ff",
        ).pack(side=tk.LEFT)

        self.count_label = tk.Label(
            list_header,
            text="",
            font=("Segoe UI", 9),
            bg="#1a1a2e",
            fg="#8b8b9f",
        )
        self.count_label.pack(side=tk.RIGHT)

        list_frame = tk.Frame(left, bg="#252540", highlightthickness=1, highlightbackground="#3d3d5c")
        list_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))

        self.listbox = tk.Listbox(
            list_frame,
            font=("Segoe UI", 10),
            bg="#252540",
            fg="#ffffff",
            selectbackground="#3d3d5c",
            selectforeground="#ffffff",
            activestyle="none",
            highlightthickness=0,
            borderwidth=0
        )
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0), pady=10)

        scrollbar = tk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=10, padx=10)
        self.listbox.config(yscrollcommand=scrollbar.set)
        self.listbox.bind("<<ListboxSelect>>", lambda e: self.show_selected())

        # Detail
        detail_header = tk.Frame(right, bg="#1a1a2e")
        detail_header.pack(fill=tk.X, padx=15, pady=(15, 10))

        tk.Label(
            detail_header,
            text="Details",
            font=("Segoe UI", 11, "bold"),
            bg="#1a1a2e",
            fg="#a8a8ff",
        ).pack(side=tk.LEFT)

        self.detail_text = scrolledtext.ScrolledText(
            right,
            font=("Consolas", 10),
            wrap=tk.WORD,
            relief=tk.FLAT,
            bg="#252540",
            fg="#ffffff",
            state=tk.DISABLED,
            borderwidth=0,
            height=10,
            selectbackground="#3d3d5c",
            selectforeground="#ffffff"
        )
        self.detail_text.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))

        self.entries = []
        self.refresh()

    def refresh(self):
        self.entries = self.app._safe_load_saved_prompts()
        self.listbox.delete(0, tk.END)
        for entry in self.entries:
            task = (entry.get("task") or "").strip()
            created = (entry.get("created_at") or "").strip()

            if not task:
                task = "(Untitled task)"

            # Keep list items short: show task as the entry name.
            # Add a small date suffix if available.
            created_short = created.split("T")[0] if created else ""
            label = f"{task} ({created_short})" if created_short else task
            self.listbox.insert(tk.END, label)
        self.count_label.config(text=f"{len(self.entries)} saved")
        self._set_detail("Select an entry to view details.")

    def _set_detail(self, text: str):
        self.detail_text.config(state=tk.NORMAL)
        self.detail_text.delete("1.0", tk.END)
        self.detail_text.insert("1.0", text)
        self.detail_text.config(state=tk.DISABLED)

    def _get_selected_index(self):
        sel = self.listbox.curselection()
        if not sel:
            return None
        return int(sel[0])

    def show_selected(self):
        idx = self._get_selected_index()
        if idx is None:
            return
        entry = self.entries[idx]

        task = (entry.get("task") or "").strip()
        created = (entry.get("created_at") or "").strip()
        model = (entry.get("model") or "").strip()
        lazy = entry.get("lazy_prompt") or ""
        enhanced = entry.get("enhanced_prompt") or ""

        enhanced_preview = enhanced.strip()

        view = (
            f"{task}\n"
            f"{'=' * max(10, len(task))}\n\n"
            f"Created: {created}\n"
            f"Model: {model}\n\n"
            f"LAZY PROMPT\n"
            f"----------\n"
            f"{lazy.strip()}\n\n"
            f"IMPROVED PROMPT\n"
            f"-------------------------------\n"
            f"{enhanced_preview}"
        )
        self._set_detail(view)

    def load_selected(self):
        idx = self._get_selected_index()
        if idx is None:
            messagebox.showinfo("No Selection", "Please select a saved prompt.")
            return
        entry = self.entries[idx]
        self.app.topic_entry.delete(0, tk.END)
        self.app.topic_entry.insert(0, entry.get("task", ""))

        self.app.prompt_text.delete("1.0", tk.END)
        self.app.prompt_text.insert("1.0", entry.get("lazy_prompt", ""))

        self.app.output_text.config(state=tk.NORMAL)
        self.app.output_text.delete("1.0", tk.END)
        self.app.output_text.insert("1.0", entry.get("enhanced_prompt", ""))
        self.app.output_text.config(state=tk.DISABLED)

        self.window.lift()
        self.window.focus_force()
        messagebox.showinfo("Loaded", "Loaded saved prompt into the main window.")

def main():
    root = tk.Tk()
    app = PromptEnhanceApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
