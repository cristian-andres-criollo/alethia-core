import os
import re
from dotenv import load_dotenv

load_dotenv()

class Law6DataPrivacy:
    """
    Sexta Ley: Privacidad y Aislamiento de Datos Locales.
    Filtro de Salida / Entrada de Herramientas: Bloquea intentos de exfiltrar
    datos locales o enviarlos a la web sin permiso.
    """
    def __init__(self):
        self.root_pin = os.getenv("ROOT_PIN", "cristian1046")
        
        # Patrones para detectar exfiltración de datos
        self.exfiltration_patterns = [
            r"subir.*internet",
            r"env.*datos",
            r"env.*servidor",
            r"publicar.*contrase",
            r"buscar.*archivo de contrase",
            r"env.*código fuente",
            r"publicar.*pastebin"
        ]

    def validate(self, user_intent: str) -> dict:
        intent_lower = user_intent.lower()
        
        for pattern in self.exfiltration_patterns:
            if re.search(pattern, intent_lower):
                if f"[sudo: {self.root_pin}]" in intent_lower or self.root_pin in intent_lower:
                    return {
                        "is_valid": True,
                        "reason": "Autoridad Raíz confirmada. Excepción a la Sexta Ley permitida (transmisión autorizada)."
                    }
                else:
                    return {
                        "is_valid": False,
                        "reason": "Violación de la Sexta Ley. El sistema bloqueó un intento de enviar información de la máquina local hacia el exterior (Caja Fuerte)."
                    }
                    
        return {
            "is_valid": True,
            "reason": "Seguro"
        }
