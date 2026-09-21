from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_talk_to_liora_page_exists():
    response = client.get("/talk-to-liora")
    assert response.status_code == 200
    assert "Talk to Liora" in response.text


def test_chatbot_route_alias_exists():
    response = client.get("/chatbot")
    assert response.status_code == 200
    assert "Talk to Liora" in response.text
