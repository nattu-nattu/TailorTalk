"""
Email Collection Node
--------------------
This module uses Groq LLM to naturally and sensitively collect email addresses from users, handling:
- Tone matching (professional/casual)
- Context-sensitive timing
- Trust building (explaining why email is needed)
- Error handling for invalid formats or reluctance

Requires: GROQ_API_KEY (set directly in the code)
"""

import re
import requests
from typing import List, Dict, Any
import os

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"  # Updated endpoint


def generate_email_request_prompt(context: str, communication_style: str = "neutral", previous_attempts: List[str] = None) -> str:
    """
    Generate a natural language prompt to request the user's email address, matching tone and context.
    Args:
        context (str): Current conversation context (why email is needed, what for).
        communication_style (str): Desired tone/style (e.g., 'formal', 'casual').
        previous_attempts (List[str]): Previous user responses to email requests, if any.
    Returns:
        str: Natural language prompt for email collection.
    """
    if previous_attempts is None:
        previous_attempts = []
    prompt = f"""
You are a conversational AI assistant. Craft a natural, trust-building prompt to request the user's email address.
- Match the user's tone: {communication_style}
- Explain why the email is needed: {context}
- If the user has previously declined or provided an invalid email, address their concerns or gently prompt again.
- Be sensitive to privacy and build trust.
Previous attempts: {previous_attempts}
Respond ONLY with a single prompt message in plain text. Do not include any explanation, markdown, or text outside the prompt.
"""
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "llama-3.3-70b-versatile",  # Updated model name
        "messages": [
            {"role": "system", "content": "You are an email collection assistant for calendar booking."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 128,
        "temperature": 0.6
    }
    try:
        response = requests.post(GROQ_API_URL, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        content = result["choices"][0]["message"]["content"]
        # Remove markdown or extra explanation if present
        prompt_msg = content.strip()
        if prompt_msg.startswith("```"):
            prompt_msg = re.sub(r"^```[a-zA-Z]*\\n|```$", "", prompt_msg, flags=re.MULTILINE).strip()
        return prompt_msg
    except Exception as e:
        return f"Groq API request failed or invalid prompt: {str(e)}"


def validate_email_format(email: str) -> bool:
    """
    Validate the format of an email address using regex.
    Args:
        email (str): The email address to validate.
    Returns:
        bool: True if valid, False otherwise.
    """
    pattern = r"^[\w\.-]+@[\w\.-]+\.\w{2,}$"
    return re.match(pattern, email) is not None 