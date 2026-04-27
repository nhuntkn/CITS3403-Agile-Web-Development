# Database models for the Project
# Define the database tables used by SQLAlchemy

from flask_sqlalchemy import SQLAlchemy

#create the SQLAlchemy instance, will be attached to Flask app in app.py
db = SQLAlchemy()

class ExerciseSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(20), nullable=False)
    current_weight = db.Column(db.Float, nullable=False)
    notes = db.Column(db.Text)
    total_calories = db.Column(db.Float, default=0)
    
    #one exercise session can contain many exercise rows
    #to display session details in ranking and history later
    exercises = db.relationship('SessionExercise', backref='session', cascade="all, delete-orphan")

class SessionExercise(db.Model):
    #stores one exercise row inside a session
    #example: "Cycling, 12 - 13.9 mph, 30 minutes"
    id = db.Column(db.Integer, primary_key=True)
    exercise_name = db.Column(db.String(50), nullable=False)
    activity_level = db.Column(db.String(50), nullable=False)
    minutes = db.Column(db.Integer, nullable=False)
    met_value = db.Column(db.Float, nullable=False)
    calories = db.Column(db.Float, default=0)
    
    #link this row to its parent session
    session_id = db.Column(db.Integer, db.ForeignKey('exercise_session.id'), nullable=False)
