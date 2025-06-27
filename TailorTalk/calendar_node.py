"""
Calendar Integration Node
------------------------
This module interfaces with Google Calendar to:
- Retrieve availability and busy slots
- Detect conflicts
- Suggest free slots
- Update events

Requires: Google Calendar API credentials.json in the project root
"""

from typing import List, Dict, Any
import datetime
import os
import pytz

# Google Calendar API imports
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pickle

# LLM imports (unchanged)
import requests
import re

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"  # Updated endpoint

SCOPES = ['https://www.googleapis.com/auth/calendar']
TOKEN_PATH = 'token.pickle'
CREDENTIALS_PATH = 'credentials.json'

# 1. Google Calendar API Auth

def get_calendar_service():
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

# 2. Fetch busy slots from Google Calendar

def get_calendar_availability(user_email: str, start_time: str, end_time: str) -> List[Dict[str, Any]]:
    """
    Retrieve busy slots from the user's Google Calendar between start_time and end_time.
    Args:
        user_email (str): The user's email address (not used for auth, just for info).
        start_time (str): ISO 8601 start datetime (e.g., '2024-06-10T00:00:00Z').
        end_time (str): ISO 8601 end datetime.
    Returns:
        List[Dict[str, Any]]: List of busy slots (start, end).
    """
    service = get_calendar_service()
    body = {
        "timeMin": start_time,
        "timeMax": end_time,
        "timeZone": "UTC",
        "items": [{"id": 'primary'}]
    }
    eventsResult = service.freebusy().query(body=body).execute()
    busy_times = eventsResult['calendars']['primary']['busy']
    return busy_times

# 3. Find free slots given busy slots

def find_free_slots(busy_slots: List[Dict[str, str]], start_time: str, end_time: str, slot_minutes: int = 30) -> List[Dict[str, str]]:
    """
    Given busy slots and a time range, return free slots of at least slot_minutes duration.
    Args:
        busy_slots (List[Dict[str, str]]): List of busy slots with 'start' and 'end'.
        start_time (str): ISO 8601 start datetime.
        end_time (str): ISO 8601 end datetime.
        slot_minutes (int): Minimum slot duration in minutes.
    Returns:
        List[Dict[str, str]]: List of free slots.
    """
    tz = pytz.UTC
    start = datetime.datetime.fromisoformat(start_time.replace('Z', '+00:00'))
    end = datetime.datetime.fromisoformat(end_time.replace('Z', '+00:00'))
    busy = [(datetime.datetime.fromisoformat(b['start'].replace('Z', '+00:00')),
             datetime.datetime.fromisoformat(b['end'].replace('Z', '+00:00'))) for b in busy_slots]
    busy.sort()
    free = []
    current = start
    for b_start, b_end in busy:
        if current < b_start:
            delta = (b_start - current).total_seconds() / 60
            if delta >= slot_minutes:
                free.append({
                    "start": current.isoformat(),
                    "end": b_start.isoformat()
                })
        current = max(current, b_end)
    if current < end:
        delta = (end - current).total_seconds() / 60
        if delta >= slot_minutes:
            free.append({
                "start": current.isoformat(),
                "end": end.isoformat()
            })
    return free

# 4. Update an event

def update_event(event_id: str, updated_fields: Dict[str, Any], calendar_id: str = 'primary') -> Dict[str, Any]:
    """
    Update an event with new details.
    Args:
        event_id (str): The event ID to update.
        updated_fields (Dict[str, Any]): Fields to update (e.g., start, end, summary).
        calendar_id (str): Calendar ID (default 'primary').
    Returns:
        Dict[str, Any]: The updated event resource.
    """
    service = get_calendar_service()
    event = service.events().get(calendarId=calendar_id, eventId=event_id).execute()
    event.update(updated_fields)
    updated_event = service.events().update(calendarId=calendar_id, eventId=event_id, body=event).execute()
    return updated_event

# 5. LLM-based slot ranking (unchanged)
def suggest_optimal_slots(free_slots: List[Dict[str, Any]], user_preferences: Dict[str, Any], context: str = "") -> List[Dict[str, Any]]:
    """
    Optionally use Groq LLM to rank and optimize suggested slots based on user preferences and context.
    Args:
        free_slots (List[Dict[str, Any]]): List of available time slots.
        user_preferences (Dict[str, Any]): User's scheduling preferences.
        context (str): Additional context (e.g., meeting type).
    Returns:
        List[Dict[str, Any]]: Ranked/optimized list of suggested slots.
    """
    # If LLM optimization is not needed, return free_slots as-is
    if not GROQ_API_KEY or not free_slots:
        return free_slots

    prompt = f"""
You are a scheduling assistant. Given the following available slots and user preferences, rank the slots and suggest the best options.
Free slots: {free_slots}
User preferences: {user_preferences}
Context: {context}
Respond ONLY with a JSON list of ranked slots (most preferred first). Do not include any explanation, markdown, or text outside the JSON.
"""
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "llama-3.3-70b-versatile",  # Updated model name
        "messages": [
            {"role": "system", "content": "You are a scheduling optimization assistant."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 512,
        "temperature": 0.2
    }
    import json as pyjson
    try:
        response = requests.post(GROQ_API_URL, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        content = result["choices"][0]["message"]["content"]
        try:
            ranked_slots = pyjson.loads(content)
            return ranked_slots
        except Exception as e:
            # Try to extract JSON substring
            match = re.search(r'\[.*\]', content, re.DOTALL)
            if match:
                try:
                    ranked_slots = pyjson.loads(match.group(0))
                    return ranked_slots
                except Exception as e2:
                    return free_slots  # Fallback: return original slots if LLM fails
            return free_slots  # Fallback: return original slots if LLM fails
    except Exception as e:
        return free_slots  # Fallback: return original slots if LLM fails 