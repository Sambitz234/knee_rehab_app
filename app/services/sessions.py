from sqlalchemy.orm import Session
from .. import models, schemas


def get_session(db: Session, id: int) -> schemas.SessionOut | None:
    s = db.get(models.ExerciseSession, id)
    if not s:
        return None
    return s


def update_session(db: Session, id: int, payload: schemas.SessionUpdate) -> schemas.SessionOut | None:
    s = db.get(models.ExerciseSession, id)
    if not s:
        return None
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(s, field, value)
    db.commit()
    db.refresh(s)
    return s


def delete_session(db: Session, id: int) -> bool:
    s = db.get(models.ExerciseSession, id)
    if not s:
        return False
    db.delete(s)
    db.commit()
    return True


def create_session(db: Session, payload: schemas.SessionCreate) -> schemas.SessionOut:
    # Ensure exercise exists
    if not db.get(models.Exercise, payload.exercise_id):
        return None
    s = models.ExerciseSession(**payload.model_dump())
    db.add(s)
    db.commit()
    db.refresh(s)
    return s


def list_sessions(db: Session, from_date=None, to_date=None, exercise_id=None):
    q = db.query(models.ExerciseSession)
    if from_date:
        q = q.filter(models.ExerciseSession.date >= from_date)
    if to_date:
        q = q.filter(models.ExerciseSession.date <= to_date)
    if exercise_id:
        q = q.filter(models.ExerciseSession.exercise_id == exercise_id)
    return q.order_by(models.ExerciseSession.date.desc(), models.ExerciseSession.id.desc()).all()
