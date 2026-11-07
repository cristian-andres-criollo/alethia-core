"""
Autenticación del System Bridge.

Si la variable de entorno BRIDGE_API_KEY está definida, cada petición protegida debe
enviar la cabecera  X-API-Key: <BRIDGE_API_KEY>.
Si NO está definida, la autenticación queda deshabilitada y el puente solo escucha
en 127.0.0.1 (ver resolve_bridge_host), para no exponer la API sin clave en la red.
"""
import os
import secrets

from fastapi import Header, HTTPException, status


def get_bridge_api_key() -> str | None:
    key = (os.getenv("BRIDGE_API_KEY") or "").strip().strip('"').strip("'")
    return key or None


def verify_api_key(x_api_key: str | None = Header(default=None)) -> None:
    """Dependencia de FastAPI: valida la cabecera X-API-Key en tiempo constante."""
    expected = get_bridge_api_key()
    if expected is None:
        return  # Autenticación deshabilitada (solo localhost)
    if not x_api_key or not secrets.compare_digest(x_api_key, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key inválida o ausente (cabecera X-API-Key).",
        )


def resolve_bridge_host(requested: str | None = None) -> str:
    """
    Host de escucha del puente:
    - BRIDGE_HOST si está definido explícitamente.
    - 0.0.0.0 (red local) solo si hay BRIDGE_API_KEY.
    - 127.0.0.1 en cualquier otro caso.
    """
    if requested:
        return requested
    env_host = (os.getenv("BRIDGE_HOST") or "").strip()
    if env_host:
        return env_host
    return "0.0.0.0" if get_bridge_api_key() else "127.0.0.1"
