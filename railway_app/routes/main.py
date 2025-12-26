from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import Train, Booking
from ..utils import calculate_travel_time

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Renders the homepage."""
    return render_template('index.html')

@main_bp.route('/search', methods=['POST'])
def search():
    """Optimized search using Database-level filtering and Aggregation for seat counts."""
    source = request.form.get('source', '').strip()
    destination = request.form.get('destination', '').strip()
    time_filter = request.form.get('time_filter', 'all')

    query = {
        'source__iexact': source,
        'destination__iexact': destination
    }

    if time_filter == 'morning':
        query['departure_time__gte'] = '05:00'
        query['departure_time__lt'] = '12:00'
    elif time_filter == 'afternoon':
        query['departure_time__gte'] = '12:00'
        query['departure_time__lt'] = '17:00'
    elif time_filter == 'evening':
        query['departure_time__gte'] = '17:00'
        query['departure_time__lt'] = '24:00'

    trains = list(Train.objects(**query))
    
    if not trains:
        return render_template('results.html', trains=[], source=source, destination=destination)

    train_ids = [t.pk for t in trains]
    
    pipeline = [
        {"$match": {"train": {"$in": train_ids}, "status": "Confirmed"}},
        {"$group": {"_id": "$train", "count": {"$sum": 1}}}
    ]
    agg_results = list(Booking.objects.aggregate(*pipeline))
    confirmed_counts = {res['_id']: res['count'] for res in agg_results}

    for train in trains:
        count = confirmed_counts.get(train.pk, 0)
        train.available_seats = train.total_seats - count
        train.travel_time = calculate_travel_time(train.departure_time, train.arrival_time)
            
    return render_template('results.html', trains=trains, source=source, destination=destination)

@main_bp.route('/train_route/<train_id>')
def train_route(train_id):
    """Displays the specific route stops for a train."""
    train = Train.objects.get_or_404(id=train_id)
    return render_template('train_route.html', train=train)

@main_bp.route('/train_route_check')
def train_route_check():
    """Handles the route search from the navbar modal."""
    query = request.args.get('train_query')
    if not query: 
        return redirect(url_for('main.index'))
    train = Train.objects(train_name__iexact=query).first() or \
            Train.objects(train_name__icontains=query).first()
    
    if train:
        return redirect(url_for('main.train_route', train_id=train.id))
    else:
        flash(f'No train found matching "{query}".', 'danger')
        return redirect(url_for('main.index'))