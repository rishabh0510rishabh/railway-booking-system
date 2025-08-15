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
    print("Adding users...")
    users_to_add = [
        {'username': 'admin', 'password': 'password123', 'role': 'admin'},
        {'username': 'alice', 'password': 'password', 'role': 'user'},
        {'username': 'bob', 'password': 'password', 'role': 'user'}
    ]
    for user_data in users_to_add:
        new_user = User(username=user_data['username'], role=user_data['role'])
        new_user.set_password(user_data['password'])
        db.session.add(new_user)
    db.session.commit()
    print(f"-> Added {len(users_to_add)} users.")

    # 2. Add Trains
    print("Adding trains...")
    train_data = [
        {'name': 'Shatabdi Express', 'source': 'New Delhi', 'dest': 'Lucknow', 'time': '06:15', 'seats': 150},
        {'name': 'Rajdhani Express', 'source': 'Mumbai', 'dest': 'New Delhi', 'time': '17:00', 'seats': 200},
        {'name': 'Duronto Express', 'source': 'Kolkata', 'dest': 'Pune', 'time': '05:45', 'seats': 180},
        {'name': 'Tejas Express', 'source': 'Chennai', 'dest': 'Madurai', 'time': '06:00', 'seats': 120},
        {'name': 'Gatimaan Express', 'source': 'Delhi', 'dest': 'Agra', 'time': '08:10', 'seats': 100},
        {'name': 'Deccan Queen', 'source': 'Mumbai', 'dest': 'Pune', 'time': '17:10', 'seats': 160},
        {'name': 'Goa Express', 'source': 'Vasco da Gama', 'dest': 'Delhi', 'time': '15:00', 'seats': 190},
        {'name': 'Punjab Mail', 'source': 'Mumbai', 'dest': 'Firozpur', 'time': '19:35', 'seats': 260},
    ]
    for train_info in train_data:
        db.session.add(Train(train_name=train_info['name'], source=train_info['source'], destination=train_info['dest'], departure_time=train_info['time'], total_seats=train_info['seats']))
    db.session.commit()
    print(f"-> Added {len(train_data)} trains.")

    # 3. Add a large number of realistic bookings
    print("Adding realistic bookings...")
    
    # Make Shatabdi Express (ID 1, 150 seats) nearly full (5 seats left)
    for i in range(145):
        user_id = 2 if i % 2 == 0 else 3 # Alternate between Alice and Bob
        db.session.add(Booking(pnr_number=generate_pnr(), user_id=user_id, train_id=1, passenger_name=f'Passenger S{i+1}', passenger_age=30, seat_class='Sleeper'))

    # Make Rajdhani Express (ID 2, 200 seats) nearly full (2 seats left)
    for i in range(198):
        user_id = 3 if i % 2 == 0 else 2 # Alternate between Bob and Alice
        db.session.add(Booking(pnr_number=generate_pnr(), user_id=user_id, train_id=2, passenger_name=f'Passenger R{i+1}', passenger_age=40, seat_class='AC 2 Tier'))

    # Make Duronto Express (ID 3, 180 seats) COMPLETELY FULL
    for i in range(180):
        user_id = 2
        db.session.add(Booking(pnr_number=generate_pnr(), user_id=user_id, train_id=3, passenger_name=f'Passenger D{i+1}', passenger_age=25, seat_class='AC 3 Tier'))

    # Add a few bookings to Tejas Express (ID 4) to leave it mostly available
    db.session.add(Booking(pnr_number=generate_pnr(), user_id=2, train_id=4, passenger_name='Alice Smith', passenger_age=34, seat_class='AC 1st Class'))
    db.session.add(Booking(pnr_number=generate_pnr(), user_id=3, train_id=4, passenger_name='Bob Johnson', passenger_age=45, seat_class='AC 1st Class'))

    db.session.commit()
    print("-> Realistic bookings added successfully.")

    print("\n✅ Database has been successfully initialized and populated!")
