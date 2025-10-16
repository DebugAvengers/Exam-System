from __init__ import db
from flask_login import UserMixin
from datetime import datetime, time


#Exam config
EXAM_TYPES = ['Math', 'Science', 'English']
# fills the time slots with times
TIME_SLOTS = [f"{h:02d}:00" for h in range(9, 18)]  
# converts to standard time format
TIME_SLOTS_LABELS = [time(h, 0).strftime('%I:%M %p').lstrip('0') for h in range(9, 18)]
# pairs the non standard and standard time formats
# we see the standard format but the backend gets the non standard format
TIME_SLOTS_PAIRS = list(zip(TIME_SLOTS, TIME_SLOTS_LABELS))
# needed to display friendly time labels in templates
TIME_SLOTS_MAP = dict(TIME_SLOTS_PAIRS)
MAX_CAPACITY = 20
MAX_UNIQUE_EXAMS = 3

# Database Columns
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    NSHEID = db.Column(db.String(10), unique=True, nullable=False)
    FirstName = db.Column(db.String(10), unique=False, nullable=False)
    LastName = db.Column(db.String(10), unique=False, nullable=False)
    email = db.Column(db.String(100) , unique=True, nullable=False) 
    password = db.Column(db.String(1000) , nullable=False)
    is_staff = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now()) 
    # relationship to registrations (Registration model)
    registrations = db.relationship('Registration', backref='student', lazy=True)

    # returns the amount of exams student is registered for
    def exam_count_check(self):
        unique_exams = db.session.query(Registration.exam_type)\
            .filter_by(user_id=self.id)\
            .distinct()\
            .count()
        return unique_exams
    
    # checks if the student can take more exams
    def exam_check(self):
        return self.exam_count_check() < MAX_UNIQUE_EXAMS
    
    # returns the amount of remaining exams the student can take
    def remaining_exams(self):
        return MAX_UNIQUE_EXAMS - self.exam_count_check()
    
    def get_exams(self):
        exams  = db.session.query(Registration.exam_type)\
            .filter_by(user_id=self.id)\
            .distinct()\
            .all()
        return [exam[0] for exam in exams]
    

# Database Columns for Registration table    
class Registration(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    exam_type = db.Column(db.String(50), nullable=False)
    time_slot = db.Column(db.String(50), nullable=False)
    registered_at = db.Column(db.DateTime, default=datetime.utcnow)