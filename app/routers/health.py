from fastapi import APIRouter, Depends, Response
from sqlalchemy import text
from sqlalchemy.orm import Session
from ..database import get_db
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

router = APIRouter(prefix="", tags=["health"])


@router.get("/health")
def health(db: Session = Depends(get_db)):
    """Return basic health status and check DB with a simple query."""
    try:
        # simple lightweight DB check
        db.execute(text("SELECT 1"))
        return {"status": "ok", "db": "ok"}
    except Exception:
        return {"status": "ok", "db": "error"}


@router.get("/metrics")
def metrics() -> Response:
    """Expose Prometheus metrics in text format."""
    data = generate_latest()
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)
