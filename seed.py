from app import app, db, Train

# A list of 25 train entries
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

with app.app_context():
    # Optional: Delete all existing trains to start fresh
    Train.query.delete()

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
    print(f"Successfully added {len(train_data)} trains to the database.")