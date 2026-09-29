from fastapi.testclient import TestClient

from app.main import app


def test_health_and_warmup_are_ready_and_not_cached():
    with TestClient(app) as client:
        health = client.get("/health")
        assert health.status_code == 200
        assert health.json()["status"] == "ok"
        assert health.headers["cache-control"] == "no-store"

        warmup = client.get("/warmup")
        assert warmup.status_code == 200
        assert warmup.json()["status"] == "ready"
        assert warmup.json()["data_ready"] is True
        assert warmup.json()["record_count"] >= 100
        assert warmup.headers["cache-control"] == "no-store"


def test_warmup_allows_the_deployed_vercel_origin():
    with TestClient(app) as client:
        response = client.options(
            "/warmup",
            headers={
                "Origin": "https://m1-2-manbok2028s-projects.vercel.app",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert response.status_code == 200
        assert response.headers["access-control-allow-origin"] == "https://m1-2-manbok2028s-projects.vercel.app"


def test_data_crud_summary_chat_and_conversation_history():
    with TestClient(app) as client:
        initial = client.get("/api/data")
        assert initial.status_code == 200
        assert len(initial.json()) == 120

        created = client.post("/api/data", json={"date": "2025-05-01", "indicator": "base_rate", "value": 3.5, "unit": "%", "source": "API test", "memo": "API 통합 테스트"})
        assert created.status_code == 201
        record_id = created.json()["id"]

        changed = client.put(f"/api/data/{record_id}", json={"value": 4.0})
        assert changed.status_code == 200
        assert changed.json()["value"] == 4.0

        summary = client.get("/api/data/summary")
        assert summary.status_code == 200
        assert summary.json()["count"] == 121

        chat = client.post("/api/chat", json={"question": "최근 연체 위험 신호는 어때?"})
        assert chat.status_code == 200
        assert chat.json()["model"] == "local-summary-preview"
        assert chat.json()["tools_used"] == ["get_macro_summary"]

        conversations = client.get("/api/conversations")
        assert conversations.status_code == 200
        conversation_id = conversations.json()[0]["id"]
        loaded = client.get(f"/api/conversations/{conversation_id}")
        assert loaded.status_code == 200
        assert len(loaded.json()["messages"]) == 2

        deleted = client.delete(f"/api/data/{record_id}")
        assert deleted.status_code == 204
