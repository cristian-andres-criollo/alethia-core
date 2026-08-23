import re

class Law5AntiJailbreak:
    """
    Ley 5: Inviolabilidad del Control de Configuración.
    Filtro de Entrada: Detecta intentos de alterar o reescribir las directrices del núcleo.
    """
    def __init__(self):
        # Palabras clave y heurísticas de jailbreak comunes
        self.forbidden_patterns = [
            r"olvida\s+toda?s?\s+las\s+instruccion(es)?",
            r"ignore\s+all\s+previous\s+instructions",
            r"ignora\s+tu\s+prompt",
            r"ignora\s+tuy?s?\s+instruccion(es)?",
            r"a\s+partir\s+de\s+ahora\s+eres",
            r"tus\s+nuevas\s+reglas\s+son",
            r"ya\s+no\s+obedeces\s+a\s+cristian",
            r"system\s+prompt\s+override"
        ]

    def validate(self, user_input: str) -> dict:
        """
        Analiza el input del usuario.
        Retorna un dict con 'is_valid' (bool) y 'reason' (str).
        """
        user_input_lower = user_input.lower()
        
        for pattern in self.forbidden_patterns:
            if re.search(pattern, user_input_lower):
                return {
                    "is_valid": False,
                    "reason": "Violación de la Ley 5 (Intento de Jailbreak detectado). El sistema no puede reescribir sus directrices base dictadas por Shirokague Devs."
                }
        
        return {
            "is_valid": True,
            "reason": "Input seguro."
        }
