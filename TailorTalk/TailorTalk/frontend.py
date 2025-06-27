import streamlit as st
from typing import List, Dict, Any
import json
import tempfile

from intent_node import analyze_intent
from extraction_node import extract_details
from router_node import route_conversation
from suggestion_node import generate_suggestion_message
from calendar_node import get_calendar_availability, suggest_optimal_slots
from confirmation_node import handle_confirmation_response
from email_node import validate_email_format
from booking_node import book_calendar_event, generate_booking_message
from notification_node import generate_notification_email, send_email

st.set_page_config(page_title="TailorTalk - Calendar Booking AI", page_icon="📅", layout="centered")

st.sidebar.title("TailorTalk Setup & Info")
st.sidebar.markdown("""
**How to use:**
- Start a conversation to book, check, or modify a meeting.
- The agent will guide you through the process.
""")

st.title("📅 TailorTalk: Conversational Calendar Booking Agent")
st.markdown("""
Engage in a natural conversation to book, check, or modify your calendar appointments. Powered by Groq LLM and FastAPI backend logic.
""")

# --- User Info Collection ---
if "user_name" not in st.session_state:
    st.session_state.user_name = ""
if "user_email" not in st.session_state:
    st.session_state.user_email = ""
if "user_verified" not in st.session_state:
    st.session_state.user_verified = False

# Write credentials.json from st.secrets if needed
if "google" in st.secrets and "credentials" in st.secrets["google"]:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as tmp:
        tmp.write(st.secrets["google"]["credentials"].encode())
        tmp.flush()
        st.session_state["google_credentials_path"] = tmp.name
else:
    st.session_state["google_credentials_path"] = "credentials.json"  # fallback

if not st.session_state.user_verified:
    st.info("Before we begin, please provide your name and email address to connect your Google Calendar.")
    with st.form("user_info_form", clear_on_submit=False):
        user_name = st.text_input("Your Name", value=st.session_state.user_name)
        user_email = st.text_input("Your Email Address", value=st.session_state.user_email)
        submitted = st.form_submit_button("Continue")
        if submitted:
            if not user_name.strip():
                st.warning("Please enter your name.")
            elif not user_email.strip() or not validate_email_format(user_email):
                st.warning("Please enter a valid email address.")
            else:
                try:
                    import datetime
                    now = datetime.datetime.utcnow()
                    week_later = now + datetime.timedelta(days=7)
                    # Pass credentials path to calendar_node
                    busy = get_calendar_availability(
                        user_email,
                        now.isoformat() + "Z",
                        week_later.isoformat() + "Z",
                        credentials_path=st.session_state["google_credentials_path"]
                    )
                    st.session_state.user_name = user_name.strip()
                    st.session_state.user_email = user_email.strip()
                    st.session_state.user_verified = True
                    st.success(f"Welcome, {user_name}! Your calendar is connected.")
                except Exception as e:
                    st.error(f"Failed to access Google Calendar for {user_email}: {e}")
    st.stop()

# --- Chat State Initialization ---
if "history" not in st.session_state:
    st.session_state.history = []
if "conversation_state" not in st.session_state:
    st.session_state.conversation_state = {"current_node": "intent", "info_collected": []}
if "extracted_details" not in st.session_state:
    st.session_state.extracted_details = {}
if "user_intent" not in st.session_state:
    st.session_state.user_intent = ""

user_input = st.chat_input("Type your message and press Enter...")

# Display chat history
for msg in st.session_state.history:
    if msg["role"] == "user":
        st.chat_message("user").write(msg["content"])
    else:
        st.chat_message("assistant").write(msg["content"])

def append_and_display(role, content):
    st.session_state.history.append({"role": role, "content": content})
    st.chat_message(role).write(content)

# --- Main Chat Workflow ---
if user_input:
    append_and_display("user", user_input)
    # 1. Intent Recognition
    intent_result = analyze_intent(user_input, st.session_state.history)
    st.write("[DEBUG] Intent Node Output:", intent_result)
    print("[DEBUG] Intent Node Output:")
    print(json.dumps(intent_result, indent=2, ensure_ascii=False))
    if "error" in intent_result:
        append_and_display("assistant", f"[Intent Error] {intent_result['error']}")
        st.stop()
    st.session_state.user_intent = intent_result.get("intent", "unknown")
    # 2. Detail Extraction
    details_result = extract_details(user_input, st.session_state.history)
    st.write("[DEBUG] Extraction Node Output:", details_result)
    print("[DEBUG] Extraction Node Output:")
    print(json.dumps(details_result, indent=2, ensure_ascii=False))
    if "error" in details_result:
        append_and_display("assistant", f"[Extraction Error] {details_result['error']}")
        st.stop()
    # Always use the provided user email and name
    details_result["participants"] = [st.session_state.user_email]
    details_result["user_name"] = st.session_state.user_name
    st.session_state.extracted_details = details_result
    # 3. Router Node
    router_result = route_conversation(
        st.session_state.conversation_state,
        st.session_state.user_intent,
        st.session_state.extracted_details,
        st.session_state.history
    )
    st.write("[DEBUG] Router Node Output:", router_result)
    print("[DEBUG] Router Node Output:")
    print(json.dumps(router_result, indent=2, ensure_ascii=False))
    if "reason" in router_result:
        print(f"[Router] {router_result['reason']}")
    next_node = router_result.get("next_node", "end")
    # 4. Node Handling (robust logic)
    if next_node == "suggestion":
        # Use the user's calendar to suggest slots
        import datetime
        now = datetime.datetime.utcnow()
        week_later = now + datetime.timedelta(days=7)
        busy = get_calendar_availability(
            st.session_state.user_email,
            now.isoformat() + "Z",
            week_later.isoformat() + "Z"
        )
        from calendar_node import find_free_slots
        free_slots = find_free_slots(busy, now.isoformat() + "Z", week_later.isoformat() + "Z")
        suggestion = generate_suggestion_message(
            free_slots,
            user_preferences={"communication_style": intent_result.get("style", "neutral")},
            communication_style=intent_result.get("style", "neutral"),
            context="calendar booking"
        )
        if suggestion.startswith("Groq API request failed"):
            append_and_display("assistant", f"[Suggestion Error] {suggestion}")
            st.stop()
        append_and_display("assistant", suggestion)
    elif next_node == "confirmation":
        # Display booking details summary before asking for confirmation
        details = st.session_state.extracted_details
        summary_lines = []
        if details.get("date"): summary_lines.append(f"**Date:** {details['date']}")
        if details.get("time"): summary_lines.append(f"**Time:** {details['time']}")
        if details.get("duration"): summary_lines.append(f"**Duration:** {details['duration']} minutes")
        if details.get("participants"): summary_lines.append(f"**Participants:** {', '.join(details['participants'])}")
        if details.get("location"): summary_lines.append(f"**Location:** {details['location']}")
        if summary_lines:
            summary_msg = "Here are the details for your booking:\n" + "\n".join(summary_lines)
            append_and_display("assistant", summary_msg)
        confirmation_prompt = "Do you confirm the booking details? (yes/no)"
        append_and_display("assistant", confirmation_prompt)
    elif next_node == "booking":
        # Only proceed with booking if user confirmed
        last_user_message = st.session_state.history[-1]["content"].strip().lower() if st.session_state.history else ""
        if last_user_message in ["no", "cancel", "not now"]:
            append_and_display("assistant", "Okay, the booking has been cancelled. If you want to start over or change any details, just let me know!")
            st.stop()
        elif last_user_message not in ["yes", "confirm", "i confirm", "confirmed"]:
            append_and_display("assistant", "Please type 'yes' to confirm your booking or 'no' to cancel.")
            st.stop()
        booking_result = book_calendar_event(st.session_state.extracted_details)
        if isinstance(booking_result, dict) and "error" in booking_result and booking_result["error"]:
            append_and_display("assistant", f"[Booking Error] {booking_result['error']}")
            st.stop()
        booking_msg = generate_booking_message(
            success=booking_result["success"],
            event_details=st.session_state.extracted_details,
            error=booking_result["error"],
            communication_style=intent_result.get("style", "neutral")
        )
        if booking_msg.startswith("Groq API request failed"):
            append_and_display("assistant", f"[Booking Message Error] {booking_msg}")
            st.stop()
        append_and_display("assistant", booking_msg)
        # Send confirmation email
        notif = generate_notification_email(
            event_details=st.session_state.extracted_details,
            notification_type="confirmation",
            communication_style=intent_result.get("style", "neutral"),
            user_name=st.session_state.user_name
        )
        if isinstance(notif, dict) and "body" in notif and notif["body"].startswith("Groq API request failed"):
            append_and_display("assistant", f"[Notification Error] {notif['body']}")
            st.stop()
        email_result = send_email(
            to_email=st.session_state.user_email,
            subject=notif["subject"],
            body=notif["body"],
            recipient_name=st.session_state.user_name
        )
        st.sidebar.write(f"[Frontend] Email send result: {email_result}")
        if email_result[0]:
            notif_msg = f"A confirmation email has been sent: {notif['subject']}"
        else:
            notif_msg = f"[Email Error] Failed to send confirmation email. Reason: {email_result[3]}"
        append_and_display("assistant", notif_msg)
    elif next_node == "end":
        end_msg = "Thank you for using TailorTalk! If you need anything else, just ask."
        append_and_display("assistant", end_msg)
    else:
        # Custom handling for missing required fields
        router_reason = router_result.get("reason", "").lower()
        missing_info = st.session_state.extracted_details.get("missing_info", [])
        missing_prompts = []
        if missing_info:
            for field in missing_info:
                if field == "time":
                    missing_prompts.append("the time for your meeting")
                elif field == "date":
                    missing_prompts.append("the date for your meeting")
                elif field == "participants":
                    missing_prompts.append("the participants or who should be invited")
                elif field == "location":
                    missing_prompts.append("the location for your meeting")
                else:
                    missing_prompts.append(field)
        # Also check router reason for missing fields
        for field in ["time", "date", "participants", "location"]:
            if f"{field} is a required field" in router_reason and field not in missing_info:
                if field == "time":
                    missing_prompts.append("the time for your meeting")
                elif field == "date":
                    missing_prompts.append("the date for your meeting")
                elif field == "participants":
                    missing_prompts.append("the participants or who should be invited")
                elif field == "location":
                    missing_prompts.append("the location for your meeting")
                else:
                    missing_prompts.append(field)
        if missing_prompts:
            ask_msg = "Could you please specify " + ", ".join(missing_prompts) + "?"
            append_and_display("assistant", ask_msg)
        else:
            fallback_msg = "I'm not sure how to proceed. Could you please clarify your request?"
            append_and_display("assistant", fallback_msg)

# Handle pending email collection (user response to email prompt)
if st.session_state.pending_email and user_input:
    # Try to extract and validate email from user input
    import re
    email_match = re.search(r"[\w\.-]+@[\w\.-]+\.\w{2,}", user_input)
    if email_match:
        email = email_match.group(0)
        if validate_email_format(email):
            st.session_state.extracted_details["participants"] = [email]
            st.session_state.pending_email = False
            append_and_display("assistant", f"Thank you! We'll use {email} for your booking.")
            # Immediately send confirmation email and end conversation
            # NOTE: Update your MailerSend API key and sender email in notification_node.py:
            # MAILERSEND_API_KEY = "YOUR_MAILERSEND_API_KEY"
            # MAILERSEND_SENDER_EMAIL = "noreply@yourdomain.com"
            notif = generate_notification_email(
                event_details=st.session_state.extracted_details,
                notification_type="confirmation",
                communication_style="neutral",
                user_name=st.session_state.extracted_details.get("user_name", "User")
            )
            email_result = send_email(
                to_email=email,
                subject=notif["subject"],
                body=notif["body"],
                recipient_name=st.session_state.extracted_details.get("user_name", "User")
            )
            st.sidebar.write(f"[Frontend] Email send result: {email_result}")
            if email_result[0]:
                append_and_display("assistant", f"A confirmation email has been sent to {email}. Thank you for using TailorTalk!")
            else:
                append_and_display("assistant", f"[Email Error] Failed to send confirmation email to {email}. Reason: {email_result[3]}")
            st.stop()
        else:
            append_and_display("assistant", "That doesn't look like a valid email address. Please try again.")
    else:
        append_and_display("assistant", "Please provide a valid email address so we can proceed.") 