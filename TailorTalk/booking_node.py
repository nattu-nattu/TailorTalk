"""
Booking Execution Node
---------------------
This module handles the technical aspects of booking calendar events, sending invitations, and managing the booking transaction.
- Core booking is API-driven (Google Calendar integration placeholder)
- Groq LLM is used for user-friendly error and success messages

Requires: Google Calendar API credentials (to be configured)
Optionally: GROQ_API_KEY (set directly in the code) for LLM-based communication
"""

import requests
from typing import Dict, Any
import re
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pickle
import os
import datetime

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"  # Updated endpoint

SCOPES = ['https://www.googleapis.com/auth/calendar']
TOKEN_PATH = 'token.pickle'
CREDENTIALS_PATH = 'credentials.json'

def get_calendar_service():
    """
    Authenticate and return the Google Calendar API service.
    """
    creds = None
    if os.path.exists(TOKEN_PATH):
        with open(TOKEN_PATH, 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_PATH, 'wb') as token:
            pickle.dump(creds, token)
    service = build('calendar', 'v3', credentials=creds)
    return service


def book_calendar_event(event_details: Dict[str, Any]) -> Dict[str, Any]:
    """
    Book a calendar event using Google Calendar API.
    Args:
        event_details (Dict[str, Any]): Details for the event (date, time, participants, etc.)
    Returns:
        Dict[str, Any]: Result with 'success' (bool), 'event_id' (str, if successful), and 'error' (str, if any)
    """
    try:
        service = get_calendar_service()
        # Parse event details
        date = event_details.get("date")  # e.g., '2024-06-10'
        time = event_details.get("time")  # e.g., '14:00'
        duration = int(event_details.get("duration", 30))  # in minutes
        location = event_details.get("location", "")
        participants = event_details.get("participants", [])
        summary = event_details.get("summary", "TailorTalk Appointment")
        description = event_details.get("description", "Scheduled via TailorTalk AI agent.")
        timezone = event_details.get("timezone", "UTC")

        # Compose start and end datetime in RFC3339 format
        start_dt = datetime.datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
        end_dt = start_dt + datetime.timedelta(minutes=duration)
        start_str = start_dt.isoformat() + ("Z" if timezone == "UTC" else "")
        end_str = end_dt.isoformat() + ("Z" if timezone == "UTC" else "")

        event = {
            'summary': summary,
            'location': location,
            'description': description,
            'start': {
                'dateTime': start_str,
                'timeZone': timezone,
            },
            'end': {
                'dateTime': end_str,
                'timeZone': timezone,
            },
            'attendees': [{'email': email} for email in participants if "@" in email],
        }
        created_event = service.events().insert(calendarId='primary', body=event, sendUpdates='all').execute()
        return {"success": True, "event_id": created_event.get("id"), "error": None}
    except Exception as e:
        return {"success": False, "event_id": None, "error": str(e)}


def generate_booking_message(success: bool, event_details: Dict[str, Any], error: str = None, communication_style: str = "neutral") -> str:
    """
    Use Groq LLM to generate a user-friendly message for booking success or failure.
    Args:
        success (bool): Whether the booking was successful.
        event_details (Dict[str, Any]): The event details.
        error (str): Error message, if any.
        communication_style (str): Desired tone/style (e.g., 'formal', 'casual').
    Returns:
        str: User-facing message.
    """
    if success:
        prompt = f"""
You are a conversational AI assistant. Craft a personalized confirmation message for a successful calendar booking.
- Match the user's tone: {communication_style}
- Include event details: {event_details}
Respond ONLY with a single confirmation message in plain text. Do not include any explanation, markdown, or text outside the message.
"""
    else:
        prompt = f"""
You are a conversational AI assistant. Explain a booking failure in a user-friendly, empathetic way.
- Match the user's tone: {communication_style}
- Error details: {error}
- Suggest next steps if possible.
Respond ONLY with a single error message in plain text. Do not include any explanation, markdown, or text outside the message.
"""
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "llama-3.3-70b-versatile",  # Updated model name
        "messages": [
            {"role": "system", "content": "You are a booking communication assistant for calendar events."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 128,
        "temperature": 0.5
    }
    try:
        response = requests.post(GROQ_API_URL, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        content = result["choices"][0]["message"]["content"]
        # Remove markdown or extra explanation if present
        msg = content.strip()
        if msg.startswith("```"):
            msg = re.sub(r"^```[a-zA-Z]*\\n|```$", "", msg, flags=re.MULTILINE).strip()
        return msg
    except Exception as e:
        return f"Groq API request failed or invalid booking message: {str(e)}" 