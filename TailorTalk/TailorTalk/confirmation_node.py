"""
Confirmation Handler Node
------------------------
This module uses Groq LLM to interpret user responses during the confirmation phase, handling:
- Partial confirmations (e.g., agreeing to time but requesting duration change)
- Conditional agreements (e.g., "if John can join")
- Implicit feedback (e.g., "that's a bit late for me")
- Multi-step modifications (changing multiple aspects)

Requires: GROQ_API_KEY (set directly in the code)
"""

import requests
from typing import Dict, Any, List
import re
import os
import streamlit as st

GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"  # Updated endpoint


def handle_confirmation_response(user_response: str, booking_proposal: Dict[str, Any], conversation_history: List[Dict[str, str]]) -> Dict[str, Any]:
    """
    Interpret the user's confirmation response and determine next actions.
    Args:
        user_response (str): The user's latest message.
        booking_proposal (Dict[str, Any]): The current booking details proposed to the user.
        conversation_history (List[Dict[str, str]]): List of previous messages (role: 'user'/'assistant', content: str).
    Returns:
        Dict[str, Any]: Structured result with keys:
            - confirmation_status: 'confirmed', 'modified', 'rejected', 'clarification_needed'
            - requested_modifications: dict of changes requested by user
            - implicit_feedback: notes on inferred preferences or concerns
            - next_action: 'book', 'suggest_new', 'ask_clarification', etc.
    """
    prompt = f"""
You are a confirmation handler for a calendar booking agent. Analyze the user's response to the current booking proposal.
- Identify if the user fully confirms, partially confirms, requests modifications, or expresses implicit feedback.
- Handle conditional agreements and multi-step modifications.
- Suggest the appropriate next action (book, suggest new options, ask for clarification, etc.).

Booking proposal: {booking_proposal}
Conversation history: {conversation_history}
User response: {user_response}

Respond ONLY with a valid JSON object with keys: confirmation_status, requested_modifications, implicit_feedback, next_action. Do not include any explanation, markdown, or text outside the JSON.
"""
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "llama-3.3-70b-versatile",  # Updated model name
        "messages": [
            {"role": "system", "content": "You are a confirmation handler for calendar booking."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 512,
        "temperature": 0.2
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
                    return {"error": f"Failed to parse extracted JSON: {str(e2)}", "raw_response": content}
            return {"error": f"Failed to parse LLM response: {str(e)}", "raw_response": content}
    except requests.exceptions.RequestException as e:
        return {"error": f"Groq API request failed: {str(e)}", "raw_response": getattr(e, 'response', None) and e.response.text} 