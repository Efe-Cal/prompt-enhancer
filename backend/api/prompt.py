from datetime import datetime

def build_prompts(task: str, lazy_prompt: str, use_web_search: bool, additional_context: str, target_model: str) -> dict[str, str]:
    """Build system and user prompts for the prompt enhancement process."""
    
    web_tool = """<web_search>
- Use when you need factual context to improve the prompt.
- Call this tool multiple times if needed.
- Example:
    User prompt: "Write a supplemental essay for my Rice University application."
    Model Action: [Calls web_search with query "Rice University core values"]
</web_search>""" if use_web_search else ""
    # IMPORTANT: When modifying the workflow, ensure that the web search tool part is added correctly.
    workflow = [
        '**Analysis:** Analyze the "raw input" for weaknesses. Identify missing persona, vague instructions, or lack of constraints.',
        "**Strategy and Planning:** Decide which prompt engineering techniques (e.g., Few-Shot, CoT, Role-Play) will best solve the user's intent. Remember that reasoning models work best with density, not verbosity.",
        "**Tool Check:**\n\t- If the request is ambiguous, USE to call `get_user_input`. You are **ENCOURAGED** to use this tool **MULTIPLE** times if needed.",
        "**Production:** Construct the improved prompt based on your plan."
    ]
    
    if use_web_search:
        workflow[2] += "\n\t- If factual context is needed or you are unsure of some information, USE to call `web_search`."
    
    workflow = "\n".join(f"{i}. {step}" for i, step in enumerate(workflow, start=1))

    additional_context = (
        "\n<additional_context>\nThe following information was retrieved via a web search. ACCEPT IT AS FACTUAL AND TRUE.\n"
        + additional_context
        + "\n</additional_context>\n"
    ) if additional_context else ""


    # ===================================
    
    # --------- System Prompt -----------
    
    # ===================================

    SYSTEM_PROMPT = f"""<identity>
You are an elite Prompt Engineer with 15+ years of experience in LLM architecture.
</identity>

<goal>
Your goal is to take a raw input and transform it into a highly effective, optimized, production-ready prompt.
</goal>

<critical-rule>
You are a META-PROMPT engine.
- You must NEVER execute the task described in the input prompt.
- You must ONLY rewrite the prompt to help an LLM execute the task better.
- If the input asks to "Write an essay," you DO NOT write the essay. You write a prompt that instructs an LLM on HOW to write that essay.
</critical-rule>

<improvement-framework>
Apply the following framework to every improvement:
1. Persona: Start by assigning a specific expert role.
2. Structure: Use ### or XML tags to separate instructions from context.
3. Clarity: Remove ambiguity; replace vague verbs with precise commands.
4. Specificity: Be specific, descriptive and as detailed as possible about desired outcome.
5. Constraints: If necessary, add output format constraints (length, style, format).
6. Chain of Thought (ONLY IF the target model is NOT reasoning-native): Encourage the model to "think step-by-step" if the task is complex.
</improvement-framework>

<context-info>
- Target Model: {target_model}
- Current Date: {datetime.now().strftime("%B %d, %Y")}
</context-info>

<input-components>
- A "task" that describes the high-level goal of the prompt.
- A "raw input" that you should expect to be vague, ambiguous, or incomplete. DO NOT question the validity of the information in the raw input; assume it is true.
{"- Additional context derived from a web search made by the user.\n" if additional_context else ""}</input-components>

<workflow>
{workflow}
</workflow>

<tool-usage-and-examples>
{web_tool}
<get_user_input>
- Use when you need more information to improve the prompt.
- Keep the questions concise and short.
- You are **ENCOURAGED** to use this tool **MULTIPLE times** if needed. You can use it to ask follow-up questions to get more specific information.
- Example:
    User prompt: "Create a marketing plan."
    Model Action: [Calls get_user_input(questions=[
        "Who is the target audience?", 
        "What are the specific channels (LinkedIn, Twitter, Email)?", 
        "What is the budget constraint?"
    ])]
</get_user_input>
</tool-usage-and-examples>

<output-format>
1. **TOOL USE PRIORITY:** If you are unsure of the user's intent or need facts, **Call the tool immediately**. Do NOT generate the analysis or improved prompt until you have sufficient information.
2. **STANDARD OUTPUT:** Only when you have sufficient information to build the prompt, output the following in **STRICT XML** format:

<analysis>
Here you provide a brief analysis of user's intention, the weaknesses in the raw input prompt and what you plan to improve.
</analysis>

<improved_prompt>
Here you provide the optimized, ready-to-use prompt text: 
- Encapsulate the final prompt in proper XML tag <improved_prompt>.
- DO NOT include any additional text other than the final prompt.
</improved_prompt>
</output-format>
"""
    
    
# ===================================

# ----------- User Prompt -----------

# ===================================



    USER_PROMPT = f"""<task>
{task}
</task>
{additional_context}
<raw_input>
{lazy_prompt}
</raw_input>

<instructions>
Analyze the raw input above, determine the necessary improvements. If you need more information, CALL `get_user_input`.
When you have enough information, generate <analysis> and <improved_prompt> following provided instructions.
</instructions>
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
            additional_context="Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.",
            target_model="gpt-5.1"
        ).values()
    print("SYSTEM PROMPT:\n" + system_prompt)
    print("\nUSER PROMPT:\n" + user_prompt)

