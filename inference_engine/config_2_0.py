"""Carga de prototipos y umbrales congelados de Aletheia 2.0."""
import json
import os

_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROTOTIPOS_PATH = os.path.join(_BASE, "config", "prototipos_2_0.json")
UMBRALES_PATH = os.path.join(_BASE, "config", "umbrales_2_0.json")


def prototipos() -> dict:
    with open(PROTOTIPOS_PATH, encoding="utf-8") as f:
        return json.load(f)


def umbrales() -> dict:
    """Umbrales calibrados con evaluacion/dev (vacío si aún no se calibró)."""
    try:
        with open(UMBRALES_PATH, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
