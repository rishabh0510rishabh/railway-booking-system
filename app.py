from flask import Flask, render_template, request, redirect, url_for
import time
import random
import string
from flask import flash 
from flask_sqlalchemy import SQLAlchemy

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
    passenger_name = db.Column(db.String(100), nullable=False)
    passenger_age = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), default='Confirmed')
    
    train = db.relationship('Train', backref=db.backref('bookings', lazy=True))


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    source = request.form['source']
    destination = request.form['destination']

    trains = Train.query.filter_by(source=source, destination=destination).all()
    
    # New logic starts here
    for train in trains:
        # Count how many bookings exist for this train
        confirmed_bookings = Booking.query.filter_by(train_id=train.id).count()
        # Calculate available seats
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
    train_id = request.form['train_id']
    passenger_name = request.form['passenger_name']
    passenger_age = request.form['passenger_age']

    new_booking = Booking(
        pnr_number=generate_pnr(),
        train_id=train_id,
        passenger_name=passenger_name,
        passenger_age=passenger_age
    )
    
    db.session.add(new_booking)
    db.session.commit()
    
    # Redirect to the new confirmation page, passing the new PNR
    return redirect(url_for('booking_confirmation', pnr=new_booking.pnr_number))

# Add this new route to show the confirmation page
@app.route('/confirmation/<pnr>')
def booking_confirmation(pnr):
    # Find the booking in the database using the PNR
    booking_details = Booking.query.filter_by(pnr_number=pnr).first_or_404()
    return render_template('booking_confirmation.html', booking=booking_details)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)