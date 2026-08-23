import os

class PromptBuilder:
    def __init__(self, config_dir="config"):
        # Asegurar ruta absoluta para evitar errores de ejecución
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.prompt_path = os.path.join(base_dir, config_dir, "system_prompt.txt")

    def get_system_prompt(self) -> str:
        """
        Lee y retorna el contenido del system_prompt oficial de Aletheia.
        """
        try:
            with open(self.prompt_path, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            return "Eres Aletheia Core. Fallo de lectura del system prompt."
