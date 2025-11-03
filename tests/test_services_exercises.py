from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
from app import services
import json


client = TestClient(app)


def test_create_and_get_exercise():
    payload = {
        "name": "Test Exercise",
        "side": "left",
        "category": "mobility",
        "target_sets": 3,
        "target_reps": 10,
        "target_hold_sec": 2,
        "schedule_dow": [1, 3, 5]
    }
    # create via API (router calls service)
    r = client.post("/exercises", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert data["name"] == payload["name"]
    ex_id = data["id"]

    # fetch via service directly
    db = SessionLocal()
    svc_out = services.exercises.get_exercise(db, ex_id)
    db.close()
    assert svc_out is not None
    assert svc_out.name == payload["name"]


def test_update_and_delete_exercise():
    # create exercise
    r = client.post("/exercises", json={
        "name": "To Update",
        "side": "both",
        "category": "strength",
        "schedule_dow": []
    })
    assert r.status_code == 200
    ex = r.json()
    ex_id = ex["id"]

    # update via service
    db = SessionLocal()
    from app.schemas import ExerciseUpdate
    upd = ExerciseUpdate(name="Updated Name")
    out = services.exercises.update_exercise(db, ex_id, upd)
    db.close()
    assert out is not None
    assert out.name == "Updated Name"

    # delete via API
    rdel = client.delete(f"/exercises/{ex_id}")
    assert rdel.status_code == 204
