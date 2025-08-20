import os
import random
import time
import string
import math
from app import app, db, Train, User, Booking, generate_pnr, Passenger

# --- Configuration ---
DB_FILE = 'railway.db'
BASE_FARE = 1000
SEATS_PER_COACH = {
    'Sleeper': 72,
    'AC 3 Tier': 64,
    'AC 2 Tier': 46,
    'AC 1st Class': 18
}

# --- Helper Functions (copied from app.py to make this script self-contained) ---
def calculate_fare(seat_class):
    """Calculates fare based on seat class."""
    fare_multipliers = {
        'Sleeper': 1.0,
        'AC 3 Tier': 1.5,
        'AC 2 Tier': 2.0,
        'AC 1st Class': 3.0
    }
    return BASE_FARE * fare_multipliers.get(seat_class, 1.0)

def generate_seat_number(booking_count, seat_class):
    """Generates a detailed seat number based on booking count and coach class.
    
    This function assigns a seat number in the format 'Coach-Seat-Berth'
    (e.g., 'S1-32-SL' for Sleeper Class, Coach 1, Seat 32, Side Lower Berth).
    """
    seats_in_coach = SEATS_PER_COACH.get(seat_class, 72)
    
    coach_number = math.ceil(booking_count / seats_in_coach)
    seat_in_coach = booking_count % seats_in_coach
    if seat_in_coach == 0:
        seat_in_coach = seats_in_coach
        coach_number -= 1
    
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

def generate_pnr():
    """Generates a unique PNR number."""
    timestamp_part = str(int(time.time()))[-6:]
    random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"PNR{timestamp_part}{random_part}"


# --- Main Execution ---
with app.app_context():
    # Delete old database if it exists to ensure a clean start
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)
        print("Old database removed.")

    # Create all tables based on the models in app.py
    db.create_all()
    print("Database tables created.")

    # 1. Add Users
    print("Adding default users...")
    
    admin_user = User(username='admin', role='admin', email='admin@example.com', phone_number='1234567890', profile_picture='default_profile.png')
    admin_user.set_password('password123')
    db.session.add(admin_user)

    test_user = User(username='testuser', role='user', email='testuser@example.com', phone_number='0987654321', profile_picture='default_profile.png')
    test_user.set_password('password')
    db.session.add(test_user)
    
    db.session.commit()
    print("-> Added 'admin' and 'testuser'.")

    # 2. Add Trains
    print("Adding train data...")
    train_data = [
        {'name': 'Shatabdi Express', 'source': 'New Delhi', 'dest': 'Lucknow', 'time': '06:15', 'seats': 150},
        {'name': 'Rajdhani Express', 'source': 'Mumbai', 'dest': 'New Delhi', 'time': '17:00', 'seats': 200},
        {'name': 'Duronto Express', 'source': 'Kolkata', 'dest': 'Pune', 'time': '05:45', 'seats': 180},
        {'name': 'Tejas Express', 'source': 'Chennai', 'dest': 'Madurai', 'time': '06:00', 'seats': 120},
        {'name': 'Gatimaan Express', 'source': 'Delhi', 'dest': 'Agra', 'time': '08:10', 'seats': 100},
        {'name': 'Deccan Queen', 'source': 'Mumbai', 'dest': 'Pune', 'time': '17:10', 'seats': 160},
        {'name': 'Goa Express', 'source': 'Vasco da Gama', 'dest': 'Delhi', 'time': '15:00', 'seats': 190},
        {'name': 'Punjab Mail', 'source': 'Mumbai', 'dest': 'Firozpur', 'time': '19:35', 'seats': 260},
        {'name': 'Bihar Sampark Kranti Exp', 'source': 'New Delhi', 'dest': 'Darbhanga', 'time': '07:40', 'seats': 130},
    ]
    for train_info in train_data:
        db.session.add(Train(train_name=train_info['name'], source=train_info['source'], destination=train_info['dest'], departure_time=train_info['time'], total_seats=train_info['seats']))
    db.session.commit()
    print(f"-> Added {len(train_data)} trains.")

    # 3. Add a large number of realistic bookings
    print("Adding realistic bookings...")
    
    admin_id = User.query.filter_by(username='admin').first().id
    test_user_id = User.query.filter_by(username='testuser').first().id

    db.session.add(Passenger(user_id=test_user_id, name='Alice Smith', age=34, berth_preference='Upper'))
    db.session.add(Passenger(user_id=test_user_id, name='Bob Johnson', age=45, berth_preference='Lower'))
    db.session.add(Passenger(user_id=admin_id, name='Charlie Brown', age=65, berth_preference='Lower'))
    db.session.commit()
    print("-> Saved passengers added.")

    def get_berth_preference(age):
        if age >= 60:
            return random.choice(['Lower', 'Side Lower'])
        return random.choice(['Lower', 'Middle', 'Upper', 'Side Lower', 'Side Upper'])

    # Make Shatabdi Express (ID 1, 150 seats) nearly full (5 seats left)
    for i in range(145):
        user_id = test_user_id if i % 2 == 0 else admin_id
        age = random.randint(18, 70)
        berth = get_berth_preference(age)
        seat_num = generate_seat_number(i + 1, 'Sleeper')
        fare = calculate_fare('Sleeper')
        db.session.add(Booking(pnr_number=generate_pnr(), user_id=user_id, train_id=1, passenger_name=f'Passenger S{i+1}', passenger_age=age, seat_class='Sleeper', berth_preference=berth, status='Confirmed', seat_number=seat_num, fare=fare))

    # Make Rajdhani Express (ID 2, 200 seats) nearly full (2 seats left)
    for i in range(198):
        user_id = admin_id if i % 2 == 0 else test_user_id
        age = random.randint(18, 70)
        berth = get_berth_preference(age)
        seat_num = generate_seat_number(i + 1, 'AC 2 Tier')
        fare = calculate_fare('AC 2 Tier')
        db.session.add(Booking(pnr_number=generate_pnr(), user_id=user_id, train_id=2, passenger_name=f'Passenger R{i+1}', passenger_age=age, seat_class='AC 2 Tier', berth_preference=berth, status='Confirmed', seat_number=seat_num, fare=fare))

    # Make Duronto Express (ID 3, 180 seats) COMPLETELY FULL and then add RAC/WL
    for i in range(180):
        user_id = test_user_id
        age = random.randint(18, 70)
        berth = get_berth_preference(age)
        seat_num = generate_seat_number(i + 1, 'AC 3 Tier')
        fare = calculate_fare('AC 3 Tier')
        db.session.add(Booking(pnr_number=generate_pnr(), user_id=user_id, train_id=3, passenger_name=f'Passenger D{i+1}', passenger_age=age, seat_class='AC 3 Tier', berth_preference=berth, status='Confirmed', seat_number=seat_num, fare=fare))

    # Add 10 RAC tickets for the Duronto Express
    for i in range(10):
        user_id = test_user_id
        age = random.randint(18, 70)
        berth = get_berth_preference(age)
        rac_num = i + 1
        fare = calculate_fare('AC 3 Tier')
        db.session.add(Booking(pnr_number=generate_pnr(), user_id=user_id, train_id=3, passenger_name=f'Passenger D{i+181}', passenger_age=age, seat_class='AC 3 Tier', berth_preference=berth, status='RAC', seat_number=f"RAC-{rac_num}", fare=fare))

    # Add a few bookings to Tejas Express (ID 4) to leave it mostly available
    db.session.add(Booking(pnr_number=generate_pnr(), user_id=test_user_id, train_id=4, passenger_name='Alice Smith', passenger_age=34, seat_class='AC 1st Class', berth_preference='Upper', status='Confirmed', seat_number=generate_seat_number(1, 'AC 1st Class'), fare=calculate_fare('AC 1st Class')))
    db.session.add(Booking(pnr_number=generate_pnr(), user_id=admin_id, train_id=4, passenger_name='Bob Johnson', passenger_age=45, seat_class='AC 1st Class', berth_preference='Lower', status='Confirmed', seat_number=generate_seat_number(2, 'AC 1st Class'), fare=calculate_fare('AC 1st Class')))
    db.session.add(Booking(pnr_number=generate_pnr(), user_id=admin_id, train_id=4, passenger_name='Charlie Brown', passenger_age=65, seat_class='AC 1st Class', berth_preference='Side Lower', status='Confirmed', seat_number=generate_seat_number(3, 'AC 1st Class'), fare=calculate_fare('AC 1st Class')))

    db.session.commit()
    print("-> Realistic bookings added successfully.")

    print("\n✅ Database has been successfully initialized and populated!")
