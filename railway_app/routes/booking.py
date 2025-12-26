import os
import tempfile
import base64
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, make_response
from models import Train, Booking, User, Passenger
from ..utils import (generate_pnr, calculate_fare, generate_seat_number, 
                     send_ticket_email, generate_qr_code)
from datetime import datetime
from fpdf import FPDF

booking_bp = Blueprint('booking', __name__)

@booking_bp.route('/book/<train_id>')
def book(train_id):
    if not session.get('logged_in'):
        flash('You must be logged in to book a ticket.', 'danger')
        return redirect(url_for('auth.login'))
    
    train_to_book = Train.objects.get_or_404(id=train_id)
    user = User.objects.get(id=session['user_id'])
    return render_template('booking_form.html', train=train_to_book, saved_passengers=user.saved_passengers)

@booking_bp.route('/submit_booking', methods=['POST'])
def submit_booking():
    if not session.get('logged_in'):
        return redirect(url_for('auth.login'))

    user = User.objects.get(id=session['user_id'])
    train_id = request.form.get('train_id')
    train_to_book = Train.objects.get(id=train_id)
    
    passenger_name = request.form.get('passenger_name')
    passenger_age = int(request.form.get('passenger_age', 0))
    seat_class = request.form.get('seat_class', 'Sleeper')
    requested_berth = request.form.get('berth_preference')
    save_passenger_flag = request.form.get('save_passenger')
    email = request.form.get('email_address') or user.email

    # Calculate Status (Confirmed/RAC/Waitlisted)
    confirmed_bookings = Booking.objects(train=train_to_book, status='Confirmed').count()
    rac_bookings = Booking.objects(train=train_to_book, status='RAC').count()
    waitlisted_bookings = Booking.objects(train=train_to_book, status='Waitlisted').count()

    status = 'Confirmed'
    seat_number = None
    rac_limit = train_to_book.total_seats + (train_to_book.total_seats // 10) 
    
    if confirmed_bookings < train_to_book.total_seats:
        status = 'Confirmed'
        seat_number = generate_seat_number(confirmed_bookings + 1, train_to_book.total_seats, seat_class)
    elif confirmed_bookings + rac_bookings < rac_limit:
        status = 'RAC'
        seat_number = f"RAC-{rac_bookings + 1}"
    else:
        status = 'Waitlisted'
        seat_number = f"WL-{waitlisted_bookings + 1}"

    new_booking = Booking(
        pnr_number=generate_pnr(),
        train=train_to_book,
        user=user,
        passenger_name=passenger_name,
        passenger_age=passenger_age,
        seat_class=seat_class,
        berth_preference=requested_berth,
        status=status,
        seat_number=seat_number,
        fare=calculate_fare(seat_class)
    ).save()

    if save_passenger_flag:
        exists = any(p.name == passenger_name and p.age == passenger_age for p in user.saved_passengers)
        if not exists:
            user.saved_passengers.append(Passenger(name=passenger_name, age=passenger_age, berth_preference=requested_berth))
            user.save()
    
    # Send Email
    ticket_details = {
        'pnr': new_booking.pnr_number, 'passenger_name': passenger_name, 'passenger_age': passenger_age,
        'train_name': train_to_book.train_name, 'route': f"{train_to_book.source} ➝ {train_to_book.destination}",
        'departure_time': train_to_book.departure_time, 'seat_number': seat_number,
        'seat_class': seat_class, 'status': status, 'fare': f"₹{new_booking.fare:.2f}",
        'booking_date': datetime.now().strftime("%d %b %Y")
    }
    send_ticket_email(email, ticket_details)

    return redirect(url_for('booking.booking_confirmation', pnr=new_booking.pnr_number))

@booking_bp.route('/confirmation/<pnr>')
def booking_confirmation(pnr):
    booking = Booking.objects.get_or_404(pnr_number=pnr)
    return render_template('booking_confirmation.html', booking=booking)

@booking_bp.route('/pnr_status')
def pnr_status():
    pnr = request.args.get('pnr', '').strip()
    if not pnr: return redirect(url_for('main.index'))
    booking = Booking.objects(pnr_number=pnr).first()
    if booking:
        return render_template('ticket_details.html', booking=booking)
    flash('Invalid PNR Number.', 'danger')
    return redirect(url_for('main.index'))

@booking_bp.route('/my_bookings')
def my_bookings():
    if not session.get('logged_in'): return redirect(url_for('auth.login'))
    user = User.objects.get(id=session['user_id'])
    page = request.args.get('page', 1, type=int)
    per_page = 10
    bookings = Booking.objects(user=user).order_by('-id').skip((page - 1) * per_page).limit(per_page)
    total_pages = (Booking.objects(user=user).count() + per_page - 1) // per_page
    return render_template('my_bookings.html', bookings=bookings, page=page, total_pages=total_pages)

@booking_bp.route('/download_ticket/<pnr>')
def download_ticket(pnr):
    booking = Booking.objects.get_or_404(pnr_number=pnr)
    
    # Restored Original PDF Settings from app.py
    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.add_page()
    
    BLUE_HEADER = (13, 71, 161)
    TEXT_COLOR = (50, 50, 50)
    GREEN_PRICE = (46, 125, 50)
    
    # Blue Header Rectangle
    pdf.set_fill_color(*BLUE_HEADER)
    pdf.rect(10, 10, 190, 30, 'F')
    
    # Header Text
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", "B", 20)
    pdf.set_xy(20, 20)
    pdf.cell(0, 0, "RAILWAY E-TICKET")
    
    # PNR Section
    pdf.set_font("Arial", "", 12)
    pdf.set_xy(140, 18)
    pdf.cell(50, 5, "PNR NUMBER", 0, 1, 'R')
    pdf.set_font("Arial", "B", 16)
    pdf.set_xy(140, 24)
    pdf.cell(50, 5, booking.pnr_number, 0, 1, 'R')
    
    # Main Content Border
    pdf.set_draw_color(200, 200, 200)
    pdf.rect(10, 40, 190, 110)
    
    pdf.set_text_color(*TEXT_COLOR)
    y_start = 55
    x_left = 20
    
    # Passenger Details Section
    pdf.set_font("Arial", "B", 12)
    pdf.set_xy(x_left, y_start)
    pdf.set_text_color(*BLUE_HEADER)
    pdf.cell(0, 10, "PASSENGER DETAILS")
    pdf.line(x_left, y_start+8, 90, y_start+8)
    
    pdf.set_text_color(*TEXT_COLOR)
    details_left = [
        ("Name", booking.passenger_name),
        ("Age", f"{booking.passenger_age} Years"),
        ("Berth", booking.berth_preference or 'No Preference'),
        ("Status", booking.status)
    ]
    
    y_pos = y_start + 15
    for label, value in details_left:
        pdf.set_font("Arial", "B", 10)
        pdf.set_xy(x_left, y_pos)
        pdf.cell(30, 6, f"{label}:")
        pdf.set_font("Arial", "", 10)
        pdf.cell(40, 6, str(value))
        y_pos += 8

    # Journey Details Section
    x_right = 110
    pdf.set_font("Arial", "B", 12)
    pdf.set_xy(x_right, y_start)
    pdf.set_text_color(*BLUE_HEADER)
    pdf.cell(0, 10, "JOURNEY DETAILS")
    pdf.line(x_right, y_start+8, 180, y_start+8)
    
    pdf.set_text_color(*TEXT_COLOR)
    details_right = [
        ("Train", booking.train.train_name),
        ("Route", f"{booking.train.source} -> {booking.train.destination}"),
        ("Class", booking.seat_class),
        ("Seat No", booking.seat_number or 'Allocated later')
    ]
    
    y_pos = y_start + 15
    for label, value in details_right:
        pdf.set_font("Arial", "B", 10)
        pdf.set_xy(x_right, y_pos)
        pdf.cell(30, 6, f"{label}:")
        pdf.set_font("Arial", "", 10)
        pdf.cell(40, 6, str(value))
        y_pos += 8
        
    # QR Code handling (using original temp file logic)
    qr_data = f"PNR:{booking.pnr_number}|{booking.passenger_name}|{booking.train.train_name}"
    qr_base64 = generate_qr_code(qr_data)
    qr_bytes = base64.b64decode(qr_base64)
    
    with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as temp_qr:
        temp_qr.write(qr_bytes)
        temp_qr_path = temp_qr.name
    
    pdf.image(temp_qr_path, x=85, y=105, w=35)
    os.remove(temp_qr_path)
    
    # Fare Footer
    pdf.set_fill_color(240, 240, 240)
    pdf.rect(11, 138, 188, 11, 'F')
    pdf.set_xy(10, 140)
    pdf.set_font("Arial", "B", 12)
    pdf.set_text_color(*GREEN_PRICE)
    # FIX: Changed ₹ to Rs. to avoid encoding error
    pdf.cell(190, 8, f"TOTAL FARE: Rs. {booking.fare:.2f}", 0, 0, 'C')

    # Output response
    pdf_output = pdf.output(dest='S').encode('latin-1')
    response = make_response(pdf_output)
    response.headers.set('Content-Disposition', 'attachment', filename=f'ticket_{pnr}.pdf')
    response.headers.set('Content-Type', 'application/pdf')
    return response
@booking_bp.route('/print_ticket/<pnr>')
def print_ticket(pnr):
    booking = Booking.objects.get_or_404(pnr_number=pnr)
    qr_data = f"PNR: {booking.pnr_number}\nName: {booking.passenger_name}\nTrain: {booking.train.train_name}"
    qr_base64 = generate_qr_code(qr_data)
    return render_template('print_ticket.html', booking=booking, qr_code=qr_base64)

@booking_bp.route('/book_return/<pnr>')
def book_return(pnr):
    booking = Booking.objects.get_or_404(pnr_number=pnr)
    return_train = Train.objects(source__iexact=booking.train.destination, destination__iexact=booking.train.source).first()
    if return_train:
        return redirect(url_for('booking.book', train_id=str(return_train.id)))
    flash('No return train found.', 'danger')
    return redirect(url_for('booking.booking_confirmation', pnr=pnr))