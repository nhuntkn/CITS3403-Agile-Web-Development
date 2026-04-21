from flask import Flask, render_template
import sqlite3

from flask import request
from flask import redirect

app = Flask(__name__)

DB_NAME = "database.db"


def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rankings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            kg_lost REAL NOT NULL,
            kcal_burned INTEGER NOT NULL,
            streak INTEGER NOT NULL
        )
    """)

    cursor.execute("SELECT COUNT(*) FROM rankings")
    count = cursor.fetchone()[0]

    if count == 0:
        cursor.executemany("""
            INSERT INTO rankings (username, kg_lost, kcal_burned, streak)
            VALUES (?, ?, ?, ?)
        """, [
            ("Ronnie Coleman", 12.5, 9800, 21),
            ("Dorian Yates", 10.2, 9100, 18),
            ("Johnnie O. Jackson", 8.7, 8600, 15)
        ])

    conn.commit()
    conn.close()


def ensure_users_table():
    conn = get_db_connection()
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
    return render_template("web.html")


@app.route("/ranking")
def ranking():
    conn = get_db_connection()
    top_users = conn.execute("""
        SELECT username, kg_lost, kcal_burned, streak
        FROM rankings
        ORDER BY kg_lost DESC
        LIMIT 3
    """).fetchall()
    conn.close()

    return render_template("ranking.html", top_users=top_users)


@app.route("/signup", methods=["GET", "POST"])
def signup():
    ensure_users_table()

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirm = request.form.get("confirm")
        dob = request.form.get("dob")
        sex = request.form.get("sex")
        weight = request.form.get("weight")
        height = request.form.get("height")

        if password != confirm:
            return "Passwords do not match"

        conn = get_db_connection()

    
        existing_user = conn.execute(
            "SELECT * FROM users WHERE username = ?",
            (username,)
        ).fetchone()

        if existing_user:
            conn.close()
            return "Username already exists"

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
    ensure_users_table()

    conn = get_db_connection()

    if request.method == "POST":
        password = request.form.get("password")
        dob = request.form.get("dob")
        sex = request.form.get("sex")
        weight = request.form.get("weight")
        height = request.form.get("height")

        conn.execute("""
            UPDATE users
            SET password = ?, dob = ?, sex = ?, weight = ?, height = ?
            WHERE username = ?
        """, (password, dob, sex, weight, height, username))

        conn.commit()

    user = conn.execute("""
        SELECT * FROM users
        WHERE username = ?
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