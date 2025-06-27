"""
Suggestion Generation Node
-------------------------
This module uses Groq LLM to transform technical scheduling data into natural, conversational suggestions that:
- Match the user's communication style (formal, casual, etc.)
- Provide context for suggested slots
- Present multiple options clearly and engagingly
- Maintain conversational flow

Requires: GROQ_API_KEY (set directly in the code)
"""

import requests
import os
import streamlit as st
from typing import List, Dict, Any

GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"  # Updated endpoint


def generate_suggestion_message(available_slots: List[Dict[str, str]], user_preferences: Dict[str, Any], communication_style: str = "neutral", context: str = "") -> str:
    """
    Generate a natural language suggestion message for available slots, matching user tone and context.
    Args:
        available_slots (List[Dict[str, str]]): List of available time slots (dicts with 'start' and 'end').
        user_preferences (Dict[str, Any]): User's scheduling preferences.
        communication_style (str): Desired tone/style (e.g., 'formal', 'casual').
        context (str): Additional context for the meeting or user.
    Returns:
        str: Natural language suggestion message.
    """
    prompt = f"""
    You are a conversational AI assistant for scheduling. Given the following available time slots, user preferences, and communication style, craft a natural, engaging suggestion message.
    - Match the user's tone: {communication_style}
    - Provide context for why certain slots are suggested
    - Present multiple options clearly, but do not overwhelm
    - Keep the conversation flowing naturally
    
    Available slots: {available_slots}
    User preferences: {user_preferences}
    Context: {context}
    
    Respond with a single suggestion message in natural language.
    """
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "llama-3.3-70b-versatile",  # Updated model name
        "messages": [
            {"role": "system", "content": "You are a suggestion generation assistant for calendar booking."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 256,
        "temperature": 0.7
    }
    try:
        response = requests.post(GROQ_API_URL, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        try:
            content = result["choices"][0]["message"]["content"]
            return content.strip()
        except Exception as e:
            return "I'm sorry, I couldn't generate a suggestion at this time."
    except requests.exceptions.RequestException as e:
        return f"Groq API request failed: {str(e)}" 