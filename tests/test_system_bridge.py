"""System Bridge (FastAPI) — RF01-RF03 y Documentación de API REST (Trimestre 4/5)."""
import pytest
from fastapi.testclient import TestClient

import backend_tools.system_bridge as sb


@pytest.fixture
def client(monkeypatch):
    received = []

    def fake_orch(text):
        received.append(text)
        return "respuesta lógica"

    monkeypatch.setattr(sb, "_orchestrator_callback", fake_orch)
    c = TestClient(sb.app)
    c.received = received
    return c


VALID = {"client_id": "AEGIS", "task": "Enciende mi Xbox", "session_context": {"ip": "192.168.1.55"}}


def test_health(client):
    r = client.get("/api/v1/health")
    assert r.status_code == 200
    assert "online" in r.json()["status"]


def test_execute_success(client):
    r = client.post("/api/v1/execute", json=VALID)
    assert r.status_code == 200
    assert r.json() == {"status": "success", "client_id": "AEGIS", "response": "respuesta lógica"}
    assert "[SISTEMA SATÉLITE: AEGIS]" in client.received[0]
    assert "Enciende mi Xbox" in client.received[0]


def test_execute_with_metadata(client):
    r = client.post("/api/v1/execute", json={**VALID, "metadata": {"priority": "normal"}})
    assert r.status_code == 200


@pytest.mark.parametrize("missing", ["client_id", "task", "session_context"])
def test_execute_missing_field_422(client, missing):
    body = {k: v for k, v in VALID.items() if k != missing}
    r = client.post("/api/v1/execute", json=body)
    assert r.status_code == 422
    assert r.json()["detail"][0]["loc"] == ["body", missing]


def test_execute_wrong_type_422(client):
    r = client.post("/api/v1/execute", json={**VALID, "session_context": "no-es-dict"})
    assert r.status_code == 422


def test_execute_without_orchestrator_500(monkeypatch):
    monkeypatch.setattr(sb, "_orchestrator_callback", None)
    r = TestClient(sb.app).post("/api/v1/execute", json=VALID)
    assert r.status_code == 500
    assert "no está inicializado" in r.json()["detail"]


def test_execute_orchestrator_error_500(monkeypatch):
    def boom(_): raise RuntimeError("Ollama caído")
    monkeypatch.setattr(sb, "_orchestrator_callback", boom)
    r = TestClient(sb.app).post("/api/v1/execute", json=VALID)
    assert r.status_code == 500 and "Ollama caído" in r.json()["detail"]


def test_openapi_matches_spec(client):
    spec = client.get("/openapi.json").json()
    assert spec["info"]["title"] == "Aletheia Core - System Bridge"
    assert spec["info"]["version"] == "1.0.0"
    assert "/api/v1/execute" in spec["paths"] and "/api/v1/health" in spec["paths"]
    schema = spec["components"]["schemas"]["SatelliteRequest"]
    assert set(schema["required"]) == {"client_id", "task", "session_context"}


def test_swagger_and_redoc_available(client):
    assert client.get("/docs").status_code == 200
    assert client.get("/redoc").status_code == 200


def test_register_orchestrator(monkeypatch):
    monkeypatch.setattr(sb, "_orchestrator_callback", None)
    f = lambda x: x
    sb.register_orchestrator(f)
    assert sb._orchestrator_callback is f


def test_session_context_is_delegated_and_released(monkeypatch):
    """Tokenless: la sesión está disponible durante la petición y se libera al terminar."""
    from backend_tools import universal_connector as uc
    seen = {}

    def orch(_):
        seen.update(uc._current_session_context)
        return "ok"

    monkeypatch.setattr(sb, "_orchestrator_callback", orch)
    TestClient(sb.app).post("/api/v1/execute", json=VALID)
    assert seen == VALID["session_context"]
    assert uc._current_session_context == {}


def test_session_released_even_on_error(monkeypatch):
    from backend_tools import universal_connector as uc

    def boom(_): raise RuntimeError("x")
    monkeypatch.setattr(sb, "_orchestrator_callback", boom)
    TestClient(sb.app).post("/api/v1/execute", json=VALID)
    assert uc._current_session_context == {}


def test_session_tokens_not_in_llm_prompt(client):
    client.post("/api/v1/execute", json={**VALID, "session_context": {"gmail_token": "SECRETO123"}})
    assert "SECRETO123" not in client.received[0]
    assert "gmail_token" in client.received[0]  # el LLM sabe qué sesión hay, no su valor


def test_execute_requires_auth_when_key_configured(client, monkeypatch):
    monkeypatch.setenv("BRIDGE_API_KEY", "clave-test")
    assert client.post("/api/v1/execute", json=VALID).status_code == 401
    assert client.post("/api/v1/execute", json=VALID,
                       headers={"X-API-Key": "otra"}).status_code == 401
    assert client.post("/api/v1/execute", json=VALID,
                       headers={"X-API-Key": "clave-test"}).status_code == 200
    # health sigue público para los health-checks
    assert client.get("/api/v1/health").status_code == 200


def test_bridge_host_defaults(monkeypatch):
    from api_gateway.auth import resolve_bridge_host
    assert resolve_bridge_host() == "127.0.0.1"
    monkeypatch.setenv("BRIDGE_API_KEY", "k")
    assert resolve_bridge_host() == "0.0.0.0"
    monkeypatch.setenv("BRIDGE_HOST", "192.168.1.10")
    assert resolve_bridge_host() == "192.168.1.10"
