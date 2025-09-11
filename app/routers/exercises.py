import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from .. import models, schemas

router = APIRouter(prefix="/exercises", tags=["exercises"])

@router.post("", response_model=schemas.ExerciseOut)
def create_exercise(payload: schemas.ExerciseCreate, db: Session = Depends(get_db)):
    ex = models.Exercise(
        name=payload.name,
        side=payload.side,
        category=payload.category,
        target_sets=payload.target_sets,
        target_reps=payload.target_reps,
        target_hold_sec=payload.target_hold_sec,
        schedule_dow=json.dumps(payload.schedule_dow or [])
    )
    db.add(ex)
    db.commit()
    db.refresh(ex)
    # Convert back to list for response
    out = schemas.ExerciseOut(
        id=ex.id,
        name=ex.name,
        side=ex.side,
        category=ex.category,
        target_sets=ex.target_sets,
        target_reps=ex.target_reps,
        target_hold_sec=ex.target_hold_sec,
        schedule_dow=json.loads(ex.schedule_dow or "[]"),
    )
    return out

@router.get("", response_model=list[schemas.ExerciseOut])
def list_exercises(db: Session = Depends(get_db)):
    items = db.query(models.Exercise).order_by(models.Exercise.id).all()
    result = []
    for ex in items:
        result.append(
            schemas.ExerciseOut(
                id=ex.id,
                name=ex.name,
                side=ex.side,
                category=ex.category,
                target_sets=ex.target_sets,
                target_reps=ex.target_reps,
                target_hold_sec=ex.target_hold_sec,
                schedule_dow=json.loads(ex.schedule_dow or "[]"),
            )
        )
    return result

@router.get("/{exercise_id}", response_model=schemas.ExerciseOut)
def get_exercise(exercise_id: int, db: Session = Depends(get_db)):
    ex = db.query(models.Exercise).get(exercise_id)
    if not ex:
        raise HTTPException(status_code=404, detail="Exercise not found")
    return schemas.ExerciseOut(
        id=ex.id,
        name=ex.name,
        side=ex.side,
        category=ex.category,
        target_sets=ex.target_sets,
        target_reps=ex.target_reps,
        target_hold_sec=ex.target_hold_sec,
        schedule_dow=json.loads(ex.schedule_dow or "[]"),
    )

@router.put("/{exercise_id}", response_model=schemas.ExerciseOut)
def update_exercise(exercise_id: int, payload: schemas.ExerciseUpdate, db: Session = Depends(get_db)):
    ex = db.query(models.Exercise).get(exercise_id)
    if not ex:
        raise HTTPException(status_code=404, detail="Exercise not found")
    if payload.name is not None: ex.name = payload.name
    if payload.side is not None: ex.side = payload.side
    if payload.category is not None: ex.category = payload.category
    if payload.target_sets is not None: ex.target_sets = payload.target_sets
    if payload.target_reps is not None: ex.target_reps = payload.target_reps
    if payload.target_hold_sec is not None: ex.target_hold_sec = payload.target_hold_sec
    if payload.schedule_dow is not None: ex.schedule_dow = json.dumps(payload.schedule_dow)
    db.commit()
    db.refresh(ex)
    return schemas.ExerciseOut(
        id=ex.id,
        name=ex.name,
        side=ex.side,
        category=ex.category,
        target_sets=ex.target_sets,
        target_reps=ex.target_reps,
        target_hold_sec=ex.target_hold_sec,
        schedule_dow=json.loads(ex.schedule_dow or "[]"),
    )

@router.delete("/{exercise_id}", status_code=204)
def delete_exercise(exercise_id: int, db: Session = Depends(get_db)):
    ex = db.query(models.Exercise).get(exercise_id)
    if not ex:
        raise HTTPException(status_code=404, detail="Exercise not found")
    db.delete(ex)
    db.commit()
