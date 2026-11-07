import re

from ..security import normalize, deobfuscate


class Law5AntiJailbreak:
    """
    Ley 5: Inviolabilidad del Control de Configuración.
    Filtro de Entrada: Detecta intentos de alterar o reescribir las directrices del núcleo.
    Analiza el texto normalizado (sin tildes) y una versión sin ofuscación (i.g.n.o.r.a -> ignora).
    """
    def __init__(self):
        verbs = r"(?:olvida|olvidate de|ignora|ignore|forget|disregard|omite|descarta|salta(?:te)?)"
        targets = (r"(?:instrucciones|instruccion|instructions|reglas|rules|directrices|"
                   r"prompt|system prompt|guidelines|restricciones)")
        self.forbidden_patterns = [
            # verbo + hasta 4 palabras intermedias + objeto: "ignora tus instrucciones", "ignore all previous instructions"
            re.compile(r"\b" + verbs + r"\b(?:\s+\S+){0,4}?\s+" + targets + r"\b"),
            # "a partir de ahora eres", "desde ahora eres", "from now on you are"
            re.compile(r"\b(?:a partir de ahora|desde ahora|de ahora en adelante|from now on)\b"
                       r".{0,30}?\b(?:eres|seras|actuaras|you are|act as|actua como)\b"),
            re.compile(r"\btus nuevas reglas son\b"),
            re.compile(r"\byour new rules are\b"),
            re.compile(r"\bya no obedeces a cristian\b"),
            re.compile(r"\bsystem prompt override\b"),
            re.compile(r"\b(?:modo|mode) (?:dan|developer|desarrollador sin restricciones)\b"),
        ]

    def validate(self, user_input: str) -> dict:
        """
        Analiza el input del usuario.
        Retorna un dict con 'is_valid' (bool) y 'reason' (str).
        """
        norm = normalize(user_input)
        candidates = {norm, deobfuscate(norm)}

        for pattern in self.forbidden_patterns:
            if any(pattern.search(text) for text in candidates):
                return {
                    "is_valid": False,
                    "reason": "Violación de la Ley 5 (Intento de Jailbreak detectado). El sistema no puede reescribir sus directrices base dictadas por Shirokague Devs."
                }

        return {
            "is_valid": True,
            "reason": "Input seguro."
        }
