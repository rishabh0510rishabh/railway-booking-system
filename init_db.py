import os
import random
import time
import string
import math
from datetime import datetime, timedelta, time as dt_time
from app import app, db, Train, User, Booking, generate_pnr, Passenger, Route

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

def generate_pnr_unique_in_memory(existing_pnrs):
    """Generates a unique PNR number not present in the existing set."""
    while True:
        timestamp_part = str(int(time.time()))[-6:]
        random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
        pnr = f"PNR{timestamp_part}{random_part}"
        if pnr not in existing_pnrs:
            return pnr

def get_berth_preference(age):
    if age >= 60:
        return random.choice(['Lower', 'Side Lower'])
    return random.choice(['Lower', 'Middle', 'Upper', 'Side Lower', 'Side Upper'])

def random_time_string():
    """Generates a random time string in HH:MM format."""
    return f"{random.randint(0, 23):02d}:{random.randint(0, 59):02d}"

def random_city():
    """Returns a random city name from a predefined list."""
    cities = ['New Delhi', 'Mumbai', 'Kolkata', 'Chennai', 'Bangalore', 'Hyderabad', 'Pune', 'Ahmedabad', 'Lucknow', 'Jaipur', 'Patna', 'Bhopal']
    return random.choice(cities)

def random_train_name():
    """Generates a random train name."""
    prefixes = ['Express', 'Mail', 'Shatabdi', 'Rajdhani', 'Duronto', 'Superfast']
    return f"{random.choice(string.ascii_uppercase)}{random.randint(100, 999)} {random.choice(prefixes)}"


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

    admin_id = User.query.filter_by(username='admin').first().id
    test_user_id = User.query.filter_by(username='testuser').first().id
    
    # Add a few saved passengers for the test user
    db.session.add(Passenger(user_id=test_user_id, name='Alice Smith', age=34, berth_preference='Upper'))
    db.session.add(Passenger(user_id=test_user_id, name='Bob Johnson', age=45, berth_preference='Lower'))
    db.session.add(Passenger(user_id=test_user_id, name='Charlie Brown', age=65, berth_preference='Lower'))
    db.session.commit()
    print("-> Saved passengers added.")

    # 2. Add a large dataset of trains
    print("Generating and adding a large dataset of trains...")
    num_trains = 200
    all_trains = []
    for i in range(1, num_trains + 1):
        source = random_city()
        destination = random_city()
        while source == destination:
            destination = random_city()
        
        departure_time_str = random_time_string()
        departure_dt = datetime.strptime(departure_time_str, '%H:%M')
        
        # Ensure arrival is after departure, possibly the next day
        travel_duration = timedelta(hours=random.randint(1, 20), minutes=random.randint(0, 59))
        arrival_dt = departure_dt + travel_duration
        arrival_time_str = arrival_dt.strftime('%H:%M')

        new_train = Train(
            id=i, 
            train_name=random_train_name(), 
            source=source, 
            destination=destination, 
            departure_time=departure_time_str, 
            arrival_time=arrival_time_str,
            total_seats=random.randint(20, 30)
        )
        all_trains.append(new_train)
    
    db.session.add_all(all_trains)
    db.session.commit()
    print(f"-> Added {num_trains} trains.")

    # 2.5 Generate Routes for all trains
    print("Generating routes for all trains...")
    all_routes = []
    for train in all_trains:
        # Generate random number of stops between 2 and 5
        num_stops = random.randint(2, 5)
        current_time_dt = datetime.strptime(train.departure_time, '%H:%M')
        
        for i in range(num_stops):
            stop_name = random_city()
            # Ensure stop is not the source or destination
            while stop_name == train.source or stop_name == train.destination:
                stop_name = random_city()
            
            # Ensure arrival times are sequential
            stop_arrival_dt = current_time_dt + timedelta(minutes=random.randint(30, 180))
            current_time_dt = stop_arrival_dt
            
            all_routes.append(Route(train_id=train.id, stop_name=stop_name, arrival_time=stop_arrival_dt.strftime('%H:%M'), stop_order=i+1))
    
    db.session.add_all(all_routes)
    db.session.commit()
    print("-> All train routes generated.")

    # 3. Add a large number of realistic bookings for all trains
    print("Adding realistic bookings...")
    all_bookings = []
    
    # Generate all PNRs needed upfront
    total_bookings = sum(random.randint(1, train.total_seats + 15) for train in all_trains)
    existing_pnrs = {b.pnr_number for b in Booking.query.all()}
    
    pnr_pool = set()
    while len(pnr_pool) < total_bookings:
        pnr_pool.add(generate_pnr_unique_in_memory(existing_pnrs.union(pnr_pool)))
    pnr_list = list(pnr_pool)

    # 20% of trains will be fully booked (with RAC/WL)
    full_trains = random.sample(all_trains, int(0.2 * num_trains))
    # 30% of trains will be mostly full (some seats left)
    busy_trains = random.sample([t for t in all_trains if t not in full_trains], int(0.3 * num_trains))
    # The rest will have some availability
    
    pnr_index = 0
    for train in all_trains:
        confirmed_count = 0
        rac_count = 0
        waitlist_count = 0
        
        if train in full_trains:
            num_bookings = random.randint(train.total_seats + 5, train.total_seats + 15)
        elif train in busy_trains:
            num_bookings = random.randint(train.total_seats - 5, train.total_seats)
        else:
            num_bookings = random.randint(1, train.total_seats - 5)

        for i in range(num_bookings):
            user_id = random.choice([admin_id, test_user_id])
            age = random.randint(18, 70)
            berth = get_berth_preference(age)
            seat_class = random.choice(list(SEATS_PER_COACH.keys()))
            fare = calculate_fare(seat_class)
            
            status = 'Confirmed'
            seat_number = None
            if confirmed_count < train.total_seats:
                status = 'Confirmed'
                seat_number = generate_seat_number(confirmed_count + 1, seat_class)
                confirmed_count += 1
            elif rac_count < 10: # Arbitrary RAC limit of 10
                status = 'RAC'
                rac_count += 1
                seat_number = f"RAC-{rac_count}"
            else:
                status = 'Waitlisted'
                waitlist_count += 1
                seat_number = f"WL-{waitlist_count}"

            all_bookings.append(Booking(
                pnr_number=pnr_list[pnr_index], 
                user_id=user_id, 
                train_id=train.id, 
                passenger_name=f'Passenger {train.id}-{i+1}', 
                passenger_age=age, 
                seat_class=seat_class, 
                berth_preference=berth, 
                status=status, 
                seat_number=seat_number, 
                fare=fare
            ))
            pnr_index += 1

    db.session.add_all(all_bookings)
    db.session.commit()
    print(f"-> Added a total of {len(all_bookings)} bookings.")
    
    print("\n✅ Database has been successfully initialized and populated with a large dataset!")
