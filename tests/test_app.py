import copy
from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

import src.app as app_module


@pytest.fixture
def client():
    return TestClient(app_module.app)


@pytest.fixture(autouse=True)
def restore_activities():
    original_activities = copy.deepcopy(app_module.activities)
    yield
    app_module.activities.clear()
    app_module.activities.update(original_activities)


def test_get_activities_returns_activity_data(client):
    # Arrange
    expected_activity = "Chess Club"

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert expected_activity in response.json()
    assert "participants" in response.json()[expected_activity]


def test_root_redirects_to_static_page(client):
    # Arrange
    root_path = "/"

    # Act
    response = client.get(root_path, follow_redirects=False)

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_signup_adds_participant(client):
    # Arrange
    activity_name = "Art Club"
    email = "student@example.com"
    signup_path = f"/activities/{quote(activity_name)}/signup"

    # Act
    response = client.post(signup_path, params={"email": email})

    # Assert
    assert response.status_code == 200
    assert response.json()["message"] == f"Signed up {email} for {activity_name}"
    assert email in app_module.activities[activity_name]["participants"]


def test_signup_returns_not_found_for_unknown_activity(client):
    # Arrange
    activity_name = "Unknown Club"
    signup_path = f"/activities/{quote(activity_name)}/signup"

    # Act
    response = client.post(signup_path, params={"email": "student@example.com"})

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_signup_rejects_duplicate_participant(client):
    # Arrange
    activity_name = "Art Club"
    email = "student@example.com"
    app_module.activities[activity_name]["participants"].append(email)
    signup_path = f"/activities/{quote(activity_name)}/signup"

    # Act
    response = client.post(signup_path, params={"email": email})

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"
    assert app_module.activities[activity_name]["participants"].count(email) == 1


def test_signup_requires_email(client):
    # Arrange
    activity_name = "Art Club"
    signup_path = f"/activities/{quote(activity_name)}/signup"

    # Act
    response = client.post(signup_path)

    # Assert
    assert response.status_code == 422


def test_cancel_signup_removes_participant(client):
    # Arrange
    activity_name = "Art Club"
    email = "student@example.com"
    app_module.activities[activity_name]["participants"].append(email)
    signup_path = f"/activities/{quote(activity_name)}/signup"

    # Act
    response = client.delete(signup_path, params={"email": email})

    # Assert
    assert response.status_code == 200
    assert response.json()["message"] == f"Canceled {email}'s signup for {activity_name}"
    assert email not in app_module.activities[activity_name]["participants"]


def test_cancel_signup_returns_not_found_for_unknown_activity(client):
    # Arrange
    activity_name = "Unknown Club"
    signup_path = f"/activities/{quote(activity_name)}/signup"

    # Act
    response = client.delete(signup_path, params={"email": "student@example.com"})

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_cancel_signup_returns_not_found_for_unregistered_participant(client):
    # Arrange
    activity_name = "Art Club"
    email = "student@example.com"
    signup_path = f"/activities/{quote(activity_name)}/signup"

    # Act
    response = client.delete(signup_path, params={"email": email})

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Student is not signed up for this activity"