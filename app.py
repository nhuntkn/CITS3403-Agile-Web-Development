from flask import Flask, render_template

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("exercise.html")

@app.route("/dashboard")
def dashboard():
    username = "Jackson"  # TODO: replace with session user once auth is implemented
    return render_template("dashboard.html", username=username)

@app.route("/login")
def login():
    return render_template("login.html")

if __name__ == "__main__":
    app.run(debug=True)
