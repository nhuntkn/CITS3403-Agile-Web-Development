#setup Flask app and routes, connects to database, handles form submission and rendering templates

from flask import Flask, render_template, request
from models import db, ExerciseSession, SessionExercise
from data import exercise_data
from utils import calculate_calories

app = Flask(__name__)

#configure SQLite database, SQLAlchemy will store the database file inside the Flask instance folder
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///exercise_planner.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app) #attach SQLAlchemy to Flask app

@app.route("/", methods=["GET", "POST"])
def home():
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

        #create the main exercise session record
        new_session = ExerciseSession(
            date=date,
            current_weight=current_weight,
            notes=notes,
            total_calories=0
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
    #loads the dashboard page, which shows all past exercise sessions and their details
    username = "Jackson"  # TODO: replace with session user once auth is implemented
    
    sessions = ExerciseSession.query.order_by(ExerciseSession.id.desc()).all()

    return render_template("dashboard.html", username=username, sessions=sessions)

@app.route("/login")
def login():
    return render_template("login.html")

with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True)