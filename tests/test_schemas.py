# Tests for schemas (example: ExerciseCreate)
import pytest
from app.schemas import ExerciseCreate

def test_exercise_create_schema():
    ex = ExerciseCreate(name="Squat", side="left", category="strength", target_sets=3, target_reps=10, target_hold_sec=5, schedule_dow=[1,3,5])
    assert ex.name == "Squat"
    assert ex.side == "left"
    assert ex.category == "strength"
    assert ex.target_sets == 3
    assert ex.target_reps == 10
    assert ex.target_hold_sec == 5
    assert ex.schedule_dow == [1,3,5]
