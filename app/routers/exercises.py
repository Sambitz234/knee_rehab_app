import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from .. import models, schemas
from ..services import exercises as exercise_service

router = APIRouter(prefix="/exercises", tags=["exercises"])


@router.post("", response_model=schemas.ExerciseOut)
def create_exercise(payload: schemas.ExerciseCreate, db: Session = Depends(get_db)):
    return exercise_service.create_exercise(db, payload)


@router.get("", response_model=list[schemas.ExerciseOut])
def list_exercises(db: Session = Depends(get_db)):
    return exercise_service.list_exercises(db)


@router.get("/{exercise_id}", response_model=schemas.ExerciseOut)
def get_exercise(exercise_id: int, db: Session = Depends(get_db)):
    out = exercise_service.get_exercise(db, exercise_id)
    if not out:
        raise HTTPException(status_code=404, detail="Exercise not found")
    return out


@router.put("/{exercise_id}", response_model=schemas.ExerciseOut)
def update_exercise(exercise_id: int, payload: schemas.ExerciseUpdate, db: Session = Depends(get_db)):
    out = exercise_service.update_exercise(db, exercise_id, payload)
    if not out:
        raise HTTPException(status_code=404, detail="Exercise not found")
    return out


@router.delete("/{exercise_id}", status_code=204)
def delete_exercise(exercise_id: int, db: Session = Depends(get_db)):
    ok = exercise_service.delete_exercise(db, exercise_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Exercise not found")
