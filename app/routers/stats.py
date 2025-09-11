from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from ..database import get_db
from ..services.stats import weekly_adherence, progress_series
from ..schemas import WeeklyAdherenceOut, ProgressSeriesOut

router = APIRouter(prefix="/stats", tags=["stats"])

@router.get("/weekly", response_model=WeeklyAdherenceOut)
def get_weekly_adherence(db: Session = Depends(get_db)):
    return weekly_adherence(db)

@router.get("/progress", response_model=ProgressSeriesOut)
def get_progress(metric: str = Query(..., pattern="^(rom_deg|pain_0_10)$"), days: int = 30, db: Session = Depends(get_db)):
    if days <= 0 or days > 120:
        raise HTTPException(status_code=400, detail="days must be 1..120")
    return progress_series(db, metric=metric, days=days)
