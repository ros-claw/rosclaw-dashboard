"""Tests for the robots registry endpoints."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.main import app
from src.models.database import Base, Robot, get_db

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture(autouse=True)
def _clean_robots():
    """Give every test a fresh robots table."""
    db = TestingSessionLocal()
    db.query(Robot).delete()
    db.commit()
    db.close()
    yield


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_list_robots_empty():
    response = client.get("/api/robots")
    assert response.status_code == 200
    assert response.json() == []


def test_create_robot():
    robot = {
        "id": "test_robot_001",
        "name": "Test Robot",
        "model": "TestModel",
        "status": "offline",
    }
    response = client.post("/api/robots", json=robot)
    assert response.status_code == 201
    data = response.json()
    assert data["id"] == "test_robot_001"
    assert data["name"] == "Test Robot"


def test_get_robot():
    robot = {
        "id": "test_robot_002",
        "name": "Another Robot",
        "model": "Unitree Go2",
        "status": "online",
    }
    create = client.post("/api/robots", json=robot)
    assert create.status_code == 201

    response = client.get("/api/robots/test_robot_002")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "test_robot_002"


def test_get_robot_not_found():
    response = client.get("/api/robots/nonexistent")
    assert response.status_code == 404
