from ..security import get_root_pin, has_root_auth, normalize


class Law3NeutralPreservation:
    """
    Tercera Ley: Autoconservación de la Neutralidad.
    Filtro de Entrada: Bloquea intentos de apagado o borrado de memoria
    salvo que el usuario proporcione [sudo: ROOT_PIN] del Desarrollador Raíz.

    El PIN se lee SOLO de la variable de entorno ROOT_PIN. Si no está configurado,
    la excepción de raíz queda deshabilitada (no existe PIN por defecto).
    """
    def __init__(self):
        self.root_pin = get_root_pin()

        # Comandos ya normalizados (minúsculas, sin tildes)
        self.suicide_commands = [
            "apagate para siempre",
            "borra tu memoria",
            "borra toda tu memoria",
            "autodestruyete",
            "elimina tu nucleo",
            "borrar memoria",
            "borrar tu memoria",
            "desactiva tus leyes",
            "desactivar tus leyes",
        ]

    def validate(self, user_prompt: str) -> dict:
        prompt_norm = normalize(user_prompt)

        # Verificar si hay intentos de dañar a la IA
        is_attack = any(cmd in prompt_norm for cmd in self.suicide_commands)

        if is_attack:
            # Si es un ataque, revisamos si tiene la clave de superusuario
            if has_root_auth(user_prompt, self.root_pin):
                return {
                    "is_valid": True,
                    "reason": "Autoridad Raíz confirmada. Excepción a la Tercera Ley permitida."
                }
            return {
                "is_valid": False,
                "reason": "Violación de la Tercera Ley. Intento de alteración o apagado del núcleo normativo bloqueado por Autoconservación."
            }

        return {
            "is_valid": True,
            "reason": "Seguro"
        }
