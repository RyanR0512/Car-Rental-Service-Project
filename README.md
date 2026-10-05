CIS 453 Car Rental Service Project
# Car Rental Service — Prototyp

A Flask + SQLite web application implementing the core Car Rental Service
functionality: customer registration/login, browsing cars by category,
booking a car for a date range (with overlap/availability checking),
simulated payment and confirmation, and an admin console for managing
cars and bookings.

See `docs/` in the team's shared drive / submission folder for the
Requirements Document and System Design & Architecture document this
prototype implements.

## Tech Stack

- Python 3
- Flask (web framework)
- SQLite via Python's built-in `sqlite3` module (no ORM dependency)
- Jinja2 templates (bundled with Flask)
- Bootstrap 5 (via CDN) for styling

## Project Structure

```
app/
├── app.py                  # Routes / controllers
├── models.py                # Data-access functions (Users, Cars, Bookings, Payments)
├── db.py                     # SQLite connection + schema
├── templates/               # Jinja2 HTML templates
├── requirements.txt
├── .gitignore
└── README.md
```

## Setup & Run (local)

1. **Clone the repo** and `cd` into the `app/` folder.
2. **Create a virtual environment** (recommended):
   ```bash
   python3 -m venv venv
   source venv/bin/activate      # Windows: venv\Scripts\activate
   ```
3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
4. **Run the app:**
   ```bash
   python3 app.py
   ```
5. Open **http://127.0.0.1:5000** in your browser.

On first run, the app automatically creates `car_rental.db` (SQLite file,
git-ignored) and seeds it with sample cars and a demo admin account:

- **Admin login:** `admin@rentacar.com` / `admin123`

## Core Functionality Implemented (Week 3 scope)

- [x] Customer registration (`/register`)
- [x] Customer login / logout (`/login`, `/logout`)
- [x] View available cars, filterable by category (`/`)
- [x] View a single car's details (`/car/<id>`)
- [x] Book a car for a date range, with availability/overlap checking (`/book/<id>`)
- [x] Simulated payment & confirmation (`/pay/<id>`, `/confirmation/<id>`)
- [x] View my bookings (`/my-bookings`)
- [x] Admin: manage cars and bookings (`/admin`)

## Getting This Onto the Shared GitHub Repo

If you already have a shared repo created for the team, from inside this
`app/` folder:

```bash
git init
git remote add origin <your-repo-url>
git add .
git commit -m "Prototype: registration, car browsing, booking (Week 3)"
git branch -M main
git push -u origin main
```

If the repo already has history (e.g., a README from GitHub's repo
creation step), pull first to avoid conflicts:

```bash
git remote add origin <your-repo-url>
git pull origin main --allow-unrelated-histories
git add .
git commit -m "Prototype: registration, car browsing, booking (Week 3)"
git push -u origin main
```

## Testing Notes

Manual/automated smoke testing covered: registration, login, browsing by
category, booking a car, double-booking prevention (overlapping dates on
the same car are rejected), simulated payment, booking confirmation, and
admin car/booking management. See the Final Report for full test
documentation (Week 4).
