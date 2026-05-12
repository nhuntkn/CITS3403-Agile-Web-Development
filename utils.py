# Helper functions for the project
# This file stores reusable calculations used by the app
import os, hashlib, json
from datetime import timedelta

def calculate_calories(met_value, minutes, weight):
    calories = minutes * (met_value * 3.5 * weight) / 200
    return round(calories,2)

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