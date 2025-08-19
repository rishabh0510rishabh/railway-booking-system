import os
import random
from app import app, db, Train, User, Booking, generate_pnr, Passenger

# --- Configuration ---
DB_FILE = 'railway.db'

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
    
    # Create and add the admin user with email, phone, and profile picture
    admin_user = User(username='admin', role='admin', email='admin@example.com', phone_number='1234567890', profile_picture='default_profile.png')
    admin_user.set_password('password123')
    db.session.add(admin_user)

    # Create and add a test user with email, phone, and profile picture
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
    
    # Define user IDs for test bookings
    admin_id = User.query.filter_by(username='admin').first().id
    test_user_id = User.query.filter_by(username='testuser').first().id

    # Add saved passengers
    db.session.add(Passenger(user_id=test_user_id, name='Alice Smith', age=34, berth_preference='Upper'))
    db.session.add(Passenger(user_id=test_user_id, name='Bob Johnson', age=45, berth_preference='Lower'))
    db.session.add(Passenger(user_id=admin_id, name='Charlie Brown', age=65, berth_preference='Lower'))
    db.session.commit()
    print("-> Saved passengers added.")

    # A helper function to randomly assign berths with a preference for lower for seniors
    def get_berth_preference(age):
        if age >= 60:
            return random.choice(['Lower', 'Side Lower'])
        return random.choice(['Lower', 'Middle', 'Upper', 'Side Lower', 'Side Upper'])

    # Make Shatabdi Express (ID 1, 150 seats) nearly full (5 seats left)
    for i in range(145):
        user_id = test_user_id if i % 2 == 0 else admin_id
        age = random.randint(18, 70)
        berth = get_berth_preference(age)
        db.session.add(Booking(pnr_number=generate_pnr(), user_id=user_id, train_id=1, passenger_name=f'Passenger S{i+1}', passenger_age=age, seat_class='Sleeper', berth_preference=berth))

    # Make Rajdhani Express (ID 2, 200 seats) nearly full (2 seats left)
    for i in range(198):
        user_id = admin_id if i % 2 == 0 else test_user_id
        age = random.randint(18, 70)
        berth = get_berth_preference(age)
        db.session.add(Booking(pnr_number=generate_pnr(), user_id=user_id, train_id=2, passenger_name=f'Passenger R{i+1}', passenger_age=age, seat_class='AC 2 Tier', berth_preference=berth))

    # Make Duronto Express (ID 3, 180 seats) COMPLETELY FULL
    for i in range(180):
        user_id = test_user_id
        age = random.randint(18, 70)
        berth = get_berth_preference(age)
        db.session.add(Booking(pnr_number=generate_pnr(), user_id=user_id, train_id=3, passenger_name=f'Passenger D{i+1}', passenger_age=age, seat_class='AC 3 Tier', berth_preference=berth))

    # Add a few bookings to Tejas Express (ID 4) to leave it mostly available
    db.session.add(Booking(pnr_number=generate_pnr(), user_id=test_user_id, train_id=4, passenger_name='Alice Smith', passenger_age=34, seat_class='AC 1st Class', berth_preference='Upper'))
    db.session.add(Booking(pnr_number=generate_pnr(), user_id=admin_id, train_id=4, passenger_name='Bob Johnson', passenger_age=45, seat_class='AC 1st Class', berth_preference='Lower'))
    db.session.add(Booking(pnr_number=generate_pnr(), user_id=admin_id, train_id=4, passenger_name='Charlie Brown', passenger_age=65, seat_class='AC 1st Class', berth_preference='Side Lower'))

    db.session.commit()
    print("-> Realistic bookings added successfully.")

    print("\n✅ Database has been successfully initialized and populated!")