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

2. **Start the FastAPI server:**
	```bash
	uvicorn app.main:app --reload
	```
	- The app will be available at [http://127.0.0.1:8000](http://127.0.0.1:8000)

2. **Open the app in your browser:**
	- Go to [http://127.0.0.1:8000](http://127.0.0.1:8000)

### Containerization & CD (Day 10)

This repository includes a `Dockerfile` and `docker-compose.yml` to run the app and an optional local monitoring stack (Prometheus + Grafana). A sample GitHub Actions workflow (`.github/workflows/cd.yml`) is provided to build a Docker image, push to Azure Container Registry (ACR), and deploy to Azure Web App for Containers. The workflow triggers on pushes to `main`.

Required GitHub Secrets to enable the CD workflow:

- `ACR_LOGIN_SERVER` — e.g. `myregistry.azurecr.io`
- `ACR_USERNAME` — ACR username or service principal name
- `ACR_PASSWORD` — ACR password or service principal password
- `AZURE_WEBAPP_NAME` — The Azure Web App name to deploy the image to

Local verification steps:

- Build image locally: `docker build -t knee_rehab_app:local .`
- Run locally: `docker run -p 8000:8000 knee_rehab_app:local`
- Or bring up the full development stack: `docker compose up --build`
- Smoke endpoints:
  - `http://localhost:8000/health`
  - `http://localhost:8000/metrics`

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

## Running Tests & Checking Coverage

To run all backend unit tests and check code coverage:

1. **Activate your virtual environment:**
	```bash
	source .venv/bin/activate
	```

2. **Install dependencies (if not already done):**
	```bash
	pip install -r requirements.txt
	```

3. **Run all tests and show coverage report:**
	```bash
	PYTHONPATH=. pytest --cov=app --cov-report=term-missing tests/
	```

This will display a coverage summary in your terminal. For maximum grade, ensure coverage is above 90%.

---
## Troubleshooting
- If you change models, delete `rehab.db` to reset the database.
- For port conflicts, change the port in the `uvicorn` command (e.g., `--port 8080`).
- For Python errors, ensure your virtual environment is activated and dependencies are installed.

---

## License
MIT License (see LICENSE file)
# knee_rehab_app
