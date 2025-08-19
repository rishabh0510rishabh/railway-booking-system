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
    
    # Create and add the admin user with email and phone_number
    admin_user = User(username='admin', role='admin', email='admin@example.com', phone_number='1234567890')
    admin_user.set_password('password123')
    db.session.add(admin_user)

    # Create and add a test user with email and phone_number
    test_user = User(username='testuser', role='user', email='testuser@example.com', phone_number='0987654321')
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

    # Make Shatabdi Express (ID 1, 150 seats) nearly full (5 seats left)
    for i in range(145):
        user_id = test_user_id if i % 2 == 0 else admin_id
        db.session.add(Booking(pnr_number=generate_pnr(), user_id=user_id, train_id=1, passenger_name=f'Passenger S{i+1}', passenger_age=30, seat_class='Sleeper'))

    # Make Rajdhani Express (ID 2, 200 seats) nearly full (2 seats left)
    for i in range(198):
        user_id = admin_id if i % 2 == 0 else test_user_id
        db.session.add(Booking(pnr_number=generate_pnr(), user_id=user_id, train_id=2, passenger_name=f'Passenger R{i+1}', passenger_age=40, seat_class='AC 2 Tier'))

    # Make Duronto Express (ID 3, 180 seats) COMPLETELY FULL
    for i in range(180):
        db.session.add(Booking(pnr_number=generate_pnr(), user_id=test_user_id, train_id=3, passenger_name=f'Passenger D{i+1}', passenger_age=25, seat_class='AC 3 Tier'))

    # Add a few bookings to Tejas Express (ID 4) to leave it mostly available
    db.session.add(Booking(pnr_number=generate_pnr(), user_id=test_user_id, train_id=4, passenger_name='Alice Smith', passenger_age=34, seat_class='AC 1st Class'))
    db.session.add(Booking(pnr_number=generate_pnr(), user_id=admin_id, train_id=4, passenger_name='Bob Johnson', passenger_age=45, seat_class='AC 1st Class'))

    db.session.commit()
    print("-> Realistic bookings added successfully.")

    print("\n✅ Database has been successfully initialized and populated!")
