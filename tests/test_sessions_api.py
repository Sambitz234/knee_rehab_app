from datetime import date


def create_exercise(client):
    payload = {
        "name": "Heel Raise",
        "side": "both",
        "category": "strength",
    }
    r = client.post("/exercises", json=payload)
    assert r.status_code == 200
    return r.json()["id"]


def test_sessions_crud_and_filters(client):
    ex_id = create_exercise(client)

    session_payload = {
        "exercise_id": ex_id,
        "date": date.today().isoformat(),
        "sets": 2,
        "reps": 15,
        "pain_0_10": 2
    }
    # Create session
    r = client.post("/sessions", json=session_payload)
    assert r.status_code == 200
    s = r.json()
    sid = s["id"]
    assert s["exercise_id"] == ex_id

    # Get session
    r = client.get(f"/sessions/{sid}")
    assert r.status_code == 200

    # List sessions (no filters)
    r = client.get("/sessions")
    assert r.status_code == 200
    items = r.json()
    assert any(i["id"] == sid for i in items)

    # List with exercise_id filter
    r = client.get(f"/sessions?exercise_id={ex_id}")
    assert r.status_code == 200
    items = r.json()
    assert any(i["id"] == sid for i in items)

    # Update session
    update_payload = {"pain_0_10": 5}
    r = client.put(f"/sessions/{sid}", json=update_payload)
    assert r.status_code == 200
    assert r.json()["pain_0_10"] == 5

    # Delete
    r = client.delete(f"/sessions/{sid}")
    assert r.status_code == 204

    # Ensure deleted
    r = client.get(f"/sessions/{sid}")
    assert r.status_code == 404


def test_create_session_invalid_exercise(client):
    # Creating a session with a missing exercise should return 400
    payload = {"exercise_id": 999999, "date": date.today().isoformat()}
    r = client.post("/sessions", json=payload)
    assert r.status_code == 400
