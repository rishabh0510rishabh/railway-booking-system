import os
import uuid 
import time
import random
import string
import math
from flask import Flask, render_template, request, redirect, url_for, flash, session, send_from_directory, send_file
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from fpdf import FPDF
from sqlalchemy.orm import relationship

# Initialize the Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'a-very-secret-key-for-flashing'

# Configure database and upload folders
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///railway.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads/profiles'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB max file size
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Ensure the upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize SQLAlchemy with your Flask app
db = SQLAlchemy(app)

# Define constants for fare and booking statuses
BASE_FARE = 1000
SEATS_PER_COACH = {
    'Sleeper': 72,
    'AC 3 Tier': 64,
    'AC 2 Tier': 46,
    'AC 1st Class': 18
}

# --- Database Models ---
class Train(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    train_name = db.Column(db.String(100), nullable=False)
    source = db.Column(db.String(100), nullable=False)
    destination = db.Column(db.String(100), nullable=False)
    departure_time = db.Column(db.String(10), nullable=False) # e.g., '06:15'
    total_seats = db.Column(db.Integer, nullable=False)
    bookings = db.relationship('Booking', backref='train', lazy=True)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='user') # Roles: 'user' or 'admin'
    email = db.Column(db.String(100), nullable=True)
    phone_number = db.Column(db.String(20), nullable=True)
    profile_picture = db.Column(db.String(255), nullable=True)
    bookings = db.relationship('Booking', backref='user', lazy=True)
    saved_passengers = db.relationship('Passenger', backref='user', lazy=True, cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Passenger(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    berth_preference = db.Column(db.String(50), nullable=True)
    
class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pnr_number = db.Column(db.String(20), unique=True, nullable=False)
    train_id = db.Column(db.Integer, db.ForeignKey('train.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    passenger_name = db.Column(db.String(100), nullable=False)
    passenger_age = db.Column(db.Integer, nullable=False)
    seat_class = db.Column(db.String(50), nullable=False, default='Sleeper')
    berth_preference = db.Column(db.String(50), nullable=True)
    status = db.Column(db.String(20), default='Confirmed')
    seat_number = db.Column(db.String(20), nullable=True) # New column for detailed seat number
    fare = db.Column(db.Float, nullable=False, default=0.0) # New column for fare

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- Helper Functions ---
def generate_pnr():
    """Generates a unique PNR number."""
    timestamp_part = str(int(time.time()))[-6:]
    random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"PNR{timestamp_part}{random_part}"

def calculate_fare(seat_class):
    """Calculates fare based on seat class."""
    fare_multipliers = {
        'Sleeper': 1.0,
        'AC 3 Tier': 1.5,
        'AC 2 Tier': 2.0,
        'AC 1st Class': 3.0
    }
    return BASE_FARE * fare_multipliers.get(seat_class, 1.0)

def generate_seat_number(booking_count, total_seats, seat_class):
    """Generates a detailed seat number based on booking count and coach class.
    
    This function assigns a seat number in the format 'Coach-Seat-Berth'
    (e.g., 'S1-32-SL' for Sleeper Class, Coach 1, Seat 32, Side Lower Berth).
    """
    seats_in_coach = SEATS_PER_COACH.get(seat_class, 72)
    
    # Calculate Coach and Seat number
    coach_number = math.ceil(booking_count / seats_in_coach)
    seat_in_coach = booking_count % seats_in_coach
    if seat_in_coach == 0:
        seat_in_coach = seats_in_coach
    
    # Map seat number to a berth type
    berth_map = {
        'Sleeper': {1: 'SL', 2: 'LB', 3: 'MB', 4: 'UB', 5: 'SL', 6: 'SU'},
        'AC 3 Tier': {1: 'LB', 2: 'MB', 3: 'UB', 4: 'SL', 5: 'SU'},
        'AC 2 Tier': {1: 'LB', 2: 'UB', 3: 'SL', 4: 'SU'},
        'AC 1st Class': {1: 'LB', 2: 'UB'}
    }
    
    # Use modulo to cycle through berths for the given class
    berth_abbreviation = 'S'
    if seat_class in berth_map:
        berth_options = list(berth_map[seat_class].values())
        berth_abbreviation = berth_options[(seat_in_coach - 1) % len(berth_options)]

    # Get the first letter of the class for the coach name
    class_initial = seat_class[0].upper()

    return f"{class_initial}{coach_number}-{seat_in_coach}-{berth_abbreviation}"

# --- Routes ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    source = request.form['source']
    destination = request.form['destination']
    time_filter = request.form['time_filter']

    query = Train.query.filter_by(source=source, destination=destination)

    if time_filter == 'morning':
        query = query.filter(Train.departure_time >= '05:00', Train.departure_time < '12:00')
    elif time_filter == 'afternoon':
        query = query.filter(Train.departure_time >= '12:00', Train.departure_time < '17:00')
    elif time_filter == 'evening':
        query = query.filter(Train.departure_time >= '17:00', Train.departure_time < '24:00')
    
    trains = query.all()
    
    for train in trains:
        confirmed_bookings = Booking.query.filter_by(train_id=train.id, status='Confirmed').count()
        train.available_seats = train.total_seats - confirmed_bookings
        
    return render_template('results.html', trains=trains, source=source, destination=destination)

@app.route('/book/<int:train_id>')
def book(train_id):
    if not session.get('logged_in'):
        flash('You must be logged in to book a ticket.', 'danger')
        return redirect(url_for('login'))

    train_to_book = Train.query.get_or_404(train_id)
    
    # Check for seat availability based on Confirmed and RAC
    confirmed_count = Booking.query.filter_by(train_id=train_id, status='Confirmed').count()
    rac_count = Booking.query.filter_by(train_id=train_id, status='RAC').count()
    
    total_confirmed_rac = confirmed_count + rac_count
    
    # RAC tickets are counted as half seats, so we have a larger capacity
    rac_limit = train_to_book.total_seats + (train_to_book.total_seats // 10) 
    
    if total_confirmed_rac >= rac_limit:
        # If RAC is also full, check waitlist availability (e.g., up to 10% of total seats)
        waitlist_count = Booking.query.filter_by(train_id=train_id, status='Waitlisted').count()
        if waitlist_count >= train_to_book.total_seats * 0.1:
            flash('Sorry, this train is fully waitlisted.', 'danger')
            return redirect(url_for('index'))
    
    user_id = session['user_id']
    saved_passengers = Passenger.query.filter_by(user_id=user_id).all()

    return render_template('booking_form.html', train=train_to_book, saved_passengers=saved_passengers)

@app.route('/submit_booking', methods=['POST'])
def submit_booking():
    if not session.get('logged_in'):
        flash('You must be logged in to book a ticket.', 'danger')
        return redirect(url_for('login'))

    train_id = request.form['train_id']
    passenger_name = request.form['passenger_name']
    passenger_age = int(request.form['passenger_age'])
    seat_class = request.form['seat_class']
    requested_berth = request.form.get('berth_preference')
    save_passenger = request.form.get('save_passenger')
    
    # Fetch train details
    train_to_book = Train.query.get_or_404(train_id)
    
    # Calculate current booking counts for this train
    confirmed_bookings = Booking.query.filter_by(train_id=train_id, status='Confirmed').count()
    rac_bookings = Booking.query.filter_by(train_id=train_id, status='RAC').count()
    waitlisted_bookings = Booking.query.filter_by(train_id=train_id, status='Waitlisted').count()

    # Determine the status and seat number of the new booking
    status = 'Confirmed'
    seat_number = None
    
    rac_limit = train_to_book.total_seats + 10 # Let's set a fixed number of RAC seats
    
    if confirmed_bookings < train_to_book.total_seats:
        status = 'Confirmed'
        booking_count = confirmed_bookings + 1
        seat_number = generate_seat_number(booking_count, train_to_book.total_seats, seat_class)
    elif confirmed_bookings + rac_bookings < rac_limit:
        status = 'RAC'
        rac_number = rac_bookings + 1
        seat_number = f"RAC-{rac_number}"
    else:
        status = 'Waitlisted'
        waitlist_number = waitlisted_bookings + 1
        seat_number = f"WL-{waitlist_number}"

    # Calculate the fare
    fare = calculate_fare(seat_class)

    new_booking = Booking(
        pnr_number=generate_pnr(),
        train_id=train_id,
        user_id=session['user_id'],
        passenger_name=passenger_name,
        passenger_age=passenger_age,
        seat_class=seat_class,
        berth_preference=requested_berth,
        status=status,
        seat_number=seat_number,
        fare=fare
    )
    
    db.session.add(new_booking)

    if save_passenger:
        existing_passenger = Passenger.query.filter_by(user_id=session['user_id'], name=passenger_name, age=passenger_age).first()
        if not existing_passenger:
            new_passenger = Passenger(
                user_id=session['user_id'],
                name=passenger_name,
                age=passenger_age,
                berth_preference=requested_berth
            )
            db.session.add(new_passenger)
    
    db.session.commit()
    
    return redirect(url_for('booking_confirmation', pnr=new_booking.pnr_number))

@app.route('/confirmation/<pnr>')
def booking_confirmation(pnr):
    booking_details = Booking.query.filter_by(pnr_number=pnr).first_or_404()
    return render_template('booking_confirmation.html', booking=booking_details)

@app.route('/pnr_status')
def pnr_status():
    pnr = request.args.get('pnr')
    if not pnr:
        flash('Please enter a PNR number.', 'warning')
        return redirect(url_for('index'))

    booking = Booking.query.filter_by(pnr_number=pnr.strip()).first()

    if booking:
        return render_template('ticket_details.html', booking=booking)
    else:
        flash('Invalid PNR Number. Please check and try again.', 'danger')
        return redirect(url_for('index'))

@app.route('/download_ticket/<pnr>')
def download_ticket(pnr):
    booking = Booking.query.filter_by(pnr_number=pnr).first_or_404()

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "E-Ticket", 1, 1, 'C')

    pdf.set_font("Helvetica", "", 12)
    pdf.cell(0, 10, f"PNR Number: {booking.pnr_number}", 0, 1)
    pdf.cell(0, 10, f"Passenger: {booking.passenger_name}, Age: {booking.passenger_age}", 0, 1)
    
    # Display Berth/Seat details based on status
    if booking.status == 'Confirmed' or booking.status == 'RAC':
        pdf.cell(0, 10, f"Berth/Seat: {booking.seat_number}", 0, 1)
    else:
        pdf.cell(0, 10, f"Status: {booking.status}", 0, 1)

    pdf.cell(0, 10, f"Seat Class: {booking.seat_class}", 0, 1) 
    pdf.cell(0, 10, f"Fare Paid: ${booking.fare:.2f}", 0, 1)
    pdf.cell(0, 10, f"Train: {booking.train.train_name}", 0, 1)
    pdf.cell(0, 10, f"Route: {booking.train.source} to {booking.train.destination}", 0, 1)
    pdf.cell(0, 10, f"Departure Time: {booking.train.departure_time}", 0, 1)

    # Define the filename for the temporary PDF
    pdf_filename = f"ticket_{pnr}.pdf"

    # Save the PDF to a file on the server
    pdf.output(pdf_filename)

    # Send the file to the user for download
    return send_file(pdf_filename, as_attachment=True)

@app.route('/signup', methods=['POST'])
def signup():
    username = request.form['username']
    password = request.form['password']
    email = request.form.get('email')
    phone = request.form.get('phone')

    if User.query.filter_by(username=username).first():
        flash('Username already exists.', 'danger')
        return redirect(url_for('index'))
    
    if email and User.query.filter_by(email=email).first():
        flash('Email address is already registered.', 'danger')
        return redirect(url_for('index'))
        
    new_user = User(username=username, email=email, phone_number=phone)
    new_user.set_password(password)
    db.session.add(new_user)
    db.session.commit()
    
    flash('Account created successfully! Please log in.', 'success')
    return redirect(url_for('index'))

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    user = User.query.filter_by(username=username).first()
    
    if user and user.check_password(password):
        session['logged_in'] = True
        session['user_id'] = user.id
        session['username'] = user.username
        session['is_admin'] = (user.role == 'admin')
        flash(f'Welcome back, {user.username}!', 'success')
    else:
        flash('Invalid username or password.', 'danger')
        
    return redirect(url_for('index'))

@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('is_admin'):
        flash('You must be an admin to access this page.', 'danger')
        return redirect(url_for('login'))
    
    all_bookings = Booking.query.order_by(Booking.id.desc()).all()
    all_trains = Train.query.order_by(Train.train_name).all()
    
    return render_template('admin_dashboard.html', bookings=all_bookings, trains=all_trains)

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/my_bookings')
def my_bookings():
    if not session.get('logged_in'):
        flash('You must be logged in to view your bookings.', 'danger')
        return redirect(url_for('login'))

    user_id = session['user_id']
    bookings = Booking.query.filter_by(user_id=user_id).order_by(Booking.id.desc()).all()
    return render_template('my_bookings.html', bookings=bookings)

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if not session.get('logged_in'):
        flash('You must be logged in to view your profile.', 'danger')
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    user = User.query.get_or_404(user_id)

    if request.method == 'POST':
        action = request.args.get('action')
        
        if action == 'add_passenger':
            name = request.form['passenger_name']
            age = request.form['passenger_age']
            berth_preference = request.form.get('berth_preference')
            new_passenger = Passenger(user_id=user_id, name=name, age=age, berth_preference=berth_preference)
            db.session.add(new_passenger)
            db.session.commit()
            flash(f'Passenger "{name}" added successfully!', 'success')
            return redirect(url_for('profile'))
        
        elif action == 'delete_passenger':
            passenger_id = request.args.get('passenger_id')
            passenger_to_delete = Passenger.query.filter_by(id=passenger_id, user_id=user_id).first_or_404()
            db.session.delete(passenger_to_delete)
            db.session.commit()
            flash('Saved passenger removed.', 'info')
            return redirect(url_for('profile'))
        
        else: # Handle standard profile updates
            new_username = request.form['username']
            new_email = request.form['email']
            new_phone = request.form['phone']

            if new_username != user.username and User.query.filter_by(username=new_username).first():
                flash('This username is already taken. Please choose a different one.', 'danger')
                return redirect(url_for('profile'))

            user.username = new_username
            user.email = new_email
            user.phone_number = new_phone
            
            db.session.commit()
            session['username'] = user.username
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('profile'))
    
    recent_bookings = Booking.query.filter_by(user_id=user_id).order_by(Booking.id.desc()).limit(5).all()
    saved_passengers = Passenger.query.filter_by(user_id=user_id).all()

    return render_template('profile.html', user=user, recent_bookings=recent_bookings, saved_passengers=saved_passengers)

@app.route('/change_password', methods=['POST'])
def change_password():
    if not session.get('logged_in'):
        flash('You must be logged in to change your password.', 'danger')
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])
    current_password = request.form['current_password']
    new_password = request.form['new_password']
    confirm_password = request.form['confirm_password']

    if not user.check_password(current_password):
        flash('Incorrect current password.', 'danger')
    elif new_password != confirm_password:
        flash('New password and confirmation do not match.', 'danger')
    else:
        user.set_password(new_password)
        db.session.commit()
        flash('Password updated successfully!', 'success')

    return redirect(url_for('profile'))

@app.route('/profile/delete', methods=['POST'])
def delete_account():
    if not session.get('logged_in'):
        flash('You must be logged in to delete your account.', 'danger')
        return redirect(url_for('login'))

    user_id = session['user_id']
    user = User.query.get_or_404(user_id)

    Passenger.query.filter_by(user_id=user_id).delete()
    Booking.query.filter_by(user_id=user_id).delete()
    
    db.session.delete(user)
    db.session.commit()

    session.clear()
    flash('Your account has been successfully deleted.', 'info')
    return redirect(url_for('index'))

@app.route('/admin/add_train', methods=['POST'])
def add_train():
    if not session.get('is_admin'):
        return redirect(url_for('login'))

    train_name = request.form['train_name']
    source = request.form['source']
    destination = request.form['destination']
    departure_time = request.form['departure_time']
    total_seats = request.form['total_seats']

    new_train = Train(
        train_name=train_name,
        source=source,
        destination=destination,
        departure_time=departure_time,
        total_seats=total_seats
    )
    db.session.add(new_train)
    db.session.commit()

    flash(f'Train "{train_name}" has been added successfully!', 'success')
    return redirect(url_for('admin_dashboard'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
    
