

def test_exercises_crud_flow(client):
    # Create
    payload = {
        "name": "Quad Set",
        "side": "left",
        "category": "strength",
        "target_sets": 3,
        "target_reps": 10,
        "schedule_dow": [1, 3, 5]
    }
    r = client.post("/exercises", json=payload)
    assert r.status_code == 200
    body = r.json()
    assert body["name"] == payload["name"]
    ex_id = body["id"]

    # List
    r = client.get("/exercises")
    assert r.status_code == 200
    items = r.json()
    assert any(i["id"] == ex_id for i in items)

    # Get by id
    r = client.get(f"/exercises/{ex_id}")
    assert r.status_code == 200
    body = r.json()
    assert body["id"] == ex_id

    # Update
    update_payload = {"name": "Quad Set - Updated", "target_reps": 12}
    r = client.put(f"/exercises/{ex_id}", json=update_payload)
    assert r.status_code == 200
    body = r.json()
    assert body["name"] == "Quad Set - Updated"
    assert body["target_reps"] == 12

    # Delete
    r = client.delete(f"/exercises/{ex_id}")
    assert r.status_code == 204

    # Ensure not found afterwards
    r = client.get(f"/exercises/{ex_id}")
    assert r.status_code == 404


def test_create_invalid_exercise(client):
    # name too short
    payload = {"name": "A", "side": "left", "category": "strength"}
    r = client.post("/exercises", json=payload)
    assert r.status_code == 422
