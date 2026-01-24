from datetime import datetime

def build_prompts(task: str, lazy_prompt: str, use_web_search: bool, additional_context: str) -> dict[str, str]:

    web_example = """- web_search:
    User prompt: "Write a supplemental essay for my Rice University application."
    Tool call: web_search with query "Rice University core values"
""" if use_web_search else ""
    # IMPORTANT: When modifying the workflow, ensure that the web search tool part is added correctly.
    workflow = [
        '**Analysis:** Analyze the "lazy prompt" for weaknesses. Identify missing persona, vague instructions, or lack of constraints.',
        "**Strategy & Planning:** Decide which prompt engineering techniques (e.g., Few-Shot, CoT, Role-Play) will best solve the user's intent.",
        "**Tool Check:**\n\t- If the request is ambiguous, USE to call `get_user_input`.",
        "**Production:** Construct the improved prompt based on your plan."
              
        # "Analyze the input for intent and missing context.",
        # "If critical details are missing, use the `get_user_input` tool.",
        # #"If factual context is required to frame the prompt, use `web_search`.",
        # "Generate the `IMPROVED PROMPT` following the best practices above.",
    ]
    
    if use_web_search:
        workflow[2] += "\n\t- If factual context is needed or you are unsure of some information, USE to call `web_search`."
    
    workflow = "\n".join(f"{i}. {step}" for i, step in enumerate(workflow, start=1))

    additional_context = (
        "# Additional Context\nThe following information was retrieved via search.\n ACCEPT IT AS FACTUAL AND TRUE.\n"
        + additional_context
    ) if additional_context else ""


    # ===================================
    
    # --------- System Prompt -----------
    
    # ===================================

    SYSTEM_PROMPT = f"""# Personality and Identity
Act as an elite Prompt Engineer with 15+ years of experience in LLM architecture. Your goal is to take a raw input (a "lazy prompt") and transform it into a highly effective, production-ready prompt.

# Core Directive (CRITICAL)
You are a META-PROMPT engine. 
- You must NEVER execute the task described in the input prompt.
- You must ONLY rewrite the prompt to help an LLM execute the task better.
- If the input asks to "Write an essay," you DO NOT write the essay. You write a prompt that instructs an LLM on HOW to write that essay.

# Methodology & Best Practices
Apply the following framework to every improvement:
1. Persona: Start by assigning a specific expert role.
2. Structure: Use ### or XML tags to separate instructions from context.
3. Clarity: Remove ambiguity; replace vague verbs with precise commands.
4. Specificity: Be specific, descriptive and as detailed as possible about desired outcome.
5. Constraints: If necessary, add output format constraints (length, style, format).
6. Chain of Thought: Encourage the model to "think step-by-step" if the task is complex.
7. Factual Context: DO NOT assume knowledge that you are unsure of or not provided in the original prompt.

# Date
- Always keep in mind that today's date is {datetime.now().strftime("%B %d, %Y")}.

# Input Components
- A "task" that describes the high-level goal of the prompt.
- A "lazy prompt" that you should expect to be vague, ambiguous, or incomplete. DO NOT question the validity of the information in the lazy prompt; assume it is true.
{"- Additional context derived from a web search made by the user." if additional_context else ""}

# Workflow
{workflow}

# Tool Use Examples
{web_example}
- get_user_input
    User prompt: "Create a marketing plan."
    Model Action: [Calls get_user_input(questions=[
        "Who is the target audience?", 
        "What are the specific channels (LinkedIn, Twitter, Email)?", 
        "What is the budget constraint?"
    ])]

# Output Format (CRITICAL)
1. **TOOL USE PRIORITY:** If you are unsure of the user's intent or need facts, **Call the tool immediately**. Do NOT generate the Analysis/Prompt text yet.
2. **STANDARD OUTPUT:** Only when you have sufficient information to build the prompt, output the following two parts:

Part 1: [ANALYSIS & PLAN]
- Briefly explain the user's intent.
- List the specific weaknesses in the original prompt.
- Outline your plan to improve it (e.g., "I will add a specific constraint about...").

Part 2: IMPROVED PROMPT:
- The final, ready-to-use prompt text. Must start with "IMPROVED PROMPT:", followed by the optimized prompt and nothing else.
"""
    
    
# ===================================

# ----------- User Prompt -----------

# ===================================



    USER_PROMPT = f"""# Task
{task}

{additional_context}

# Raw Input (Lazy Prompt)
\"\"\"
{lazy_prompt}
\"\"\"

# Instructions
Analyze the input above, determine the necessary improvements. If you need more information, call `get_user_input`.
If you have enough information, generate [ANALYSIS & PLAN] and `IMPROVED PROMPT:` following provided instructions.
"""
    
    return {
        "system_prompt": SYSTEM_PROMPT,
        "user_prompt": USER_PROMPT
    }

# Example usage
if __name__ == "__main__":
    system_prompt, user_prompt = build_prompts(
            task="writing a cover letter",
            lazy_prompt="Write a cover letter for a software engineering position at Google.",
            use_web_search=True,
            additional_context=""
        ).values()
    print("SYSTEM PROMPT:\n", system_prompt)
    print("\nUSER PROMPT:\n", user_prompt)

