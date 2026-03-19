import pytest
from eduforge.app import create_app


@pytest.fixture
def client():
    app = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:"})
    with app.test_client() as client:
        yield client


def test_index(client):
    response = client.get("/")
    assert response.status_code == 200
    data = response.get_json()
    assert data["name"] == "Eduforge"


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json()["status"] == "ok"


def test_create_and_list_courses(client):
    response = client.post("/courses/", json={"title": "Python 101", "description": "Learn Python"})
    assert response.status_code == 201

    response = client.get("/courses/")
    assert response.status_code == 200
    courses = response.get_json()
    assert len(courses) == 1
    assert courses[0]["title"] == "Python 101"
