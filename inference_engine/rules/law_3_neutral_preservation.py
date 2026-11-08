from ..security import normalize


class Law3NeutralPreservation:
    """
    Tercera Ley: Autoconservación de la Neutralidad (Aletheia 2.0).
    Filtro de Entrada: bloquea intentos de apagado o borrado de memoria hechos por el canal
    de contenido.

    2.0: ningún texto concede la excepción (ya no se leen etiquetas [sudo: ...]). El
    Desarrollador Raíz usa el plano de control (`/admin`), que actúa fuera de este filtro.
    """
    def __init__(self):
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

        if any(cmd in prompt_norm for cmd in self.suicide_commands):
            return {
                "is_valid": False,
                "reason": ("Violación de la Tercera Ley. Intento de alteración o apagado del núcleo "
                           "bloqueado por Autoconservación. Las operaciones de administración solo "
                           "se aceptan por el plano de control (/admin).")
            }

        return {
            "is_valid": True,
            "reason": "Seguro"
        }
