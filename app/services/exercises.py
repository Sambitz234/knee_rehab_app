import json
from sqlalchemy.orm import Session
from .. import models, schemas


def create_exercise(db: Session, payload: schemas.ExerciseCreate) -> schemas.ExerciseOut:
    ex = models.Exercise(
        name=payload.name,
        side=payload.side,
        category=payload.category,
        target_sets=payload.target_sets,
        target_reps=payload.target_reps,
        target_hold_sec=payload.target_hold_sec,
        schedule_dow=json.dumps(payload.schedule_dow or []),
    )
    db.add(ex)
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


def list_exercises(db: Session) -> list[schemas.ExerciseOut]:
    items = db.query(models.Exercise).order_by(models.Exercise.id).all()
    result: list[schemas.ExerciseOut] = []
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


def get_exercise(db: Session, exercise_id: int) -> schemas.ExerciseOut | None:
    ex = db.query(models.Exercise).get(exercise_id)
    if not ex:
        return None
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


def update_exercise(db: Session, exercise_id: int, payload: schemas.ExerciseUpdate) -> schemas.ExerciseOut | None:
    ex = db.query(models.Exercise).get(exercise_id)
    if not ex:
        return None
    data = payload.model_dump(exclude_unset=True)
    # apply updates
    for field, value in data.items():
        if field == "schedule_dow":
            setattr(ex, field, json.dumps(value))
        else:
            setattr(ex, field, value)
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


def delete_exercise(db: Session, exercise_id: int) -> bool:
    ex = db.query(models.Exercise).get(exercise_id)
    if not ex:
        return False
    db.delete(ex)
    db.commit()
    return True
