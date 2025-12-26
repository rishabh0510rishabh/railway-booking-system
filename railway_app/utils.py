import time
import random
import string
import math
import qrcode
import base64
import tempfile
import os
from io import BytesIO
from datetime import datetime, timedelta
from flask import render_template, make_response, current_app
from flask_mail import Message
from fpdf import FPDF

# Import initialized mail instance from factory
from . import mail 

BASE_FARE = 1000
SEATS_PER_COACH = {'Sleeper': 72, 'AC 3 Tier': 64, 'AC 2 Tier': 46, 'AC 1st Class': 18}

def calculate_travel_time(departure_time_str, arrival_time_str):
    """Calculates duration between departure and arrival, handling overnight journeys."""
    try:
        departure_time = datetime.strptime(departure_time_str, '%H:%M')
        arrival_time = datetime.strptime(arrival_time_str, '%H:%M')
        if arrival_time < departure_time:
            arrival_time += timedelta(days=1)
        travel_duration = arrival_time - departure_time
        hours = travel_duration.seconds // 3600
        minutes = (travel_duration.seconds % 3600) // 60
        return f"{hours}h {minutes}m"
    except Exception:
        return "N/A"

def generate_pnr():
    return f"PNR{str(int(time.time()))[-6:]}{''.join(random.choices(string.ascii_uppercase + string.digits, k=4))}"

def calculate_fare(seat_class):
    multipliers = {'Sleeper': 1.0, 'AC 3 Tier': 1.5, 'AC 2 Tier': 2.0, 'AC 1st Class': 3.0}
    return BASE_FARE * multipliers.get(seat_class, 1.0)

def generate_seat_number(booking_count, total_seats, seat_class):
    seats_in_coach = SEATS_PER_COACH.get(seat_class, 72)
    coach_number = math.ceil(booking_count / seats_in_coach)
    seat_in_coach = ((booking_count - 1) % seats_in_coach) + 1
    
    berth_map = {
        'Sleeper': {1: 'SL', 2: 'LB', 3: 'MB', 4: 'UB', 5: 'SL', 6: 'SU'},
        'AC 3 Tier': {1: 'LB', 2: 'MB', 3: 'UB', 4: 'SL', 5: 'SU'},
        'AC 2 Tier': {1: 'LB', 2: 'UB', 3: 'SL', 4: 'SU'},
        'AC 1st Class': {1: 'LB', 2: 'UB'}
    }
    options = list(berth_map.get(seat_class, {1: 'S'}).values())
    berth = options[(seat_in_coach - 1) % len(options)]
    return f"{seat_class[0].upper()}{coach_number}-{seat_in_coach}-{berth}"

def generate_qr_code(data):
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(data)
    qr.make(fit=True)
    buf = BytesIO()
    qr.make_image(fill_color="black", back_color="white").save(buf)
    return base64.b64encode(buf.getvalue()).decode('ascii')

def send_ticket_email(user_email, ticket_data):
    """Sends ticket confirmation email using Flask-Mail with an explicit sender."""
    try:
        msg = Message(
            subject=f"Ticket Confirmation: #{ticket_data['pnr']}",
            sender=current_app.config['MAIL_USERNAME'], # Fix: Explicitly set sender
            recipients=[user_email]
        )
        msg.html = render_template('ticket_email.html', ticket=ticket_data)
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Mail Error: {e}")
        return False