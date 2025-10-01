from __init__ import db
from flask_login import UserMixin

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

    def __repr__(self):
        return '<User %r>' %self.username