"""
Intent Recognition Node
----------------------
This module uses Groq LLM to analyze user input and conversation history to determine:
- Primary intent (booking, question, complaint, casual, etc.)
- Confidence in the detected intent
- Communication style (formal, casual, urgent, etc.)
- Context integration (relation to previous turns)

Requires: GROQ_API_KEY (set directly in the code)
"""

import requests
from typing import Dict, Any, List
import re
import os
import streamlit as st

GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"  # Updated endpoint


def analyze_intent(user_input: str, conversation_history: List[Dict[str, str]]) -> Dict[str, Any]:
    """
    Analyze user input and conversation history to extract intent, confidence, style, and context.
    Args:
        user_input (str): The latest message from the user.
        conversation_history (List[Dict[str, str]]): List of previous messages (role: 'user'/'assistant', content: str).
    Returns:
        Dict[str, Any]: Structured result with intent, confidence, style, and context summary.
    """
    prompt = f"""
    You are an AI assistant for a calendar booking agent. Analyze the following conversation and the latest user message.
    For the latest user message, provide:
    - Primary intent (booking, question, complaint, casual, etc.)
    - Confidence (0-1)
    - Communication style (formal, casual, urgent, frustrated, etc.)
    - Context summary (how this message relates to previous turns)
    
    Conversation history:
    {conversation_history}
    
    Latest user message:
    {user_input}
    
    Respond ONLY with a valid JSON object with keys: intent, confidence, style, context_summary.
    Do not include any explanation, markdown, or text outside the JSON.
    """

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "llama-3.3-70b-versatile",  # Updated model name
        "messages": [
            {"role": "system", "content": "You are a helpful assistant for intent recognition."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 512,
        "temperature": 0.2
    }

    try:
        response = requests.post(GROQ_API_URL, headers=headers, json=data)
        print("Groq API response:", response.status_code, response.text)  # Debug print
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