
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import date
from ..database import get_db
from .. import schemas
from ..services import sessions as session_service

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.get("/{id}", response_model=schemas.SessionOut)
def get_session(id: int, db: Session = Depends(get_db)):
    s = session_service.get_session(db, id)
    if not s:
        raise HTTPException(status_code=404, detail="Session not found")
    return s


@router.put("/{id}", response_model=schemas.SessionOut)
def update_session(
    id: int,
    payload: schemas.SessionUpdate,
    db: Session = Depends(get_db),
):
    s = session_service.update_session(db, id, payload)
    if not s:
        raise HTTPException(status_code=404, detail="Session not found")
    return s


@router.delete("/{id}", status_code=204)
def delete_session(id: int, db: Session = Depends(get_db)):
    ok = session_service.delete_session(db, id)
    if not ok:
        raise HTTPException(status_code=404, detail="Session not found")


@router.post("", response_model=schemas.SessionOut)
def create_session(payload: schemas.SessionCreate, db: Session = Depends(get_db)):
    s = session_service.create_session(db, payload)
    if not s:
        raise HTTPException(status_code=400, detail="Exercise does not exist")
    return s


@router.get(
    "",
    response_model=list[schemas.SessionOut],
)
def list_sessions(
    db: Session = Depends(get_db),
    from_date: date = Query(default=None),
    to_date: date = Query(default=None),
    exercise_id: int | None = Query(default=None),
):
    return session_service.list_sessions(db, from_date, to_date, exercise_id)
