# Monitoring — Prometheus & Grafana

This folder contains local monitoring configuration used for development and
smoke-testing: a Prometheus config (`prometheus.yml`) and a Grafana dashboard
JSON (`grafana_dashboard.json`). The repository also includes a Compose file
(`docker-compose.monitoring.yml`) which can run Prometheus, Grafana and an
in-compose `app` service so the stack is self-contained.

This README explains how to run the stack, verify it, import the dashboard into
Grafana, and troubleshoot common issues on macOS.

## Files

- `docker-compose.monitoring.yml` — Compose file that runs `app`, `prometheus`,
	and `grafana` in one network.
- `prometheus.yml` — Prometheus scrape config (scrapes `app:8000` by default).
- `grafana_dashboard.json` — Example dashboard you can import into Grafana.

## Quick start (self-contained)

From the project root run:

```bash
# build the app image used by the compose file
docker compose -f docker-compose.monitoring.yml build app

# bring the whole monitoring stack up
docker compose -f docker-compose.monitoring.yml up --build
```

After the stack starts:

- Prometheus UI: http://localhost:9090/targets — look for a target `app:8000`.
- Grafana UI: http://localhost:3000 (default credentials: `admin` / `admin`).
- Application health: http://localhost:8000/health
- Metrics endpoint: http://localhost:8000/metrics

If you prefer to run the app on the host (outside Docker), change
`monitoring/prometheus.yml` to target `host.docker.internal:8000` and ensure
the host process binds to `0.0.0.0` (uvicorn `--host 0.0.0.0`).

## Grafana — add Prometheus datasource and import dashboard

1. Open Grafana at http://localhost:3000 and sign in (`admin` / `admin`).
2. Add a Prometheus datasource:
	 - Settings → Data Sources → Add data source → Prometheus
	 - URL: `http://prometheus:9090` (when using the compose stack)
	 - Save & Test.
3. Import the dashboard:
	 - Dashboards → Import → Upload `monitoring/grafana_dashboard.json`
	 - Select the Prometheus datasource you created and Import.


```bash
# make sure Grafana is up; this uses the admin credentials
curl -s -u admin:admin -H "Content-Type: application/json" \
	-X POST http://localhost:3000/api/dashboards/db \
	-d @monitoring/grafana_dashboard.json
```

Note: the API import may require the dashboard JSON to be wrapped in the
Grafana `dashboard` envelope; importing via the UI is the most straightforward
option during development.

## Prometheus config

By default `monitoring/prometheus.yml` is configured to scrape the in-compose
`app:8000` target. If you change the networking model, update the `targets`
section accordingly.

## Build & run the app image manually

```bash
docker build -t knee_rehab_app:local .
docker run --rm -p 8000:8000 knee_rehab_app:local
```

## Common troubleshooting

- Docker credential helper issues on macOS:
	- If `docker compose` fails pulling images with a `credential helper` error,
		sign in to Docker Desktop (recommended) or remove `"credsStore"` from
		`~/.docker/config.json` after backing it up. See the repository notes for
		more details.
- Prometheus shows `connection refused` for `host.docker.internal:8000`:
	- Ensure the app process binds to `0.0.0.0` (uvicorn `--host 0.0.0.0`), or run
		the app in-compose so Prometheus can access it at `app:8000`.
- Build fails due to missing Python packages:
	- Ensure `requirements.txt` contains `fastapi`, `uvicorn`, `prometheus-client`
		and other runtime dependencies, then rebuild the image.

## Useful commands

```bash
# view compose logs
docker compose -f docker-compose.monitoring.yml logs --tail 200 --follow

# check Prometheus targets
curl -sS http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | {job: .labels.job, target: .discoveredLabels.__address__, health: .health}'

# fetch app metrics directly
curl -sS http://localhost:8000/metrics | head -n 40
```

