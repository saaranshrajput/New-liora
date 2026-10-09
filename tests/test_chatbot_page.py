import json
from io import BytesIO
from urllib.error import HTTPError

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_talk_to_liora_page_exists():
    response = client.get("/talk-to-liora")
    assert response.status_code == 200
    assert "Talk to Liora" in response.text


def test_home_route_supports_head_requests():
    response = client.head("/")

    assert response.status_code == 200
    assert response.content == b""


def test_chatbot_route_alias_exists():
    response = client.get("/chatbot")
    assert response.status_code == 200
    assert "Talk to Liora" in response.text


def test_chat_endpoint_uses_configured_provider(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-api-key")
    monkeypatch.setenv("OPENAI_MODEL", "test-model")
    monkeypatch.delenv("OPENAI_API_URL", raising=False)
    captured = {}

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *_):
            return False

        def read(self):
            return json.dumps({
                "choices": [{"message": {"content": "Solar answer."}}],
            }).encode()

    def fake_urlopen(provider_request, timeout):
        captured["authorization"] = provider_request.get_header("Authorization")
        captured["payload"] = json.loads(provider_request.data.decode())
        captured["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr("app.main.urlopen", fake_urlopen)

    response = client.post("/chat", json={"message": "How does solar work?"})

    assert response.status_code == 200
    assert response.json() == {"answer": "Solar answer."}
    assert captured["authorization"] == "Bearer test-api-key"
    assert captured["payload"]["model"] == "test-model"
    assert captured["timeout"] == 30


def test_chat_endpoint_explains_provider_endpoint_errors(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-api-key")

    def fake_urlopen(*_, **__):
        raise HTTPError(
            "https://api.example.com/v1/chat/completions",
            404,
            "Not Found",
            hdrs=None,
            fp=BytesIO(b""),
        )

    monkeypatch.setattr("app.main.urlopen", fake_urlopen)

    response = client.post("/chat", json={"message": "How does solar work?"})

    assert response.status_code == 502
    assert "configured model or API endpoint" in response.json()["detail"]
