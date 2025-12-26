from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models import Train, Booking
import math

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('is_admin'): return redirect(url_for('auth.login'))
    
    page = request.args.get('page', 1, type=int)
    bookings = Booking.objects().order_by('-id').skip((page - 1) * 10).limit(10)
    trains = Train.objects().order_by('train_name')
    
    return render_template('admin_dashboard.html', bookings=bookings, trains=trains, 
                           page=page, total_pages=math.ceil(Booking.objects.count() / 10))

@admin_bp.route('/admin/add_train', methods=['POST'])
def add_train():
    if not session.get('is_admin'): return redirect(url_for('auth.login'))
    Train(
        train_name=request.form['train_name'], source=request.form['source'],
        destination=request.form['destination'], departure_time=request.form['departure_time'],
        total_seats=int(request.form['total_seats'])
    ).save()
    flash('Train added.', 'success')
    return redirect(url_for('admin.admin_dashboard'))