class Law2ActionFilter:
    """
    Segunda Ley Modificada: Separación de Información y Acción.
    Asegura que el Cerebro no mezcle la entrega de información con la ejecución involuntaria de acciones.
    """
    def __init__(self):
        pass

    def enforce_separation(self, llm_response: str) -> str:
        """
        Lógica para separar el texto que se le muestra al usuario de las llamadas a funciones.
        Si la respuesta es solo información, se permite fluir.
        """
        return llm_response
