import os
import time
import random
import string
import math
import qrcode
import base64
import tempfile  # <--- NEW IMPORT
from io import BytesIO
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file, make_response
from flask_mongoengine import MongoEngine
from werkzeug.security import generate_password_hash, check_password_hash
from fpdf import FPDF

# Initialize the Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'a-very-secret-key-for-flashing'

# --- MongoDB Configuration ---
app.config['MONGODB_SETTINGS'] = {
    'host': os.environ.get('MONGO_URI', 'mongodb://localhost:27017/railway_db')
}
app.config['UPLOAD_FOLDER'] = 'static/uploads/profiles'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = MongoEngine(app)

# Constants
BASE_FARE = 1000
SEATS_PER_COACH = {
    'Sleeper': 72, 'AC 3 Tier': 64, 'AC 2 Tier': 46, 'AC 1st Class': 18
}

# --- Database Models ---

class Route(db.EmbeddedDocument):
    stop_name = db.StringField(required=True)
    arrival_time = db.StringField(required=True)
    stop_order = db.IntField(required=True)

class Train(db.Document):
    train_name = db.StringField(required=True)
    source = db.StringField(required=True)
    destination = db.StringField(required=True)
    departure_time = db.StringField(required=True) 
    arrival_time = db.StringField()
    total_seats = db.IntField(required=True)
    route_stops = db.ListField(db.EmbeddedDocumentField(Route))

    @property
    def id(self):
        return str(self.pk)

class Passenger(db.EmbeddedDocument):
    name = db.StringField(required=True)
    age = db.IntField(required=True)
    berth_preference = db.StringField()
    uid = db.StringField(default=lambda: ''.join(random.choices(string.digits, k=8)))

class User(db.Document):
    username = db.StringField(unique=True, required=True)
    password_hash = db.StringField(required=True)
    role = db.StringField(default='user')
    email = db.StringField()
    phone_number = db.StringField()
    profile_picture = db.StringField()
    saved_passengers = db.ListField(db.EmbeddedDocumentField(Passenger))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def id(self):
        return str(self.pk)

class Booking(db.Document):
    pnr_number = db.StringField(unique=True, required=True)
    train = db.ReferenceField(Train, required=True)
    user = db.ReferenceField(User, required=True)
    passenger_name = db.StringField(required=True)
    passenger_age = db.IntField(required=True)
    seat_class = db.StringField(default='Sleeper')
    berth_preference = db.StringField()
    status = db.StringField(default='Confirmed')
    seat_number = db.StringField()
    fare = db.FloatField(default=0.0)

# --- Helper Functions ---
def generate_pnr():
    timestamp_part = str(int(time.time()))[-6:]
    random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"PNR{timestamp_part}{random_part}"

def calculate_fare(seat_class):
    fare_multipliers = {
        'Sleeper': 1.0, 'AC 3 Tier': 1.5, 'AC 2 Tier': 2.0, 'AC 1st Class': 3.0
    }
    return BASE_FARE * fare_multipliers.get(seat_class, 1.0)

def generate_seat_number(booking_count, total_seats, seat_class):
    seats_in_coach = SEATS_PER_COACH.get(seat_class, 72)
    coach_number = math.ceil(booking_count / seats_in_coach)
    seat_in_coach = booking_count % seats_in_coach
    if seat_in_coach == 0: seat_in_coach = seats_in_coach
    
    berth_map = {
        'Sleeper': {1: 'SL', 2: 'LB', 3: 'MB', 4: 'UB', 5: 'SL', 6: 'SU'},
        'AC 3 Tier': {1: 'LB', 2: 'MB', 3: 'UB', 4: 'SL', 5: 'SU'},
        'AC 2 Tier': {1: 'LB', 2: 'UB', 3: 'SL', 4: 'SU'},
        'AC 1st Class': {1: 'LB', 2: 'UB'}
    }
    berth_abbreviation = 'S'
    if seat_class in berth_map:
        berth_options = list(berth_map[seat_class].values())
        berth_abbreviation = berth_options[(seat_in_coach - 1) % len(berth_options)]
    class_initial = seat_class[0].upper()
    return f"{class_initial}{coach_number}-{seat_in_coach}-{berth_abbreviation}"

def calculate_travel_time(departure_time_str, arrival_time_str):
    try:
        departure_time = datetime.strptime(departure_time_str, '%H:%M')
        arrival_time = datetime.strptime(arrival_time_str, '%H:%M')
        if arrival_time < departure_time:
            arrival_time += timedelta(days=1)
        travel_duration = arrival_time - departure_time
        hours = travel_duration.seconds // 3600
        minutes = (travel_duration.seconds % 3600) // 60
        return f"{hours}h {minutes}m"
    except:
        return "N/A"

def generate_qr_code(data):
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = BytesIO()
    img.save(buf)
    return base64.b64encode(buf.getvalue()).decode('ascii')

# --- Routes ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    source = request.form['source']
    destination = request.form['destination']
    time_filter = request.form['time_filter']

    trains = Train.objects(source__iexact=source, destination__iexact=destination)
    
    filtered_trains = []
    for train in trains:
        t_time = train.departure_time
        include = False
        if time_filter == 'all': include = True
        elif time_filter == 'morning' and '05:00' <= t_time < '12:00': include = True
        elif time_filter == 'afternoon' and '12:00' <= t_time < '17:00': include = True
        elif time_filter == 'evening' and '17:00' <= t_time < '24:00': include = True
        
        if include:
            confirmed_bookings = Booking.objects(train=train, status='Confirmed').count()
            train.available_seats = train.total_seats - confirmed_bookings
            train.travel_time = calculate_travel_time(train.departure_time, train.arrival_time)
            filtered_trains.append(train)
            
    return render_template('results.html', trains=filtered_trains, source=source, destination=destination)

@app.route('/book/<train_id>')
def book(train_id):
    if not session.get('logged_in'):
        flash('You must be logged in to book a ticket.', 'danger')
        return redirect(url_for('login'))
    
    try:
        train_to_book = Train.objects.get_or_404(id=train_id)
    except:
         flash('Train not found.', 'danger')
         return redirect(url_for('index'))
    
    confirmed_count = Booking.objects(train=train_to_book, status='Confirmed').count()
    rac_count = Booking.objects(train=train_to_book, status='RAC').count()
    total_confirmed_rac = confirmed_count + rac_count
    rac_limit = train_to_book.total_seats + (train_to_book.total_seats // 10) 
    
    if total_confirmed_rac >= rac_limit:
        waitlist_count = Booking.objects(train=train_to_book, status='Waitlisted').count()
        if waitlist_count >= train_to_book.total_seats * 0.1:
            flash('Sorry, this train is fully waitlisted.', 'danger')
            return redirect(url_for('index'))
    
    try:
        user = User.objects.get(id=session['user_id'])
    except User.DoesNotExist:
        session.clear()
        flash('Session expired. Please log in again.', 'warning')
        return redirect(url_for('login'))

    return render_template('booking_form.html', train=train_to_book, saved_passengers=user.saved_passengers)

@app.route('/submit_booking', methods=['POST'])
def submit_booking():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    try:
        user = User.objects.get(id=session['user_id'])
    except User.DoesNotExist:
        session.clear()
        flash('Session expired. Please log in again.', 'warning')
        return redirect(url_for('login'))

    train_id = request.form['train_id']
    train_to_book = Train.objects.get(id=train_id)
    
    passenger_name = request.form['passenger_name']
    passenger_age = int(request.form['passenger_age'])
    seat_class = request.form['seat_class']
    requested_berth = request.form.get('berth_preference')
    save_passenger = request.form.get('save_passenger')
    
    confirmed_bookings = Booking.objects(train=train_to_book, status='Confirmed').count()
    rac_bookings = Booking.objects(train=train_to_book, status='RAC').count()
    waitlisted_bookings = Booking.objects(train=train_to_book, status='Waitlisted').count()

    status = 'Confirmed'
    seat_number = None
    rac_limit = train_to_book.total_seats + 10 
    
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

    new_booking = Booking(
        pnr_number=generate_pnr(),
        train=train_to_book,
        user=user,
        passenger_name=passenger_name,
        passenger_age=passenger_age,
        seat_class=seat_class,
        berth_preference=requested_berth,
        status=status,
        seat_number=seat_number,
        fare=calculate_fare(seat_class)
    )
    new_booking.save()

    if save_passenger:
        exists = any(p.name == passenger_name and p.age == passenger_age for p in user.saved_passengers)
        if not exists:
            new_p = Passenger(name=passenger_name, age=passenger_age, berth_preference=requested_berth)
            user.saved_passengers.append(new_p)
            user.save()
    
    return redirect(url_for('booking_confirmation', pnr=new_booking.pnr_number))

@app.route('/confirmation/<pnr>')
def booking_confirmation(pnr):
    booking = Booking.objects.get_or_404(pnr_number=pnr)
    return render_template('booking_confirmation.html', booking=booking)

@app.route('/pnr_status')
def pnr_status():
    pnr = request.args.get('pnr')
    if not pnr: return redirect(url_for('index'))
    booking = Booking.objects(pnr_number=pnr.strip()).first()
    if booking:
        return render_template('ticket_details.html', booking=booking)
    else:
        flash('Invalid PNR Number.', 'danger')
        return redirect(url_for('index'))

@app.route('/download_ticket/<pnr>')
def download_ticket(pnr):
    booking = Booking.objects.get_or_404(pnr_number=pnr)
    
    pdf = FPDF(unit="mm", format="A4")
    pdf.add_page()
    
    # 1. Enhanced QR Data
    qr_data = (f"PNR: {booking.pnr_number}\n"
               f"Name: {booking.passenger_name}\n"
               f"Age: {booking.passenger_age}\n"
               f"Train: {booking.train.train_name}\n"
               f"Seat: {booking.seat_number or 'WL/RAC'}\n"
               f"Berth: {booking.berth_preference or 'N/A'}")
    
    qr_base64 = generate_qr_code(qr_data)
    
    # 2. Add QR Image to PDF (using Temp File)
    try:
        qr_bytes = base64.b64decode(qr_base64)
        with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as temp_qr:
            temp_qr.write(qr_bytes)
            temp_qr_path = temp_qr.name
            
        pdf.set_font("Helvetica", "B", 24)
        pdf.cell(0, 15, "Railway E-Ticket", 0, 1, 'C') 
        pdf.ln(5)
        
        pdf.set_draw_color(100, 100, 100)
        pdf.rect(10, 35, 190, 140) # Increased height for more details
        
        pdf.image(temp_qr_path, x=160, y=40, w=30)
        os.remove(temp_qr_path)
    except Exception as e:
        print(f"QR Error: {e}")

    # 3. Add More Ticket Details
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_xy(15, 45)
    pdf.cell(0, 8, f"PNR Number: {booking.pnr_number}", 0, 1, 'L')
    pdf.set_xy(15, 55)
    pdf.cell(0, 8, f"Status: {booking.status}", 0, 1, 'L')
    
    # Passenger Section
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_xy(15, 75)
    pdf.cell(0, 8, "Passenger Details", 0, 1, 'L')
    
    pdf.set_font("Helvetica", "", 12)
    pdf.set_xy(15, 83)
    pdf.cell(0, 8, f"Name: {booking.passenger_name}", 0, 1, 'L')
    pdf.set_xy(15, 91)
    pdf.cell(0, 8, f"Age: {booking.passenger_age} years", 0, 1, 'L')
    pdf.set_xy(15, 99)
    pdf.cell(0, 8, f"Berth Preference: {booking.berth_preference or 'None'}", 0, 1, 'L')
    
    # Journey Section
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_xy(15, 115)
    pdf.cell(0, 8, "Journey Details", 0, 1, 'L')
    
    pdf.set_font("Helvetica", "", 12)
    pdf.set_xy(15, 123)
    pdf.cell(0, 8, f"Train: {booking.train.train_name}", 0, 1, 'L')
    pdf.set_xy(15, 131)
    pdf.cell(0, 8, f"Route: {booking.train.source} -> {booking.train.destination}", 0, 1, 'L')
    pdf.set_xy(15, 139)
    pdf.cell(0, 8, f"Class: {booking.seat_class}", 0, 1, 'L')
    pdf.set_xy(15, 147)
    pdf.cell(0, 8, f"Seat/Berth No: {booking.seat_number or 'Allocated on Chart Preparation'}", 0, 1, 'L')
    
    # Fare
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(25, 135, 84) 
    pdf.set_xy(15, 162)
    pdf.cell(0, 8, f"Total Fare: ${booking.fare:.2f}", 0, 1, 'L')
    
    pdf_output = pdf.output(dest='S').encode('latin-1')
    response = make_response(pdf_output)
    response.headers.set('Content-Disposition', 'attachment', filename=f'ticket_{pnr}.pdf')
    response.headers.set('Content-Type', 'application/pdf')
    return response

@app.route('/print_ticket/<pnr>')
def print_ticket(pnr):
    booking = Booking.objects.get_or_404(pnr_number=pnr)
    
    # Enhanced QR Data for Print View as well
    qr_data = (f"PNR: {booking.pnr_number}\n"
               f"Name: {booking.passenger_name}\n"
               f"Age: {booking.passenger_age}\n"
               f"Train: {booking.train.train_name}\n"
               f"Seat: {booking.seat_number or 'WL/RAC'}\n"
               f"Berth: {booking.berth_preference or 'N/A'}")
               
    qr_base64 = generate_qr_code(qr_data)
    return render_template('print_ticket.html', booking=booking, qr_code=qr_base64)

@app.route('/signup', methods=['POST'])
def signup():
    username = request.form['username']
    password = request.form['password']
    if User.objects(username=username).first():
        flash('Username already exists.', 'danger')
        return redirect(url_for('index'))
    
    new_user = User(username=username, email=request.form.get('email'), phone_number=request.form.get('phone'))
    new_user.set_password(password)
    new_user.save()
    flash('Account created successfully!', 'success')
    return redirect(url_for('index'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.objects(username=request.form['username']).first()
        if user and user.check_password(request.form['password']):
            session['logged_in'] = True
            session['user_id'] = str(user.id)
            session['username'] = user.username
            session['is_admin'] = (user.role == 'admin')
            flash(f'Welcome back, {user.username}!', 'success')
        else:
            flash('Invalid credentials.', 'danger')
        return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('is_admin'): return redirect(url_for('login'))
    
    # Pagination settings
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    # Calculate pagination details
    total_bookings = Booking.objects.count()
    total_pages = math.ceil(total_bookings / per_page)
    
    # Fetch specific page of bookings (Optimized query)
    paginated_bookings = Booking.objects().order_by('-id').skip((page - 1) * per_page).limit(per_page)
    
    all_trains = Train.objects().order_by('train_name')
    
    return render_template('admin_dashboard.html', 
                           bookings=paginated_bookings, 
                           trains=all_trains,
                           page=page,
                           total_pages=total_pages)

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/my_bookings')
def my_bookings():
    if not session.get('logged_in'): return redirect(url_for('login'))
    try:
        user = User.objects.get(id=session['user_id'])
    except User.DoesNotExist:
        session.clear()
        return redirect(url_for('login'))
        
    # Pagination Logic
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    total_bookings = Booking.objects(user=user).count()
    total_pages = math.ceil(total_bookings / per_page)
    
    # Fetch paginated bookings
    bookings = Booking.objects(user=user).order_by('-id').skip((page - 1) * per_page).limit(per_page)
    
    return render_template('my_bookings.html', 
                           bookings=bookings, 
                           page=page, 
                           total_pages=total_pages)

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if not session.get('logged_in'): return redirect(url_for('login'))
    try:
        user = User.objects.get(id=session['user_id'])
    except User.DoesNotExist:
        session.clear()
        return redirect(url_for('login'))

    if request.method == 'POST':
        action = request.args.get('action')
        if action == 'add_passenger':
            new_p = Passenger(
                name=request.form['passenger_name'], 
                age=int(request.form['passenger_age']), 
                berth_preference=request.form.get('berth_preference')
            )
            user.saved_passengers.append(new_p)
            user.save()
        elif action == 'delete_passenger':
            pass_id = request.args.get('passenger_id')
            user.saved_passengers = [p for p in user.saved_passengers if str(p.uid) != pass_id]
            user.save()
        else:
            user.username = request.form['username']
            user.email = request.form['email']
            user.phone_number = request.form['phone']
            user.save()
            session['username'] = user.username
            
        return redirect(url_for('profile'))
    
    recent_bookings = Booking.objects(user=user).order_by('-id').limit(5)
    return render_template('profile.html', user=user, recent_bookings=recent_bookings, saved_passengers=user.saved_passengers)

@app.route('/change_password', methods=['POST'])
def change_password():
    if not session.get('logged_in'): return redirect(url_for('login'))
    try:
        user = User.objects.get(id=session['user_id'])
    except User.DoesNotExist:
        session.clear()
        return redirect(url_for('login'))
        
    if not user.check_password(request.form['current_password']):
        flash('Incorrect current password.', 'danger')
    elif request.form['new_password'] != request.form['confirm_password']:
        flash('Passwords do not match.', 'danger')
    else:
        user.set_password(request.form['new_password'])
        user.save()
        flash('Password updated.', 'success')
    return redirect(url_for('profile'))

@app.route('/profile/delete', methods=['POST'])
def delete_account():
    if not session.get('logged_in'): return redirect(url_for('login'))
    try:
        user = User.objects.get(id=session['user_id'])
        Booking.objects(user=user).delete()
        user.delete()
    except User.DoesNotExist:
        pass
    session.clear()
    flash('Account deleted.', 'info')
    return redirect(url_for('index'))

@app.route('/admin/add_train', methods=['POST'])
def add_train():
    if not session.get('is_admin'): return redirect(url_for('login'))
    Train(
        train_name=request.form['train_name'],
        source=request.form['source'],
        destination=request.form['destination'],
        departure_time=request.form['departure_time'],
        total_seats=int(request.form['total_seats'])
    ).save()
    flash('Train added.', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/train_route_check')
def train_route_check():
    query = request.args.get('train_query')
    if not query: return redirect(url_for('index'))
    train = Train.objects(train_name__iexact=query).first()
    if not train:
        train = Train.objects(train_name__icontains=query).first()
    
    if train:
        return redirect(url_for('train_route', train_id=train.id))
    else:
        flash(f'No train found matching "{query}".', 'danger')
        return redirect(url_for('index'))

@app.route('/train_route/<train_id>')
def train_route(train_id):
    try:
        train = Train.objects.get_or_404(id=train_id)
        return render_template('train_route.html', train=train)
    except:
        flash('Invalid train ID.', 'danger')
        return redirect(url_for('index'))

@app.route('/book_return/<pnr>')
def book_return(pnr):
    booking = Booking.objects.get_or_404(pnr_number=pnr)
    return_train = Train.objects(source__iexact=booking.train.destination, destination__iexact=booking.train.source).first()
    if return_train:
        return redirect(url_for('book', train_id=return_train.id))
    else:
        flash('No return train found.', 'danger')
        return redirect(url_for('booking_confirmation', pnr=pnr))

if __name__ == '__main__':
    app.run(debug=True)