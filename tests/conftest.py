import os
import socket
import threading
from pathlib import Path

import pytest
from werkzeug.serving import make_server

os.environ.setdefault("SECRET_KEY", "test-secret-key")

TEST_DB_PATH = Path(__file__).resolve().parents[1] / "instance" / "test_exercise_planner.db"
TEST_DB_URI = "sqlite:///" + TEST_DB_PATH.as_posix()
os.environ["DATABASE_URL"] = TEST_DB_URI

import app as app_module
from app import app as flask_app
from models import db, User

flask_app.config.update(
    TESTING=True,
    MAIL_USERNAME="test@example.com",
    MAIL_PASSWORD="test-password",
    WTF_CSRF_ENABLED=False,
)


@pytest.fixture()
def app():
    TEST_DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    with flask_app.app_context():
        db.session.remove()
        db.drop_all()
        db.create_all()
        yield flask_app
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def runner(app):
    return app.test_cli_runner()


@pytest.fixture()
def captured_reset_codes(monkeypatch):
    sent = []

    def fake_send_reset_email(to_email, code):
        sent.append({"email": to_email, "code": code})

    monkeypatch.setattr(app_module, "send_reset_email", fake_send_reset_email)
    return sent


@pytest.fixture()
def captured_signup_codes(monkeypatch):
    sent = []

    def fake_send_verification_email(to_email, code):
        sent.append({"email": to_email, "code": code})

    monkeypatch.setattr(app_module, "send_verification_email", fake_send_verification_email)
    return sent


def create_user(username="alice", email="alice@example.com", password="Validpass123!", **kwargs):
    user = User(
        username=username,
        email=email,
        dob=kwargs.get("dob", "2000-01-01"),
        gender=kwargs.get("gender", "Female"),
        weight=kwargs.get("weight", 60),
        height=kwargs.get("height", 165),
        calorie_goal=kwargs.get("calorie_goal", 1000),
    )
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return user


def login(client, username="alice", password="Validpass123!"):
    return client.post(
        "/login",
        data={"username": username, "password": password},
        follow_redirects=False,
    )


def free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


@pytest.fixture()
def live_server(app):
    port = free_port()
    server = make_server("127.0.0.1", port, app)
    thread = threading.Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()

    try:
        yield f"http://127.0.0.1:{port}"
    finally:
        server.shutdown()
        thread.join(timeout=5)
