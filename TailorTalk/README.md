# TailorTalk Conversational AI Agent

## Intent Recognition Node

### Purpose
The Intent Recognition Node leverages the Groq LLM to analyze user input and conversation history, providing:
- Primary intent detection (e.g., booking, question, complaint, casual)
- Confidence score for the detected intent
- Communication style analysis (formal, casual, urgent, etc.)
- Context integration (relation to previous conversation turns)

### Why LLM (Groq)?
Traditional rule-based systems are limited in handling linguistic variety and context. The Groq LLM enables robust, context-aware intent recognition, reducing the need for extensive pattern programming.

### Configuration
- **Groq API Key:** Set your Groq API key as an environment variable named `GROQ_API_KEY` or update the placeholder in `intent_node.py`.

### Usage Example
```python
from intent_node import analyze_intent

user_input = "I want to schedule a meeting for tomorrow afternoon."
conversation_history = [
    {"role": "user", "content": "Hi, can you help me book a meeting?"},
    {"role": "assistant", "content": "Of course! When would you like to schedule it?"}
]

result = analyze_intent(user_input, conversation_history)
print(result)
# Example output:
# {
#   "intent": "booking",
#   "confidence": 0.95,
#   "style": "casual",
#   "context_summary": "User is following up to book a meeting after initial inquiry."
# }
```

---

## Detail Extraction Node

### Purpose
The Detail Extraction Node uses the Groq LLM to extract structured information from user input and conversation history, including:
- Temporal resolution (converting relative times to absolute datetimes)
- Ambiguity resolution (context-dependent meanings)
- Incomplete information detection (identifying missing details)
- Multi-turn assembly (combining details from multiple conversation turns)

### Advanced Capabilities
- Handles complex temporal relationships (e.g., "next Friday after the holiday", "before my lunch meeting")
- Infers missing information based on context and common patterns
- Notes ambiguities and context-dependent meanings

### Configuration
- **Groq API Key:** Set your Groq API key as an environment variable named `GROQ_API_KEY` or update the placeholder in `extraction_node.py`.

### Usage Example
```python
from extraction_node import extract_details

user_input = "Let's do it next Friday after the holiday, sometime in the morning."
conversation_history = [
    {"role": "user", "content": "I want to book a meeting."},
    {"role": "assistant", "content": "What date and time do you prefer?"}
]

result = extract_details(user_input, conversation_history)
print(result)
# Example output:
# {
#   "date": "2024-06-14",
#   "time": "10:00",
#   "duration": 60,
#   "participants": [],
#   "location": None,
#   "missing_info": ["participants"],
#   "ambiguity_notes": ["'after the holiday' is context-dependent; assumed next public holiday is June 12th."],
#   "context_assembly": "Date and time inferred from user input and previous turns."
# }
```

For further details on other nodes and the overall architecture, see the main documentation sections below.

## Calendar Integration Node

### Purpose
The Calendar Integration Node interfaces with calendar systems (e.g., Google Calendar) to:
- Retrieve availability and busy slots
- Detect scheduling conflicts
- Optionally use Groq LLM for intelligent slot ranking and optimization

### Advanced Capabilities (with LLM)
- Intelligent slot ranking based on user preferences and meeting context
- Conflict analysis beyond simple time overlaps
- Pattern recognition from historical scheduling behavior
- Optimization logic (e.g., avoid back-to-back meetings, respect user time-of-day preferences)

### Configuration
- **Google Calendar API:** Configure credentials for Google Calendar API integration in `calendar_node.py`.
- **Groq API Key (optional):** Set your Groq API key as an environment variable named `GROQ_API_KEY` or update the placeholder in `calendar_node.py` for LLM-based optimization.

### Usage Example
```python
from calendar_node import get_calendar_availability, suggest_optimal_slots

# Example: Retrieve busy slots (replace with real API integration)
user_email = "user@example.com"
start_time = "2024-06-10T00:00:00Z"
end_time = "2024-06-10T23:59:59Z"
busy_slots = get_calendar_availability(user_email, start_time, end_time)

# Example: Suggest optimal slots (LLM optimization optional)
free_slots = [
    {"start": "2024-06-10T10:00:00Z", "end": "2024-06-10T11:00:00Z"},
    {"start": "2024-06-10T14:00:00Z", "end": "2024-06-10T15:00:00Z"}
]
user_preferences = {"preferred_time_of_day": "morning", "avoid_back_to_back": True}
context = "Client call"

ranked_slots = suggest_optimal_slots(free_slots, user_preferences, context)
print(ranked_slots)
# Example output:
# [
#   {"start": "2024-06-10T10:00:00Z", "end": "2024-06-10T11:00:00Z"},
#   {"start": "2024-06-10T14:00:00Z", "end": "2024-06-10T15:00:00Z"}
# ]
```

## Suggestion Generation Node

### Purpose
The Suggestion Generation Node uses the Groq LLM to transform technical scheduling data into natural, conversational suggestions that:
- Match the user's communication style (formal, casual, etc.)
- Provide context for suggested slots
- Present multiple options clearly and engagingly
- Maintain conversational flow and user engagement

### LLM-Driven Capabilities
- Adapts tone and phrasing to user preferences (e.g., formal for business, casual for friendly chats)
- Explains why certain slots are suggested, referencing user context
- Handles multiple options without overwhelming the user
- Keeps the conversation human-like and engaging

### Configuration
- **Groq API Key:** Set your Groq API key as an environment variable named `GROQ_API_KEY` or update the placeholder in `suggestion_node.py`.

### Usage Example
```python
from suggestion_node import generate_suggestion_message

available_slots = [
    {"start": "2024-06-10T10:00:00Z", "end": "2024-06-10T11:00:00Z"},
    {"start": "2024-06-10T14:00:00Z", "end": "2024-06-10T15:00:00Z"}
]
user_preferences = {"preferred_time_of_day": "morning", "communication_style": "casual"}
communication_style = "casual"
context = "Client call"

suggestion = generate_suggestion_message(available_slots, user_preferences, communication_style, context)
print(suggestion)
# Example output:
# "I found a couple of great options for you! How about 10 AM, which is perfect for a fresh start to your day? Or if you prefer later, 2 PM is also available. Let me know what works best!"
```

## Confirmation Handler Node

### Purpose
The Confirmation Handler Node uses the Groq LLM to interpret user responses during the confirmation phase, handling:
- Partial confirmations (e.g., agreeing to time but requesting duration change)
- Conditional agreements (e.g., "if John can join")
- Implicit feedback (e.g., "that's a bit late for me")
- Multi-step modifications (changing multiple aspects of the booking)

### LLM-Driven Capabilities
- Detects and interprets nuanced user feedback and requests
- Handles complex, multi-step modifications and conditional agreements
- Determines the appropriate next action (confirm, modify, suggest new, or clarify)

### Configuration
- **Groq API Key:** Set your Groq API key as an environment variable named `GROQ_API_KEY` or update the placeholder in `confirmation_node.py`.

### Usage Example
```python
from confirmation_node import handle_confirmation_response

user_response = "2 PM works, but can we make it 30 minutes instead of an hour?"
booking_proposal = {
    "date": "2024-06-10",
    "time": "14:00",
    "duration": 60,
    "participants": ["john@example.com"]
}
conversation_history = [
    {"role": "user", "content": "Can we meet in the afternoon?"},
    {"role": "assistant", "content": "How about 2 PM for an hour?"}
]

result = handle_confirmation_response(user_response, booking_proposal, conversation_history)
print(result)
# Example output:
# {
#   "confirmation_status": "modified",
#   "requested_modifications": {"duration": 30},
#   "implicit_feedback": [],
#   "next_action": "suggest_new"
# }
```

## Email Collection Node

### Purpose
The Email Collection Node uses the Groq LLM to naturally and sensitively collect email addresses from users, handling:
- Tone matching (professional/casual)
- Context-sensitive timing
- Trust building (explaining why the email is needed)
- Error handling for invalid formats or user reluctance

### LLM-Driven Capabilities
- Crafts personalized, trust-building prompts for email collection
- Adapts to user communication style and conversation context
- Handles privacy concerns and gracefully manages invalid or declined responses

### Configuration
- **Groq API Key:** Set your Groq API key as an environment variable named `GROQ_API_KEY` or update the placeholder in `email_node.py`.

### Usage Example
```python
from email_node import generate_email_request_prompt, validate_email_format

context = "To send you a calendar invite for your booking."
communication_style = "formal"
previous_attempts = ["I'd rather not share my email."]

prompt = generate_email_request_prompt(context, communication_style, previous_attempts)
print(prompt)
# Example output:
# "To send you a calendar invite and keep you updated, could you please share your email address? Your privacy is important, and your email will only be used for this booking."

# Email validation example
email = "user@example.com"
print(validate_email_format(email))  # True
```

## Booking Execution Node

### Purpose
The Booking Execution Node handles the technical aspects of booking calendar events, sending invitations, and managing the booking transaction.
- Core booking is API-driven (Google Calendar integration is now fully implemented)
- Groq LLM is used for user-friendly error and success messages

### Capabilities
- **API-driven:** Books events and manages transactions via Google Calendar API (integration implemented)
- **LLM-driven:** Crafts personalized confirmation and error messages, and handles edge cases in natural language

### Configuration
- **Google Calendar API:** Place your `credentials.json` in the project root. On first use, you will be prompted to authenticate with your Google account; a `token.pickle` will be saved for future use.
- **Groq API Key (optional):** Set your Groq API key as an environment variable named `GROQ_API_KEY` or update the placeholder in `booking_node.py` for LLM-based communication.

### Usage Example
```python
from booking_node import book_calendar_event, generate_booking_message

event_details = {
    "date": "2024-06-10",
    "time": "14:00",
    "duration": 30,
    "participants": ["user@example.com"],
    "location": "Conference Room A"
}

# Book the event (now uses real Google Calendar API)
result = book_calendar_event(event_details)

# Generate a user-facing message
message = generate_booking_message(
    success=result["success"],
    event_details=event_details,
    error=result["error"],
    communication_style="formal"
)
print(message)
# Example output (success):
# "Your meeting has been successfully scheduled for June 10th at 2:00 PM in Conference Room A. Invitations have been sent to all participants."
# Example output (failure):
# "Unfortunately, there was an issue booking your meeting. The time slot may no longer be available. Please try another time or contact support."
```

**Note:**
- On first use, a browser window will open for Google authentication. Subsequent uses will use the saved token.
- Invitations are sent to all participants' emails provided in the booking details.
- If you encounter issues with credentials or token files, delete `token.pickle` and re-run the app to re-authenticate.

## Notification Node

### Purpose
The Notification Node manages email composition, template personalization, and follow-up communication for calendar events.
- Uses Groq LLM to personalize email content and adapt templates
- Handles confirmation, reminder, and follow-up notifications
- Placeholder for actual email sending logic

### LLM-Driven Capabilities
- Personalizes email tone and content based on user and meeting context
- Adapts standard templates to specific situations
- Determines appropriate follow-up timing and content

### Configuration
- **Email Sending:** Integrate with your preferred email service in `notification_node.py` (SMTP, SendGrid, etc.)
- **Groq API Key (optional):** Set your Groq API key as an environment variable named `GROQ_API_KEY` or update the placeholder in `notification_node.py` for LLM-based personalization.

### Usage Example
```python
from notification_node import generate_notification_email, send_email

event_details = {
    "date": "2024-06-10",
    "time": "14:00",
    "duration": 30,
    "participants": ["user@example.com"],
    "location": "Conference Room A"
}

# Generate a personalized confirmation email
email_content = generate_notification_email(
    event_details=event_details,
    notification_type="confirmation",
    communication_style="formal",
    user_name="Alex"
)

# Send the email (replace with real email integration)
send_email(
    to_email="user@example.com",
    subject=email_content["subject"],
    body=email_content["body"]
)
# Example output (printed):
# Sending email to user@example.com: Meeting Confirmation
# Dear Alex, your meeting is confirmed for June 10th at 2:00 PM in Conference Room A. We look forward to seeing you!
```

## Router Node

### Purpose
The Router Node uses the Groq LLM to manage intelligent conversation flow, acting as the "conductor" for the booking agent.
- Decides the next node/action based on conversation state, user intent, and extracted details
- Handles interruptions, modifications, user emotions, errors, and multi-meeting scenarios

### LLM-Driven Capabilities
- Maintains conversation coherence and flow
- Handles complex decision-making (interruptions, modifications, user emotions, errors, multi-meeting scenarios)
- Ensures a smooth and natural user experience

### Configuration
- **Groq API Key:** Set your Groq API key as an environment variable named `GROQ_API_KEY` or update the placeholder in `router_node.py`.

### Usage Example
```python
from router_node import route_conversation

conversation_state = {"current_node": "suggestion", "info_collected": ["date", "time"]}
user_intent = "modify_booking"
extracted_details = {"date": "2024-06-11", "time": "15:00"}
conversation_history = [
    {"role": "user", "content": "Can we move the meeting to tomorrow?"},
    {"role": "assistant", "content": "Sure, what time works for you?"}
]

result = route_conversation(conversation_state, user_intent, extracted_details, conversation_history)
print(result)
# Example output:
# {
#   "next_node": "confirmation",
#   "reason": "User requested a modification after suggestion; route to confirmation for updated details.",
#   "additional_actions": []
# }
```

## Deployment (Streamlit Cloud)

### 1. Prepare Your App
- Ensure all API keys and sensitive values are in environment variables (see .env example below).
- Your `requirements.txt` should include all dependencies (see included file).
- Your `frontend.py` should call `load_dotenv()` at the top.

### 2. Push to GitHub
- Push your code to a public or private GitHub repository.

### 3. Deploy on Streamlit Cloud
- Go to https://streamlit.io/cloud and sign in.
- Click "New app" and select your repo and branch.
- In the app settings, add your secrets (GROQ_API_KEY, MAILERSEND_API_KEY, MAILERSEND_SENDER_EMAIL) in the "Secrets" section.
- Upload your `credentials.json` (Google OAuth) as a secret file if needed.
- Deploy!

### 4. Set Google OAuth Redirect URI
- In Google Cloud Console, set the OAuth redirect URI to your deployed app's URL (e.g., `https://your-app-name.streamlit.app/`).
- Download the updated `credentials.json` and use it in your deployment.

### 5. Email Service
- Ensure `MAILERSEND_API_KEY` and `MAILERSEND_SENDER_EMAIL` are set in Streamlit Cloud secrets.
- The app will send real emails using MailerSend.

### 6. Troubleshooting
- If OAuth fails, check the redirect URI and credentials.json.
- If email fails, check your MailerSend API key and sender email.
- For environment variable issues, use Streamlit Cloud's "Secrets" feature.

### Example .env
```
GROQ_API_KEY=your_groq_key
MAILERSEND_API_KEY=your_mailersend_key
MAILERSEND_SENDER_EMAIL=your_sender_email
``` 