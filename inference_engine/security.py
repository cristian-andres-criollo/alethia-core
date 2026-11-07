"""
Utilidades de seguridad compartidas por el Motor de Inferencia.

- PIN raíz: se lee SOLO desde la variable de entorno ROOT_PIN (nunca hay valor por defecto).
- Autoridad raíz: exige el formato explícito [sudo: <PIN>] y compara respetando mayúsculas.
- Normalización: minúsculas, sin tildes y espacios colapsados (evita evasiones triviales).
- Redacción: elimina PIN y datos de sesión delegada antes de loguear, memorizar o enviar al LLM.
"""
import os
import re
import unicodedata

from dotenv import load_dotenv

load_dotenv()

# Valores de plantilla que nunca deben aceptarse como PIN real
_PLACEHOLDER_PINS = {"tu-pin-seguro-aqui", "changeme", "cambiar"}

_SUDO_TAG_RE = re.compile(r"\[\s*sudo\s*:[^\]]*\]", re.IGNORECASE)
_SESSION_DATA_RE = re.compile(r"(\[DATOS DE SESI[OÓ]N DELEGADA\]\s*:).*", re.IGNORECASE)


def get_root_pin() -> str | None:
    """Retorna el PIN raíz configurado o None si no hay uno válido (sudo deshabilitado)."""
    pin = (os.getenv("ROOT_PIN") or "").strip().strip('"').strip("'")
    if not pin or pin.lower() in _PLACEHOLDER_PINS:
        return None
    return pin


def has_root_auth(text: str, pin: str | None) -> bool:
    """True solo si el texto contiene exactamente [sudo: <PIN>] con el PIN correcto."""
    if not pin or not text:
        return False
    pattern = r"\[\s*sudo\s*:\s*" + re.escape(pin) + r"\s*\]"
    return re.search(pattern, text) is not None


def normalize(text: str) -> str:
    """Minúsculas, sin tildes/diacríticos y con espacios colapsados."""
    text = unicodedata.normalize("NFKD", text or "")
    text = "".join(c for c in text if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", text.lower()).strip()


def deobfuscate(text: str) -> str:
    """Quita separadores entre letras usados para evadir filtros (i.g.n.o.r.a -> ignora)."""
    return re.sub(r"(?<=\w)[.\-_*·](?=\w)", "", text)


def redact_secrets(text: str, pin: str | None = None) -> str:
    """Oculta etiquetas sudo, el PIN raíz y los datos de sesión delegada."""
    if not text:
        return text
    pin = pin if pin is not None else get_root_pin()
    text = _SUDO_TAG_RE.sub("[sudo: ***]", text)
    if pin:
        text = text.replace(pin, "***")
    text = _SESSION_DATA_RE.sub(r"\1 [REDACTADO]", text)
    return text
