# tests/test_fastapi_app.py
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_create_user_endpoint():
    response = client.post("/users", json={
        "name": "Keita",
        "email": "keita@example.com"
    })
    assert response.status_code == 200
    assert "User Keita registered successfully" in response.json()["message"]