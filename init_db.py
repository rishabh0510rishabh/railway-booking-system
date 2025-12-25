import random
import time
import string
from datetime import datetime, timedelta
from app import app, db, Train, User, Booking, Route, Passenger, generate_pnr

# --- Configuration ---
cities = ['New Delhi', 'Mumbai', 'Kolkata', 'Chennai', 'Bangalore', 'Hyderabad', 'Pune', 'Ahmedabad', 'Lucknow', 'Jaipur']
prefixes = ['Express', 'Mail', 'Shatabdi', 'Rajdhani', 'Duronto', 'Superfast']

def random_time_string():
    return f"{random.randint(0, 23):02d}:{random.randint(0, 59):02d}"

with app.app_context():
    # Clear existing data
    print("Clearing database...")
    User.drop_collection()
    Train.drop_collection()
    Booking.drop_collection()

    # 1. Add Users
    print("Adding users...")
    admin = User(username='admin', role='admin', email='admin@example.com')
    admin.set_password('password123')
    admin.save()

    test_user = User(username='testuser', role='user', email='test@example.com')
    test_user.set_password('password')
    # Add saved passengers embedded in the user
    test_user.saved_passengers = [
        Passenger(name='Alice Smith', age=34, berth_preference='Upper'),
        Passenger(name='Bob Johnson', age=45, berth_preference='Lower')
    ]
    test_user.save()

    # 2. Add Trains
    print("Generating trains...")
    for i in range(50): # Reduced count for faster init
        source = random.choice(cities)
        dest = random.choice(cities)
        while source == dest: dest = random.choice(cities)
        
        dept = random_time_string()
        dept_dt = datetime.strptime(dept, '%H:%M')
        arrival_dt = dept_dt + timedelta(hours=random.randint(2, 12))
        
        t = Train(
            train_name=f"{random.choice(string.ascii_uppercase)}{random.randint(100,999)} {random.choice(prefixes)}",
            source=source,
            destination=dest,
            departure_time=dept,
            arrival_time=arrival_dt.strftime('%H:%M'),
            total_seats=random.randint(20, 50)
        )
        
        # Add Routes (Embedded)
        current_time = dept_dt
        for j in range(random.randint(2, 4)):
             current_time += timedelta(minutes=60)
             stop_name = random.choice(cities)
             if stop_name not in [source, dest]:
                 t.route_stops.append(Route(
                     stop_name=stop_name, 
                     arrival_time=current_time.strftime('%H:%M'), 
                     stop_order=j+1
                 ))
        t.save()

    print("✅ Database initialized with MongoDB!")