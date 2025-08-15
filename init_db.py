import os
from app import app, db, Train, Booking, generate_pnr

# --- Configuration ---
DB_FILE = 'railway.db'

# --- Train Data ---
# This list remains the same
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
    {'name': 'Punjab Mail', 'source': 'Mumbai', 'dest': 'Firozpur', 'time': '19:35', 'seats': 260},
    {'name': 'Flying Ranee', 'source': 'Mumbai', 'dest': 'Surat', 'time': '17:55', 'seats': 140},
    {'name': 'Coromandel Express', 'source': 'Shalimar', 'dest': 'Chennai', 'time': '15:20', 'seats': 210},
    {'name': 'Goa Express', 'source': 'Vasco da Gama', 'dest': 'Delhi', 'time': '15:00', 'seats': 190},
    {'name': 'Kerala Express', 'source': 'New Delhi', 'dest': 'Trivandrum', 'time': '11:25', 'seats': 230},
    {'name': 'Karnataka Express', 'source': 'Bengaluru', 'dest': 'New Delhi', 'time': '19:20', 'seats': 215},
    {'name': 'Tamil Nadu Express', 'source': 'Chennai', 'dest': 'New Delhi', 'time': '22:00', 'seats': 240},
    {'name': 'Andhra Pradesh Express', 'source': 'Visakhapatnam', 'dest': 'New Delhi', 'time': '06:25', 'seats': 205},
    {'name': 'Grand Trunk Express', 'source': 'New Delhi', 'dest': 'Chennai', 'time': '16:10', 'seats': 255},
    {'name': 'Mangala Lakshadweep', 'source': 'Delhi', 'dest': 'Ernakulam', 'time': '05:40', 'seats': 225},
    {'name': 'Vaishali Express', 'source': 'New Delhi', 'dest': 'Saharsa', 'time': '20:40', 'seats': 300},
    {'name': 'Poorva Express', 'source': 'Howrah', 'dest': 'New Delhi', 'time': '08:15', 'seats': 210},
    {'name': 'Kashi Vishwanath', 'source': 'New Delhi', 'dest': 'Varanasi', 'time': '11:35', 'seats': 280},
    {'name': 'Prayagraj Express', 'source': 'New Delhi', 'dest': 'Prayagraj', 'time': '22:10', 'seats': 260},
    {'name': 'Lucknow Mail', 'source': 'New Delhi', 'dest': 'Lucknow', 'time': '22:05', 'seats': 270}
]

# --- Main Execution ---
with app.app_context():
    # Check if the database file exists and delete it for a clean start
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)
        print("Old database removed.")

    # Create tables
    db.create_all()
    print("Database tables created.")

    # Add trains
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

    # --- Add Realistic Bookings ---
    print("Adding realistic bookings...")

    # 1. Add some varied, individual bookings
    initial_bookings = [
        (1, 'Amit Kumar', 34, 'Sleeper'), (1, 'Priya Sharma', 28, 'AC 2 Tier'),
        (2, 'Rajesh Singh', 45, 'AC 1st Class'), (3, 'Sunita Devi', 52, 'Sleeper'),
        (8, 'Deepak Gupta', 41, 'Sleeper'), (10, 'Neha Reddy', 25, 'AC 2 Tier'),
        (15, 'Suresh Patil', 60, 'Sleeper'), (20, 'Manoj Tiwari', 38, 'Sleeper'),
    ]
    for train_id, name, age, s_class in initial_bookings:
        db.session.add(Booking(pnr_number=generate_pnr(), train_id=train_id, passenger_name=name, passenger_age=age, seat_class=s_class))
    
    # 2. Make Gatimaan Express (ID 5, 100 seats) COMPLETELY FULL
    for i in range(100):
        db.session.add(Booking(pnr_number=generate_pnr(), train_id=5, passenger_name=f'Passenger G{i+1}', passenger_age=30, seat_class='Sleeper'))

    # 3. Make Deccan Queen (ID 9, 160 seats) NEARLY FULL (5 seats left)
    for i in range(155):
        db.session.add(Booking(pnr_number=generate_pnr(), train_id=9, passenger_name=f'Passenger D{i+1}', passenger_age=35, seat_class='AC 3 Tier'))
        
    # 4. Make Tejas Express (ID 4, 120 seats) NEARLY FULL (4 seats left)
    for i in range(116):
        db.session.add(Booking(pnr_number=generate_pnr(), train_id=4, passenger_name=f'Passenger T{i+1}', passenger_age=40, seat_class='AC 2 Tier'))

    db.session.commit()
    print("Realistic bookings added successfully.")
    print("\n✅ Database has been successfully initialized and populated!")
