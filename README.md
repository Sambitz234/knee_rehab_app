# Knee Rehab Tracker App

## Overview
This is a modern, full-stack knee rehabilitation tracker application built with FastAPI (Python), SQLAlchemy (SQLite), and a responsive HTML/CSS/JS frontend. It allows users to log exercises, track rehab sessions, and visualize progress with charts.

---

## Features
- Add, edit, and delete rehab exercises
- Log daily exercise sessions with pain tracking
- View Exercise Category Distributiona and Pain-over-time charts
- Modern, responsive UI

---

## Prerequisites
- Python 3.8+
- (Recommended) Virtual environment tool: `venv` or `virtualenv`

---

## Setup Instructions

1. **Clone the repository:**
	```bash
	git clone https://github.com/Sambitz234/knee_rehab_app.git
	cd knee_rehab_app
	```

2. **Create and activate a virtual environment:**
	```bash
	python3 -m venv .venv
	source .venv/bin/activate
	```

3. **Install dependencies:**
	```bash
	pip install -r requirements.txt
	```

4. **(Optional) Initialize the database:**
	- The app will auto-create `rehab.db` on first run. To reset, delete `rehab.db`.

---

## Running the Application

1. **Start the FastAPI server:**
	```bash
	uvicorn app.main:app --reload
	```
	- The app will be available at [http://127.0.0.1:8000](http://127.0.0.1:8000)

2. **Open the app in your browser:**
	- Go to [http://127.0.0.1:8000](http://127.0.0.1:8000)

---

## File Structure

```
knee_rehab_app/
│ 
├── app/
│   ├── __init__.py
│   ├── main.py           # FastAPI entry point, HTML rendering
│   ├── models.py         # SQLAlchemy ORM models
│   ├── schemas.py        # Pydantic schemas
│   ├── database.py       # DB connection
│   │ 
│   ├── routers/
│   │   ├── exercises.py  # Exercise CRUD endpoints
│   │   ├── sessions.py   # Session CRUD endpoints
│   │ 
│   └── static/
│   │   ├── styles.css    # App styles
│   │   └── ui.js         # Frontend JS
│   │ 
├── requirements.txt
├── rehab.db              # SQLite DB 
└── README.md
```

---

## Troubleshooting
- If you change models, delete `rehab.db` to reset the database.
- For port conflicts, change the port in the `uvicorn` command (e.g., `--port 8080`).
- For Python errors, ensure your virtual environment is activated and dependencies are installed.

---

## License
MIT License (see LICENSE file)
# knee_rehab_app
