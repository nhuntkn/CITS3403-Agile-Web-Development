#setup Flask app and routes, connects to database, handles form submission and rendering templates

from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_migrate import Migrate
from models import db, ExerciseSession, SessionExercise, User, Friend, Message, Like
from data import exercise_data
from utils import calculate_calories
from datetime import date as current_date
from werkzeug.utils import secure_filename
import os

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

    return render_template("signup.html")

@app.route('/check_username')
def check_username():
    username = request.args.get('username')

    user = User.query.filter_by(username=username).first()

    return jsonify({
        "exists": True if user else False
    })

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


#-------!!  account  -------#
@app.route("/account", methods=["GET","POST"])
@login_required
def account():
    user = current_user

    # stats
    sessions = ExerciseSession.query.filter_by(user_id=user.id).all()
    total_calories = round(sum(s.total_calories for s in sessions),2)
    total_sessions = len(sessions)
    bmi = round(user.weight/((user.height/100)**2),2) if user.weight and user.height else None

    if request.method == "POST":
        form = request.form.get("form_type")

        # update profile
        if form == "update_profile":

            dob = request.form.get("dob")
            gender = request.form.get("gender")
            weight = request.form.get("weight")
            height = request.form.get("height")
            calorie = request.form.get("calorie_goal")

            if dob and dob > current_date.today().isoformat():
                return render_template("account.html", user=user, bmi=bmi, total_calories=total_calories, total_sessions=total_sessions, error="Invalid DOB")

            if gender not in ["Male","Female","",None]:
                return render_template("account.html", user=user, bmi=bmi, total_calories=total_calories, total_sessions=total_sessions, error="Invalid gender")

            try:
                user.weight = float(weight) if weight and float(weight)>0 else None
                user.height = float(height) if height and float(height)>0 else None
                user.calorie_goal = int(calorie) if calorie and int(calorie)>0 else user.calorie_goal
            except:
                return render_template("account.html", user=user, bmi=bmi, total_calories=total_calories, total_sessions=total_sessions, error="Invalid number")

            user.dob, user.gender = dob, gender

            # avatar
            f = request.files.get('avatar')
            if f and f.filename:
                if f.filename.rsplit('.',1)[-1].lower() not in ['jpg','jpeg','png']:
                    return render_template("account.html", user=user, bmi=bmi, total_calories=total_calories, total_sessions=total_sessions, error="Invalid image")

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
            db.session.commit()

        # change password
        elif form == "change_password":
            pw = request.form.get("new_password","").strip()
            cf = request.form.get("confirm_password","").strip()

            if not pw or len(pw)<6 or not any(c.isalpha() for c in pw):
                return render_template("account.html", user=user, bmi=bmi, total_calories=total_calories, total_sessions=total_sessions, error="Invalid password")

            if pw != cf:
                return render_template("account.html", user=user, bmi=bmi, total_calories=total_calories, total_sessions=total_sessions, error="Mismatch")

            if user.check_password(pw):
                return render_template("account.html", user=user, bmi=bmi, total_calories=total_calories, total_sessions=total_sessions, error="Same as old")

            user.set_password(pw)

        db.session.commit()
        return redirect(url_for("account"))

    return render_template("account.html",
        user=user,
        bmi=bmi,
        total_calories=total_calories,
        total_sessions=total_sessions
    )

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

    result = [{"username": u.username} for u in users]

    return jsonify(result)

@app.route('/api/add_friend', methods=['POST'])
@login_required
def add_friend():
    data = request.get_json()
    username = data.get("username", "").strip()

    # find target user by username
    target = User.query.filter_by(username=username).first()
    if not target:
        return jsonify({"error": "invalid user"})

    # prevent adding yourself
    if target.id == current_user.id:
        return jsonify({"error": "cannot add yourself"})

    # check existing relationship (both directions)
    existing = Friend.query.filter(
        ((Friend.sender_id == current_user.id) & (Friend.receiver_id == target.id)) |
        ((Friend.sender_id == target.id) & (Friend.receiver_id == current_user.id))
    ).first()

    if existing:
        # already friends
        if existing.status == "accepted":
            return jsonify({"message": "already friends"})

        # request already sent by current user
        if existing.sender_id == current_user.id:
            return jsonify({"message": "already sent"})

        # target has sent request → auto accept
        if existing.sender_id == target.id:
            existing.status = "accepted"
            db.session.commit()
            return jsonify({"message": "friend added"})

    # create new friend request
    new_req = Friend(
        sender_id=current_user.id,
        receiver_id=target.id,
        status="pending"
    )

    db.session.add(new_req)
    db.session.commit()

    return jsonify({"message": "request sent"})

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
            pending.append(sender.username)

    # find all accepted relationships
    relations = Friend.query.filter_by(status="accepted").all()

    # collect friend usernames (both directions)
    friends = []
    for r in relations:

        # current user is sender → friend is receiver
        if r.sender_id == user_id:
            u = User.query.get(r.receiver_id)
            if u:
                friends.append(u.username)

        # current user is receiver → friend is sender
        elif r.receiver_id == user_id:
            u = User.query.get(r.sender_id)
            if u:
                friends.append(u.username)

    # sort lists for stable display
    pending.sort()
    friends.sort()

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
        return jsonify({"error": "invalid user"})

    # find pending request sent to current user
    req = Friend.query.filter_by(
        sender_id=target.id,
        receiver_id=current_user.id,
        status="pending"
    ).first()

    # check if request exists
    if not req:
        return jsonify({"error": "no request found"})

    # accept request
    req.status = "accepted"
    db.session.commit()

    # return result
    return jsonify({"message": "friend added"})

@app.route('/api/reject_friend', methods=['POST'])
@login_required
def reject_friend():

    # get request data
    data = request.get_json()
    username = data.get("username", "").strip()

    # find target user by username
    target = User.query.filter_by(username=username).first()
    if not target:
        return jsonify({"error": "invalid user"})

    # find pending request sent to current user
    req = Friend.query.filter_by(
        sender_id=target.id,
        receiver_id=current_user.id,
        status="pending"
    ).first()

    # check if request exists
    if not req:
        return jsonify({"error": "no request found"})

    # delete request
    db.session.delete(req)
    db.session.commit()

    # return result
    return jsonify({"message": "request rejected"})

#---!  message  ---#
@app.route('/api/messages')
@login_required
def get_messages():

    # get current user id
    user_id = current_user.id

    # find inbox messages (received by current user)
    inbox_msgs = Message.query.filter_by(
        receiver_id=user_id
    ).order_by(Message.id.desc()).all()

    # find sent messages (sent by current user)
    sent_msgs = Message.query.filter_by(
        sender_id=user_id
    ).order_by(Message.id.desc()).all()

    # build inbox data
    inbox = []
    for m in inbox_msgs:

        # find sender username
        sender = User.query.get(m.sender_id)

        # check if current user liked this message
        liked = Like.query.filter_by(
            user_id=user_id,
            message_id=m.id
        ).first() is not None

        inbox.append({
            "id": m.id,
            "session_name": m.session_name,
            "minutes": m.minutes,
            "date": m.date,
            "from_username": sender.username if sender else "",
            "liked": liked
        })

    # build sent data
    sent = []
    for m in sent_msgs:

        # find receiver username
        receiver = User.query.get(m.receiver_id)

        sent.append({
            "id": m.id,
            "session_name": m.session_name,
            "minutes": m.minutes,
            "date": m.date,
            "to_username": receiver.username if receiver else "",
            "likes_count": m.likes_count
        })

    # return result for frontend
    return jsonify({
        "inbox": inbox,
        "sent": sent
    })

@app.route('/api/like', methods=['POST'])
@login_required
def like_message():

    # get request data
    data = request.get_json()
    message_id = data.get("message_id")

    # find message by id
    msg = Message.query.get(message_id)
    if not msg:
        return jsonify({"error": "invalid message"})

    # check if user already liked this message
    existing = Like.query.filter_by(
        user_id=current_user.id,
        message_id=message_id
    ).first()

    # if already liked → unlike (toggle off)
    if existing:
        db.session.delete(existing)
        msg.likes_count = max(0, msg.likes_count - 1)
        db.session.commit()
        return jsonify({"message": "unliked"})

    # if not liked → add like
    new_like = Like(
        user_id=current_user.id,
        message_id=message_id
    )

    db.session.add(new_like)
    msg.likes_count += 1
    db.session.commit()

    # return result
    return jsonify({"message": "liked"})


with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True)