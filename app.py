import os
import uuid # Used for generating a unique filename for the profile picture
from flask import Flask, render_template, request, redirect, url_for, flash, session, send_from_directory,send_file
import time
import random
import string
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from fpdf import FPDF
from sqlalchemy.orm import relationship

# Initialize the Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'a-very-secret-key-for-flashing'


app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///railway.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads/profiles'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB max file size
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Ensure the upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


# Initialize SQLAlchemy with your Flask app
db = SQLAlchemy(app)


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
    berth_preference = db.Column(db.String(50), nullable=True)  # New column for berth preference
    status = db.Column(db.String(20), default='Confirmed')

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    source = request.form['source']
    destination = request.form['destination']
    time_filter = request.form['time_filter']

    # Start with the basic query
    query = Train.query.filter_by(source=source, destination=destination)

    # Apply time filter if not 'all'
    if time_filter == 'morning':
        query = query.filter(Train.departure_time >= '05:00', Train.departure_time < '12:00')
    elif time_filter == 'afternoon':
        query = query.filter(Train.departure_time >= '12:00', Train.departure_time < '17:00')
    elif time_filter == 'evening':
        query = query.filter(Train.departure_time >= '17:00', Train.departure_time < '24:00')
    
    trains = query.all()
    
    for train in trains:
        confirmed_bookings = Booking.query.filter_by(train_id=train.id).count()
        train.available_seats = train.total_seats - confirmed_bookings
        
    return render_template('results.html', trains=trains, source=source, destination=destination)

def generate_pnr():
    # Generates a unique PNR number
    timestamp_part = str(int(time.time()))[-6:]
    random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"PNR{timestamp_part}{random_part}"

@app.route('/book/<int:train_id>')
def book(train_id):
    if not session.get('logged_in'):
        flash('You must be logged in to book a ticket.', 'danger')
        return redirect(url_for('login'))

    train_to_book = Train.query.get_or_404(train_id)
    
    # Check for seat availability
    confirmed_bookings = Booking.query.filter_by(train_id=train_id).count()
    available_seats = train_to_book.total_seats - confirmed_bookings
    
    if available_seats <= 0:
        flash('Sorry, no seats available on this train.', 'danger') # 'danger' is a bootstrap class for red alerts
        return redirect(url_for('index')) # Redirect back to home/search page
    
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

    # Logic for assigning berth preference
    final_berth_preference = None
    berth_options = ['Lower', 'Middle', 'Upper', 'Side Lower', 'Side Upper']
    
    # Rule: If age >= 60, only allow Lower or Side Lower
    if passenger_age >= 60:
        berth_options = ['Lower', 'Side Lower']
        if requested_berth not in berth_options:
            final_berth_preference = random.choice(berth_options)
        else:
            final_berth_preference = requested_berth
    else:
        # 60% chance to get the preferred berth if selected, otherwise random
        if requested_berth and random.random() < 0.6:
            final_berth_preference = requested_berth
        else:
            final_berth_preference = random.choice(berth_options)

    new_booking = Booking(
        pnr_number=generate_pnr(),
        train_id=train_id,
        user_id=session['user_id'],
        passenger_name=passenger_name,
        passenger_age=passenger_age,
        seat_class=seat_class,
        berth_preference=final_berth_preference
    )
    
    db.session.add(new_booking)

    if save_passenger:
        existing_passenger = Passenger.query.filter_by(user_id=session['user_id'], name=passenger_name, age=passenger_age).first()
        if not existing_passenger:
            new_passenger = Passenger(
                user_id=session['user_id'],
                name=passenger_name,
                age=passenger_age,
                berth_preference=final_berth_preference
            )
            db.session.add(new_passenger)
    
    db.session.commit()
    
    return redirect(url_for('booking_confirmation', pnr=new_booking.pnr_number))

@app.route('/confirmation/<pnr>')
def booking_confirmation(pnr):
    # Find the booking in the database using the PNR
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
    pdf.cell(0, 10, f"Train: {booking.train.train_name}", 0, 1)
    pdf.cell(0, 10, f"Route: {booking.train.source} to {booking.train.destination}", 0, 1)
    pdf.cell(0, 10, f"Departure Time: {booking.train.departure_time}", 0, 1)
    pdf.cell(0, 10, f"Status: {booking.status}", 0, 1)

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
        
    # --- PASS NEW FIELDS TO THE USER OBJECT ---
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
    
    # Fetch all data needed for the dashboard
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
    # Find all bookings linked to the current user's ID
    bookings = Booking.query.filter_by(user_id=user_id).order_by(Booking.id.desc()).all()
    return render_template('my_bookings.html', bookings=bookings)

# This is the new route for the user's profile
@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if not session.get('logged_in'):
        flash('You must be logged in to view your profile.', 'danger')
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    user = User.query.get_or_404(user_id)

    # Handle POST requests with an action parameter
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
    
    # Fetch user's recent bookings for the summary
    recent_bookings = Booking.query.filter_by(user_id=user_id).order_by(Booking.id.desc()).limit(5).all()
    
    # Fetch user's saved passengers
    saved_passengers = Passenger.query.filter_by(user_id=user_id).all()

    return render_template('profile.html', user=user, recent_bookings=recent_bookings, saved_passengers=saved_passengers)

# A new route for handling password changes
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

    # First, delete all bookings and saved passengers associated with the user
    Passenger.query.filter_by(user_id=user_id).delete()
    Booking.query.filter_by(user_id=user_id).delete()
    
    # Then, delete the user themselves
    db.session.delete(user)
    db.session.commit()

    session.clear()
    flash('Your account has been successfully deleted.', 'info')
    return redirect(url_for('index'))

# this new route will handle adding a train
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
