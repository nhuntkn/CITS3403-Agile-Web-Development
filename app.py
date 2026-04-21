from flask import Flask, render_template
import sqlite3

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


if __name__ == "__main__":
    init_db()
    app.run(debug=True)