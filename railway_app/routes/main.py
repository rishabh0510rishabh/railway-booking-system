from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import Train, Booking
from ..utils import calculate_travel_time

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    return render_template('index.html')

@main_bp.route('/search', methods=['POST'])
def search():
    source = request.form['source']
    destination = request.form['destination']
    time_filter = request.form['time_filter']

    trains = Train.objects(source__iexact=source, destination__iexact=destination)
    
    filtered_trains = []
    for train in trains:
        t_time = train.departure_time
        include = False
        if time_filter == 'all': include = True
        elif time_filter == 'morning' and '05:00' <= t_time < '12:00': include = True
        elif time_filter == 'afternoon' and '12:00' <= t_time < '17:00': include = True
        elif time_filter == 'evening' and '17:00' <= t_time < '24:00': include = True
        
        if include:
            confirmed_bookings = Booking.objects(train=train, status='Confirmed').count()
            train.available_seats = train.total_seats - confirmed_bookings
            train.travel_time = calculate_travel_time(train.departure_time, train.arrival_time)
            filtered_trains.append(train)
            
    return render_template('results.html', trains=filtered_trains, source=source, destination=destination)

@main_bp.route('/train_route/<train_id>')
def train_route(train_id):
    train = Train.objects.get_or_404(id=train_id)
    return render_template('train_route.html', train=train)

@main_bp.route('/train_route_check')
def train_route_check():
    query = request.args.get('train_query')
    if not query: return redirect(url_for('main.index'))
    train = Train.objects(train_name__iexact=query).first() or \
            Train.objects(train_name__icontains=query).first()
    
    if train:
        return redirect(url_for('main.train_route', train_id=train.id))
    else:
        flash(f'No train found matching "{query}".', 'danger')
        return redirect(url_for('main.index'))