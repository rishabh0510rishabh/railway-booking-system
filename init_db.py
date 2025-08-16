import os
from app import app, db, Train, User, Booking, generate_pnr

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
    
    # Create an admin user
    admin_user = User(username='admin', role='admin')
    admin_user.set_password('password123')
    db.session.add(admin_user)

    # Create a regular user for testing
    test_user = User(username='testuser', role='user')
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
        {'name': 'Tejas Express', 'source': 'Chennai', 'dest': 'Madurai', 'time': '06:00', 'seats': 5}, # Nearly Full
        {'name': 'Gatimaan Express', 'source': 'Delhi', 'dest': 'Agra', 'time': '08:10', 'seats': 100},
    ]
    for train_info in train_data:
        db.session.add(Train(train_name=train_info['name'], source=train_info['source'], destination=train_info['dest'], departure_time=train_info['time'], total_seats=train_info['seats']))
    db.session.commit()
    print(f"-> Added {len(train_data)} trains.")

    # 3. Add Anonymous Bookings for Testing
    print("Adding anonymous booking data...")
    # Add 3 bookings to Tejas Express (ID 4) to test availability logic
    booking1 = Booking(pnr_number=generate_pnr(), train_id=4, passenger_name='Test Passenger 1', passenger_age=30, seat_class='AC Chair Car')
    booking2 = Booking(pnr_number=generate_pnr(), train_id=4, passenger_name='Test Passenger 2', passenger_age=45, seat_class='AC Chair Car')
    booking3 = Booking(pnr_number=generate_pnr(), train_id=1, passenger_name='Test Passenger 3', passenger_age=25, seat_class='Sleeper')
    
    db.session.add_all([booking1, booking2, booking3])
    db.session.commit()
    print("-> Added 3 anonymous bookings.")

    print("\n✅ Database has been successfully initialized for Version 1.0!")
