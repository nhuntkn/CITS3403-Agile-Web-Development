from datetime import date

from models import db, User
from utils import calculate_calories, getStartWeek


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


def test_test_database_is_used(app):
    assert "test_exercise_planner.db" in app.config["SQLALCHEMY_DATABASE_URI"]

    user = User(username="dbcheck", email="dbcheck@example.com")
    user.set_password("Validpass123!")
    db.session.add(user)
    db.session.commit()

    assert User.query.filter_by(username="dbcheck").first() is not None
