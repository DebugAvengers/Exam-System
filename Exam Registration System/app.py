from flask import Flask, request, jsonify, render_template, url_for, flash, redirect
from flask_login import login_user
from __init__ import create_app
from models import User
from werkzeug.security import check_password_hash
import re

app = create_app()

@app.route('/', methods = ['GET'])
def home():
    return render_template('home.html')

@app.route('/login', methods = ['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        # checks for correct email format
        pattern = r'^[0-9]{10}@student\.csn\.edu$'
        if not re.match(pattern, email):
            flash('email must be a valid CSN student email address')
            return render_template('login.html')
        
        # checks for 10 digit student ID
        if not re.match(r'^[0-9]{10}@student\.csn\.edu$', email):
            flash('Email must start with a 10-digit student ID')
            return render_template('login.html')
        
        # authentication 
        user = User.query.filter_by(email=email).first()
        if user and user.password == password:
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password')
            return render_template('login.html')
        
    return render_template('login.html')

@app.route('/dashboard', methods = ['GET'])
def dashboard():
    return render_template('dashboard.html')


if __name__ == '__main__':
    app.run(debug = True) 