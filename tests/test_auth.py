import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.db import Base, get_db
from app.main import app


@pytest.fixture
def client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    testing_session = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
    )

    def override_get_db():
        db = testing_session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


def test_signup_then_signin_and_reject_wrong_password(client):
    email = "auth-check@example.com"
    password = "correct-horse-22"

    signup = client.post(
        "/register",
        json={"name": "Test User", "email": email, "password": password},
    )
    assert signup.status_code == 200
    assert signup.json()["email"] == email

    signin = client.post(
        "/login",
        json={"email": email, "password": password},
    )
    assert signin.status_code == 200
    assert signin.json()["email"] == email

    wrong_password = client.post(
        "/login",
        json={"email": email, "password": "incorrect-password"},
    )
    assert wrong_password.status_code == 401


def test_signup_rejects_duplicate_email(client):
    account = {"name": "Test User", "email": "duplicate@example.com", "password": "correct-horse-22"}

    assert client.post("/register", json=account).status_code == 200
    duplicate = client.post("/register", json=account)

    assert duplicate.status_code == 409
