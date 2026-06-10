from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from src.app import app, activities


client = TestClient(app)

INITIAL_ACTIVITIES = deepcopy(activities)


@pytest.fixture(autouse=True)
def reset_activities():
    # Arrange: restore the initial in-memory activities before each test
    activities.clear()
    activities.update(deepcopy(INITIAL_ACTIVITIES))
    yield


def test_root_redirect():
    # Act
    resp = client.get("/", follow_redirects=False)
    # Assert
    assert resp.status_code in (301, 302, 307, 308)
    assert resp.headers["location"] == "/static/index.html"


def test_get_activities():
    # Act
    resp = client.get("/activities")
    # Assert
    assert resp.status_code == 200
    data = resp.json()
    assert "Chess Club" in data
    assert isinstance(data["Chess Club"]["participants"], list)


def test_signup_success():
    # Arrange
    email = "new.student@mergington.edu"
    assert email not in activities["Drama Club"]["participants"]
    # Act
    resp = client.post("/activities/Drama%20Club/signup", params={"email": email})
    # Assert
    assert resp.status_code == 200
    assert email in activities["Drama Club"]["participants"]


def test_signup_duplicate_prevention():
    # Arrange
    existing = activities["Chess Club"]["participants"][0]
    # Act
    resp = client.post("/activities/Chess%20Club/signup", params={"email": existing})
    # Assert
    assert resp.status_code == 400
    assert resp.json()["detail"] == "Student already signed up for this activity"


def test_remove_participant_success():
    # Arrange
    email = activities["Chess Club"]["participants"][0]
    assert email in activities["Chess Club"]["participants"]
    # Act
    resp = client.delete("/activities/Chess%20Club/participants", params={"email": email})
    # Assert
    assert resp.status_code == 200
    assert email not in activities["Chess Club"]["participants"]


def test_remove_participant_not_found():
    # Act
    resp = client.delete("/activities/Chess%20Club/participants", params={"email": "not@here.com"})
    # Assert
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Participant not found in activity"


def test_remove_from_missing_activity():
    # Act
    resp = client.delete("/activities/NoSuch/participants", params={"email": "a@b.com"})
    # Assert
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Activity not found"
