import re

# Mapa de idiomas soportados (nombre en español/inglés -> código ISO)
LANGUAGE_MAP = {
    # Idiomas principales
    "turco": "tr", "turkish": "tr",
    "inglés": "en", "ingles": "en", "english": "en",
    "español": "es", "spanish": "es",
    "francés": "fr", "frances": "fr", "french": "fr",
    "alemán": "de", "aleman": "de", "german": "de",
    "italiano": "it", "italian": "it",
    "portugués": "pt", "portugues": "pt", "portuguese": "pt",
    "ruso": "ru", "russian": "ru",
    "chino": "zh-CN", "chinese": "zh-CN",
    "japonés": "ja", "japones": "ja", "japanese": "ja",
    "coreano": "ko", "korean": "ko",
    "árabe": "ar", "arabe": "ar", "arabic": "ar",
    "hindi": "hi",
    "holandés": "nl", "holandes": "nl", "dutch": "nl",
    "polaco": "pl", "polish": "pl",
    "sueco": "sv", "swedish": "sv",
    "noruego": "no", "norwegian": "no",
    "finlandés": "fi", "finlandes": "fi", "finnish": "fi",
    "griego": "el", "greek": "el",
    "hebreo": "he", "hebrew": "he",
    "vietnamita": "vi", "vietnamese": "vi",
    "tailandés": "th", "tailandes": "th", "thai": "th",
    "indonesio": "id", "indonesian": "id",
    "rumano": "ro", "romanian": "ro",
    "húngaro": "hu", "hungaro": "hu", "hungarian": "hu",
    "checo": "cs", "czech": "cs",
    "catalán": "ca", "catalan": "ca",
    "ucraniano": "uk", "ukrainian": "uk",
}

# Patrones para detectar si el usuario pide un idioma específico
LANGUAGE_PATTERNS = [
    r"en idioma (\w+)",
    r"en (\w+) por favor",
    r"en (\w+)$",
    r"in (\w+) please",
    r"in (\w+)$",
    r"traducido al (\w+)",
    r"translated to (\w+)",
    r"escríbelo en (\w+)",
    r"responde en (\w+)",
]


def detect_target_language(user_prompt: str) -> str | None:
    """
    Detecta si el usuario pidió un idioma específico en su mensaje.
    Retorna el código ISO del idioma o None si no detectó ninguno.
    """
    prompt_lower = user_prompt.lower()
    for pattern in LANGUAGE_PATTERNS:
        match = re.search(pattern, prompt_lower)
        if match:
            lang_word = match.group(1).strip()
            lang_code = LANGUAGE_MAP.get(lang_word)
            if lang_code and lang_code != "es":  # No traducir si pide español
                return lang_code
    return None


def translate_text(text: str, target_lang: str) -> str:
    """
    Traduce el texto al idioma de destino usando deep-translator (Google Translate).
    Retorna el texto original si falla.
    """
    try:
        from deep_translator import GoogleTranslator
        # Google Translate tiene límite de ~5000 chars por petición
        # Si el texto es largo, lo dividimos en párrafos
        if len(text) <= 4500:
            translated = GoogleTranslator(source="auto", target=target_lang).translate(text)
            return translated if translated else text
        else:
            # Dividir por párrafos y traducir por partes
            paragraphs = text.split("\n\n")
            translated_parts = []
            for para in paragraphs:
                if para.strip():
                    try:
                        t = GoogleTranslator(source="auto", target=target_lang).translate(para)
                        translated_parts.append(t if t else para)
                    except Exception:
                        translated_parts.append(para)
            return "\n\n".join(translated_parts)
    except ImportError:
        return text  # Si no está instalado, retorna original
    except Exception:
        return text  # Si falla la traducción, retorna original
