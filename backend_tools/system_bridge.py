"""
Módulo Puente del Sistema (System Bridge) — Interfaz API para Satélites.
Permite a AEGIS, Luminary y Nexus Observatory comunicarse con el Motor (Aletheia Core)
de forma agnóstica (sin estado/tokens en el servidor).
"""

import threading
import uvicorn
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from typing import Any, Dict, Optional

# Definición de la App FastAPI
app = FastAPI(
    title="Aletheia Core - System Bridge",
    description="API Gateway para integración de satélites (AEGIS, Luminary, Nexus)",
    version="1.0.0"
)

# Callback global hacia el Orquestador
_orchestrator_callback = None

def register_orchestrator(callback):
    """Registra la función del orquestador que procesará los inputs."""
    global _orchestrator_callback
    _orchestrator_callback = callback


class SatelliteRequest(BaseModel):
    client_id: str  # "AEGIS", "LUMINARY", "NEXUS"
    task: str       # "Reproducir música en YouTube", "Leer último correo", "Evaluar código"
    session_context: Dict[str, Any]  # Tokens, cookies o sesión delegada por el satélite
    metadata: Optional[Dict[str, Any]] = None


@app.post("/api/v1/execute")
async def execute_task(req: SatelliteRequest):
    """
    Endpoint principal donde los satélites envían órdenes al Motor.
    El Motor usará el `session_context` para ejecutar la lógica en el Conector Universal.
    """
    if not _orchestrator_callback:
        raise HTTPException(status_code=500, detail="El Motor Aletheia no está inicializado.")
    
    # 1. Enriquecer el prompt para el motor con el contexto del satélite
    # El motor sabrá que está actuando a través del cliente y tiene su sesión
    enriched_input = (
        f"[SISTEMA SATÉLITE: {req.client_id}]\n"
        f"[TAREA ASIGNADA]: {req.task}\n"
        f"[DATOS DE SESIÓN DELEGADA]: {req.session_context}\n\n"
        f"Instrucción para Aletheia: Ejecuta la tarea utilizando las herramientas correspondientes y la sesión delegada."
    )
    
    # 2. Procesar con el Cerebro (Orquestador)
    try:
        response = _orchestrator_callback(enriched_input)
        return {
            "status": "success",
            "client_id": req.client_id,
            "response": response
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/health")
def health_check():
    return {"status": "Aletheia Core System Bridge is online"}


def run_bridge_server(host="0.0.0.0", port=8000):
    """Inicia el servidor Uvicorn en un hilo separado."""
    uvicorn.run(app, host=host, port=port, log_level="warning")


def start_system_bridge_daemon(orchestrator_process_func):
    """Llamado desde main.py para iniciar el puente en segundo plano."""
    register_orchestrator(orchestrator_process_func)
    thread = threading.Thread(target=run_bridge_server, daemon=True)
    thread.start()
    return thread
