# Tests for exercises endpoints
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_get_exercises():
    response = client.get("/exercises/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
