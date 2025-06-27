"""
Notification Node
----------------
This module manages email composition, template personalization, and follow-up communication for calendar events.
- Uses Groq LLM to personalize email content and adapt templates
- Handles confirmation, reminder, and follow-up notifications
- Uses MailerSend (mailsender) API for real email sending

Requires: MailerSend API key and sender email (set directly in the code)
Optionally: GROQ_API_KEY (set directly in the code) for LLM-based personalization
"""

import requests
from typing import Dict, Any, Optional
import re
from mailersend import emails
import streamlit as st
import os

GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"  # Updated endpoint

# MailerSend configuration
MAILERSEND_API_KEY = st.secrets["MAILERSEND_API_KEY"]
MAILERSEND_SENDER_NAME = "TailorTalk Bot"
MAILERSEND_SENDER_EMAIL = st.secrets["MAILERSEND_SENDER_EMAIL"]

# Real email sending implementation using MailerSend

def send_email(to_email: str, subject: str, body: str, recipient_name: str = "User", reply_to: Optional[dict] = None) -> tuple:
    """
    Send an email using MailerSend.
    Args:
        to_email (str): Recipient's email address.
        subject (str): Email subject.
        body (str): Email body (plain text and HTML).
        recipient_name (str): Recipient's real name for personalization.
        reply_to (dict, optional): Reply-to dict with 'name' and 'email'.
    Returns:
        tuple: (success: bool, status: int, data: dict, error_message: str)
    """
    mailer = emails.NewEmail(MAILERSEND_API_KEY)
    mail_body = {}
    mail_from = {
        "name": MAILERSEND_SENDER_NAME,
        "email": MAILERSEND_SENDER_EMAIL,
    }
    recipients = [
        {
            "name": recipient_name,
            "email": to_email,
        }
    ]
    mailer.set_mail_from(mail_from, mail_body)
    mailer.set_mail_to(recipients, mail_body)
    mailer.set_subject(subject, mail_body)
    mailer.set_plaintext_content(body, mail_body)
    mailer.set_html_content(f"<p>{body}</p>", mail_body)
    if reply_to and isinstance(reply_to, dict) and reply_to:
        mailer.set_reply_to(reply_to, mail_body)
    try:
        status, data = mailer.send(mail_body)
        st.sidebar.write(f"[MailerSend] Status: {status}")
        st.sidebar.write(f"[MailerSend] Data: {data}")
        error_message = None
        if isinstance(data, dict) and 'message' in data:
            st.sidebar.write(f"[MailerSend] Error Message: {data.get('message')}")
            error_message = data.get('message')
        elif isinstance(data, str):
            st.sidebar.write(f"[MailerSend] Response: {data}")
            error_message = data if status != 202 else None
        return (status == 202, status, data, error_message)
    except Exception as e:
        st.sidebar.write(f"[MailerSend] Exception: {e}")
        return (False, None, None, str(e))


def generate_notification_email(event_details: Dict[str, Any], notification_type: str = "confirmation", communication_style: str = "neutral", user_name: str = "User") -> Dict[str, str]:
    """
    Use Groq LLM to generate a personalized notification email (subject and body).
    Args:
        event_details (Dict[str, Any]): Details of the event (date, time, location, etc.)
        notification_type (str): Type of notification ('confirmation', 'reminder', 'followup')
        communication_style (str): Desired tone/style (e.g., 'formal', 'casual').
        user_name (str): Name of the recipient for personalization.
    Returns:
        Dict[str, str]: {'subject': ..., 'body': ...}
    """
    prompt = f"""
You are an AI assistant for calendar notifications. Compose a {notification_type} email for the following event:
Event details: {event_details}
Recipient name: {user_name}
Tone: {communication_style}
- Personalize the content and adapt the template to the context.
- For reminders/follow-ups, include appropriate timing and call to action.
Respond ONLY with a valid JSON object with keys: subject, body. Do not include any explanation, markdown, or text outside the JSON.
"""
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "llama-3.3-70b-versatile",  # Updated model name
        "messages": [
            {"role": "system", "content": "You are a notification email assistant for calendar events."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 256,
        "temperature": 0.5
    }
    try:
        response = requests.post(GROQ_API_URL, headers=headers, json=data)
        response.raise_for_status()
        import json as pyjson
        result = response.json()
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
                    return {"subject": "Notification", "body": f"Failed to parse extracted JSON: {str(e2)}"}
            return {"subject": "Notification", "body": f"Failed to parse LLM response: {str(e)}"}
    except requests.exceptions.RequestException as e:
        return {"subject": "Notification", "body": f"Groq API request failed: {str(e)}"} 