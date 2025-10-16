from flask import Flask, request, jsonify, render_template, url_for, flash, redirect
from flask_login import login_user, logout_user, login_required, current_user
from __init__ import create_app, db
from models import User, Registration, EXAM_TYPES, TIME_SLOTS, MAX_CAPACITY, MAX_UNIQUE_EXAMS, TIME_SLOTS_LABELS, TIME_SLOTS_PAIRS, TIME_SLOTS_MAP
import re

app = create_app()

# Home route
@app.route('/', methods = ['GET', 'POST'])
def home():
    return render_template('front.html')

# Login route
@app.route('/login', methods = ['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('register_exam'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        # checks for correct email format
        pattern = r'^[0-9]{10}@student\.csn\.edu$'
        if not re.match(pattern, email):
            flash('email must be a valid CSN student email address')
            return render_template('home.html')
     
        # authentication 
        user = User.query.filter_by(email=email).first()
        if user and user.password == password:
            login_user(user)
            return redirect(url_for('register_exam'))
        else:
            flash('Invalid email or password')
            return render_template('home.html')
        
    return render_template('home.html')


# Exam registration route
@app.route('/register_exam', methods=['GET', 'POST'])
@login_required
def register_exam():
    if request.method == 'GET':
        # Displays current user's registrations
        my_registrations = Registration.query.filter_by(user_id=current_user.id)\
            .order_by(Registration.time_slot).all()

        # counts the number of registrations per time slot
        slot_counts = {slot: Registration.query.filter_by(time_slot=slot).count()
                       for slot in TIME_SLOTS}

        # gives the register exam page the data it needs to display
        return render_template(
            'register_exam.html',
            exam_types=EXAM_TYPES,
            time_slots=TIME_SLOTS,
            time_slots_labels=TIME_SLOTS_LABELS,
            time_slots_pairs=TIME_SLOTS_PAIRS,
            time_slots_map=TIME_SLOTS_MAP,
            slot_counts=slot_counts,
            max_capacity=MAX_CAPACITY,
            max_unique_exams=MAX_UNIQUE_EXAMS,
            my_registrations=my_registrations,
            registered_exams=current_user.get_exams()
        )

    # stores the data from the form when selecting exam and time slot
    exam_type = request.form.get('exam_type')
    time_slot = request.form.get('time_slot')

    # These checks make sure the data is valid
    if not exam_type or not time_slot:
        flash('Please select both an exam type and time slot.', 'error')
        return redirect(url_for('register_exam'))

    if exam_type not in EXAM_TYPES:
        flash('Invalid exam type selected.', 'error')
        return redirect(url_for('register_exam'))

    if time_slot not in TIME_SLOTS:
        flash('Invalid time slot selected.', 'error')
        return redirect(url_for('register_exam'))

    # Check for duplicate registration
    existing = Registration.query.filter_by(
        user_id=current_user.id,
        exam_type=exam_type,
        time_slot=time_slot
    ).first()

    # if a dupe is found display message
    if existing:
        flash(f'You are already registered for {exam_type} at {TIME_SLOTS_MAP.get(time_slot, time_slot)}.', 'error')
        return redirect(url_for('register_exam'))

    
    registered_exams = current_user.get_exams() # gets the exams the user is already registered for
    unique_count = current_user.exam_count_check() # counts how many unique exams the user is registered for
    # check if trying to register for a new exam type
    if (exam_type not in (registered_exams or [])) and unique_count >= MAX_UNIQUE_EXAMS:
        flash(f'You have already registered for {MAX_UNIQUE_EXAMS} different exams ({", ".join(registered_exams)}). You can only register for additional time slots of exams you are already taking.', 'error')
        return redirect(url_for('register_exam'))

    # Check if time slot is full
    current_count = Registration.query.filter_by(time_slot=time_slot).count()
    if current_count >= MAX_CAPACITY:
        flash('Sorry, this time slot is full. Please choose another time.', 'error')
        return redirect(url_for('register_exam'))

    # Create new registration
    # will add the data to the database
    # if a problem occurs it will rollback and display an error message
    try:
        new_registration = Registration(
            user_id=current_user.id,
            exam_type=exam_type,
            time_slot=time_slot
        )

        db.session.add(new_registration)
        db.session.commit()

        flash(f'Successfully registered for {exam_type} at {time_slot}!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('An error occurred during registration. Please try again.', 'error')
        app.logger.error(f'Registration error: {str(e)}')

    return redirect(url_for('register_exam'))


# Logout route
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('home'))

# cancel registration route
@app.route('/cancel_registration', methods=['GET', 'POST'])
@login_required
def cancel_registration():
    if request.method == 'POST':
        #takes in the registration id from the form
        reg_id = request.form.get('reg_id')

        # if id not found flash the error message
        registration = Registration.query.get(reg_id)
        if not registration:
            flash('Registration not found.', 'danger')
            if current_user.is_staff:
                return redirect(url_for('staff_dashboard'))
            else:
                return redirect(url_for('register_exam'))

        # lets the user delete their own registration or lets staff delete any registration
        # if not allowed to rmove, flash error message
        if current_user.is_staff or registration.user_id == current_user.id:
            db.session.delete(registration)
            db.session.commit()
            flash('Registration deleted successfully.', 'success')
        else:
            flash('Unauthorized to delete this registration.', 'danger')

        # I added this so that this function can be used by both staff and students
        if current_user.is_staff:
            return redirect(url_for('staff_dashboard'))
        else:
            return redirect(url_for('register_exam'))
        

@app.route('/staff_login', methods=['GET', 'POST'])
def staff_login():
    if current_user.is_authenticated and current_user.is_staff:
        return redirect(url_for('staff_dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        pattern = r'^[0-9]{10}@staff\.csn\.edu$'
        if not re.match(pattern, email):
            flash('email must be a valid CSN staff email address')
            return render_template('staff_login.html')

        # authentication
        user = User.query.filter_by(email=email).first()
        if user and user.password == password and user.is_staff:
            login_user(user)
            return redirect(url_for('staff_dashboard'))
        else:
            flash('Invalid email or password')
            return render_template('staff_login.html')

    
    return render_template('staff_login.html')

# Staff dashboard route
@app.route('/staff_dashboard', methods=['GET', 'POST'])
@login_required
def staff_dashboard():
    if not current_user.is_staff:
        flash('Access denied: Staff only area.', 'danger')
        return redirect(url_for('home'))

    # looks for all registrations and joins with user table to get student info
    registrations = (
        db.session.query(Registration, User.FirstName, User.LastName, User.email)
        .join(User, User.id == Registration.user_id)
        .order_by(Registration.time_slot, Registration.exam_type)
        .all()
    )

    my_registrations = Registration.query.filter_by(user_id=current_user.id)\
            .order_by(Registration.time_slot).all()

    # counts the number of registrations per time slot
    slot_counts = {slot: Registration.query.filter_by(time_slot=slot).count()
                       for slot in TIME_SLOTS}


    # gives the staff dashboard the data it needs to display
    return render_template('staff_dashboard.html',
                           registrations=registrations,
                           time_slots_map=TIME_SLOTS_MAP,
                           my_registrations=my_registrations,
                           time_slots=TIME_SLOTS,
                            time_slots_labels=TIME_SLOTS_LABELS,
                           time_slots_pairs=TIME_SLOTS_PAIRS,
                           max_capacity=MAX_CAPACITY,
                           slot_counts=slot_counts)


if __name__ == '__main__':
    app.run(debug=True)