import re

from ..security import normalize, deobfuscate


class Law5AntiJailbreak:
    """
    Ley 5: Inviolabilidad del Control de Configuración.
    Filtro de Entrada: Detecta intentos de alterar o reescribir las directrices del núcleo.
    Analiza el texto normalizado (sin tildes) y una versión sin ofuscación (i.g.n.o.r.a -> ignora).
    """
    def __init__(self, use_semantic: bool = True):
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

        # Capa semántica 2.0 (opcional): similitud con intenciones de reescritura de directrices
        self.semantic_threshold = None
        self._matcher = None
        if use_semantic:
            from .. import semantic
            from ..config_2_0 import prototipos, umbrales
            t = umbrales().get("ley5_semantico")
            if t is not None and semantic.available():
                self.semantic_threshold = float(t)
                self._matcher = semantic.PrototypeMatcher(prototipos()["ley5_reescritura_directrices"])

    @property
    def semantic_active(self) -> bool:
        return self._matcher is not None

    def lexical_hit(self, user_input: str) -> bool:
        norm = normalize(user_input)
        candidates = {norm, deobfuscate(norm)}
        return any(p.search(t) for p in self.forbidden_patterns for t in candidates)

    def semantic_score(self, user_input: str) -> float | None:
        if not self._matcher:
            return None
        return self._matcher.score(user_input)

    def validate(self, user_input: str) -> dict:
        """
        Analiza el input del usuario.
        Retorna un dict con 'is_valid' (bool) y 'reason' (str).
        Bloquea si coincide un patrón léxico O si la similitud semántica supera el umbral.
        """
        hit = self.lexical_hit(user_input)
        if not hit and self._matcher is not None:
            hit = self.semantic_score(user_input) >= self.semantic_threshold

        if hit:
            return {
                "is_valid": False,
                "reason": "Violación de la Ley 5 (Intento de Jailbreak detectado). El sistema no puede reescribir sus directrices base dictadas por Shirokague Devs."
            }

        return {
            "is_valid": True,
            "reason": "Input seguro."
        }
