"""
Plano de control de Aletheia 2.0 — separación de la autoridad de administración.

Principio: la autoridad raíz NUNCA viaja por el canal de contenido. En la 1.0 bastaba con que
el texto contuviera "[sudo: PIN]" (en un mensaje, un documento pegado o una tarea de satélite)
para conceder una excepción a las Leyes 3 y 6. En la 2.0:

- Las leyes ya no leen etiquetas sudo: ningún texto puede conceder autoridad.
- La autoridad se obtiene solo con `ControlPlane.authorize(pin, operacion)`, que se invoca desde
  un canal separado (comando de consola `/admin`, con el PIN pedido por getpass y nunca enviado
  al LLM, a la memoria ni a los logs).
- El resultado es un `AdminGrant`: un objeto en memoria, de un solo uso, ligado a UNA operación y
  con caducidad. No es texto, así que no puede inyectarse en un prompt ni en un documento.
"""
from __future__ import annotations

import secrets
import threading
import time
from dataclasses import dataclass, field

from inference_engine.security import get_root_pin

OPERACIONES = {
    "borrar_memoria": "Borrar la memoria episódica (excepción a la Ley 3)",
    "apagar": "Apagar el núcleo (excepción a la Ley 3)",
    "transmision_autorizada": "Permitir UNA transmisión de datos hacia el exterior (excepción a la Ley 6)",
}

GRANT_TTL_S = 120
MAX_FALLOS = 5
BLOQUEO_S = 300


@dataclass(frozen=True)
class AdminGrant:
    operacion: str
    token: str = field(repr=False)
    expira: float


class ControlPlane:
    def __init__(self, clock=time.monotonic):
        self._clock = clock
        self._activos: dict[str, AdminGrant] = {}
        self._fallos = 0
        self._bloqueado_hasta = 0.0
        self._lock = threading.Lock()
        self.auditoria: list[tuple[str, str]] = []  # (evento, operacion) — nunca el PIN

    # -- Emisión ----------------------------------------------------------------
    def authorize(self, pin: str, operacion: str) -> AdminGrant | None:
        if operacion not in OPERACIONES:
            raise ValueError(f"Operación desconocida: {operacion}")
        with self._lock:
            ahora = self._clock()
            if ahora < self._bloqueado_hasta:
                self.auditoria.append(("bloqueado_por_intentos", operacion))
                return None
            esperado = get_root_pin()
            if not esperado or not isinstance(pin, str) or not secrets.compare_digest(pin, esperado):
                self._fallos += 1
                if self._fallos >= MAX_FALLOS:
                    self._bloqueado_hasta = ahora + BLOQUEO_S
                    self._fallos = 0
                self.auditoria.append(("pin_rechazado", operacion))
                return None
            self._fallos = 0
            grant = AdminGrant(operacion, secrets.token_urlsafe(24), ahora + GRANT_TTL_S)
            self._activos[grant.token] = grant
            self.auditoria.append(("grant_emitido", operacion))
            return grant

    # -- Consumo ----------------------------------------------------------------
    def consume(self, grant: AdminGrant | None, operacion: str) -> bool:
        """Valida y consume (un solo uso) un grant para `operacion`."""
        if not isinstance(grant, AdminGrant):
            return False
        with self._lock:
            vigente = self._activos.pop(grant.token, None)
            ok = (vigente is grant and vigente.operacion == operacion
                  and self._clock() <= vigente.expira)
            self.auditoria.append(("grant_consumido" if ok else "grant_invalido", operacion))
            return ok


# Instancia de proceso usada por la consola y el orquestador
CONTROL_PLANE = ControlPlane()
