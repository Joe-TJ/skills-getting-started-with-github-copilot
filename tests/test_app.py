import copy
import urllib.parse

import pytest
import src.app as app_module
from fastapi.testclient import TestClient
from src.app import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def restore_activities():
    """Reset global activities state before each test to prevent state bleed."""
    original = copy.deepcopy(app_module.activities)
    yield
    app_module.activities.clear()
    app_module.activities.update(original)


def _encode(name: str) -> str:
    return urllib.parse.quote(name, safe="")


# ── GET /activities ────────────────────────────────────────────────────────────

def test_get_activities_returns_200():
    response = client.get("/activities")
    assert response.status_code == 200


def test_get_activities_returns_non_empty_dict():
    data = client.get("/activities").json()
    assert isinstance(data, dict) and len(data) > 0


def test_get_activities_contains_chess_club():
    data = client.get("/activities").json()
    assert "Chess Club" in data


# ── POST /activities/{name}/signup ─────────────────────────────────────────────

def test_signup_new_participant_returns_200():
    response = client.post(
        f"/activities/{_encode('Chess Club')}/signup?email=new@mergington.edu"
    )
    assert response.status_code == 200


def test_signup_new_participant_message():
    email = "new@mergington.edu"
    response = client.post(
        f"/activities/{_encode('Chess Club')}/signup?email={email}"
    )
    assert response.json() == {"message": f"Signed up {email} for Chess Club"}


def test_signup_adds_participant():
    email = "new@mergington.edu"
    client.post(f"/activities/{_encode('Chess Club')}/signup?email={email}")
    data = client.get("/activities").json()
    assert email in data["Chess Club"]["participants"]


def test_signup_duplicate_returns_400():
    email = "michael@mergington.edu"  # already in Chess Club
    response = client.post(
        f"/activities/{_encode('Chess Club')}/signup?email={email}"
    )
    assert response.status_code == 400


def test_signup_nonexistent_activity_returns_404():
    response = client.post(
        f"/activities/{_encode('NonExistentActivity')}/signup?email=x@y.com"
    )
    assert response.status_code == 404


# ── DELETE /activities/{name}/participants ─────────────────────────────────────

def test_delete_participant_returns_200():
    email = "michael@mergington.edu"
    response = client.delete(
        f"/activities/{_encode('Chess Club')}/participants?email={email}"
    )
    assert response.status_code == 200


def test_delete_participant_message():
    email = "michael@mergington.edu"
    response = client.delete(
        f"/activities/{_encode('Chess Club')}/participants?email={email}"
    )
    assert response.json() == {"message": f"Unregistered {email} from Chess Club"}


def test_delete_participant_is_removed():
    email = "michael@mergington.edu"
    client.delete(f"/activities/{_encode('Chess Club')}/participants?email={email}")
    data = client.get("/activities").json()
    assert email not in data["Chess Club"]["participants"]


def test_delete_nonexistent_participant_returns_404():
    response = client.delete(
        f"/activities/{_encode('Chess Club')}/participants?email=nobody@mergington.edu"
    )
    assert response.status_code == 404


def test_delete_participant_from_nonexistent_activity_returns_404():
    response = client.delete(
        f"/activities/{_encode('NonExistentActivity')}/participants?email=x@y.com"
    )
    assert response.status_code == 404
