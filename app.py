from flask import Flask, render_template, request, redirect
import sqlite3
import re

app = Flask(__name__)

DB_NAME = "database.db"


def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS rankings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            kg_lost REAL NOT NULL,
            kcal_burned INTEGER NOT NULL,
            streak INTEGER NOT NULL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            dob TEXT,
            sex TEXT,
            weight REAL,
            height REAL
        )
    """)

    conn.commit()
    conn.close()


@app.route("/")
def home():
    return render_template("exercise.html")


@app.route("/dashboard")
def dashboard():
    username = "Jackson"
    return render_template("dashboard.html", username=username)


@app.route("/login")
def login():
    return render_template("login.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    init_db()

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirm = request.form.get("confirm")
        dob = request.form.get("dob")
        sex = request.form.get("sex")
        weight = request.form.get("weight")
        height = request.form.get("height")

        # password validation
        if len(password) < 6 or not re.search(r"[A-Za-z]", password):
            return render_template("signup.html",
                                   error="Password must be at least 6 characters and contain letters")

        if password != confirm:
            return render_template("signup.html",
                                   error="Passwords do not match")

        conn = get_db_connection()

        existing_user = conn.execute(
            "SELECT * FROM users WHERE username = ?",
            (username,)
        ).fetchone()

        if existing_user:
            conn.close()
            return render_template("signup.html",
                                   error="Username already exists")

        conn.execute("""
            INSERT INTO users (username, password, dob, sex, weight, height)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (username, password, dob, sex, weight, height))

        conn.commit()
        conn.close()

        return redirect(f"/profile/{username}")

    return render_template("signup.html")


@app.route("/profile/<username>", methods=["GET", "POST"])
def profile(username):
    init_db()

    conn = get_db_connection()

    if request.method == "POST":
        dob = request.form.get("dob")
        sex = request.form.get("sex")
        weight = request.form.get("weight")
        height = request.form.get("height")

        conn.execute("""
            UPDATE users
            SET dob = ?, sex = ?, weight = ?, height = ?
            WHERE username = ?
        """, (dob, sex, weight, height, username))

        conn.commit()

    user = conn.execute("""
        SELECT * FROM users WHERE username = ?
    """, (username,)).fetchone()

    stats = conn.execute("""
        SELECT kcal_burned, streak
        FROM rankings
        WHERE username = ?
    """, (username,)).fetchone()

    conn.close()

    return render_template("profile.html", user=user, stats=stats)


if __name__ == "__main__":
    init_db()
    app.run(debug=True)