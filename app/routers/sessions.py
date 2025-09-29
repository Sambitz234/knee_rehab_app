
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from datetime import date
from ..database import get_db
from .. import models, schemas

router = APIRouter(prefix="/sessions", tags=["sessions"])

@router.get("/{id}", response_model=schemas.SessionOut)
def get_session(id: int, db: Session = Depends(get_db)):
    s = db.query(models.ExerciseSession).get(id)
    if not s:
        raise HTTPException(status_code=404, detail="Session not found")
    return s

@router.put("/{id}", response_model=schemas.SessionOut)
def update_session(id: int, payload: schemas.SessionUpdate, db: Session = Depends(get_db)):
    s = db.query(models.ExerciseSession).get(id)
    if not s:
        raise HTTPException(status_code=404, detail="Session not found")
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(s, field, value)
    db.commit()
    db.refresh(s)
    return s

@router.delete("/{id}", status_code=204)
def delete_session(id: int, db: Session = Depends(get_db)):
    s = db.query(models.ExerciseSession).get(id)
    if not s:
        raise HTTPException(status_code=404, detail="Session not found")
    db.delete(s)
    db.commit()

@router.post("", response_model=schemas.SessionOut)
def create_session(payload: schemas.SessionCreate, db: Session = Depends(get_db)):
    # Ensure exercise exists
    if not db.query(models.Exercise).get(payload.exercise_id):
        raise HTTPException(status_code=400, detail="Exercise does not exist")
    s = models.ExerciseSession(**payload.model_dump())
    db.add(s)
    db.commit()
    db.refresh(s)
    return s

@router.get("", response_model=list[schemas.SessionOut])
def list_sessions(
    db: Session = Depends(get_db),
    from_date: date = Query(default=None),
    to_date: date = Query(default=None),
    exercise_id: int | None = Query(default=None)
):
    q = db.query(models.ExerciseSession)
    if from_date:
        q = q.filter(models.ExerciseSession.date >= from_date)
    if to_date:
        q = q.filter(models.ExerciseSession.date <= to_date)
    if exercise_id:
        q = q.filter(models.ExerciseSession.exercise_id == exercise_id)
    return q.order_by(models.ExerciseSession.date.desc(), models.ExerciseSession.id.desc()).all()
