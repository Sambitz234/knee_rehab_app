from fastapi import FastAPI, Request
from .database import Base, engine
from .routers import exercises, sessions, health
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
import time
from prometheus_client import Counter, Histogram

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Knee Rehab Habit Tracker", version="0.1.0")

app.include_router(exercises.router)
app.include_router(sessions.router)
app.include_router(health.router)

# Prometheus metrics
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "path", "status"],
)
REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency",
    ["method", "path"],
)
ERROR_COUNT = Counter(
    "http_request_errors_total",
    "Total HTTP request errors",
    ["method", "path", "status"],
)


@app.get("/")
@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/ui")


app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start = time.perf_counter()
    method = request.method
    path = request.url.path
    try:
        response = await call_next(request)
        status = str(response.status_code)
        return response
    except Exception:
        # increment error counter and re-raise
        ERROR_COUNT.labels(method=method, path=path, status="500").inc()
        raise
    finally:
        # Observe latency and increment counters
        elapsed = time.perf_counter() - start
        # If response is available in finally, get status; otherwise default to 500
        try:
            status = str(response.status_code)
        except Exception:
            status = "500"
        REQUEST_COUNT.labels(method=method, path=path, status=status).inc()
        REQUEST_LATENCY.labels(method=method, path=path).observe(elapsed)


@app.get("/ui", response_class=HTMLResponse)
def ui_page():
    return FileResponse("app/static/ui.html", media_type="text/html")

