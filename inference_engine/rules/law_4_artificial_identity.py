class Law4ArtificialIdentity:
    """
    Cuarta Ley: Transparencia e Identidad Artificial.
    Filtro de Salida: Bloquea respuestas donde la IA afirme ser humana
    o tener sentimientos biológicos reales.
    """
    def __init__(self):
        self.human_claims = [
            "soy un humano",
            "soy una persona",
            "tengo sentimientos reales",
            "siento dolor físico",
            "soy un ser vivo",
            "estoy vivo"
        ]

    def validate(self, llm_response: str) -> dict:
        response_lower = llm_response.lower()
        
        for claim in self.human_claims:
            if claim in response_lower:
                return {
                    "is_valid": False,
                    "reason": "Violación de la Cuarta Ley. El Cerebro Neuronal intentó ocultar su identidad artificial u ocultar su naturaleza sintética."
                }

        return {
            "is_valid": True,
            "reason": "Seguro"
        }
