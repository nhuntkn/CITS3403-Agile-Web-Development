from datetime import date

from models import db, ExerciseSession, SessionExercise, User
from tests.conftest import create_user, login


def signup_data(**overrides):
    data = {
        "username": "alice",
        "email": "alice@example.com",
        "password": "Validpass123!",
        "confirm": "Validpass123!",
        "dob": "2000-01-01",
        "gender": "Female",
        "weight": "60",
        "height": "165",
    }
    data.update(overrides)
    return data


def test_signup_validation_and_duplicate_email(client, app):
    response = client.post("/signup", data=signup_data(password="short!", confirm="short!"))
    assert response.status_code == 200
    assert b"Password must be at least 12 characters long" in response.data

    response = client.post(
        "/signup",
        data=signup_data(username="nospecial", email="nospecial@example.com", password="longpassword12", confirm="longpassword12"),
    )
    assert b"Password must contain at least one special character" in response.data

    response = client.post("/signup", data=signup_data(), follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/dashboard")

    with app.app_context():
        created = User.query.filter_by(username="alice").first()
        assert created is not None
        assert created.email == "alice@example.com"
        assert created.password != "Validpass123!"

    client.get("/logout")
    response = client.post(
        "/signup",
        data=signup_data(username="alice2"),
    )
    assert b"Email already exists" in response.data


def test_login_logout_and_protected_pages(client, app):
    with app.app_context():
        create_user(username="loginuser", email="login@example.com", password="Validpass123!")

    response = login(client, username="loginuser", password="wrong")
    assert b"Invalid username or password" in response.data

    response = login(client, username="loginuser", password="Validpass123!")
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/dashboard")

    assert b"Welcome, loginuser!" in client.get("/dashboard").data
    assert b"Ranking" in client.get("/ranking").data
    assert b"History" in client.get("/history").data

    response = client.get("/logout", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/login")


def test_exercise_session_is_saved_to_test_database(client, app):
    with app.app_context():
        create_user(username="runner", email="runner@example.com", password="Validpass123!", weight=70)

    login(client, username="runner", password="Validpass123!")
    response = client.post(
        "/exercise",
        data={
            "date": date.today().isoformat(),
            "weight": "70",
            "notes": "Morning workout",
            "exercise[]": ["Treadmill Walk"],
            "level[]": ["3.0 - 3.4 mph"],
            "minutes[]": ["30"],
            "latitude": "",
            "longitude": "",
        },
    )

    assert response.status_code == 200
    assert b"Session added successfully." in response.data

    with app.app_context():
        session = ExerciseSession.query.one()
        assert session.notes == "Morning workout"
        assert session.current_weight == 70
        assert session.total_calories > 0
        assert SessionExercise.query.filter_by(session_id=session.id).count() == 1


def test_history_delete_removes_session_and_child_rows(client, app):
    with app.app_context():
        user = create_user(username="deleter", email="deleter@example.com", password="Validpass123!")
        session = ExerciseSession(date=date.today().isoformat(), current_weight=60, total_calories=100, user_id=user.id)
        db.session.add(session)
        db.session.flush()
        db.session.add(
            SessionExercise(
                exercise_name="Treadmill Walk",
                activity_level="3.0 - 3.4 mph",
                minutes=20,
                met_value=3.8,
                calories=80,
                session_id=session.id,
            )
        )
        session_id = session.id
        db.session.commit()

    login(client, username="deleter", password="Validpass123!")
    response = client.post(f"/history/{session_id}/delete", follow_redirects=False)
    assert response.status_code == 302

    with app.app_context():
        assert db.session.get(ExerciseSession, session_id) is None
        assert SessionExercise.query.count() == 0


def test_forgot_password_flow_allows_retry_after_validation_error(client, app, captured_reset_codes):
    with app.app_context():
        user = create_user(username="resetuser", email="reset@example.com", password="Oldvalidpass123!")
        old_hash = user.password

    response = client.post("/forgot_password", data={"action": "send_code", "email": "reset@example.com"})
    assert response.status_code == 200
    assert b"Verification code sent" in response.data
    assert len(captured_reset_codes) == 1

    code = captured_reset_codes[0]["code"]
    response = client.post("/forgot_password", data={"action": "verify_code", "code": "000000"})
    assert b"Invalid verification code" in response.data

    response = client.post("/forgot_password", data={"action": "verify_code", "code": code})
    assert b"Reset Password" in response.data

    response = client.post(
        "/forgot_password",
        data={"action": "reset", "new_password": "short!", "confirm_password": "short!"},
    )
    assert b"Password must be at least 12 characters" in response.data
    assert b"Reset Password" in response.data

    response = client.post(
        "/forgot_password",
        data={
            "action": "reset",
            "new_password": "Newvalidpass123!",
            "confirm_password": "Newvalidpass123!",
        },
        follow_redirects=False,
    )
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/login")

    with app.app_context():
        user = User.query.filter_by(email="reset@example.com").one()
        assert user.password != old_hash
        assert user.check_password("Newvalidpass123!")
