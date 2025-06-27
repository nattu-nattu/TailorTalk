"""
Router Node
-----------
This module uses Groq LLM to manage intelligent conversation flow, acting as the "conductor" for the booking agent.
- Decides the next node/action based on conversation state, user intent, and extracted details
- Handles interruptions, modifications, user emotions, errors, and multi-meeting scenarios

Requires: GROQ_API_KEY (set directly in the code)
"""

import requests
from typing import Dict, Any, List
import re
import os

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"  # Updated endpoint


def route_conversation(conversation_state: Dict[str, Any], user_intent: str, extracted_details: Dict[str, Any], conversation_history: List[Dict[str, str]]) -> Dict[str, Any]:
    """
    Decide the next node/action for the conversation based on current state, intent, and details.
    Args:
        conversation_state (Dict[str, Any]): Current state of the conversation (e.g., which node, what info collected).
        user_intent (str): Detected user intent.
        extracted_details (Dict[str, Any]): Structured details extracted from user input.
        conversation_history (List[Dict[str, str]]): List of previous messages (role: 'user'/'assistant', content: str).
    Returns:
        Dict[str, Any]: Routing decision with keys:
            - next_node: Name of the next node to activate
            - reason: Explanation for the routing decision
            - additional_actions: List of any extra actions to take (optional)
    """
    prompt = f"""
    You are a conversation router for a calendar booking agent. Analyze the current conversation state, user intent, extracted details, and conversation history. Decide the most appropriate next node or action to keep the conversation smooth and helpful.
    - Handle interruptions (e.g., user asks a question mid-booking)
    - Allow modifications after confirmation
    - Address user frustration or confusion
    - Explain errors if needed
    - Support booking multiple meetings in one conversation
    
    Conversation state: {conversation_state}
    User intent: {user_intent}
    Extracted details: {extracted_details}
    Conversation history: {conversation_history}
    
    Respond ONLY with a valid JSON object with keys: next_node, reason, additional_actions. Do not include any explanation, markdown, or text outside the JSON.
    """
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "llama-3.3-70b-versatile",  # Updated model name
        "messages": [
            {"role": "system", "content": "You are a conversation router for a calendar booking agent."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 256,
        "temperature": 0.3
    }
    try:
        response = requests.post(GROQ_API_URL, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        import json as pyjson
        try:
            content = result["choices"][0]["message"]["content"]
            parsed = pyjson.loads(content)
            return parsed
        except Exception as e:
            # Try to extract JSON substring
            match = re.search(r'\{.*\}', content, re.DOTALL)
            if match:
                try:
                    parsed = pyjson.loads(match.group(0))
                    return parsed
                except Exception as e2:
                    return {"next_node": "end", "reason": f"Failed to parse extracted JSON: {str(e2)}", "additional_actions": []}
            return {"next_node": "end", "reason": f"Failed to parse LLM response: {str(e)}", "additional_actions": []}
    except requests.exceptions.RequestException as e:
        return {"next_node": "end", "reason": f"Groq API request failed: {str(e)}", "additional_actions": []} 