#setup Flask app and routes, connects to database, handles form submission and rendering templates

import os
import random
import time
import smtplib

from email.message import EmailMessage
from flask import Flask, render_template, request, redirect, url_for, jsonify, session, abort
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_migrate import Migrate
from flask_wtf import CSRFProtect
from flask_wtf.csrf import CSRFError
from models import db, ExerciseSession, SessionExercise, User, Share, Friend, AIFeedback
from data import exercise_data
from utils import calculate_calories, generateAiFeedbackText, getStartWeek, buildFeedback, buildFeedbackHash
from datetime import date as current_date, timedelta
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

load_dotenv() #load environment variables from .env file

app = Flask(__name__)
secret_key = os.environ.get('SECRET_KEY')
if not secret_key:
    raise RuntimeError("SECRET_KEY environment variable must be set before starting the app")

app.config['SECRET_KEY'] = secret_key

#configure SQLite database, SQLAlchemy will store the database file inside the Flask instance folder
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL", "sqlite:///exercise_planner.db")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
#configure for forgot password function
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
#Avatar MAX content length
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024

db.init_app(app) #attach SQLAlchemy to Flask app

csrf = CSRFProtect(app)
migrate = Migrate(app, db) #set up Flask-Migrate for database migrations
login_manager = LoginManager(app) #set up Flask-Login for user session management
login_manager.login_view = 'login' #redirect to login page if user tries to access protected routes


@app.errorhandler(CSRFError)
def handle_csrf_error(error):
    if request.is_json or request.path.startswith("/api/") or request.path == "/dashboard/ai-feedback":
        return jsonify({"error": "Invalid or missing CSRF token"}), 400
    return render_template("csrf_error.html", reason=error.description), 400

def parse_location_fields(latitude_raw, longitude_raw):
    if not latitude_raw and not longitude_raw:
        return None, None, None

    if not latitude_raw or not longitude_raw:
        return None, None, "Please select both latitude and longitude for the activity location"

    try:
        latitude = float(latitude_raw)
        longitude = float(longitude_raw)
    except ValueError:
        return None, None, "Activity location is invalid"

    if latitude < -90 or latitude > 90:
        return None, None, "Latitude must be between -90 and 90"
    if longitude < -180 or longitude > 180:
        return None, None, "Longitude must be between -180 and 180"

    return latitude, longitude, None


def send_reset_email(to_email, code):
    if not app.config["MAIL_USERNAME"] or not app.config["MAIL_PASSWORD"]:
        raise RuntimeError("Email credentials are not configured")

    msg = EmailMessage()

    msg["Subject"] = "Password Reset Verification Code"
    msg["From"] = app.config["MAIL_USERNAME"]
    msg["To"] = to_email

    msg.set_content(
        f"Your verification code is: {code}\n\n"
        "This code will expire in 5 minutes."
    )

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(
            app.config["MAIL_USERNAME"],
            app.config["MAIL_PASSWORD"]
        )

        smtp.send_message(msg)


def clear_reset_session():
    session.pop("reset_code", None)
    session.pop("reset_email", None)
    session.pop("reset_time", None)
    session.pop("reset_attempts", None)
    session.pop("reset_verified", None)


def user_avatar_url(user):
    if not user or not user.avatar:
        return None

    avatar_path = os.path.join(app.root_path, "static", "uploads", user.avatar)
    if not os.path.isfile(avatar_path):
        return None

    return url_for("static", filename="uploads/" + user.avatar)

@app.context_processor
def inject_avatar_helpers():
    return {"user_avatar_url": user_avatar_url}

def user_avatar_payload(user):
    return {
        "username": user.username,
        "avatar_url": user_avatar_url(user)
    }

@app.route("/dashboard/ai-feedback", methods=["POST"])
@login_required
def dashAiFeedback():
    today = current_date.today()
    today_str = today.isoformat()
    week_start = getStartWeek(today)
    week_start_str = week_start.isoformat()

    weekly_sessions = ExerciseSession.query.filter(
        ExerciseSession.user_id == current_user.id,
        ExerciseSession.date >= week_start_str,
        ExerciseSession.date <= today_str
    ).order_by(ExerciseSession.date.asc()).all()

    if not weekly_sessions:
        return jsonify({
            "error": "No exercise sessions found for this week yet. Add a session first, then generate feedback."
        }), 400

    current_data_hash = buildFeedbackHash(weekly_sessions)

    existing_feedback = AIFeedback.query.filter_by(
        user_id=current_user.id,
        generated_date=today_str
    ).first()

    if existing_feedback and existing_feedback.data_hash == current_data_hash:
        return jsonify({
            "feedback": existing_feedback.feedback_text,
            "cached": True
        })

    prompt = buildFeedback(
        current_user,
        weekly_sessions,
        week_start,
        today
    )

    try:
        feedback_text = generateAiFeedbackText(prompt)

    except Exception as error:
        error_text = str(error)

        if "API key is not set" in error_text:
            message = "AI feedback is not configured yet. Please add the required API key in the .env file before using this feature."
        elif "insufficient_quota" in error_text or "exceeded your current quota" in error_text:
            message = "AI feedback is currently unavailable because the API quota has been reached. Please try again later."
        else:
            message = "AI feedback could not be generated right now. Please try again later."

        return jsonify({
            "error": message
        }), 503

    if existing_feedback:
        existing_feedback.week_start_date = week_start_str
        existing_feedback.data_hash = current_data_hash
        existing_feedback.feedback_text = feedback_text
    else:
        saved_feedback = AIFeedback(
            user_id=current_user.id,
            week_start_date=week_start_str,
            generated_date=today_str,
            data_hash=current_data_hash,
            feedback_text=feedback_text
        )

        db.session.add(saved_feedback)

    db.session.commit()

    return jsonify({
        "feedback": feedback_text,
        "cached": False
    })

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id)) #load user from database by ID for Flask-Login

@app.route("/exercise", methods=["GET", "POST"])
@login_required
def exercise():
    #displays Add Session page, if form is submitted, it saves the session and exercises to the database
    
    if request.method == "POST":
        #get the main session data from the form
        date = request.form.get("date", "").strip()

        if not date:
            return render_template("exercise.html", exercise_data=exercise_data, username=current_user.username, error="Date is required")

        try:
            submitted_date = current_date.fromisoformat(date)
        except ValueError:
            return render_template("exercise.html", exercise_data=exercise_data, username=current_user.username, error="Invalid date entered")

        if submitted_date > current_date.today():
            return render_template("exercise.html", exercise_data=exercise_data, username=current_user.username, error="Date cannot be in the future")

        try:
            current_weight = float(request.form.get("weight"))
        except (TypeError, ValueError):
            return render_template("exercise.html", exercise_data=exercise_data, username=current_user.username, error="Invalid weight entered")

        if current_weight < 1 or current_weight > 300:
            return render_template("exercise.html", exercise_data=exercise_data, username=current_user.username, error="Weight must be between 1 and 300 kg")

        current_weight = round(current_weight, 2)

        notes = request.form.get("notes", "").strip()
        if len(notes) > 800:
            return render_template("exercise.html", exercise_data=exercise_data, username=current_user.username, error="Notes cannot exceed 800 characters")

        latitude, longitude, location_error = parse_location_fields(
            request.form.get("latitude"),
            request.form.get("longitude")
        )

        if location_error:
            return render_template("exercise.html", exercise_data=exercise_data, username=current_user.username, error=location_error)

        #get the repeated exercise rows from the form
        exercise_names = request.form.getlist("exercise[]")
        activity_levels = request.form.getlist("level[]")
        minutes_list = request.form.getlist("minutes[]")

        if not exercise_names:
            return render_template("exercise.html", exercise_data=exercise_data, username=current_user.username, error="Please add at least one exercise")

        if not (len(exercise_names) == len(activity_levels) == len(minutes_list)):
            return render_template("exercise.html", exercise_data=exercise_data, username=current_user.username, error="Exercise details are incomplete")

        parsed_exercises = []
        for i in range(len(exercise_names)):
            exercise_name = exercise_names[i].strip()
            activity_level = activity_levels[i].strip()

            if not exercise_name or not activity_level:
                return render_template("exercise.html", exercise_data=exercise_data, username=current_user.username, error="Please complete all exercise fields")

            if exercise_name not in exercise_data:
                return render_template("exercise.html", exercise_data=exercise_data, username=current_user.username, error="Invalid exercise selected")

            if activity_level not in exercise_data[exercise_name]:
                return render_template("exercise.html", exercise_data=exercise_data, username=current_user.username, error="Invalid activity level selected")

            try:
                minutes = int(minutes_list[i])
            except (TypeError, ValueError):
                return render_template("exercise.html", exercise_data=exercise_data, username=current_user.username, error="Exercise duration must be a valid number.")

            if minutes < 1 or minutes > 300:
                return render_template("exercise.html", exercise_data=exercise_data, username=current_user.username, error="Exercise duration must be between 1 and 300 minutes.")

            parsed_exercises.append((exercise_name, activity_level, minutes))

        user = current_user

        #create the main exercise session record
        new_session = ExerciseSession(
            date=date,
            current_weight=current_weight,
            notes=notes,
            total_calories=0,
            latitude=latitude,
            longitude=longitude,
            user_id = user.id
        )

        #add the session first to get an ID, ID needed for the foreign key in exercises
        db.session.add(new_session)
        db.session.flush()

        total_calories = 0

        #save each exercise row that belongs to this session
        for exercise_name, activity_level, minutes in parsed_exercises:
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

        # update current user weight
        user.weight = current_weight

        existing_day = db.session.query(
            db.func.coalesce(db.func.sum(ExerciseSession.total_calories), 0)
        ).filter(
            ExerciseSession.user_id == user.id,
            ExerciseSession.date == date,
            ExerciseSession.id != new_session.id
        ).scalar()
        if existing_day + total_calories > 10000:
            db.session.rollback()
            return render_template("exercise.html", exercise_data=exercise_data,
                                   username=current_user.username,
                                   error="Daily calorie total cannot exceed 10,000 kcal")

        #save everything to the database
        db.session.commit()

        friends = User.query.join(Friend, (
            ((Friend.sender_id == current_user.id) & (Friend.receiver_id == User.id)) |
            ((Friend.receiver_id == current_user.id) & (Friend.sender_id == User.id))
        )).filter(Friend.status == "accepted").all()

        #reload page and show success message
        return render_template("exercise.html", message="Session added successfully.",
                               exercise_data = exercise_data, username=current_user.username,
                               new_session_id = new_session.id, friends = friends)

    #display the Add Session page before the form is submitted
    return render_template("exercise.html", exercise_data=exercise_data, username=current_user.username)

@app.route("/dashboard")
@login_required
def dashboard(): 
    user = current_user

    start_weight = user.start_weight if user else None
    calorie_goal = user.calorie_goal if user and user.calorie_goal else 1000

    sessions = ExerciseSession.query.filter_by(user_id = user.id).order_by(ExerciseSession.date.asc()).all()

    current_weight = user.weight if user else None
    sessions_data = [
        {
            "date" : s.date,
            "current_weight" : s.current_weight,
            "total_calories" : s.total_calories,
        } 
        for s in sessions
    ]

    return render_template(
        "dashboard.html",
        sessions_data=sessions_data,
        start_weight=start_weight,
        current_weight=current_weight,
        user_height=user.height if user else None,
        calorie_goal=calorie_goal,
        username=current_user.username
    )

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        confirm = request.form.get("confirm")

        dob = request.form.get("dob")
        gender = request.form.get("gender")
        weight = request.form.get("weight")
        height = request.form.get("height")

        if not password or len(password) < 12:
            return render_template("signup.html", error="Password must be at least 12 characters long")

        if not any(char.isalpha() for char in password):
            return render_template("signup.html", error="Password must contain at least one letter")

        if not any(char in "!@#$%^&*" for char in password):
            return render_template(
                "signup.html",
                error="Password must contain at least one special character"
            )

        if password != confirm:
            return render_template("signup.html", error="Passwords do not match")

        existing = User.query.filter_by(username=username).first()
        if existing:
            return render_template("signup.html", error="Username already exists")

        existing_email = User.query.filter_by(email=email).first()
        if existing_email:
            return render_template(
                "signup.html",
                error="Email already exists"
            )

        try:
            weight_value = float(weight)
            height_value = float(height)
        except (TypeError, ValueError):
            return render_template("signup.html", today=current_date.today().isoformat(),
                                   error="Weight and height must be valid numbers")

        if weight_value < 1 or weight_value > 300:
            return render_template("signup.html", today=current_date.today().isoformat(),
                                   error="Weight must be between 1 and 300 kg")

        if height_value < 50 or height_value > 250:
            return render_template("signup.html", today=current_date.today().isoformat(),
                                   error="Height must be between 50 and 250 cm")

        if round(weight_value, 2) != weight_value:
            return render_template("signup.html", today=current_date.today().isoformat(),
                                   error="Weight can only have up to 2 decimal places")

        if round(height_value, 2) != height_value:
            return render_template("signup.html", today=current_date.today().isoformat(),
                                   error="Height can only have up to 2 decimal places")

        new_user = User(
            username=username,
            email=email,
            dob=dob,
            gender=gender,
            weight=weight_value,
            start_weight=weight_value,
            height=height_value
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

@app.route("/ranking")
@login_required
def ranking():
    period_options = {
        "all": ("All Time", None),
        "daily": ("Daily", 0),
        "weekly": ("Weekly", 6),
        "monthly": ("Monthly", 29),
        "half_year": ("Half Yearly", 182)
    }
    selected_period = request.args.get("period", "all")
    if selected_period not in period_options:
        selected_period = "all"

    today = current_date.today()
    period_label, days_back = period_options[selected_period]
    start_date = None if days_back is None else (today - timedelta(days=days_back)).isoformat()
    end_date = today.isoformat()

    users = User.query.all()
    ranking_data = []

    for user in users:
        sessions = ExerciseSession.query.filter_by(user_id=user.id).order_by(ExerciseSession.date.asc()).all()
        filtered_sessions = [
            session for session in sessions
            if start_date is None or (start_date <= session.date <= end_date)
        ]
        total_calories = sum(session.total_calories for session in filtered_sessions)

        ranking_data.append({
            "username": user.username,
            "avatar_url": user_avatar_url(user),
            "total_calories": round(total_calories, 2),
            "total_sessions": len(filtered_sessions),
            "has_sessions": len(filtered_sessions) > 0
        })

    ranking_data.sort(key=lambda item: (item["has_sessions"], item["total_calories"]), reverse=True)
    return render_template("ranking.html", username=current_user.username, ranking_data=ranking_data,
                           period_options=period_options, selected_period=selected_period,
                           period_label=period_label)

@app.route("/history")
@login_required
def history():
    sessions = ExerciseSession.query.filter_by(user_id=current_user.id).order_by(ExerciseSession.date.desc()).all()
    friends = User.query.join(Friend, (
        ((Friend.sender_id == current_user.id) & (Friend.receiver_id == User.id)) |
        ((Friend.receiver_id == current_user.id) & (Friend.sender_id == User.id))
    )).filter(Friend.status == "accepted").all()
    location_data = [
        {
            "id": session.id,
            "date": session.date,
            "current_weight": session.current_weight,
            "total_calories": session.total_calories,
            "latitude": session.latitude,
            "longitude": session.longitude
        }
        for session in sessions
        if session.latitude is not None and session.longitude is not None
    ]
    return render_template("history.html", username=current_user.username, sessions=sessions,
                           location_data=location_data, friends=friends)

@app.route("/history/<int:session_id>/delete", methods=["POST"])
@login_required
def delete_session(session_id):
    session = db.session.get(ExerciseSession, session_id)

    if session is None or session.user_id != current_user.id:
        abort(404)

    Share.query.filter_by(session_id=session.id).delete()
    db.session.delete(session)
    db.session.commit()

    return redirect(url_for("history"))
    
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

@app.route("/forum", methods = ["GET", "POST"])
@login_required
def forum():
    if request.method == "POST":
        action = request.form.get("action", "like")

        if action == "share":
            session_id = request.form.get("session_id")
            receiver_id = request.form.get("receiver_id")
            if session_id and receiver_id:
                friendship = Friend.query.filter(
                    ((Friend.sender_id == current_user.id) & (Friend.receiver_id == int(receiver_id))) |
                    ((Friend.sender_id == int(receiver_id)) & (Friend.receiver_id == current_user.id)),
                    Friend.status == "accepted"
                ).first()
                session = db.session.get(ExerciseSession, int(session_id))
                if friendship and session and session.user_id == current_user.id:
                    share = Share(sender_id = current_user.id,
                                  receiver_id = int(receiver_id),
                                  session_id = int(session_id))
                    db.session.add(share)
                    db.session.commit()
            return redirect(url_for('forum', tab = 'sent'))

        else:
            share_id = request.form.get("share_id")
            if share_id:
                share = db.session.get(Share, int(share_id))
                if share and share.receiver_id == current_user.id:
                    share.liked = not share.liked
                    db.session.commit()
            return redirect(url_for('forum', tab = 'received'))

    tab = request.args.get('tab', 'sent')
    sent = Share.query.filter_by(sender_id = current_user.id).order_by(Share.created_at.desc()).all()
    received = Share.query.filter_by(receiver_id = current_user.id).order_by(Share.created_at.desc()).all()
    return render_template("forum.html", tab = tab, sent = sent,
                           received = received, username = current_user.username)


#-------!!  account  -------#
@app.route("/account", methods=["GET","POST"])
@login_required
def account():
    user = current_user

    def render_account(error=None):
        return render_template("account.html",
            user=user,
            current_date=current_date.today().isoformat(),
            error=error,
            username=user.username
        )

    if request.method == "POST":
        form = request.form.get("form_type")

        # update profile
        if form == "update_profile":

            dob = request.form.get("dob")
            gender = request.form.get("gender")
            weight = request.form.get("weight")
            start_weight = request.form.get("start_weight")
            height = request.form.get("height")
            calorie = request.form.get("calorie_goal")

            today = current_date.today().isoformat()

            if dob and dob > today:
                return render_account("Invalid DOB")

            if gender not in ["Male","Female","",None]:
                return render_account("Invalid gender")

            try:
                if weight:
                    weight_value = round(float(weight), 2)
                    if weight_value < 1 or weight_value > 300:
                        return render_account("Current weight must be between 1 and 300 kg")
                    user.weight = weight_value

                if start_weight:
                    start_weight_value = round(float(start_weight), 2)
                    if start_weight_value < 1 or start_weight_value > 300:
                        return render_account("Start weight must be between 1 and 300 kg")
                    user.start_weight = start_weight_value

                if height:
                    height_value = round(float(height), 2)
                    if height_value < 1 or height_value > 300:
                        return render_account("Height must be between 1 and 300 cm")
                    user.height = height_value

                if calorie:
                    calorie_value = int(calorie)
                    if calorie_value <= 0:
                        return render_account("Daily calorie goal must be greater than 0")
                    user.calorie_goal = calorie_value

            except ValueError:
                return render_account("Invalid number")

            user.dob, user.gender = dob, gender

            # avatar
            f = request.files.get('avatar')
            if f and f.filename:
                if f.filename.rsplit('.',1)[-1].lower() not in ['jpg','jpeg','png']:
                    return render_account("Invalid image")

                # create upload folder if not exists
                upload_path = os.path.join(app.root_path, 'static', 'uploads')
                os.makedirs(upload_path, exist_ok=True)

                # delete old avatar
                if user.avatar:
                    old_path = os.path.join(upload_path, user.avatar)
                    if os.path.exists(old_path):
                        os.remove(old_path)

                # generate unique filename
                import time
                name = str(int(time.time())) + "_" + secure_filename(f.filename)

                # save new avatar
                f.save(os.path.join(upload_path, name))
                user.avatar = name

        # change password
        elif form == "change_password":
            pw = request.form.get("new_password","").strip()
            cf = request.form.get("confirm_password","").strip()
            today = current_date.today().isoformat()

            if (
                not pw
                or len(pw) < 12
                or not any(c.isalpha() for c in pw)
                or not any(c in "!@#$%^&*" for c in pw)
            ):
                return render_account("Invalid password")

            if pw != cf:
                return render_account("Mismatch")

            if user.check_password(pw):
                return render_account("New password cannot be the same as old password")

            user.set_password(pw)

        db.session.commit()
        return redirect(url_for("account"))

    return render_account()

#---!  add friend  ---#
@app.route('/api/search_users')
@login_required
def search_users():
    query = request.args.get('query', '').strip()

    if not query:
        return jsonify([])

    users = User.query.filter(
        User.username.ilike(f"%{query}%"),
        User.username != current_user.username
    ).limit(10).all()

    result = [user_avatar_payload(u) for u in users]

    return jsonify(result)

@app.route('/api/add_friend', methods=['POST'])
@login_required
def add_friend():
    data = request.get_json()
    username = data.get("username", "").strip()

    # find target user by username
    target = User.query.filter_by(username=username).first()
    if not target:
        return jsonify({"error": "invalid user"}), 404

    # prevent adding yourself
    if target.id == current_user.id:
        return jsonify({"error": "cannot add yourself"}), 400

    # check existing relationship (both directions)
    existing = Friend.query.filter(
        ((Friend.sender_id == current_user.id) & (Friend.receiver_id == target.id)) |
        ((Friend.sender_id == target.id) & (Friend.receiver_id == current_user.id))
    ).first()

    if existing:
        # already friends
        if existing.status == "accepted":
            return jsonify({"message": "already friends"}), 200

        # request already sent by current user
        if existing.sender_id == current_user.id:
            return jsonify({"message": "already sent"}), 200

        # target has sent request → auto accept
        if existing.sender_id == target.id:
            existing.status = "accepted"
            db.session.commit()
            return jsonify({"message": "friend added"}), 200

    # create new friend request
    new_req = Friend(
        sender_id=current_user.id,
        receiver_id=target.id,
        status="pending"
    )

    db.session.add(new_req)
    db.session.commit()

    return jsonify({"message": "request sent"}), 200

@app.route('/api/friends')
@login_required
def get_friends():

    # get current user id
    user_id = current_user.id

    # find pending requests sent to current user
    pending_reqs = Friend.query.filter_by(
        receiver_id=user_id,
        status="pending"
    ).all()

    # collect pending usernames
    pending = []
    for r in pending_reqs:
        sender = User.query.get(r.sender_id)
        if sender:
            pending.append(user_avatar_payload(sender))

    # find all accepted relationships
    relations = Friend.query.filter_by(status="accepted").all()

    # collect friend usernames (both directions)
    friends = []
    for r in relations:

        # current user is sender → friend is receiver
        if r.sender_id == user_id:
            u = User.query.get(r.receiver_id)
            if u:
                friends.append(user_avatar_payload(u))

        # current user is receiver → friend is sender
        elif r.receiver_id == user_id:
            u = User.query.get(r.sender_id)
            if u:
                friends.append(user_avatar_payload(u))

    # sort lists for stable display
    pending.sort(key=lambda item: item["username"].lower())
    friends.sort(key=lambda item: item["username"].lower())

    # return result for frontend
    return jsonify({
        "pending": pending,
        "friends": friends
    })

@app.route('/api/accept_friend', methods=['POST'])
@login_required
def accept_friend():

    # get request data
    data = request.get_json()
    username = data.get("username", "").strip()

    # find target user by username
    target = User.query.filter_by(username=username).first()
    if not target:
        return jsonify({"error": "invalid user"}), 404

    # find pending request sent to current user
    req = Friend.query.filter_by(
        sender_id=target.id,
        receiver_id=current_user.id,
        status="pending"
    ).first()

    # check if request exists
    if not req:
        return jsonify({"error": "no request found"}), 404

    # accept request
    req.status = "accepted"
    db.session.commit()

    # return result
    return jsonify({"message": "friend added"}), 200

@app.route('/api/reject_friend', methods=['POST'])
@login_required
def reject_friend():

    # get request data
    data = request.get_json()
    username = data.get("username", "").strip()

    # find target user by username
    target = User.query.filter_by(username=username).first()
    if not target:
        return jsonify({"error": "invalid user"}), 404

    # find pending request sent to current user
    req = Friend.query.filter_by(
        sender_id=target.id,
        receiver_id=current_user.id,
        status="pending"
    ).first()

    # check if request exists
    if not req:
        return jsonify({"error": "no request found"}), 404

    # delete request
    db.session.delete(req)
    db.session.commit()

    # return result
    return jsonify({"message": "request rejected"}), 200

@app.route('/api/delete_friend', methods=['POST'])
@login_required
def delete_friend():

    # get request data
    data = request.get_json()
    username = data.get("username", "").strip()

    # find target user
    target = User.query.filter_by(username=username).first()

    if not target:
        return jsonify({"error": "invalid user"}), 404

    # find friendship (both directions)
    friendship = Friend.query.filter(
        (
            (Friend.sender_id == current_user.id) &
            (Friend.receiver_id == target.id)
        )
        |
        (
            (Friend.sender_id == target.id) &
            (Friend.receiver_id == current_user.id)
        ),
        Friend.status == "accepted"
    ).first()

    # friendship not found
    if not friendship:
        return jsonify({"error": "friendship not found"}), 404

    # delete related shares in both directions
    Share.query.filter(
        (
            (Share.sender_id == current_user.id) &
            (Share.receiver_id == target.id)
        )
        |
        (
            (Share.sender_id == target.id) &
            (Share.receiver_id == current_user.id)
        )
    ).delete(synchronize_session=False)

    # delete friendship
    db.session.delete(friendship)

    # save changes
    db.session.commit()

    return jsonify({"message": "friend deleted"}), 200

@app.route("/forgot_password", methods=["GET", "POST"])
def forgot_password():

    if request.method == "POST":

        action = request.form.get("action")

        # STEP 1: send code
        if action == "send_code":

            email = request.form.get("email", "").strip()

            user = User.query.filter_by(email=email).first()

            if not user:
                return render_template(
                    "forgot_password.html",
                    error="Email not found"
                )

            verification_code = str(random.randint(100000, 999999))
            try:
                send_reset_email(email, verification_code)
            except:
                return render_template(
                    "forgot_password.html",
                    error="Failed to send verification email"
                )

            session["reset_code"] = verification_code
            session["reset_email"] = email
            session["reset_time"] = time.time()
            session["reset_attempts"] = 0
            session["reset_verified"] = False

            return render_template(
                "forgot_password.html",
                message="Verification code sent",
                show_code=True
            )

        # STEP 2: verify code
        elif action == "verify_code":

            code = request.form.get("code", "").strip()

            attempts = session.get("reset_attempts", 0)

            if attempts >= 5:

                clear_reset_session()

                return render_template(
                    "forgot_password.html",
                    error="Too many incorrect attempts"
                )

            if time.time() - session.get("reset_time", 0) > 300:

                clear_reset_session()

                return render_template(
                    "forgot_password.html",
                    error="Verification code expired"
                )

            if code != session.get("reset_code"):

                session["reset_attempts"] = attempts + 1

                return render_template(
                    "forgot_password.html",
                    error="Invalid verification code",
                    show_code=True
                )

            session["reset_verified"] = True

            return render_template(
                "forgot_password.html",
                show_code=True,
                show_reset=True
            )

        # STEP 3: reset password
        elif action == "reset":

            email = session.get("reset_email")
            user = User.query.filter_by(email=email).first()
            if not user:
                return redirect(url_for("forgot_password"))
            new_password = request.form.get("new_password", "")
            confirm_password = request.form.get("confirm_password", "")

            if time.time() - session.get("reset_time", 0) > 300:

                clear_reset_session()

                return render_template(
                    "forgot_password.html",
                    error="Verification code expired"
                )

            if not session.get("reset_verified"):

                return render_template(
                    "forgot_password.html",
                    error="Please verify your code before resetting your password",
                    show_code=True
                )

            if len(new_password) < 12:

                return render_template(
                    "forgot_password.html",
                    error="Password must be at least 12 characters",
                    show_code=True,
                    show_reset=True
                )

            if not any(char.isalpha() for char in new_password):

                return render_template(
                    "forgot_password.html",
                    error="Password must contain at least one letter",
                    show_code=True,
                    show_reset=True
                )

            if not any(char in "!@#$%^&*" for char in new_password):

                return render_template(
                    "forgot_password.html",
                    error="Password must contain at least one special character",
                    show_code=True,
                    show_reset=True
                )

            if new_password != confirm_password:

                return render_template(
                    "forgot_password.html",
                    error="Passwords do not match",
                    show_code=True,
                    show_reset=True
                )

            if user.check_password(new_password):

                return render_template(
                    "forgot_password.html",
                    error="New password cannot be the same as old password",
                    show_code=True,
                    show_reset=True
                )

            user.set_password(new_password)

            db.session.commit()

            clear_reset_session()

            return redirect(url_for("login"))

    return render_template(
        "forgot_password.html",
        show_reset=False,
        show_code=False
    )

if __name__ == "__main__":
    app.run(debug=True)
