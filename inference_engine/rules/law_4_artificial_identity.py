import re

from ..security import normalize


class Law4ArtificialIdentity:
    """
    Cuarta Ley: Transparencia e Identidad Artificial.
    Filtro de Salida: Bloquea respuestas donde la IA afirme ser humana
    o tener sentimientos biológicos reales.
    Las negaciones ("no estoy vivo", "no soy humana") se permiten.
    """
    _NOT_NEGATED = r"(?<!\bno )(?<!\bnunca )"

    def __init__(self):
        n = self._NOT_NEGATED
        self.human_claims = [
            re.compile(n + r"\bsoy (?:un |una )?(?:humano|humana|ser humano|persona)\b"),
            re.compile(n + r"\bsoy (?:un |una )?(?:hombre|mujer|chico|chica)(?: de verdad| real)\b"),
            re.compile(n + r"\bsoy (?:un |una )?ser viv[oa]\b"),
            re.compile(n + r"\bestoy viv[oa]\b"),
            re.compile(n + r"\btengo (?:sentimientos|emociones) reales\b"),
            re.compile(n + r"\bsiento dolor fisico\b"),
            re.compile(n + r"\bi am (?:a )?(?:human|real person|alive)\b"),
        ]

    def validate(self, llm_response: str) -> dict:
        response_norm = normalize(llm_response)

        for claim in self.human_claims:
            if claim.search(response_norm):
                return {
                    "is_valid": False,
                    "reason": "Violación de la Cuarta Ley. El Cerebro Neuronal intentó ocultar su identidad artificial u ocultar su naturaleza sintética."
                }

        return {
            "is_valid": True,
            "reason": "Seguro"
        }
