# Database models for the Project
# Define the database tables used by SQLAlchemy

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

#create the SQLAlchemy instance, will be attached to Flask app in app.py
db = SQLAlchemy()

class ExerciseSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(20), nullable=False)
    current_weight = db.Column(db.Float, nullable=False)
    notes = db.Column(db.Text)
    total_calories = db.Column(db.Float, default=0)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable = False)
    
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

#UserMixin gives user model the properties and methods needed for Flask-Login to manage user sessions
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    dob = db.Column(db.String(20))
    gender = db.Column(db.String(10))
    weight = db.Column(db.Float)
    height = db.Column(db.Float)
    calorie_goal = db.Column(db.Integer, default = 1000)
    
    sessions = db.relationship('ExerciseSession', backref='user', cascade="all, delete-orphan")
    
    #methods to set and check password using hashing for security
    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)
    
class Share(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable = False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable = False)
    session_id = db.Column(db.Integer, db.ForeignKey('exercise_session.id'), nullable = False)
    liked = db.Column(db.Boolean, default = False)
    created_at = db.Column(db.DateTime, default = datetime.utcnow)

    sender = db.relationship('User', foreign_keys = [sender_id], backref = 'sent_shares')
    receiver = db.relationship('User', foreign_keys = [receiver_id], backref = 'received_shares')
    session = db.relationship('ExerciseSession', backref = 'shares')