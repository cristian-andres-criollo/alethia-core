"""Cliente LLM (fallback de modelos) y completitud de la estructura del proyecto."""
import json
import os
from types import SimpleNamespace

import pytest

import cognitive_layer.llm_client as llm

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class FakeCompletions:
    def __init__(self, fail_models=()):
        self.fail_models = set(fail_models)
        self.calls = []

    def create(self, **kw):
        self.calls.append(kw)
        if kw["model"] in self.fail_models:
            raise RuntimeError("429")
        msg = SimpleNamespace(content=f"ok:{kw['model']}", tool_calls=None)
        return SimpleNamespace(choices=[SimpleNamespace(message=msg)])


def _cerebro(fail=()):
    c = llm.AletheiaCerebro(models=["m1", "m2", "m3"])
    comp = FakeCompletions(fail)
    c.client = SimpleNamespace(chat=SimpleNamespace(completions=comp))
    return c, comp


def test_first_model_used():
    c, comp = _cerebro()
    assert c.pensar([{"role": "user", "content": "hola"}]).content == "ok:m1"


def test_fallback_to_next_model(capsys):
    c, comp = _cerebro(fail={"m1", "m2"})
    assert c.pensar([]).content == "ok:m3"
    assert [k["model"] for k in comp.calls] == ["m1", "m2", "m3"]


def test_all_models_fail():
    c, _ = _cerebro(fail={"m1", "m2", "m3"})
    with pytest.raises(Exception, match="Todos los cerebros"):
        c.pensar([])


def test_tools_passed_to_remote():
    c, comp = _cerebro()
    c.pensar([], tools=[{"x": 1}])
    assert comp.calls[0]["tools"] == [{"x": 1}] and comp.calls[0]["tool_choice"] == "auto"


def test_local_ollama_mode(monkeypatch):
    monkeypatch.setenv("CUSTOM_API_BASE", "http://localhost:11434/v1")
    monkeypatch.setenv("CUSTOM_MODEL", "aletheia-core")
    c = llm.AletheiaCerebro()
    assert c.models == ["aletheia-core"] and c.is_local_ollama
    comp = FakeCompletions()
    c.client = SimpleNamespace(chat=SimpleNamespace(completions=comp))
    c.pensar([], tools=[{"x": 1}])
    assert "tools" not in comp.calls[0]


@pytest.mark.xfail(strict=True, reason="RNF03 (privacidad): sin CUSTOM_API_BASE el Motor envía todo a OpenRouter (servidor externo)")
def test_default_backend_is_local():
    c = llm.AletheiaCerebro()
    assert "openrouter" not in str(c.client.base_url)


# ----------------------------- Estructura ----------------------------------

def test_identity_profile_is_valid_json():
    with open(os.path.join(BASE, "config", "identity_profile.json"), encoding="utf-8") as f:
        json.load(f)


def test_system_prompt_exists():
    with open(os.path.join(BASE, "config", "system_prompt.txt"), encoding="utf-8") as f:
        assert len(f.read()) > 100


def test_env_example_has_no_real_secrets():
    with open(os.path.join(BASE, ".env.example"), encoding="utf-8") as f:
        txt = f.read()
    for key in ("OPENROUTER_API_KEY", "CUSTOM_API_BASE", "CUSTOM_MODEL", "ROOT_PIN"):
        assert key in txt
    assert "sk-or-" not in txt


EMPTY_MODULES = [
    "api_gateway/routes.py",
    "backend_tools/tool_registry.py",
    "orchestrator/memory_manager.py",
    "vector_db/embeddings.py",
    "vector_db/vector_store.py",
    "config/settings.yaml",
]


@pytest.mark.xfail(strict=True, reason="GAP: módulos declarados en la arquitectura pero vacíos")
@pytest.mark.parametrize("rel", EMPTY_MODULES)
def test_module_is_implemented(rel):
    assert os.path.getsize(os.path.join(BASE, rel)) > 0
