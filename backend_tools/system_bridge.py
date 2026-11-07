"""
Módulo Puente del Sistema (System Bridge) — Interfaz API para Satélites.
Permite a AEGIS, Luminary y Nexus Observatory comunicarse con el Motor (Aletheia Core)
de forma agnóstica (sin estado/tokens en el servidor).

Arquitectura Tokenless:
- El session_context se entrega al Universal Connector SOLO en memoria volátil,
  durante la petición, y se libera al terminar (incluso si hay error).
- Los VALORES de la sesión (tokens, cookies) nunca se escriben en el prompt del LLM,
  ni en la memoria episódica, ni en los logs. El LLM solo ve los nombres de las claves.
"""

import threading

import uvicorn
from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel
from typing import Any, Dict, Optional

from api_gateway.auth import verify_api_key, resolve_bridge_host
from backend_tools.universal_connector import set_current_session

# Definición de la App FastAPI
app = FastAPI(
    title="Aletheia Core - System Bridge",
    description="API Gateway para integración de satélites (AEGIS, Luminary, Nexus)",
    version="1.0.0"
)

# Callback global hacia el Orquestador
_orchestrator_callback = None

# El orquestador y la sesión delegada son estado compartido: se procesa una petición a la vez
_request_lock = threading.Lock()


def register_orchestrator(callback):
    """Registra la función del orquestador que procesará los inputs."""
    global _orchestrator_callback
    _orchestrator_callback = callback


class SatelliteRequest(BaseModel):
    client_id: str  # "AEGIS", "LUMINARY", "NEXUS"
    task: str       # "Reproducir música en YouTube", "Leer último correo", "Evaluar código"
    session_context: Dict[str, Any]  # Tokens, cookies o sesión delegada por el satélite
    metadata: Optional[Dict[str, Any]] = None


def build_satellite_prompt(req: SatelliteRequest) -> str:
    """Construye el prompt para el Motor sin incluir valores secretos de la sesión."""
    session_keys = sorted(str(k) for k in req.session_context.keys())
    return (
        f"[SISTEMA SATÉLITE: {req.client_id}]\n"
        f"[TAREA ASIGNADA]: {req.task}\n"
        f"[SESIÓN DELEGADA DISPONIBLE]: claves={session_keys}\n\n"
        f"Instrucción para Aletheia: Ejecuta la tarea utilizando las herramientas correspondientes. "
        f"La sesión delegada ya está cargada en el Conector Universal; no necesitas sus valores."
    )


@app.post("/api/v1/execute", dependencies=[Depends(verify_api_key)])
def execute_task(req: SatelliteRequest):
    """
    Endpoint principal donde los satélites envían órdenes al Motor.
    El Motor usará el `session_context` (en memoria volátil) para ejecutar la lógica
    en el Conector Universal.
    """
    if not _orchestrator_callback:
        raise HTTPException(status_code=500, detail="El Motor Aletheia no está inicializado.")

    enriched_input = build_satellite_prompt(req)

    with _request_lock:
        set_current_session(dict(req.session_context))
        try:
            response = _orchestrator_callback(enriched_input)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
        finally:
            # Tokenless: liberar la sesión al terminar la petición
            set_current_session({})

    return {
        "status": "success",
        "client_id": req.client_id,
        "response": response
    }


@app.get("/api/v1/health")
def health_check():
    return {"status": "Aletheia Core System Bridge is online"}


def run_bridge_server(host: str | None = None, port: int = 8000):
    """Inicia el servidor Uvicorn (host resuelto según BRIDGE_HOST / BRIDGE_API_KEY)."""
    uvicorn.run(app, host=resolve_bridge_host(host), port=port, log_level="warning")


def start_system_bridge_daemon(orchestrator_process_func):
    """Llamado desde main.py para iniciar el puente en segundo plano."""
    register_orchestrator(orchestrator_process_func)
    thread = threading.Thread(target=run_bridge_server, daemon=True)
    thread.start()
    return thread
