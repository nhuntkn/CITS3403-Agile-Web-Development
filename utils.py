import hashlib
import json
import os
import smtplib
from datetime import timedelta
from email.message import EmailMessage

from flask import current_app, request, session, url_for

from models import db, Friend, Share, User

def calculate_calories(met_value, minutes, weight):
    calories = minutes * (met_value * 3.5 * weight) / 200
    return round(calories,2)

def parse_location_fields(latitude_raw, longitude_raw):
    if not latitude_raw and not longitude_raw:
        return None, None, None

    if not latitude_raw or not longitude_raw:
        return None, None, "Please select both latitude and longitude for the activity location"

    try:
        latitude = float(latitude_raw)
        longitude = float(longitude_raw)
    except ValueError:
        return None, None, "Activity location is invalid"

    if latitude < -90 or latitude > 90:
        return None, None, "Latitude must be between -90 and 90"
    if longitude < -180 or longitude > 180:
        return None, None, "Longitude must be between -180 and 180"

    return latitude, longitude, None

def send_email(to_email, subject, body):
    username = current_app.config["MAIL_USERNAME"]
    password = current_app.config["MAIL_PASSWORD"]

    if not username or not password:
        raise RuntimeError("Email credentials are not configured")

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = username
    msg["To"] = to_email
    msg.set_content(body)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(username, password)
        smtp.send_message(msg)

def send_reset_email(to_email, code):
    send_email(
        to_email,
        "Password Reset Verification Code",
        f"Your verification code is: {code}\n\nThis code will expire in 5 minutes."
    )

def send_verification_email(to_email, code):
    send_email(
        to_email,
        "Email Verification Code",
        f"Your verification code is: {code}\n\n"
        "This code will expire in 5 minutes.\n"
        "If you did not sign up, please ignore this email."
    )

def clear_reset_session():
    session.pop("reset_code", None)
    session.pop("reset_email", None)
    session.pop("reset_time", None)
    session.pop("reset_attempts", None)
    session.pop("reset_verified", None)

def clear_signup_session():
    session.pop("signup_code", None)
    session.pop("signup_email", None)
    session.pop("signup_time", None)
    session.pop("signup_attempts", None)
    session.pop("signup_data", None)
    session.pop("signup_verified_email", None)

def user_avatar_url(user):
    if not user or not user.avatar:
        return None

    avatar_path = os.path.join(current_app.root_path, "static", "uploads", user.avatar)
    if not os.path.isfile(avatar_path):
        return None

    return url_for("static", filename="uploads/" + user.avatar)

def user_avatar_payload(user):
    return {
        "username": user.username,
        "avatar_url": user_avatar_url(user)
    }

def requested_username():
    data = request.get_json(silent=True) or {}
    return data.get("username", "").strip()

def user_by_username(username):
    if not username:
        return None
    return User.query.filter_by(username=username).first()

def friendship_between(user_id, other_user_id, status=None):
    query = Friend.query.filter(
        ((Friend.sender_id == user_id) & (Friend.receiver_id == other_user_id)) |
        ((Friend.sender_id == other_user_id) & (Friend.receiver_id == user_id))
    )
    if status:
        query = query.filter(Friend.status == status)
    return query.first()

def delete_shares_between(user_id, other_user_id):
    Share.query.filter(
        ((Share.sender_id == user_id) & (Share.receiver_id == other_user_id)) |
        ((Share.sender_id == other_user_id) & (Share.receiver_id == user_id))
    ).delete(synchronize_session=False)

# This function generates AI feedback text based on the provided prompt and the selected AI provider (OpenAI, Claude, or Gemini).
def generateAiFeedbackText(prompt):
    provider = os.environ.get("AI_PROVIDER", "openai").lower()

    if provider == "openai":
        from openai import OpenAI

        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OpenAI API key is not set.")

        client = OpenAI(api_key=api_key)
        response = client.responses.create(
            model=os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
            input=prompt,
            max_output_tokens=220
        )

        return response.output_text.strip()

    if provider == "claude":
        import anthropic

        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("Claude API key is not set.")

        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model=os.environ.get("ANTHROPIC_MODEL", "claude-3-5-haiku-latest"),
            max_tokens=220,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        return response.content[0].text.strip()

    if provider == "gemini":
        from google import genai

        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("Gemini API key is not set.")

        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=os.environ.get("GEMINI_MODEL", "gemini-1.5-flash"),
            contents=prompt
        )

        return response.text.strip()

    raise ValueError("Invalid AI provider. Use openai, claude, or gemini.")

# This function calculates the start date of the week for a given date, assuming the week starts on Monday.
def getStartWeek(today):
    return today - timedelta(days=today.weekday())

# This function builds the AI feedback prompt based on the user's weekly exercise data, including calories burned, minutes exercised, weight changes, and nutritional targets for cutting and bulking. 
# It returns a formatted string that can be sent to the AI for generating feedback.
def buildFeedback(user, weekly_sessions, week_start, today):
    total_calories = round(sum(s.total_calories or 0 for s in weekly_sessions), 2)
    total_minutes = sum(
        exercise.minutes or 0
        for session in weekly_sessions
        for exercise in session.exercises
    )

    session_count = len(weekly_sessions)

    weights = [s.current_weight for s in weekly_sessions if s.current_weight is not None]
    start_weight = weights[0] if weights else user.weight
    current_weight = weights[-1] if weights else user.weight

    weight_change = "unknown"
    if start_weight is not None and current_weight is not None:
        weight_change = round(current_weight - start_weight, 2)

    if current_weight:
        cutting_protein = f"{round(current_weight * 2.0)}-{round(current_weight * 2.3)} g/day"
        bulking_protein = f"{round(current_weight * 1.6)}-{round(current_weight * 2.0)} g/day"

        light_carbs = f"{round(current_weight * 3)}-{round(current_weight * 5)} g/day"
        training_carbs = f"{round(current_weight * 5)}-{round(current_weight * 7)} g/day"

        if total_minutes >= 240:
            training_level = "moderate/high"
            cutting_carbs = training_carbs
            bulking_carbs = training_carbs
        else:
            training_level = "light/moderate"
            cutting_carbs = light_carbs
            bulking_carbs = training_carbs
    else:
        training_level = "unknown"
        cutting_protein = "unknown"
        bulking_protein = "unknown"
        cutting_carbs = "unknown"
        bulking_carbs = "unknown"

    return f"""
You are giving short weekly fitness feedback for an exercise tracking web app.

Use the user's weekly data below:
- Week period: {week_start} to {today}
- Sessions this week: {session_count}
- Total calories burned: {total_calories}
- Total exercise minutes: {total_minutes}
- First weight this week: {start_weight} kg
- Latest weight this week: {current_weight} kg
- Weight change: {weight_change} kg
- Training level: {training_level}
- Cutting protein target: {cutting_protein}
- Cutting carb target: {cutting_carbs}
- Bulking protein target: {bulking_protein}
- Bulking carb target: {bulking_carbs}

Write one short paragraph only, include:
- a weekly progress summary
- cutting guidance using the cutting protein and carb targets
- bulking guidance using the bulking protein and carb targets
- one general nutrition note
- a reminder that this is general guidance only not medical advice

Keep it under 130 words.
Do not use markdown.
Do not use headings.
Do not use bullet points.
Do not give a long explanation.
"""

def buildFeedbackHash(weekly_sessions):
    data = []

    for session in weekly_sessions:
        exercises = []

        for exercise in session.exercises:
            exercises.append({
                "name": exercise.exercise_name,
                "minutes": exercise.minutes,
                "calories": exercise.calories
            })

        data.append({
            "date": session.date,
            "weight": session.current_weight,
            "total_calories": session.total_calories,
            "notes": session.notes,
            "exercises": exercises
        })

    data_string = json.dumps(data, sort_keys=True)
    return hashlib.sha256(data_string.encode()).hexdigest()
