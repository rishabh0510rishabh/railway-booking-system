from flask import Flask, render_template, request, redirect, url_for, flash, make_response, send_file, session
import time
import random
import string
from flask_sqlalchemy import SQLAlchemy
from fpdf import FPDF
from werkzeug.security import generate_password_hash, check_password_hash

# Initialize the Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'a-very-secret-key-for-flashing'


app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///railway.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy with your Flask app
db = SQLAlchemy(app)


class Train(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    train_name = db.Column(db.String(100), nullable=False)
    source = db.Column(db.String(100), nullable=False)
    destination = db.Column(db.String(100), nullable=False)
    departure_time = db.Column(db.String(10), nullable=False) # e.g., '06:15'
    total_seats = db.Column(db.Integer, nullable=False)

class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pnr_number = db.Column(db.String(20), unique=True, nullable=False)
    train_id = db.Column(db.Integer, db.ForeignKey('train.id'), nullable=False)

    # Add this user_id foreign key
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    passenger_name = db.Column(db.String(100), nullable=False)
    passenger_age = db.Column(db.Integer, nullable=False)
    seat_class = db.Column(db.String(50), nullable=False, default='Sleeper')
    status = db.Column(db.String(20), default='Confirmed')

    train = db.relationship('Train', backref=db.backref('bookings', lazy=True))
    # Add this relationship to the User model
    user = db.relationship('User', backref=db.backref('bookings', lazy=True))

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='user') # Roles: 'user' or 'admin'

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

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
    train_to_book = Train.query.get_or_404(train_id)
    
    # Check for seat availability
    confirmed_bookings = Booking.query.filter_by(train_id=train_id).count()
    available_seats = train_to_book.total_seats - confirmed_bookings
    
    if available_seats <= 0:
        flash('Sorry, no seats available on this train.', 'danger') # 'danger' is a bootstrap class for red alerts
        return redirect(url_for('index')) # Redirect back to home/search page

    return render_template('booking_form.html', train=train_to_book)


@app.route('/submit_booking', methods=['POST'])
def submit_booking():
    if not session.get('logged_in'):
        flash('You must be logged in to book a ticket.', 'danger')
        return redirect(url_for('login'))

    train_id = request.form['train_id']
    passenger_name = request.form['passenger_name']
    passenger_age = request.form['passenger_age']
    seat_class = request.form['seat_class']

    new_booking = Booking(
        pnr_number=generate_pnr(),
        train_id=train_id,
        user_id=session['user_id'], # Link booking to logged-in user
        passenger_name=passenger_name,
        passenger_age=passenger_age,
        seat_class=seat_class
    )
    
    db.session.add(new_booking)
    db.session.commit()
    
    return redirect(url_for('booking_confirmation', pnr=new_booking.pnr_number))
# new route to show the confirmation page
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

    if User.query.filter_by(username=username).first():
        flash('Username already exists.', 'danger')
        return redirect(url_for('index'))

    new_user = User(username=username)
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