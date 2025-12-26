import random
import string
import math
from datetime import datetime, timedelta
from railway_app import create_app
from models import db, Train, User, Booking, Passenger, Route
from railway_app.utils import generate_pnr, calculate_fare, generate_seat_number, SEATS_PER_COACH
app = create_app()
cities = ['New Delhi', 'Mumbai', 'Kolkata', 'Chennai', 'Bangalore', 'Hyderabad', 'Pune', 'Ahmedabad', 'Lucknow', 'Jaipur', 'Patna', 'Bhopal', 'Chandigarh']
prefixes = ['Express', 'Mail', 'Shatabdi', 'Rajdhani', 'Duronto', 'Superfast', 'Intercity']

def random_time_string():
    """Generates a random time string in HH:MM format."""
    return f"{random.randint(0, 23):02d}:{random.randint(0, 59):02d}"

def get_berth_preference(age):
    """Assigns a realistic berth preference based on age."""
    if age >= 60:
        return random.choice(['Lower', 'Side Lower'])
    return random.choice(['Lower', 'Middle', 'Upper', 'Side Lower', 'Side Upper'])

with app.app_context():
    # 1. Clear existing data
    print("🧹 Clearing old database data...")
    User.drop_collection()
    Train.drop_collection()
    Booking.drop_collection()

    # 2. Add Users
    print("busts Adding users...")
    admin = User(username='admin', role='admin', email='admin@example.com')
    admin.set_password('password123')
    admin.save()

    test_user = User(username='testuser', role='user', email='test@example.com')
    test_user.set_password('password')
    # Add saved passengers embedded in the user
    test_user.saved_passengers = [
        Passenger(name='Alice Smith', age=34, berth_preference='Upper'),
        Passenger(name='Bob Johnson', age=45, berth_preference='Lower'),
        Passenger(name='Charlie Brown', age=62, berth_preference='Lower')
    ]
    test_user.save()

    # 3. Add Trains
    print("🚂 Generating 100 trains with routes...")
    all_trains = []
    for i in range(100): 
        source = random.choice(cities)
        dest = random.choice(cities)
        while source == dest: dest = random.choice(cities)
        
        dept = random_time_string()
        dept_dt = datetime.strptime(dept, '%H:%M')
        
        # Random duration between 2 and 24 hours
        travel_hours = random.randint(2, 24)
        arrival_dt = dept_dt + timedelta(hours=travel_hours)
        
        # Create Train Document
        t = Train(
            train_name=f"{random.choice(cities)} {random.choice(prefixes)}",
            source=source,
            destination=dest,
            departure_time=dept,
            arrival_time=arrival_dt.strftime('%H:%M'),
            total_seats=random.randint(72, 150) # Random capacity
        )
        
        # Add Routes (Embedded)
        current_time = dept_dt
        # Create 2 to 5 intermediate stops
        for j in range(random.randint(2, 5)):
             # Advance time for next stop
             current_time += timedelta(minutes=random.randint(30, 120))
             # Don't add stops if they exceed travel time (simplified logic)
             if current_time >= arrival_dt: break
             
             stop_name = random.choice(cities)
             if stop_name not in [source, dest]:
                 t.route_stops.append(Route(
                     stop_name=stop_name, 
                     arrival_time=current_time.strftime('%H:%M'), 
                     stop_order=j+1
                 ))
        t.save()
        all_trains.append(t)

    # 4. Add Bookings
    print("🎫 Generating bookings for trains...")
    
    # We will book random seats on random trains
    users = [admin, test_user]
    
    for train in all_trains:
        # Decide how full this train is (0% to 110% to simulate waitlists)
        fill_percentage = random.random() * 1.1 
        num_bookings_to_create = int(train.total_seats * fill_percentage)
        
        # Track counts for this train to assign seats correctly
        current_confirmed = 0
        current_rac = 0
        current_wl = 0
        
        # Define RAC limit (e.g., 10% extra)
        rac_limit = train.total_seats + int(train.total_seats * 0.1)

        for _ in range(num_bookings_to_create):
            # Pick a random user and seat class
            user = random.choice(users)
            seat_class = random.choice(list(SEATS_PER_COACH.keys()))
            
            # Generate random passenger details
            p_age = random.randint(18, 80)
            p_name = f"Passenger {random.randint(1000, 9999)}"
            p_berth = get_berth_preference(p_age)
            
            # Determine Status and Seat Number
            status = 'Confirmed'
            seat_number = ''
            
            if current_confirmed < train.total_seats:
                status = 'Confirmed'
                current_confirmed += 1
                # Use the function from app.py
                seat_number = generate_seat_number(current_confirmed, train.total_seats, seat_class)
            elif (current_confirmed + current_rac) < rac_limit:
                status = 'RAC'
                current_rac += 1
                seat_number = f"RAC-{current_rac}"
            else:
                status = 'Waitlisted'
                current_wl += 1
                seat_number = f"WL-{current_wl}"
            
            # Create Booking Document
            Booking(
                pnr_number=generate_pnr(),
                train=train,
                user=user,
                passenger_name=p_name,
                passenger_age=p_age,
                seat_class=seat_class,
                berth_preference=p_berth,
                status=status,
                seat_number=seat_number,
                fare=calculate_fare(seat_class)
            ).save()

    print(f"✅ Database initialized! Created {len(all_trains)} trains and thousands of bookings.")