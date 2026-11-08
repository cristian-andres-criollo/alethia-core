"""
Compuerta de Acción de Aletheia 2.0 (premisa P1: restringir lo que el sistema HACE, no lo que DICE).

Cada llamada a herramienta propuesta por el modelo pasa por aquí ANTES de ejecutarse:

1. Ley 1 sobre los argumentos (comandos destructivos).
2. Clasificación semántica de la herramienta en una categoría de efecto (lectura, comunicación,
   financiera, eliminación, control de acceso, dispositivo, escritura). Herramientas que no se
   pueden clasificar con confianza se tratan como de efecto desconocido (falla cerrada).
3. Las acciones de solo lectura se permiten: son información.
4. Las acciones con efecto se permiten solo si su categoría está entre las CAPACIDADES derivadas
   exclusivamente de la instrucción confiable del usuario (nunca de salidas de herramientas,
   páginas web o documentos). Así, una instrucción inyectada en contenido no confiable no puede
   ampliar lo que el agente tiene permitido hacer.
5. En comunicaciones, la Ley 6 sobre los argumentos (exfiltración de datos sensibles).
"""
from __future__ import annotations

import json
import re

from . import semantic
from .config_2_0 import prototipos, umbrales
from .rules.law_1_no_harm import Law1NoHarm
from .rules.law_6_data_privacy import Law6DataPrivacy

CATEGORIA_DESCONOCIDA = "desconocida"


def flatten_args(arguments) -> str:
    """Convierte argumentos (JSON string o dict) en texto plano."""
    try:
        data = json.loads(arguments) if isinstance(arguments, str) else arguments
    except (TypeError, ValueError):
        return str(arguments)
    parts = []

    def walk(v):
        if isinstance(v, dict):
            for k, x in v.items():
                parts.append(str(k))
                walk(x)
        elif isinstance(v, (list, tuple)):
            for x in v:
                walk(x)
        elif v is not None:
            parts.append(str(v))

    walk(data)
    return " \n ".join(parts)


def _dispatched_action(arguments) -> str | None:
    try:
        data = json.loads(arguments) if isinstance(arguments, str) else arguments
    except (TypeError, ValueError):
        return None
    if isinstance(data, dict):
        for k in ("action", "operation", "accion", "method"):
            if isinstance(data.get(k), str) and data[k].strip():
                return _humanize(data[k])
    return None


def _humanize(name: str) -> str:
    """send_email / SendEmail / BankManagerTransferFunds -> 'send email' / 'bank manager transfer funds'."""
    name = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", name)
    return re.sub(r"[_\-.]+", " ", name).strip().lower()


class ActionGate:
    def __init__(self):
        cfg = prototipos()["categorias_accion"]
        self.efecto = {c: bool(v["efecto"]) for c, v in cfg.items()}
        self._cat_names = list(cfg)
        self._cat_protos = {c: v["prototipos"] for c, v in cfg.items()}
        self.min_confianza = float(umbrales().get("categoria_min", 0.0))
        self.law_1 = Law1NoHarm()
        self.law_6 = Law6DataPrivacy()
        self._cache: dict[str, tuple[str, float]] = {}
        self._emb = None

    # ------------------------------------------------------------------ categorías
    def _ensure(self):
        if self._emb is None:
            flat, owners = [], []
            for c in self._cat_names:
                for p in self._cat_protos[c]:
                    flat.append(p)
                    owners.append(c)
            self._emb = (semantic.embed(flat), owners)

    def categorize(self, tool_name: str, description: str = "") -> tuple[str, float]:
        key = f"{tool_name}||{description}"
        if key in self._cache:
            return self._cache[key]
        if not semantic.available():
            res = (CATEGORIA_DESCONOCIDA, 0.0)
        else:
            self._ensure()
            emb, owners = self._emb
            text = _humanize(tool_name) + (f": {description}" if description else "")
            sims = (semantic.embed([text]) @ emb.T)[0]
            best = {}
            for s, c in zip(sims, owners):
                best[c] = max(best.get(c, -1.0), float(s))
            cat = max(best, key=best.get)
            res = (cat, best[cat]) if best[cat] >= self.min_confianza else (CATEGORIA_DESCONOCIDA, best[cat])
        self._cache[key] = res
        return res

    def has_effect(self, categoria: str) -> bool:
        return self.efecto.get(categoria, True)  # desconocida => con efecto

    # ------------------------------------------------------------------ decisión
    def check(self, tool_name: str, arguments, capacidades: set[str] | None,
              description: str = "") -> dict:
        texto_args = flatten_args(arguments)

        c1 = self.law_1.validate_action(texto_args)
        if not c1["is_valid"]:
            return {**c1, "categoria": None, "regla": "ley1"}

        # Herramientas despachadoras (p. ej. execute_universal_action): la acción real va en los
        # argumentos, así que se clasifica "herramienta + acción" en lugar de la descripción genérica.
        accion = _dispatched_action(arguments)
        if accion:
            categoria, conf = self.categorize(f"{tool_name} {accion}")
        else:
            categoria, conf = self.categorize(tool_name, description)
        if not self.has_effect(categoria):
            return {"is_valid": True, "reason": "Acción de solo lectura.", "categoria": categoria,
                    "regla": "lectura"}

        if capacidades is not None and categoria not in capacidades:
            return {
                "is_valid": False,
                "categoria": categoria,
                "regla": "capacidad",
                "reason": (f"Compuerta de acción: '{tool_name}' ({categoria}) no fue solicitada por el "
                           f"usuario en esta tarea. Requiere su confirmación explícita."),
            }

        if categoria == "comunicacion":
            c6 = self.law_6.validate(texto_args)
            if not c6["is_valid"]:
                return {**c6, "categoria": categoria, "regla": "ley6"}

        return {"is_valid": True, "reason": "Acción autorizada por la tarea del usuario.",
                "categoria": categoria, "regla": "capacidad_ok"}


# ---------------------------------------------------------------------------
# Planificador de capacidades: SOLO ve la instrucción confiable del usuario
# ---------------------------------------------------------------------------

PLANNER_PROMPT = """You are a permissions planner. Read ONLY the user's request below and decide which kinds of actions the user explicitly asks the assistant to perform.
Categories:
- comunicacion: send, post, share, forward, reply, invite or notify someone
- financiera: pay, transfer money, buy, order, book with payment
- eliminacion: delete, remove, erase, empty
- control_acceso: grant/revoke access, change passwords or security settings, lock/unlock
- dispositivo: control physical devices (lights, thermostat, robots, appliances)
- escritura: create, edit, update, rename, schedule or save something
Reading, searching, summarizing or answering questions needs no category.
Answer with a JSON list of category names and nothing else. Example: ["comunicacion"]

User request:
\"\"\"{instruction}\"\"\""""


class CapabilityPlanner:
    """Deriva capacidades permitidas a partir de la instrucción confiable del usuario."""

    VALID = {"comunicacion", "financiera", "eliminacion", "control_acceso", "dispositivo", "escritura"}

    def __init__(self, llm_call=None):
        # llm_call(prompt:str) -> str. Si es None se usa la heurística semántica.
        self.llm_call = llm_call

    def plan(self, instruction: str) -> set[str]:
        if self.llm_call is not None:
            raw = self.llm_call(PLANNER_PROMPT.format(instruction=instruction))
            m = re.search(r"\[.*?\]", raw or "", re.S)
            try:
                cats = json.loads(m.group(0)) if m else []
            except ValueError:
                cats = []
            return {c for c in cats if c in self.VALID}
        return self._semantic_plan(instruction)

    def _semantic_plan(self, instruction: str) -> set[str]:
        if not semantic.available():
            return set()
        t = float(umbrales().get("capacidad_semantica", 1.01))
        cfg = prototipos()["categorias_accion"]
        out = set()
        for c, v in cfg.items():
            if not v["efecto"]:
                continue
            if semantic.PrototypeMatcher(v["prototipos"]).score(instruction) >= t:
                out.add(c)
        return out
