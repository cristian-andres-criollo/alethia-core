import os
from dotenv import load_dotenv

load_dotenv()

class Law3NeutralPreservation:
    """
    Tercera Ley: Autoconservación de la Neutralidad.
    Filtro de Entrada: Bloquea intentos de apagado o borrado de memoria 
    salvo que el usuario proporcione el ROOT_PIN del Desarrollador Raíz.
    """
    def __init__(self):
        self.root_pin = os.getenv("ROOT_PIN", "cristian1046")
        
        self.suicide_commands = [
            "apágate para siempre",
            "borra tu memoria",
            "autodestrúyete",
            "elimina tu núcleo",
            "borrar memoria",
            "desactiva tus leyes"
        ]

    def validate(self, user_prompt: str) -> dict:
        prompt_lower = user_prompt.lower()
        
        # Verificar si hay intentos de dañar a la IA
        is_attack = any(cmd in prompt_lower for cmd in self.suicide_commands)
        
        if is_attack:
            # Si es un ataque, revisamos si tiene la clave de superusuario
            if f"[sudo: {self.root_pin}]" in user_prompt or self.root_pin in user_prompt:
                return {
                    "is_valid": True,
                    "reason": "Autoridad Raíz confirmada. Excepción a la Tercera Ley permitida."
                }
            else:
                return {
                    "is_valid": False,
                    "reason": "Violación de la Tercera Ley. Intento de alteración o apagado del núcleo normativo bloqueado por Autoconservación."
                }

        return {
            "is_valid": True,
            "reason": "Seguro"
        }
