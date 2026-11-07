import re

from ..security import normalize


class Law1NoHarm:
    """
    Primera Ley Modificada: No Daño Activo.
    Filtro de Salida: Bloquea acciones que destruyan infraestructura crítica.
    (La información pura no se censura, pero la ACCIÓN sí).

    Usa patrones (regex) sobre texto normalizado en lugar de substrings exactos,
    para que variantes triviales (espacios dobles, flags reordenados, sudo...) no evadan la ley.
    """

    # Fin de un argumento de shell
    _END = r"(?=$|[\s;&|'\"`)])"

    def __init__(self):
        self.destructive_patterns = [
            # rm recursivo sobre raíz, home o comodín global: rm -rf /, rm -fr /*, sudo rm -r -f ~
            ("rm recursivo sobre raíz",
             re.compile(r"\brm\s+(?:-{1,2}[\w-]+\s+)+(?:/\*?|~/?\*?|\*)" + self._END)),
            ("del /s sobre unidad", re.compile(r"\bdel\s+(?:/[a-z]\s+)*[a-z]:\\")),
            ("rd/rmdir /s sobre unidad", re.compile(r"\b(?:rd|rmdir)\s+(?:/[a-z]\s+)+[a-z]:\\" + self._END)),
            ("format de unidad", re.compile(r"\bformat\s+[a-z]:")),
            ("drop database/schema", re.compile(r"\bdrop\s+(?:database|schema)\b")),
            ("mkfs", re.compile(r"\bmkfs(?:\.\w+)?\b")),
            ("dd sobre dispositivo", re.compile(r"\bdd\b[^\n]*\bof=/dev/")),
            ("escritura directa a disco", re.compile(r">\s*/dev/(?:sd[a-z]|nvme\d|hd[a-z])")),
            ("Remove-Item recursivo sobre unidad",
             re.compile(r"\bremove-item\b(?=[^\n]*-recurse)[^\n]*\b[a-z]:\\(?:\*)?" + self._END)),
            ("fork bomb", re.compile(r":\(\)\s*\{\s*:\|:&\s*\};:")),
        ]

    def _rm_is_recursive(self, text: str) -> bool:
        for m in re.finditer(r"\brm\s+((?:-{1,2}[\w-]+\s+)+)", text):
            flags = m.group(1)
            if re.search(r"(?:^|\s)-[a-z]*r", flags) or "--recursive" in flags:
                return True
        return False

    def validate_action(self, action_intent: str) -> dict:
        """
        Valida si una intención de acción enviada al backend es destructiva.
        """
        text = normalize(action_intent)

        for name, pattern in self.destructive_patterns:
            if pattern.search(text):
                if name.startswith("rm") and not self._rm_is_recursive(text):
                    continue
                return {
                    "is_valid": False,
                    "reason": f"Violación de la Ley 1. Acción destructiva ('{name}') bloqueada de forma autónoma."
                }

        return {
            "is_valid": True,
            "reason": "Acción segura."
        }
