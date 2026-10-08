import json
import re
import base64
from io import BytesIO
from time import time
from unittest.mock import Mock
from urllib.error import HTTPError

import pytest
from fastapi.testclient import TestClient
from cryptography.hazmat.primitives.asymmetric import rsa
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from jose import jwt

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


def test_password_reset_email_link_updates_password(client, monkeypatch):
    email = "password-reset@example.com"
    old_password = "old-password-123"
    new_password = "new-password-456"
    assert client.post(
        "/register",
        json={"name": "Reset User", "email": email, "password": old_password},
    ).status_code == 200

    monkeypatch.setenv("RESEND_API_KEY", "test-resend-key")
    monkeypatch.setenv("PUBLIC_URL", "https://liora.example.com")
    sent_emails = []

    class EmailResponse:
        def __enter__(self):
            return self

        def __exit__(self, *_):
            return False

    def fake_urlopen(request, timeout):
        assert timeout == 15
        sent_emails.append(json.loads(request.data.decode("utf-8")))
        return EmailResponse()

    monkeypatch.setattr("app.main.urlopen", fake_urlopen)
    reset_request = client.post("/forgot-password", json={"email": email})
    assert reset_request.status_code == 200
    assert reset_request.json()["message"] == (
        "If an account exists for this email, a reset link will arrive shortly. "
        "Check your spam folder too."
    )

    reset_url = re.search(
        r"https?://\S+reset_token=([A-Za-z0-9_-]+)",
        sent_emails[0]["text"],
    ).group(0)
    token = reset_url.split("reset_token=", 1)[1]

    reset_response = client.post(
        "/reset-password",
        json={"token": token, "password": new_password},
    )
    assert reset_response.status_code == 200
    assert client.post(
        "/login",
        json={"email": email, "password": new_password},
    ).status_code == 200
    assert client.post(
        "/login",
        json={"email": email, "password": old_password},
    ).status_code == 401
    assert client.post(
        "/reset-password",
        json={"token": token, "password": "another-password"},
    ).status_code == 400


def test_solar_recommendation_page_has_no_chat_widget(client):
    response = client.get("/solar-recommendation")

    assert response.status_code == 200
    assert "Chat with Liora" not in response.text
    assert 'src="/chat.js"' not in response.text


def test_google_signin_verifies_token_and_creates_account(client, monkeypatch):
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_numbers = private_key.public_key().public_numbers()

    def encode_integer(value):
        raw = value.to_bytes((value.bit_length() + 7) // 8, "big")
        return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")

    jwks = {
        "keys": [
            {
                "kty": "RSA",
                "use": "sig",
                "kid": "test-key",
                "alg": "RS256",
                "n": encode_integer(public_numbers.n),
                "e": encode_integer(public_numbers.e),
            }
        ]
    }
    nonce = "secure-test-nonce-that-is-long-enough"
    identity_token = jwt.encode(
        {
            "iss": "https://accounts.google.com",
            "aud": "test-google-client",
            "sub": "google-user-123",
            "email": "google-user@example.com",
            "email_verified": True,
            "name": "Google User",
            "nonce": nonce,
            "exp": int(time()) + 60,
        },
        private_key,
        algorithm="RS256",
        headers={"kid": "test-key"},
    )

    class JwksResponse:
        def __enter__(self):
            return self

        def __exit__(self, *_):
            return False

        def read(self):
            return json.dumps(jwks).encode("utf-8")

    monkeypatch.setenv("GOOGLE_CLIENT_ID", "test-google-client")
    monkeypatch.setattr("app.main.urlopen", Mock(return_value=JwksResponse()))
    response = client.post(
        "/auth/google",
        json={"identity_token": identity_token, "nonce": nonce},
    )

    assert response.status_code == 200
    assert response.json()["email"] == "google-user@example.com"
    assert response.json()["name"] == "Google User"


def test_oauth_is_disabled_without_provider_configuration(client, monkeypatch):
    monkeypatch.delenv("GOOGLE_CLIENT_ID", raising=False)

    response = client.post(
        "/auth/google",
        json={
            "identity_token": "a" * 40,
            "nonce": "secure-test-nonce-that-is-long-enough",
        },
    )

    assert response.status_code == 503


def test_auth_page_keeps_social_options_visible_without_provider_keys(client):
    response = client.get("/login-page")

    assert response.status_code == 200
    assert "Continue with Apple" in response.text
    assert "Continue with Google" in response.text


def test_auth_config_reports_unconfigured_integrations(client, monkeypatch):
    monkeypatch.delenv("GOOGLE_CLIENT_ID", raising=False)
    monkeypatch.delenv("APPLE_CLIENT_ID", raising=False)
    monkeypatch.delenv("RESEND_API_KEY", raising=False)
    monkeypatch.delenv("PUBLIC_URL", raising=False)
    monkeypatch.delenv("RENDER_EXTERNAL_URL", raising=False)

    response = client.get("/auth/config")

    assert response.status_code == 200
    assert response.json() == {
        "google_client_id": None,
        "apple_client_id": None,
        "password_reset_enabled": False,
    }


def test_forgot_password_omits_internal_environment_variable_name(client, monkeypatch):
    monkeypatch.delenv("RESEND_API_KEY", raising=False)

    response = client.post(
        "/forgot-password",
        json={"email": "auth-check@example.com"},
    )

    assert response.status_code == 503
    assert "RESEND_API_KEY" not in response.json()["detail"]


def test_forgot_password_does_not_claim_delivery_for_unknown_email(client, monkeypatch):
    monkeypatch.setenv("RESEND_API_KEY", "test-resend-key")
    monkeypatch.setenv("PUBLIC_URL", "https://liora.example.com")
    send_email = Mock(side_effect=AssertionError("No account means no reset email."))
    monkeypatch.setattr("app.main.urlopen", send_email)

    response = client.post(
        "/forgot-password",
        json={"email": "not-registered@example.com"},
    )

    assert response.status_code == 200
    assert response.json()["message"] == (
        "If an account exists for this email, a reset link will arrive shortly. "
        "Check your spam folder too."
    )
    send_email.assert_not_called()


def test_contact_form_sends_to_configured_inbox(client, monkeypatch):
    monkeypatch.setenv("RESEND_API_KEY", "test-resend-key")
    monkeypatch.setenv("CONTACT_FROM_EMAIL", "Liora <hello@example.com>")
    monkeypatch.setenv("CONTACT_TO_EMAIL", "inbox@example.com")
    provider_response = Mock()
    provider_response.__enter__ = Mock(return_value=provider_response)
    provider_response.__exit__ = Mock(return_value=False)
    send_email = Mock(return_value=provider_response)
    monkeypatch.setattr("app.main.urlopen", send_email)

    response = client.post(
        "/contact",
        json={
            "name": "Solar Customer",
            "email": "customer@example.com",
            "message": "Please contact me about a solar plan.",
        },
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Your message was accepted by the email service."
    sent_payload = json.loads(send_email.call_args.args[0].data.decode("utf-8"))
    assert sent_payload["from"] == "Liora <hello@example.com>"
    assert sent_payload["to"] == ["inbox@example.com"]
    assert sent_payload["reply_to"] == "customer@example.com"


def test_contact_form_reports_resend_sender_rejection(client, monkeypatch):
    monkeypatch.setenv("RESEND_API_KEY", "test-resend-key")
    monkeypatch.setenv("CONTACT_FROM_EMAIL", "Liora <unverified@example.com>")
    rejection = HTTPError(
        "https://api.resend.com/emails",
        403,
        "Forbidden",
        {},
        BytesIO(b'{"message":"sender not verified"}'),
    )
    monkeypatch.setattr("app.main.urlopen", Mock(side_effect=rejection))

    response = client.post(
        "/contact",
        json={
            "name": "Solar Customer",
            "email": "customer@example.com",
            "message": "Please contact me.",
        },
    )

    assert response.status_code == 502
    assert response.json()["detail"] == "Resend rejected the message: sender not verified"
