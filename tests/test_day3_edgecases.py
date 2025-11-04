from datetime import date


def test_get_nonexistent_exercise(client):
    resp = client.get("/exercises/9999")
    assert resp.status_code == 404


def test_delete_nonexistent_session(client):
    resp = client.delete("/sessions/9999")
    assert resp.status_code == 404


def test_create_session_with_missing_exercise(client):
    payload = {
        "exercise_id": 9999,
        "date": date.today().isoformat(),
        "sets": 1,
    }
    resp = client.post("/sessions", json=payload)
    assert resp.status_code == 400
