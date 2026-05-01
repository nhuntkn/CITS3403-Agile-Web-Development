#setup Flask app and routes, connects to database, handles form submission and rendering templates

from flask import Flask, render_template, request, redirect, session, url_for
from models import db, ExerciseSession, SessionExercise, User
from data import exercise_data
from utils import calculate_calories

app = Flask(__name__)

app.config['SECRET_KEY'] = '1234'

#configure SQLite database, SQLAlchemy will store the database file inside the Flask instance folder
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///exercise_planner.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app) #attach SQLAlchemy to Flask app

@app.route("/exercise", methods=["GET", "POST"])
def exercise():
    if "username" not in session:
        return redirect(url_for("login"))
    
    #displays Add Session page, if form is submitted, it saves the session and exercises to the database
    
    if request.method == "POST":
        #get the main session data from the form
        date = request.form.get("date")
        current_weight = float(request.form.get("weight"))
        notes = request.form.get("notes")

        #get the repeated exercise rows from the form
        exercise_names = request.form.getlist("exercise[]")
        activity_levels = request.form.getlist("level[]")
        minutes_list = request.form.getlist("minutes[]")

        user = User.query.filter_by(username = session["username"]).first()
        #create the main exercise session record
        new_session = ExerciseSession(
            date=date,
            current_weight=current_weight,
            notes=notes,
            total_calories=0,
            user_id = user.id
        )

        #add the session first to get an ID, ID needed for the foreign key in exercises
        db.session.add(new_session)
        db.session.flush()

        total_calories = 0

        #save each exercise row that belongs to this session
        for i in range(len(exercise_names)):
            exercise_name = exercise_names[i]
            activity_level = activity_levels[i]
            minutes = int(minutes_list[i])

            #find MET value for the exercise and activity level
            met_value = exercise_data[exercise_name][activity_level]

            calories = calculate_calories(
                met_value,
                minutes,
                current_weight
            )

            #create the database record for this exercise row
            new_exercise = SessionExercise(
                exercise_name=exercise_name,
                activity_level=activity_level,
                minutes=minutes,
                met_value=met_value,
                calories=calories,
                session_id=new_session.id
            )

            total_calories = total_calories + calories
            db.session.add(new_exercise)

        #store the total calories for the full session
        new_session.total_calories = round(total_calories, 2)

        #save everything to the database
        db.session.commit()
        #reload page and show success message
        return render_template("exercise.html", message="Session added successfully.", exercise_data = exercise_data)

    #display the Add Session page before the form is submitted
    return render_template("exercise.html", exercise_data=exercise_data)

@app.route("/dashboard")
def dashboard():
    if "username" not in session:
        return redirect(url_for("login"))
    
    username = session["username"] 
    user = User.query.filter_by(username = username).first()
    start_weight = user.weight if user else None
    calorie_goal = user.calorie_goal if user and user.calorie_goal else 1000

    sessions = ExerciseSession.query.filter_by(user_id = user.id).order_by(ExerciseSession.date.asc()).all()

    sessions_data = [
        {
            "date" : s.date,
            "current_weight" : s.current_weight,
            "total_calories" : s.total_calories,
        } 
        for s in sessions
    ]

    return render_template("dashboard.html", username = username, sessions_data = sessions_data, start_weight = start_weight, 
                           user_height = user.height if user else None, calorie_goal = calorie_goal)

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirm = request.form.get("confirm")

        dob = request.form.get("dob")
        gender = request.form.get("gender")
        weight = request.form.get("weight")
        height = request.form.get("height")

        if not password or len(password) < 6:
            return render_template("signup.html", error="Password must be at least 6 characters long")

        if not any(char.isupper() for char in password):
            return render_template("signup.html", error="Password must include at least one uppercase letter")

        if not any(char.islower() for char in password):
            return render_template("signup.html", error="Password must include at least one lowercase letter")

        if not any(char in "!@#$%^&*()_+-=[]{}|;':\",./<>?" for char in password):
            return render_template("signup.html", error="Password must include at least one special character")

        if password != confirm:
            return render_template("signup.html", error="Passwords do not match")

        existing = User.query.filter_by(username=username).first()
        if existing:
            return render_template("signup.html", error="Username already exists")

        new_user = User(
            username=username,
            password=password,
            dob=dob,
            gender=gender,
            weight=float(weight) if weight else None,
            height=float(height) if height else None
        )

        db.session.add(new_user)
        db.session.commit()

        session['username'] = username
        return redirect(url_for('dashboard'))

    return render_template("signup.html")


@app.route("/profile", methods=["GET", "POST"])
def profile():
    if 'username' not in session:
        return redirect('/login')

    user = User.query.filter_by(username=session['username']).first()

    sessions = ExerciseSession.query.all()
    total_calories = sum(s.total_calories for s in sessions)
    total_sessions = len(sessions)

    stats = {
        "total_calories": round(total_calories, 2),
        "total_sessions": total_sessions
    }

    if request.method == 'POST':
        user.dob = request.form.get('dob')
        user.gender = request.form.get('gender')

        weight = request.form.get('weight')
        height = request.form.get('height')

        user.weight = float(weight) if weight else None
        user.height = float(height) if height else None

        calorie_goal = request.form.get("calorie_goal")
        user.calorie_goal = int(calorie_goal) if calorie_goal else 1000

        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        if new_password:
            if len(new_password) <= 6:
                return render_template("profile.html", user=user, stats=stats, error="Password must be more than 6 characters long")
            if not any(char.isupper() for char in new_password):
                return render_template("profile.html", user=user, stats=stats, error="Password must include at least one uppercase letter")
            if not any(char.islower() for char in new_password):
                return render_template("profile.html", user=user, stats=stats, error="Password must include at least one lowercase letter")
            if not any(char in "!@#$%^&*()_+-=[]{}|;':\",./<>?" for char in new_password):
                return render_template("profile.html", user=user, stats=stats, error="Password must include at least one special character")
            if new_password != confirm_password:
                return render_template("profile.html", user=user, stats=stats, error="Passwords do not match")
            user.password = new_password

        db.session.commit()

    return render_template("profile.html", user=user, stats=stats, username = session["username"])

@app.route("/ranking")
def ranking():
    if 'username' not in session:
        return redirect(url_for("login"))
    return render_template("ranking.html")

@app.route("/history")
def history():
    if 'username' not in session:
        return redirect(url_for("login"))
    return render_template("history.html")
    
@app.route("/", methods = ["GET", "POST"])
@app.route("/login", methods = ["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        user = User.query.filter_by(username = username, password = password).first()
        if user:
            session["username"] = user.username
            return redirect(url_for("dashboard"))
        return render_template("login.html", error = "Invalid username or password")
    
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("username", None)
    return redirect(url_for("login"))

with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True)