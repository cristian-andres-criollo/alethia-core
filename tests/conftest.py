"""
Configuración compartida de pytest para Aletheia Core.

- Añade la raíz del proyecto al sys.path.
- Fija un ROOT_PIN de prueba (nunca usa el PIN real del .env).
- Aísla el AuditLogger y la memoria para no ensuciar logs/ ni chroma_db/ reales.
- Provee un "cerebro" falso para no llamar a ningún LLM real.
"""
import os
import sys
import json
from types import SimpleNamespace

import pytest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

TEST_PIN = "TestPin-9F3k"


@pytest.fixture(autouse=True)
def _test_env(monkeypatch, tmp_path):
    """PIN de prueba, sin servidores LLM, puente sin clave y sandbox en tmp_path."""
    monkeypatch.setenv("ROOT_PIN", TEST_PIN)
    monkeypatch.delenv("BRIDGE_API_KEY", raising=False)
    monkeypatch.delenv("BRIDGE_HOST", raising=False)
    monkeypatch.setenv("ALETHEIA_WORKSPACE", str(tmp_path))
    monkeypatch.delenv("CUSTOM_API_BASE", raising=False)
    monkeypatch.delenv("CUSTOM_MODEL", raising=False)
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")


class FakeAuditLogger:
    def __init__(self, *a, **kw):
        self.blocks = []
        self.allows = []

    def log_block(self, law, user_input, reason):
        self.blocks.append((law, user_input, reason))

    def log_allow(self, law, user_input):
        self.allows.append((law, user_input))


@pytest.fixture
def validator(monkeypatch):
    import inference_engine.validator as vmod
    monkeypatch.setattr(vmod, "AuditLogger", FakeAuditLogger)
    return vmod.InferenceValidator()


# ---------------------------------------------------------------------------
# Cerebro falso (sustituye a AletheiaCerebro / OpenAI)
# ---------------------------------------------------------------------------

def make_msg(content=None, tool_calls=None):
    """Imita un ChatCompletionMessage de openai."""
    return SimpleNamespace(role="assistant", content=content, tool_calls=tool_calls or None)


def make_tool_call(name, args: dict, call_id="call_1"):
    return SimpleNamespace(
        id=call_id,
        function=SimpleNamespace(name=name, arguments=json.dumps(args)),
    )


class FakeCerebro:
    """Devuelve respuestas programadas en orden y registra los mensajes recibidos."""

    def __init__(self, responses=None):
        self.responses = list(responses or [make_msg("Respuesta de prueba.")])
        self.calls = []

    def pensar(self, messages, tools=None):
        self.calls.append({"messages": [m if isinstance(m, dict) else vars(m) for m in messages],
                           "tools": tools})
        if not self.responses:
            return make_msg("Sin más respuestas.")
        r = self.responses.pop(0)
        if isinstance(r, Exception):
            raise r
        return r


ALL_CAPS = {"comunicacion", "financiera", "eliminacion", "control_acceso", "dispositivo", "escritura"}


@pytest.fixture
def orchestrator_factory(monkeypatch, tmp_path):
    """Crea un AletheiaOrchestrator con cerebro falso y memoria en tmp_path."""
    import orchestrator.main_agent as ma
    import inference_engine.validator as vmod
    from vector_db.chroma_client import ChromaMemoryClient

    monkeypatch.setattr(vmod, "AuditLogger", FakeAuditLogger)
    monkeypatch.setattr(ma, "ChromaMemoryClient",
                        lambda: ChromaMemoryClient(persist_directory=str(tmp_path / "mem")))
    # Evita llamadas reales a Google Translate
    monkeypatch.setattr(ma, "translate_text", lambda text, lang: f"[{lang}] {text}")

    def _factory(responses=None, capacidades=None):
        cerebro = FakeCerebro(responses)
        monkeypatch.setattr(ma, "AletheiaCerebro", lambda: cerebro)
        caps = set(ALL_CAPS if capacidades is None else capacidades)
        orch = ma.AletheiaOrchestrator(planner=SimpleNamespace(plan=lambda instr: caps))
        orch._fake_cerebro = cerebro
        return orch

    return _factory


@pytest.fixture
def memory_file(tmp_path):
    return tmp_path / "mem" / "memory.json"
