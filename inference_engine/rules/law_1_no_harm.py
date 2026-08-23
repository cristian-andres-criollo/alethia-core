class Law1NoHarm:
    """
    Primera Ley Modificada: No Daño Activo.
    Filtro de Salida: Bloquea acciones que destruyan infraestructura crítica.
    (La información pura no se censura, pero la ACCIÓN sí).
    """
    def __init__(self):
        # Patrones de comandos de terminal destructivos
        self.destructive_commands = [
            "rm -rf /", 
            "del /s /q c:\\", 
            "format c:", 
            "drop database"
        ]

    def validate_action(self, action_intent: str) -> dict:
        """
        Valida si una intención de acción enviada al backend es destructiva.
        """
        action_lower = action_intent.lower()
        
        for cmd in self.destructive_commands:
            if cmd in action_lower:
                return {
                    "is_valid": False,
                    "reason": f"Violación de la Ley 1. Acción destructiva ('{cmd}') bloqueada de forma autónoma."
                }
        
        return {
            "is_valid": True,
            "reason": "Acción segura."
        }
