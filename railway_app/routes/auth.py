from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from models import User, Booking, Passenger

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/signup', methods=['POST'])
def signup():
    username = request.form['username']
    password = request.form['password']
    if User.objects(username=username).first():
        flash('Username already exists.', 'danger')
        return redirect(url_for('main.index'))
    
    new_user = User(username=username, email=request.form.get('email'), 
                    phone_number=request.form.get('phone'))
    new_user.password_hash = generate_password_hash(password)
    new_user.save()
    flash('Account created successfully!', 'success')
    return redirect(url_for('main.index'))

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.objects(username=request.form['username']).first()
        if user and check_password_hash(user.password_hash, request.form['password']):
            session['logged_in'] = True
            session['user_id'] = str(user.id)
            session['username'] = user.username
            session['is_admin'] = (user.role == 'admin')
            flash(f'Welcome back, {user.username}!', 'success')
        else:
            flash('Invalid credentials.', 'danger')
        return redirect(url_for('main.index'))
    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('Logged out.', 'info')
    return redirect(url_for('main.index'))

@auth_bp.route('/profile', methods=['GET', 'POST'])
def profile():
    if not session.get('logged_in'): 
        return redirect(url_for('auth.login'))
    
    user = User.objects.get(id=session['user_id'])

    if request.method == 'POST':
        action = request.args.get('action')
        if action == 'add_passenger':
            new_p = Passenger(
                name=request.form['passenger_name'], 
                age=int(request.form['passenger_age']), 
                berth_preference=request.form.get('berth_preference')
            )
            user.saved_passengers.append(new_p)
            user.save()
        elif action == 'delete_passenger':
            pass_id = request.args.get('passenger_id')
            user.saved_passengers = [p for p in user.saved_passengers if str(p.uid) != pass_id]
            user.save()
        else:
            user.username = request.form['username']
            user.email = request.form['email']
            user.phone_number = request.form['phone']
            user.save()
            session['username'] = user.username
            
        return redirect(url_for('auth.profile'))
    
    recent_bookings = Booking.objects(user=user).order_by('-id').limit(5)
    return render_template('profile.html', user=user, recent_bookings=recent_bookings)

@auth_bp.route('/change_password', methods=['POST'])
def change_password():
    user = User.objects.get(id=session['user_id'])
    if not check_password_hash(user.password_hash, request.form['current_password']):
        flash('Incorrect current password.', 'danger')
    elif request.form['new_password'] != request.form['confirm_password']:
        flash('Passwords do not match.', 'danger')
    else:
        user.password_hash = generate_password_hash(request.form['new_password'])
        user.save()
        flash('Password updated.', 'success')
    return redirect(url_for('auth.profile'))

@auth_bp.route('/profile/delete', methods=['POST'])
def delete_account():
    user = User.objects.get(id=session['user_id'])
    Booking.objects(user=user).delete()
    user.delete()
    session.clear()
    flash('Account deleted.', 'info')
    return redirect(url_for('main.index'))