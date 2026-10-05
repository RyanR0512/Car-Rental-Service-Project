"""
Data Access Layer for the Car Rental Service prototype.
Uses Python's built-in sqlite3 module directly (no external ORM dependency
required), while keeping a small object-mapping style API so the rest of
the app can work with row objects rather than raw tuples.
"""

import sqlite3
import os
from datetime import datetime

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, 'car_rental.db')

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    phone TEXT,
    license_no TEXT,
    role TEXT DEFAULT 'customer',
    created_at TEXT
);

CREATE TABLE IF NOT EXISTS cars (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    make TEXT NOT NULL,
    model TEXT NOT NULL,
    category TEXT NOT NULL,
    daily_rate REAL NOT NULL,
    available INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS bookings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL REFERENCES users(id),
    car_id INTEGER NOT NULL REFERENCES cars(id),
    start_date TEXT NOT NULL,
    end_date TEXT NOT NULL,
    status TEXT DEFAULT 'PENDING_PAYMENT',
    total_cost REAL NOT NULL,
    created_at TEXT
);

CREATE TABLE IF NOT EXISTS payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    booking_id INTEGER NOT NULL REFERENCES bookings(id),
    amount REAL NOT NULL,
    method TEXT DEFAULT 'card',
    status TEXT DEFAULT 'SUCCESS',
    created_at TEXT
);
"""


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_conn()
    conn.executescript(SCHEMA)
    conn.commit()
    conn.close()


def now():
    return datetime.utcnow().isoformat(timespec='seconds')
