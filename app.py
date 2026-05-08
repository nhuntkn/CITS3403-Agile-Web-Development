#setup Flask app and routes, connects to database, handles form submission and rendering templates

from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_migrate import Migrate
from models import db, ExerciseSession, SessionExercise, User
from data import exercise_data
from utils import calculate_calories
from datetime import date as current_date

app = Flask(__name__)

app.config['SECRET_KEY'] = '1234'

#configure SQLite database, SQLAlchemy will store the database file inside the Flask instance folder
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///exercise_planner.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app) #attach SQLAlchemy to Flask app

migrate = Migrate(app, db) #set up Flask-Migrate for database migrations
login_manager = LoginManager(app) #set up Flask-Login for user session management
login_manager.login_view = 'login' #redirect to login page if user tries to access protected routes

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id)) #load user from database by ID for Flask-Login

@app.route("/exercise", methods=["GET", "POST"])
@login_required
def exercise():
    #displays Add Session page, if form is submitted, it saves the session and exercises to the database
    
    if request.method == "POST":
        #get the main session data from the form
        date = request.form.get("date")
        if date > current_date.today().isoformat():
            return render_template("exercise.html", exercise_data=exercise_data, username=current_user.username, error="Date cannot be in the future")
        current_weight = float(request.form.get("weight"))
        notes = request.form.get("notes")

        #get the repeated exercise rows from the form
        exercise_names = request.form.getlist("exercise[]")
        activity_levels = request.form.getlist("level[]")
        minutes_list = request.form.getlist("minutes[]")

        user = current_user

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
        return render_template("exercise.html", message="Session added successfully.", exercise_data = exercise_data, username=current_user.username)

    #display the Add Session page before the form is submitted
    return render_template("exercise.html", exercise_data=exercise_data, username=current_user.username)

@app.route("/dashboard")
@login_required
def dashboard(): 
    user = current_user
    username = current_user.username

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

        if not any(char.isalpha() for char in password):
            return render_template("signup.html", error="Password must contain at least one letter")

        if password != confirm:
            return render_template("signup.html", error="Passwords do not match")

        existing = User.query.filter_by(username=username).first()
        if existing:
            return render_template("signup.html", error="Username already exists")

        new_user = User(
            username=username,
            dob=dob,
            gender=gender,
            weight=float(weight) if weight else None,
            height=float(height) if height else None
        )

        new_user.set_password(password)

        db.session.add(new_user)
        db.session.commit()

        login_user(new_user)
        return redirect(url_for('dashboard'))

    return render_template("signup.html", today=current_date.today().isoformat())

@app.route('/check_username')
def check_username():
    username = request.args.get('username', '').strip()

    # prevent empty username query
    if not username:
        return jsonify({
            "exists": False
        })

    user = User.query.filter_by(username=username).first()

    return jsonify({
        "exists": True if user else False
    })

@app.route("/account", methods=["GET", "POST"])
@login_required
def account():
    user = current_user
    username = current_user.username

    sessions = ExerciseSession.query.filter_by(user_id = user.id).all()
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
            if len(new_password) < 6:
                return render_template("account.html", user=user, stats=stats, error="Password must be more than 6 characters long")
            if not any(char.isupper() for char in new_password):
                return render_template("account.html", user=user, stats=stats, error="Password must include at least one uppercase letter")
            if not any(char.islower() for char in new_password):
                return render_template("account.html", user=user, stats=stats, error="Password must include at least one lowercase letter")
            if not any(char in "!@#$%^&*()_+-=[]{}|;':\",./<>?" for char in new_password):
                return render_template("account.html", user=user, stats=stats, error="Password must include at least one special character")
            if new_password != confirm_password:
                return render_template("account.html", user=user, stats=stats, error="Passwords do not match")
            user.set_password(new_password)

        db.session.commit()

    return render_template("account.html", user=user, stats=stats, username=username)

@app.route("/ranking")
def ranking():
    return render_template("ranking.html")

@app.route("/history")
@login_required
def history():
    return render_template("history.html")
    
@app.route("/", methods = ["GET", "POST"])
@app.route("/login", methods = ["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        user = User.query.filter_by(username = username).first()

        if user is None or not user.check_password(password):
            return render_template("login.html", error = "Invalid username or password")
        
        login_user(user)
        return redirect(url_for("dashboard"))
    
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

# with app.app_context():
#     db.create_all()

if __name__ == "__main__":
    app.run(debug=True)