from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_home_route_supports_head_requests():
    response = client.head("/")

    assert response.status_code == 200
    assert response.content == b""


def test_chatbot_routes_are_removed():
    for path in ("/talk-to-liora", "/chatbot", "/chat.js"):
        response = client.get(path)
        assert response.status_code == 404

    response = client.post("/chat", json={"message": "How does solar work?"})

    assert response.status_code == 404


def test_home_page_has_no_chat_widget():
    response = client.get("/")

    assert response.status_code == 200
    assert "chatbot" not in response.text.lower()
    assert 'src="/chat.js"' not in response.text
