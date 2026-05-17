from datetime import date

from models import db, ExerciseSession, SessionExercise, User
from utils import buildFeedbackHash, calculate_calories, getStartWeek, parse_location_fields


def test_passwords_are_hashed_and_checked(app):
    user = User(username="hashuser", email="hash@example.com")
    user.set_password("Validpass123!")

    assert user.password != "Validpass123!"
    assert user.check_password("Validpass123!")
    assert not user.check_password("wrong-password")


def test_calculate_calories_rounds_to_two_decimals():
    assert calculate_calories(3.8, 30, 70) == 139.65


def test_get_start_week_returns_monday():
    assert getStartWeek(date(2026, 5, 14)).isoformat() == "2026-05-11"


def test_parse_location_fields_validates_coordinates():
    latitude, longitude, error = parse_location_fields("-31.95", "115.86")
    assert latitude == -31.95
    assert longitude == 115.86
    assert error is None

    latitude, longitude, error = parse_location_fields("91", "115.86")
    assert latitude is None
    assert longitude is None
    assert error == "Latitude must be between -90 and 90"

    latitude, longitude, error = parse_location_fields("-31.95", "")
    assert latitude is None
    assert longitude is None
    assert error == "Please select both latitude and longitude for the activity location"


def test_build_feedback_hash_is_stable_and_changes_with_session_data():
    session = ExerciseSession(
        date="2026-05-17",
        current_weight=70,
        total_calories=120,
        notes="Morning session",
    )
    session.exercises = [
        SessionExercise(
            exercise_name="Treadmill Walk",
            activity_level="3.0 - 3.4 mph",
            minutes=30,
            met_value=3.8,
            calories=120,
        )
    ]

    first_hash = buildFeedbackHash([session])
    assert first_hash == buildFeedbackHash([session])

    session.exercises[0].minutes = 35
    assert buildFeedbackHash([session]) != first_hash


def test_test_database_is_used(app):
    assert "test_exercise_planner.db" in app.config["SQLALCHEMY_DATABASE_URI"]

    user = User(username="dbcheck", email="dbcheck@example.com")
    user.set_password("Validpass123!")
    db.session.add(user)
    db.session.commit()

    assert User.query.filter_by(username="dbcheck").first() is not None
