import os
from app import app, db, Train, User, Booking, generate_pnr

# --- Configuration ---
DB_FILE = 'railway.db'

# --- Train Data ---
train_data = [
    {'name': 'Shatabdi Express', 'source': 'New Delhi', 'dest': 'Lucknow', 'time': '06:15', 'seats': 150},
    {'name': 'Rajdhani Express', 'source': 'Mumbai', 'dest': 'New Delhi', 'time': '17:00', 'seats': 200},
    {'name': 'Duronto Express', 'source': 'Kolkata', 'dest': 'Pune', 'time': '05:45', 'seats': 180},
    {'name': 'Tejas Express', 'source': 'Chennai', 'dest': 'Madurai', 'time': '06:00', 'seats': 120},
    {'name': 'Gatimaan Express', 'source': 'Delhi', 'dest': 'Agra', 'time': '08:10', 'seats': 100},
    {'name': 'Humsafar Express', 'source': 'Gorakhpur', 'dest': 'Anand Vihar', 'time': '20:00', 'seats': 250},
    {'name': 'Garib Rath', 'source': 'Patna', 'dest': 'New Delhi', 'time': '19:30', 'seats': 300},
    {'name': 'Sampark Kranti', 'source': 'Bengaluru', 'dest': 'Delhi', 'time': '22:00', 'seats': 220},
    {'name': 'Deccan Queen', 'source': 'Mumbai', 'dest': 'Pune', 'time': '17:10', 'seats': 160},
    {'name': 'Howrah Mail', 'source': 'Kolkata', 'dest': 'Mumbai', 'time': '23:45', 'seats': 280},
]

# --- User Data ---
# (username, password, role)
users_to_add = [
    ('admin', 'password123', 'admin'),
    ('alice', 'password', 'user'),
    ('bob', 'password', 'user')
]

# --- Main Execution ---
with app.app_context():
    # Delete old database if it exists
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)
        print("Old database removed.")

    # Create all tables
    db.create_all()
    print("Database tables created.")

    # 1. Add Users
    for username, password, role in users_to_add:
        new_user = User(username=username, role=role)
        new_user.set_password(password)
        db.session.add(new_user)
    db.session.commit()
    print(f"Added {len(users_to_add)} users.")

    # 2. Add Trains
    for train_info in train_data:
        train = Train(
            train_name=train_info['name'],
            source=train_info['source'],
            destination=train_info['dest'],
            departure_time=train_info['time'],
            total_seats=train_info['seats']
        )
        db.session.add(train)
    db.session.commit()
    print(f"Added {len(train_data)} trains.")

    # 3. Add Bookings linked to users
    # (user_id, train_id, passenger_name, passenger_age, seat_class)
    bookings_to_add = [
        (2, 1, 'Alice Smith', 34, 'Sleeper'),      # Alice books Shatabdi
        (2, 5, 'Alice Smith', 34, 'AC 2 Tier'),     # Alice books Gatimaan
        (3, 2, 'Bob Johnson', 45, 'AC 1st Class'),  # Bob books Rajdhani
        (3, 8, 'Bob Johnson', 45, 'Sleeper'),       # Bob books Sampark Kranti
    ]
    for user_id, train_id, name, age, s_class in bookings_to_add:
        booking = Booking(
            pnr_number=generate_pnr(),
            user_id=user_id,
            train_id=train_id,
            passenger_name=name,
            passenger_age=age,
            seat_class=s_class
        )
        db.session.add(booking)
    db.session.commit()
    print(f"Added {len(bookings_to_add)} dummy bookings linked to users.")

    print("\n✅ Database has been successfully initialized with users, trains, and bookings!")
