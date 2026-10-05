"""
Data access functions for Users, Cars, Bookings, and Payments.
Built on top of db.py (sqlite3). Rows are returned as sqlite3.Row objects,
which support both dict-style (row['field']) and attribute-style access
via the helper Row wrapper below, so templates can do car.make, car.daily_rate, etc.
"""

from db import get_conn, now


class R:
    """Thin wrapper so Jinja templates can use dot-access on sqlite3.Row results."""
    def __init__(self, row):
        self._row = row
    def __getattr__(self, item):
        try:
            return self._row[item]
        except (IndexError, KeyError):
            raise AttributeError(item)
    def __getitem__(self, item):
        return self._row[item]


# ---------------- Users ----------------

def create_user(name, email, password_hash, phone, license_no, role='customer'):
    conn = get_conn()
    cur = conn.execute(
        "INSERT INTO users (name, email, password_hash, phone, license_no, role, created_at) VALUES (?,?,?,?,?,?,?)",
        (name, email, password_hash, phone, license_no, role, now())
    )
    conn.commit()
    uid = cur.lastrowid
    conn.close()
    return uid

def get_user_by_email(email):
    conn = get_conn()
    row = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    conn.close()
    return R(row) if row else None

def get_user(user_id):
    conn = get_conn()
    row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return R(row) if row else None


# ---------------- Cars ----------------

def list_cars(category=None):
    conn = get_conn()
    if category:
        rows = conn.execute("SELECT * FROM cars WHERE category = ? ORDER BY category, daily_rate", (category,)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM cars ORDER BY category, daily_rate").fetchall()
    conn.close()
    return [R(r) for r in rows]

def list_categories():
    conn = get_conn()
    rows = conn.execute("SELECT DISTINCT category FROM cars ORDER BY category").fetchall()
    conn.close()
    return [r['category'] for r in rows]

def get_car(car_id):
    conn = get_conn()
    row = conn.execute("SELECT * FROM cars WHERE id = ?", (car_id,)).fetchone()
    conn.close()
    return R(row) if row else None

def create_car(make, model, category, daily_rate, available=1):
    conn = get_conn()
    cur = conn.execute(
        "INSERT INTO cars (make, model, category, daily_rate, available) VALUES (?,?,?,?,?)",
        (make, model, category, daily_rate, available)
    )
    conn.commit()
    cid = cur.lastrowid
    conn.close()
    return cid

def update_car(car_id, make, model, category, daily_rate, available):
    conn = get_conn()
    conn.execute(
        "UPDATE cars SET make=?, model=?, category=?, daily_rate=?, available=? WHERE id=?",
        (make, model, category, daily_rate, available, car_id)
    )
    conn.commit()
    conn.close()

def delete_car(car_id):
    conn = get_conn()
    conn.execute("DELETE FROM cars WHERE id = ?", (car_id,))
    conn.commit()
    conn.close()


# ---------------- Bookings ----------------

def car_is_available(car_id, start_date, end_date, exclude_booking_id=None):
    conn = get_conn()
    q = """SELECT id FROM bookings
           WHERE car_id = ? AND status = 'CONFIRMED'
             AND start_date <= ? AND end_date >= ?"""
    params = [car_id, str(end_date), str(start_date)]
    if exclude_booking_id:
        q += " AND id != ?"
        params.append(exclude_booking_id)
    row = conn.execute(q, params).fetchone()
    conn.close()
    return row is None

def create_booking(customer_id, car_id, start_date, end_date, total_cost, status='PENDING_PAYMENT'):
    conn = get_conn()
    cur = conn.execute(
        "INSERT INTO bookings (customer_id, car_id, start_date, end_date, status, total_cost, created_at) VALUES (?,?,?,?,?,?,?)",
        (customer_id, car_id, str(start_date), str(end_date), status, total_cost, now())
    )
    conn.commit()
    bid = cur.lastrowid
    conn.close()
    return bid

def get_booking(booking_id):
    conn = get_conn()
    row = conn.execute("""
        SELECT b.*, c.make as car_make, c.model as car_model, c.category as car_category,
               u.name as customer_name
        FROM bookings b
        JOIN cars c ON c.id = b.car_id
        JOIN users u ON u.id = b.customer_id
        WHERE b.id = ?""", (booking_id,)).fetchone()
    conn.close()
    if not row:
        return None
    b = R(row)
    b.car = _CarStub(row['car_make'], row['car_model'], row['car_category'])
    b.customer = _NameStub(row['customer_name'])
    return b

class _CarStub:
    def __init__(self, make, model, category):
        self.make, self.model, self.category = make, model, category

class _NameStub:
    def __init__(self, name):
        self.name = name

def list_bookings_for_customer(customer_id):
    conn = get_conn()
    rows = conn.execute("""
        SELECT b.*, c.make as car_make, c.model as car_model
        FROM bookings b JOIN cars c ON c.id = b.car_id
        WHERE b.customer_id = ? ORDER BY b.start_date DESC""", (customer_id,)).fetchall()
    conn.close()
    out = []
    for row in rows:
        b = R(row)
        b.car = _CarStub(row['car_make'], row['car_model'], None)
        out.append(b)
    return out

def list_all_bookings():
    conn = get_conn()
    rows = conn.execute("""
        SELECT b.*, c.make as car_make, c.model as car_model, u.name as customer_name
        FROM bookings b
        JOIN cars c ON c.id = b.car_id
        JOIN users u ON u.id = b.customer_id
        ORDER BY b.start_date DESC""").fetchall()
    conn.close()
    out = []
    for row in rows:
        b = R(row)
        b.car = _CarStub(row['car_make'], row['car_model'], None)
        b.customer = _NameStub(row['customer_name'])
        out.append(b)
    return out

def update_booking_status(booking_id, status):
    conn = get_conn()
    conn.execute("UPDATE bookings SET status = ? WHERE id = ?", (status, booking_id))
    conn.commit()
    conn.close()


# ---------------- Payments ----------------

def create_payment(booking_id, amount, method='card', status='SUCCESS'):
    conn = get_conn()
    cur = conn.execute(
        "INSERT INTO payments (booking_id, amount, method, status, created_at) VALUES (?,?,?,?,?)",
        (booking_id, amount, method, status, now())
    )
    conn.commit()
    pid = cur.lastrowid
    conn.close()
    return pid
