"""
Example: How to integrate user questions into your LLM tool calling

This shows how to modify your enhance_prompt function to ask users
questions when the LLM calls a tool that needs user input.
"""

from api.tasks import ask_user_question


def example_tool_with_user_input(task_id: str, query: str) -> str:
    """
    Example tool that asks the user for clarification.
    
    In your actual implementation, you'd modify your tool calling logic
    to use this pattern when the LLM calls a tool that needs user input.
    """
    
    # Ask the user a question
    user_answer = ask_user_question(
        task_id=task_id,
        question=f"The AI wants to search for: '{query}'. Should I proceed with this search, or would you like to modify it?"
    )
    
    # Process the answer
    if user_answer.lower() in ['yes', 'proceed', 'ok']:
        # Continue with original query
        return perform_search(query)
    else:
        # Use the modified query from user
        return perform_search(user_answer)


def perform_search(query: str) -> str:
    """Placeholder for actual search logic"""
    return f"Search results for: {query}"


# ============================================================
# How to integrate into your existing enhance_prompt function
# ============================================================

def enhance_prompt_with_user_input(task_id: str, task: str, lazy_prompt: str, 
                                   model: str, use_web_search: bool = True):
    """
    Modified version of enhance_prompt that can ask user questions.
    """
    from openai import OpenAI
    import os
    import json
    
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    messages = [
        {"role": "system", "content": "You are an expert prompt engineer."},
        {"role": "user", "content": f"Improve this prompt: {lazy_prompt}"},
    ]
    
    # Define a tool that requires user input
    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_user_preference",
                "description": "Ask the user for their preference on how to enhance the prompt",
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
    
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        tools=tools
    )
    
    # Handle tool calls
    while response.choices[0].message.tool_calls:
        messages.append(response.choices[0].message)
        
        for tool_call in response.choices[0].message.tool_calls:
            if tool_call.function.name == "get_user_preference":
                args = json.loads(tool_call.function.arguments)
                
                # ASK USER VIA WEBSOCKET
                user_answer = ask_user_question(
                    task_id=task_id,
                    question=args["question"]
                )
                
                # Add user answer to conversation
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": user_answer
                })
        
        # Continue the conversation
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=tools
        )
    
    return response.choices[0].message.content


# ============================================================
# Example: Adding to an existing tool
# ============================================================

def web_search_with_confirmation(task_id: str, query: str) -> str:
    """
    Example: Modify your existing web_search to ask for confirmation
    """
    
    # Ask user if they want to proceed with this search
    confirmation = ask_user_question(
        task_id=task_id,
        question=f"About to search the web for: '{query}'. Proceed? (yes/no/modify)"
    )
    
    if confirmation.lower() == 'no':
        return "User declined the search."
    elif confirmation.lower() not in ['yes', 'proceed']:
        # User wants to modify the query
        query = confirmation
    
    # Proceed with the actual search
    import requests
    response = requests.get(
        'https://search.hackclub.com/res/v1/web/search',
        params={'q': query}
    )
    
    return response.text
