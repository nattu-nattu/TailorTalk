"""
Detail Extraction Node
---------------------
This module uses Groq LLM to extract structured information from user input and conversation history, including:
- Temporal resolution (converting relative times to absolute datetimes)
- Ambiguity resolution (context-dependent meanings)
- Incomplete information detection (what's missing)
- Multi-turn assembly (combining details from conversation turns)

Requires: GROQ_API_KEY (set directly in the code)
"""

import requests
from typing import Dict, Any, List
import re
import os

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"  # Updated endpoint


def extract_details(user_input: str, conversation_history: List[Dict[str, str]]) -> Dict[str, Any]:
    """
    Extract structured details (date, time, duration, participants, etc.) from user input and conversation history.
    Args:
        user_input (str): The latest message from the user.
        conversation_history (List[Dict[str, str]]): List of previous messages (role: 'user'/'assistant', content: str).
    Returns:
        Dict[str, Any]: Structured result with extracted details, missing info, and ambiguity notes.
    """
    prompt = f"""
    You are an expert assistant for a calendar booking agent. Analyze the following conversation and the latest user message.
    Extract the following as a JSON object:
    - date (absolute, e.g., 2024-06-10)
    - time (24h format, e.g., 15:00)
    - duration (in minutes)
    - participants (list of names or emails, if any)
    - location (if mentioned)
    - missing_info (list of required details not provided)
    - ambiguity_notes (list of ambiguities or context-dependent meanings)
    - context_assembly (summary of how details were gathered across turns)
    
    Handle complex temporal expressions (e.g., "next Friday after the holiday", "before my lunch meeting").
    Infer missing information if possible, and note any assumptions.
    
    Conversation history:
    {conversation_history}
    
    Latest user message:
    {user_input}
    
    Respond ONLY with a valid JSON object with the keys above. Do not include any explanation, markdown, or text outside the JSON.
    """

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "llama-3.3-70b-versatile",  # Updated model name
        "messages": [
            {"role": "system", "content": "You are a detail extraction assistant for calendar booking."},
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