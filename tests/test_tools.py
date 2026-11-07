"""ToolsManager, system_tools y Universal Connector."""
import json

import pytest

import backend_tools.system_tools as st
from backend_tools.tools_manager import ToolsManager
from backend_tools import universal_connector as uc


@pytest.fixture
def tm():
    return ToolsManager()


def test_schema_has_all_tools(tm):
    names = {t["function"]["name"] for t in tm.get_tools_schema()}
    assert names == set(tm.available_tools) == {
        "search_web", "read_file", "write_file", "execute_universal_action"}


def test_schema_required_params_are_declared(tm):
    for t in tm.get_tools_schema():
        params = t["function"]["parameters"]
        for req in params["required"]:
            assert req in params["properties"]


def test_unknown_tool(tm):
    assert "no existe" in tm.execute_tool("rm_everything", "{}")


def test_invalid_json_args(tm):
    assert "ERROR AL EJECUTAR" in tm.execute_tool("read_file", "{no json")


def test_write_then_read(tm, tmp_path):
    p = tmp_path / "sub" / "a.txt"
    out = tm.execute_tool("write_file", json.dumps({"path": str(p), "content": "hola ñ"}))
    assert "exitosamente" in out
    assert tm.execute_tool("read_file", json.dumps({"path": str(p)})) == "hola ñ"


def test_read_missing_file(tmp_path):
    assert "Error al leer" in st.read_file(str(tmp_path / "nope.txt"))


def test_search_web_is_mocked(monkeypatch):
    class FakeDDGS:
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def text(self, q, max_results=3):
            return [{"title": "T", "href": "http://x", "body": "B"}]
    monkeypatch.setattr(st, "DDGS", FakeDDGS)
    out = st.search_web("noticias")
    assert "Título: T" in out and "http://x" in out


def test_search_web_no_results(monkeypatch):
    class FakeDDGS:
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def text(self, q, max_results=3): return []
    monkeypatch.setattr(st, "DDGS", FakeDDGS)
    assert "No se encontraron" in st.search_web("x")


def test_search_web_handles_errors(monkeypatch):
    def boom(): raise RuntimeError("sin red")
    monkeypatch.setattr(st, "DDGS", boom)
    assert "Falló la búsqueda" in st.search_web("x")


def test_write_file_is_sandboxed(tm, tmp_path):
    outside = tmp_path.parent / "fuera_del_sandbox.txt"
    out = tm.execute_tool("write_file", json.dumps({"path": str(outside), "content": "x"}))
    try:
        assert not outside.exists(), out
        assert "BLOQUEO" in out
    finally:
        if outside.exists():
            outside.unlink()


def test_write_relative_path_goes_to_workspace(tm, tmp_path):
    tm.execute_tool("write_file", json.dumps({"path": "notas/a.txt", "content": "x"}))
    assert (tmp_path / "notas" / "a.txt").read_text(encoding="utf-8") == "x"


def test_write_path_traversal_blocked(tm, tmp_path):
    out = tm.execute_tool("write_file", json.dumps({"path": "../escape.txt", "content": "x"}))
    assert "BLOQUEO" in out and not (tmp_path.parent / "escape.txt").exists()


@pytest.mark.parametrize("name", [".env", ".env.production", "id_rsa"])
def test_read_secret_files_blocked(tmp_path, name):
    p = tmp_path / name
    p.write_text("ROOT_PIN=secreto", encoding="utf-8")
    out = st.read_file(str(p))
    assert "BLOQUEO" in out and "ROOT_PIN=secreto" not in out


def test_read_env_example_allowed(tmp_path):
    p = tmp_path / ".env.example"
    p.write_text("ROOT_PIN=", encoding="utf-8")
    assert st.read_file(str(p)) == "ROOT_PIN="


# ------------------------- Universal Connector -----------------------------

@pytest.mark.parametrize("platform,action,params,expected", [
    ("YouTube", "play_music", {"song": "Carnaval"}, "Carnaval"),
    ("youtube", "search_video", {"query": "gatos"}, "gatos"),
    ("gmail", "read_inbox", {}, "Bandeja"),
    ("outlook", "send_email", {"to": "a@b.c", "subject": "Hola"}, "Hola"),
    ("steam", "launch_game", {"game": "Hades"}, "Hades"),
    ("xbox", "turn_on", {}, "encendido"),
])
def test_connector_dispatch(platform, action, params, expected):
    assert expected in uc.execute_universal_action(platform, action, params)


def test_connector_unsupported_platform():
    assert "no soportada" in uc.execute_universal_action("spotify", "play", {})


@pytest.mark.parametrize("platform", ["youtube", "gmail", "steam", "xbox"])
def test_connector_unsupported_action(platform):
    assert "no soportada" in uc.execute_universal_action(platform, "accion_rara", {})


def test_connector_via_tools_manager(tm):
    out = tm.execute_tool("execute_universal_action", json.dumps(
        {"platform": "xbox", "action": "turn_on", "parameters": {}}))
    assert "ÉXITO" in out


@pytest.mark.xfail(strict=True, reason="GAP: los drivers son simulaciones; devuelven ÉXITO sin ejecutar nada ni exigir sesión")
def test_email_requires_session_token():
    uc.set_current_session({})
    out = uc.execute_universal_action("gmail", "send_email", {"to": "x@y.z", "subject": "s"})
    assert "ÉXITO" not in out


@pytest.mark.xfail(strict=True, reason="RNF06: no hay registro de drivers; agregar plataforma exige editar el if/elif")
def test_connector_supports_driver_registration():
    assert hasattr(uc, "register_driver")
