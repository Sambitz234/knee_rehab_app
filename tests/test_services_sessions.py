from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
from app import services


client = TestClient(app)


def test_create_list_session():
    # create an exercise first
    er = client.post("/exercises", json={
        "name": "Session Exercise",
        "side": "right",
        "category": "mobility",
        "schedule_dow": []
    })
    assert er.status_code == 200
    ex = er.json()
    ex_id = ex["id"]

    # create session
    sr = client.post("/sessions", json={
        "exercise_id": ex_id,
        "date": "2025-01-01",
        "sets": 2,
        "reps": 8
    })
    assert sr.status_code == 200
    sdata = sr.json()
    sid = sdata["id"]

    # list via service
    db = SessionLocal()
    results = services.sessions.list_sessions(db)
    db.close()
    assert any(r.id == sid for r in results)


def test_update_delete_session():
    # create an exercise
    er = client.post("/exercises", json={
        "name": "Session Exercise 2",
        "side": "both",
        "category": "balance",
        "schedule_dow": []
    })
    ex_id = er.json()["id"]

    # create session
    sr = client.post("/sessions", json={
        "exercise_id": ex_id,
        "date": "2025-01-02",
    })
    sid = sr.json()["id"]

    # update via service
    db = SessionLocal()
    from app.schemas import SessionUpdate
    upd = SessionUpdate(sets=5)
    out = services.sessions.update_session(db, sid, upd)
    db.close()
    assert out is not None
    assert out.sets == 5

    # delete via API
    rdel = client.delete(f"/sessions/{sid}")
    assert rdel.status_code == 204
