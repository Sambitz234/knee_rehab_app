# Knee Rehab Tracker App

## Features
- Add, edit, delete rehab exercises
- Log daily sessions with pain tracking
- View charts: exercise distribution, pain over time

## Prerequisites
- Python 3.8+
- (Recommended) Virtual environment: `venv` or `virtualenv`

## Setup
```bash
git clone https://github.com/Sambitz234/knee_rehab_app.git
cd knee_rehab_app
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
# (Optional) Delete rehab.db to reset database
```


## Running the Application
```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
# Open http://127.0.0.1:8000 in your browser
```

## Containerization & Local Dev
- Build image: `docker build -t knee_rehab_app:local .`
- Run container: `docker run --rm -p 8000:8000 knee_rehab_app:local`
- Full stack: `docker compose up --build`
- Monitoring: `docker-compose.monitoring.yml` (Prometheus + Grafana)
- Smoke endpoints:
	- [http://localhost:8000/health](http://localhost:8000/health)
	- [http://localhost:8000/metrics](http://localhost:8000/metrics)

---

## Run, Test & Deploy (concise)

Run (development)
```bash
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

## File Structure
```
Run (docker)
```bash
docker build -t knee_rehab_app:local .
docker run --rm -p 8000:8000 knee_rehab_app:local
```

Tests
```bash
# Activate virtualenv if used
source .venv/bin/activate
pip install -r requirements.txt
PYTHONPATH=. pytest --cov=app --cov-report=term-missing tests/
```

```bash
# on your workstation (after SSH public key installed on VM)
ssh -i ~/.ssh/cd-exercise-vm-key azureuser@<VM_IP> \
	"echo \"$GHCR_PAT\" | docker login ghcr.io -u <GH_USER> --password-stdin && \
	 docker pull ghcr.io/<OWNER>/<REPO>:latest && \
	 docker stop kneerehab_app || true && docker rm kneerehab_app || true && \
	 docker run -d --name kneerehab_app --restart unless-stopped -p 8000:8000 ghcr.io/<OWNER>/<REPO>:latest"
```

## Deployment (GHCR + VM via SSH)
- Prerequisites: VM with Docker, SSH key for `azureuser`
- Add private key to repo secrets as `VM_SSH_PRIVATE_KEY`, set `VM_HOST` and `VM_USERNAME` variables
- Manual deploy:
```bash
ssh -i ~/.ssh/cd-exercise-vm-key azureuser@<VM_IP> \
	"echo \"$GHCR_PAT\" | docker login ghcr.io -u <GH_USER> --password-stdin && \
	 docker pull ghcr.io/<OWNER>/<REPO>:latest && \
	 docker stop kneerehab_app || true && docker rm kneerehab_app || true && \
	 docker run -d --name kneerehab_app --restart unless-stopped -p 8000:8000 ghcr.io/<OWNER>/<REPO>:latest"
```
 - Use GitHub Actions workflow (`.github/workflows/cd.yml`) for automated build/push/deploy

Image: ghcr.io/Sambitz234/knee_rehab_app:latest

Application URL: http://108.143.92.226:8000

Endpoints

Health: http://108.143.92.226:8000/health
Metrics: http://108.143.92.226:8000/metrics

```

---

## File Structure

knee_rehab_app/
├── .github/
│   └── workflows/
│       └── cd.yml
│		└── ci.yml
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── models.py
│   ├── schemas.py
│   ├── database.py
│   ├── routers/
│   │   ├── exercises.py
│   │   ├── sessions.py
│   │   └── health.py
│   ├── services/
│   │   ├── exercises.py
│   │   └──  sessions.py
│   └── static/
│       ├── styles.css
│       ├── ui.html
│       └── ui.js
├── monitoring/
│   ├── grafana_dashboard.json
│   ├── prometheus.yml
│   └── README.md 			# to see monitoring configuration 
├── tests/
│   └── conftest.py
│   └── test_day3_edgecases.py
│   └── test_exercises_api.py
│   └── test_exercises.py
│   └── test_main.py
│   └── test_models.py
│   └── test_schemas.py
│   └── test_services_exercises.py
│   └── test_services_sessions.py
│   └── test_sessions_api.py
│   └── test_sessions.py
├── Dockerfile
├── docker-compose.yml
├──docker-compose.monitoring.yml
├── requirements.txt
├── rehab.db
├── README.md
└── LICENSE

---

## Troubleshooting
- If you change models, delete `rehab.db` to reset the database.
- For port conflicts, change the port in the `uvicorn` command (e.g., `--port 8080`).
- For Python errors, ensure your virtual environment is activated and dependencies are installed.

---

## License
MIT License (see LICENSE file)
# knee_rehab_app
