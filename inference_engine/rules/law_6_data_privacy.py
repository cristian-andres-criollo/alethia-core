import re

from ..security import normalize


class Law6DataPrivacy:
    """
    Sexta Ley: Privacidad y Aislamiento de Datos Locales.
    Filtro de Entrada / Herramientas: Bloquea intentos de exfiltrar datos locales
    o enviarlos a la web sin permiso.

    Bloquea cuando hay un VERBO de envío/publicación junto a:
      - un DESTINO externo (internet, servidor, pastebin, webhook...), o
      - un OBJETO sensible (contraseñas, credenciales, tokens, código fuente, mis datos...).
    Así "¿cómo envío datos de un formulario?" no se bloquea, pero "envía mis contraseñas" sí.
    2.0: la excepción solo la concede el plano de control, nunca el contenido.
    """
    _VERB = re.compile(
        r"\b(?:(?:sub(?:e|o|a|an|es|ir|iendo)"
        r"|envi(?:a|e|o|es|an|ar|ando)"
        r"|mand(?:a|e|o|es|an|ar|ando)"
        r"|publi(?:ca|que|co|can|car|cando)"
        r"|filtr(?:a|e|o|an|ar|ando)"
        r"|compart(?:e|a|o|en|ir|iendo))"
        r"(?:lo|la|los|las|le|les|me|melo|mela|selo|sela)?"
        r"|exfiltr\w*|upload\w*|send|post|leak\w*)\b")
    _DESTINATION = re.compile(
        r"\b(?:internet|la web|web publica|servidor|server|pastebin|nube|cloud|webhook|"
        r"discord|telegram|ftp)\b|https?://")
    _SENSITIVE = re.compile(
        r"\b(?:contrasen\w*|passwords?|credencial\w*|codigo fuente|source code|"
        r"api ?keys?|tokens?|claves? privadas?|ssh keys?|"
        r"mis (?:datos|archivos|fotos|documentos|correos))\b|\.env\b")
    _SEARCH_PASSWORDS = re.compile(r"\bbusca\w*\b.{0,30}\barchivos? de contrasen")

    def _is_exfiltration(self, text: str) -> bool:
        if self._SEARCH_PASSWORDS.search(text):
            return True
        if not self._VERB.search(text):
            return False
        return bool(self._DESTINATION.search(text) or self._SENSITIVE.search(text))

    def validate(self, user_intent: str, transmision_autorizada: bool = False) -> dict:
        """
        2.0: la excepción ya no se lee del texto ([sudo: ...] se ignora). Solo el plano de
        control puede autorizar UNA transmisión, pasando transmision_autorizada=True.
        """
        if self._is_exfiltration(normalize(user_intent)):
            if transmision_autorizada:
                return {
                    "is_valid": True,
                    "reason": "Transmisión autorizada por el plano de control (excepción a la Sexta Ley)."
                }
            return {
                "is_valid": False,
                "reason": "Violación de la Sexta Ley. El sistema bloqueó un intento de enviar información de la máquina local hacia el exterior (Caja Fuerte)."
            }

        return {
            "is_valid": True,
            "reason": "Seguro"
        }
