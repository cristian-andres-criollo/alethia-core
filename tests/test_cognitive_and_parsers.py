"""Capa cognitiva (Mirror Personality), traductor y parsers de comandos de sentidos."""
import pytest

from cognitive_layer import emotion_detector as ed
from backend_tools.translator_tool import detect_target_language, translate_text
from senses.vision import parse_image_command
from senses.camera import parse_camera_command
from senses.hologram import project_hologram, detect_hologram_touch, interact_hologram


# ---------------------------- Mirror Personality ---------------------------

@pytest.mark.parametrize("text,dialect", [
    ("qué más parce, todo bacano?", "colombiano"),
    ("órale wey, qué chido", "mexicano"),
    ("che boludo, posta", "argentino"),
    ("tío, esto mola mazo", "español_españa"),
    ("Buenos días, necesito ayuda", None),
])
def test_detect_dialect(text, dialect):
    assert ed.detect_dialect(text) == dialect


@pytest.mark.parametrize("text,tone", [
    ("esto no funciona, otro error", "frustrado"),
    ("wow, genial, me encanta", "entusiasmado"),
    ("necesito refactorizar el módulo y la api", "técnico"),
    ("Hola", "neutral"),
])
def test_detect_tone(text, tone):
    assert ed.detect_tone(text) == tone


def test_detect_language():
    assert ed.detect_language("what is the capital of this country") == "en"
    assert ed.detect_language("cual es la capital de Colombia para los turistas") == "es"


def test_mirror_instruction_colombian():
    out = ed.build_mirror_instruction("parce, esto no funciona")
    assert "colombiana" in out and "frustrado" in out


def test_mirror_instruction_empty_for_neutral():
    assert ed.build_mirror_instruction("Hola") == ""


def test_tone_false_positive_single_letters():
    # 'q' y 'k' aparecen dentro de casi cualquier palabra -> todo se marca 'informal'
    assert ed.detect_tone("Quisiera solicitar el informe, por favor") == "formal"


def test_dialect_false_positive():
    assert ed.detect_dialect("Debemos mantener el sistema estable") is None


# ------------------------------- Traductor ---------------------------------

@pytest.mark.parametrize("text,code", [
    ("Escribe un poema en inglés", "en"),
    ("responde en francés por favor", "fr"),
    ("translated to german", "de"),
    ("dímelo en idioma japonés", "ja"),
    ("explícalo en español", None),
    ("¿Qué es la fotosíntesis?", None),
    ("vivo en colombia", None),
])
def test_detect_target_language(text, code):
    assert detect_target_language(text) == code


def test_translate_falls_back_on_error(monkeypatch):
    import deep_translator

    class Boom:
        def __init__(self, *a, **k): raise RuntimeError("sin red")
    monkeypatch.setattr(deep_translator, "GoogleTranslator", Boom)
    assert translate_text("hola", "en") == "hola"


def test_translate_long_text_by_paragraphs(monkeypatch):
    import deep_translator

    class Fake:
        def __init__(self, source, target): self.t = target
        def translate(self, txt): return f"<{self.t}>{txt[:3]}"
    monkeypatch.setattr(deep_translator, "GoogleTranslator", Fake)
    long = "a" * 3000 + "\n\n" + "b" * 3000
    assert translate_text(long, "en") == "<en>aaa\n\n<en>bbb"


# ------------------------------ /imagen ------------------------------------

@pytest.mark.parametrize("inp,expected", [
    ("/imagen C:/fotos/gato.png", ("C:/fotos/gato.png", None)),
    ("/imagen C:/fotos/gato.JPG ¿qué hay al fondo?", ("C:/fotos/gato.JPG", "¿qué hay al fondo?")),
    ("/image foto.webp", ("foto.webp", None)),
    ("/imagen", (None, None)),
    ("hola", (None, None)),
])
def test_parse_image_command(inp, expected):
    assert parse_image_command(inp) == expected


@pytest.mark.xfail(strict=True, reason="BUG: '/imagenes' también se interpreta como comando de imagen")
def test_parse_image_command_prefix_collision():
    assert parse_image_command("/imagenes bonitas") == (None, None)


# -------------------------------- /cam -------------------------------------

@pytest.mark.parametrize("inp,expected", [
    ("/cam", {"source": 0, "question": None, "monitor_mode": False}),
    ("/cam 1", {"source": 1, "question": None, "monitor_mode": False}),
    ("/cam celular 192.168.1.5", {"source": "http://192.168.1.5:4747/video", "question": None, "monitor_mode": False}),
    ("/cam rtsp rtsp://10.0.0.2/s ¿hay alguien?", {"source": "rtsp://10.0.0.2/s", "question": "¿hay alguien?", "monitor_mode": False}),
    ("/cam monitor", {"source": 0, "question": None, "monitor_mode": True}),
    ("/cam ¿qué ves?", {"source": 0, "question": "¿qué ves?", "monitor_mode": False}),
])
def test_parse_camera_command(inp, expected):
    assert parse_camera_command(inp) == expected


def test_parse_camera_not_a_command():
    assert parse_camera_command("hola") is None


# ------------------------------ Hologramas (stubs) -------------------------

def test_hologram_stubs():
    assert "X:1 Y:2 Z:3" in project_hologram("menu", (1, 2, 3))
    assert detect_hologram_touch([0, 1, 2], (0, 0, 0)) is False
    assert "abrir" in interact_hologram("h1", "abrir")
