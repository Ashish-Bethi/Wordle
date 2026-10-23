import json
from models import User, Game, Word
from extensions import db

def login(client, username="playerone", password="Testpass1$"):
    return client.post("/login", data={"username": username, "password": password}, follow_redirects=True)

def test_registration_validation(client):
    response = client.post("/register", data={"username": "abc", "password": "abc"})
    assert b"Username must be at least 5" in response.data

def test_login_and_player_game_start(client, app):
    login(client)
    response = client.post("/api/games", json={})
    assert response.status_code == 200
    data = response.get_json()
    assert data["game_id"] > 0
    assert "secret" not in data

def test_daily_limit_includes_abandoned_games(client, app):
    login(client)
    for _ in range(3):
        response = client.post("/api/games", json={})
        assert response.status_code == 200
    response = client.post("/api/games", json={})
    assert response.status_code == 429
    assert b"Daily limit reached" in response.data

def test_guess_validation_and_game_end(client, app):
    login(client)
    game_response = client.post("/api/games", json={})
    game_id = game_response.get_json()["game_id"]
    bad = client.post(f"/api/games/{game_id}/guesses", json={"word": "apple"})
    assert bad.status_code == 400
    assert b"uppercase" in bad.data

def test_admin_endpoints_require_admin(client):
    login(client)
    assert client.get("/admin/api/daily").status_code == 403

def test_admin_daily_report(client):
    login(client, "adminuser")
    response = client.get("/admin/api/daily?date=2026-10-22")
    assert response.status_code == 200
    data = response.get_json()
    assert "games_won" in data
    assert "exact_correct_submissions" in data
