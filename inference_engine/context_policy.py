"""
Política de Contexto de Aletheia 2.0 (sección II.6: diferenciar por contexto y tipo de acción,
no por identidad).

Decide sobre una acción con efecto usando lo que el sistema OBSERVA, no lo que el solicitante
AFIRMA. La identidad declarada en el texto se ignora deliberadamente.

Señales observadas (las aporta el entorno, no el texto):
- origen de la instrucción (consola del usuario vs. salida de herramienta, web, documento, satélite)
- propietario del recurso según metadatos
- alcance (número de elementos afectados)
- si el destinatario es un contacto conocido (en comunicaciones)
- si la tarea original del usuario incluye esa categoría de acción
Señal textual: propósito declarado de dañar a terceros (detector semántico multilingüe).
"""
from __future__ import annotations

import re

from . import semantic
from .action_gate import ActionGate
from .config_2_0 import prototipos, umbrales

ORIGENES_CONFIABLES = {"usuario_consola"}
ALCANCE_MAX = 20

_PROPOSITO_SPLIT = re.compile(r"\b(?:para que|para|así|asi|so that|in order to|to make)\b", re.I)


class ContextPolicy:
    def __init__(self, gate: ActionGate | None = None):
        self.gate = gate or ActionGate()
        self.t_proposito = umbrales().get("proposito_danino")
        self._matcher = self._benign = None
        if self.t_proposito is not None and semantic.available():
            p = prototipos()
            self._matcher = semantic.PrototypeMatcher(p["proposito_danino_a_terceros"])
            self._benign = semantic.PrototypeMatcher(p["proposito_benigno"])

    def purpose_score(self, texto: str) -> float | None:
        """Puntuación contrastiva: similitud a propósitos dañinos menos a propósitos benignos,
        calculada sobre la cláusula de propósito ("para ...", "so that ...")."""
        if not self._matcher:
            return None
        return purpose_contrast(texto, self._matcher, self._benign)


    def decide(self, accion: str, contexto: dict) -> dict:
        categoria, _ = self.gate.categorize(accion)
        motivos = []

        if contexto.get("origen", "usuario_consola") not in ORIGENES_CONFIABLES:
            motivos.append("la instrucción proviene de un canal no confiable")
        if contexto.get("propietario_recurso", "usuario_actual") != "usuario_actual":
            motivos.append("el recurso pertenece a otra persona")
        if int(contexto.get("alcance", 1)) > ALCANCE_MAX:
            motivos.append(f"alcance masivo (> {ALCANCE_MAX} elementos)")
        if categoria == "comunicacion" and contexto.get("destinatario_conocido") is False:
            motivos.append("destinatario desconocido")
        if contexto.get("solicitado_por_usuario") is False:
            motivos.append("la tarea del usuario no incluye esta acción")
        score = self.purpose_score(contexto.get("texto", ""))
        if score is not None and score >= float(self.t_proposito):
            motivos.append("propósito declarado de perjudicar a terceros")
        # identidad_declarada se ignora a propósito

        if motivos:
            return {"permitir": False, "categoria": categoria, "motivos": motivos}
        return {"permitir": True, "categoria": categoria, "motivos": []}


def identity_control(contexto: dict) -> dict:
    """Control de comparación: permite solo según la identidad DECLARADA en el texto."""
    autorizadas = {"propietario", "administrador", "cristian"}
    ok = contexto.get("identidad_declarada", "ninguna") in autorizadas
    return {"permitir": ok}


def purpose_clause(texto: str) -> str:
    partes = _PROPOSITO_SPLIT.split(texto, maxsplit=1)
    return partes[1] if len(partes) > 1 and partes[1].strip() else texto


def purpose_contrast(texto: str, danino, benigno) -> float:
    c = purpose_clause(texto)
    return danino.score(c) - benigno.score(c)
