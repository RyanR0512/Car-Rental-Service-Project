"""
Car Rental Service - Prototype Implementation
CIS453 Model Project

Core functionality implemented:
  - Customer registration & login (session-based auth)
  - Browse available cars by category
  - Book a car for a date range (with availability checking)
  - Simulated payment & confirmation
  - Admin: manage cars (add/edit/remove) and view/manage bookings

Tech stack: Python (Flask), SQLite (via sqlite3), Jinja2 templates.
See docs/System_Design_and_Architecture.docx for the full justification.
"""

from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from functools import wraps
import db as dbmod
import models as m

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-secret-key-change-in-production'


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def current_user():
    uid = session.get('user_id')
    if not uid:
        return None
    return m.get_user(uid)


def login_required(view_func):
    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if not current_user():
            flash("Please log in to continue.", "warning")
            return redirect(url_for('login'))
        return view_func(*args, **kwargs)
    return wrapped


def admin_required(view_func):
    @wraps(view_func)
    def wrapped(*args, **kwargs):
        u = current_user()
        if not u or u.role != 'admin':
            flash("Admin access required.", "danger")
            return redirect(url_for('index'))
        return view_func(*args, **kwargs)
    return wrapped


# ---------------------------------------------------------------------------
# Public / Customer routes
# ---------------------------------------------------------------------------

@app.route('/')
def index():
    category = request.args.get('category', '')
    cars = m.list_cars(category or None)
    categories = m.list_categories()
    return render_template('index.html', cars=cars, categories=categories, selected=category, user=current_user())


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name'].strip()
        email = request.form['email'].strip().lower()
        password = request.form['password']
        phone = request.form.get('phone', '').strip()
        license_no = request.form.get('license_no', '').strip()

        if not name or not email or not password:
            flash("Name, email, and password are required.", "danger")
            return redirect(url_for('register'))

        if m.get_user_by_email(email):
            flash("An account with that email already exists.", "danger")
            return redirect(url_for('register'))

        m.create_user(name, email, generate_password_hash(password), phone, license_no, role='customer')
        flash("Registration successful. Please log in.", "success")
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email'].strip().lower()
        password = request.form['password']
        user = m.get_user_by_email(email)
        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            flash(f"Welcome back, {user.name}!", "success")
            return redirect(url_for('admin_dashboard') if user.role == 'admin' else url_for('index'))
        flash("Invalid email or password.", "danger")
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for('index'))


@app.route('/car/<int:car_id>')
def car_detail(car_id):
    car = m.get_car(car_id)
    if not car:
        flash("Car not found.", "danger")
        return redirect(url_for('index'))
    return render_template('car_detail.html', car=car, user=current_user())


@app.route('/book/<int:car_id>', methods=['GET', 'POST'])
@login_required
def book_car(car_id):
    car = m.get_car(car_id)
    if not car:
        flash("Car not found.", "danger")
        return redirect(url_for('index'))

    if request.method == 'POST':
        try:
            start_date = datetime.strptime(request.form['start_date'], '%Y-%m-%d').date()
            end_date = datetime.strptime(request.form['end_date'], '%Y-%m-%d').date()
        except (ValueError, KeyError):
            flash("Please provide valid dates.", "danger")
            return redirect(url_for('book_car', car_id=car_id))

        if end_date < start_date:
            flash("End date must be after start date.", "danger")
            return redirect(url_for('book_car', car_id=car_id))

        if not m.car_is_available(car_id, start_date, end_date):
            flash("Sorry, this car is not available for the selected dates.", "danger")
            return redirect(url_for('book_car', car_id=car_id))

        days = (end_date - start_date).days or 1
        total_cost = round(days * car.daily_rate, 2)

        booking_id = m.create_booking(current_user().id, car.id, start_date, end_date, total_cost)
        return redirect(url_for('pay_booking', booking_id=booking_id))

    return render_template('book_car.html', car=car)


@app.route('/pay/<int:booking_id>', methods=['GET', 'POST'])
@login_required
def pay_booking(booking_id):
    booking = m.get_booking(booking_id)
    if not booking or booking.customer_id != current_user().id:
        flash("You do not have access to that booking.", "danger")
        return redirect(url_for('index'))

    if request.method == 'POST':
        # Simulated payment gateway call: any well-formed 16-digit card number "succeeds".
        card_number = request.form.get('card_number', '').replace(' ', '')
        if len(card_number) != 16 or not card_number.isdigit():
            flash("Enter a valid 16-digit card number (simulation).", "danger")
            return redirect(url_for('pay_booking', booking_id=booking_id))

        m.create_payment(booking.id, booking.total_cost, method='card', status='SUCCESS')
        m.update_booking_status(booking.id, 'CONFIRMED')
        flash("Payment successful! Your booking is confirmed.", "success")
        return redirect(url_for('booking_confirmation', booking_id=booking.id))

    return render_template('pay.html', booking=booking)


@app.route('/confirmation/<int:booking_id>')
@login_required
def booking_confirmation(booking_id):
    booking = m.get_booking(booking_id)
    if not booking or booking.customer_id != current_user().id:
        flash("You do not have access to that booking.", "danger")
        return redirect(url_for('index'))
    return render_template('confirmation.html', booking=booking)


@app.route('/my-bookings')
@login_required
def my_bookings():
    bookings = m.list_bookings_for_customer(current_user().id)
    return render_template('my_bookings.html', bookings=bookings)


# ---------------------------------------------------------------------------
# Admin routes
# ---------------------------------------------------------------------------

@app.route('/admin')
@admin_required
def admin_dashboard():
    cars = m.list_cars()
    bookings = m.list_all_bookings()
    return render_template('admin_dashboard.html', cars=cars, bookings=bookings)


@app.route('/admin/car/add', methods=['GET', 'POST'])
@admin_required
def admin_add_car():
    if request.method == 'POST':
        m.create_car(
            request.form['make'], request.form['model'],
            request.form['category'], float(request.form['daily_rate']), available=1
        )
        flash("Car added.", "success")
        return redirect(url_for('admin_dashboard'))
    return render_template('admin_car_form.html', car=None)


@app.route('/admin/car/<int:car_id>/edit', methods=['GET', 'POST'])
@admin_required
def admin_edit_car(car_id):
    car = m.get_car(car_id)
    if not car:
        flash("Car not found.", "danger")
        return redirect(url_for('admin_dashboard'))
    if request.method == 'POST':
        m.update_car(
            car_id, request.form['make'], request.form['model'],
            request.form['category'], float(request.form['daily_rate']),
            1 if 'available' in request.form else 0
        )
        flash("Car updated.", "success")
        return redirect(url_for('admin_dashboard'))
    return render_template('admin_car_form.html', car=car)


@app.route('/admin/car/<int:car_id>/delete', methods=['POST'])
@admin_required
def admin_delete_car(car_id):
    m.delete_car(car_id)
    flash("Car removed.", "info")
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/booking/<int:booking_id>/cancel', methods=['POST'])
@admin_required
def admin_cancel_booking(booking_id):
    m.update_booking_status(booking_id, 'CANCELLED')
    flash("Booking cancelled.", "info")
    return redirect(url_for('admin_dashboard'))


# ---------------------------------------------------------------------------
# DB bootstrap / seed data
# ---------------------------------------------------------------------------

def seed_data():
    if m.list_cars():
        return
    sample_cars = [
        ('Toyota', 'Corolla', 'Economy', 35.00),
        ('Honda', 'Civic', 'Economy', 38.00),
        ('Toyota', 'Camry', 'Sedan', 48.00),
        ('Nissan', 'Altima', 'Sedan', 45.00),
        ('Ford', 'Explorer', 'SUV', 68.00),
        ('Jeep', 'Grand Cherokee', 'SUV', 72.00),
        ('Chevrolet', 'Suburban', 'Luxury', 95.00),
    ]
    for make, model, category, rate in sample_cars:
        m.create_car(make, model, category, rate, available=1)

    if not m.get_user_by_email('admin@rentacar.com'):
        m.create_user('System Admin', 'admin@rentacar.com',
                       generate_password_hash('admin123'), '', '', role='admin')


dbmod.init_db()
seed_data()


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
