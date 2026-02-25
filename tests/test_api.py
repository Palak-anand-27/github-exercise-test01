import copy
import pytest
from fastapi.testclient import TestClient

from src import app as app_module

client = TestClient(app_module.app)

@pytest.fixture(autouse=True)
def reset_activities():
    # snapshot original activities and restore after each test
    original = copy.deepcopy(app_module.activities)
    yield
    app_module.activities.clear()
    app_module.activities.update(original)


def test_get_activities():
    response = client.get("/activities")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    # ensure one of the known activities is present
    assert "Chess Club" in data


def test_signup_success():
    email = "newstudent@mergington.edu"
    activity = "Chess Club"
    assert email not in app_module.activities[activity]["participants"]

    response = client.post(f"/activities/{activity}/signup?email={email}")
    assert response.status_code == 200
    assert email in app_module.activities[activity]["participants"]
    assert "Signed up" in response.json().get("message", "")


def test_signup_duplicate_fails():
    email = "duplicate@mergington.edu"
    activity = "Chess Club"
    # first signup should succeed
    r1 = client.post(f"/activities/{activity}/signup?email={email}")
    assert r1.status_code == 200

    # second attempt should return 400
    r2 = client.post(f"/activities/{activity}/signup?email={email}")
    assert r2.status_code == 400
    assert r2.json()["detail"] == "Student already signed up"


def test_signup_nonexistent_activity():
    r = client.post("/activities/NotReal/signup?email=foo@bar.com")
    assert r.status_code == 404
    assert r.json()["detail"] == "Activity not found"


def test_signup_full_activity():
    # create a temporary activity that is already full
    name = "Tiny Club"
    app_module.activities[name] = {
        "description": "small",
        "schedule": "none",
        "max_participants": 1,
        "participants": ["someone@mergington.edu"],
    }
    r = client.post(f"/activities/{name}/signup?email=new@student.edu")
    assert r.status_code == 400
    assert r.json()["detail"] == "Activity is full"


def test_remove_participant_success():
    email = "removeme@mergington.edu"
    activity = "Programming Class"
    # ensure present
    if email not in app_module.activities[activity]["participants"]:
        app_module.activities[activity]["participants"].append(email)

    r = client.delete(f"/activities/{activity}/participants?email={email}")
    assert r.status_code == 200
    assert email not in app_module.activities[activity]["participants"]
    assert "Removed" in r.json().get("message", "")


def test_remove_nonexistent_participant():
    r = client.delete("/activities/Chess Club/participants?email=noone@x.com")
    assert r.status_code == 404
    assert r.json()["detail"] == "Participant not found"


def test_remove_from_nonexistent_activity():
    r = client.delete("/activities/Fake/participants?email=a@b.com")
    assert r.status_code == 404
    assert r.json()["detail"] == "Activity not found"
