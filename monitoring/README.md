# Monitoring (Prometheus + Grafana) — Local setup

This folder contains a minimal local monitoring stack to scrape the app `/metrics` endpoint and visualize metrics in Grafana.

Files:
- `prometheus.yml` — Prometheus scrape config (scrapes `host.docker.internal:8000/metrics` by default).
- `grafana_dashboard.json` — A small dashboard with request rate, latency and error panels.
- `../docker-compose.monitoring.yml` — Compose file to run Prometheus and Grafana.

Quick start (app running locally on host at http://localhost:8000):

1. Start Prometheus + Grafana:
```bash
docker compose -f docker-compose.monitoring.yml up --build
```

2. Verify Prometheus is scraping the app:
- Open http://localhost:9090 → Status → Targets. Ensure `knee_rehab_app` target is UP (host.docker.internal:8000).

3. Open Grafana at http://localhost:3000 (admin/admin).
- Create a Prometheus data source (URL: `http://prometheus:9090` if using compose network, otherwise `http://localhost:9090`).
- Import `monitoring/grafana_dashboard.json` via Create → Import → Upload JSON.

Notes:
- On macOS Docker, `host.docker.internal` allows containers to reach services on the host. If you run the app in a container in the same compose network, change the `prometheus.yml` target to `app:8000` and add an `app` service to the compose file.
- This setup is intended for local development and review only. Do not expose `/metrics` publicly in production; protect it using network rules or authentication.

Basic verification:
```bash
curl -sS http://localhost:8000/health
curl -sS http://localhost:8000/metrics | head -n 40
```
