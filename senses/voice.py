"""
Módulo de Voz de Aletheia — Text-to-Speech (TTS).
Usa edge-tts (Motor de Microsoft Edge, gratuito, voces naturales, multilingüe).
Solo se activa cuando el usuario habló por micrófono.
"""

import asyncio
import os
import tempfile

# Mapa de idioma → voz de Edge TTS
VOICE_MAP = {
    "es": "es-CO-GonzaloNeural",     # Español colombiano (acento neutro)
    "en": "en-US-AriaNeural",         # Inglés americano, femenina y natural
    "fr": "fr-FR-DeniseNeural",       # Francés
    "de": "de-DE-KatjaNeural",        # Alemán
    "it": "it-IT-ElsaNeural",         # Italiano
    "pt": "pt-BR-FranciscaNeural",    # Portugués brasileño
    "tr": "tr-TR-AhmetNeural",        # Turco
    "ru": "ru-RU-SvetlanaNeural",     # Ruso
    "ar": "ar-SA-ZariyahNeural",      # Árabe
    "ja": "ja-JP-NanamiNeural",       # Japonés
    "ko": "ko-KR-SunHiNeural",        # Coreano
    "zh": "zh-CN-XiaoxiaoNeural",     # Chino mandarín
    "nl": "nl-NL-ColetteNeural",      # Holandés
    "pl": "pl-PL-AgnieszkaNeural",    # Polaco
}

DEFAULT_VOICE = "es-CO-GonzaloNeural"


def get_voice_for_language(lang_code: str) -> str:
    """Retorna la voz de Edge TTS correspondiente al idioma."""
    # Normalizar código (ej: "es-CO" → "es")
    base_lang = lang_code.split("-")[0].lower() if lang_code else "es"
    return VOICE_MAP.get(base_lang, DEFAULT_VOICE)


async def _synthesize_async(text: str, voice: str, output_path: str):
    """Sintetiza el texto a audio y lo guarda en output_path."""
    import edge_tts
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_path)


def speak(text: str, language: str = "es"):
    """
    Convierte el texto a voz y lo reproduce.
    Args:
        text: El texto a leer en voz alta.
        language: Código ISO del idioma (ej: "es", "en", "tr").
    """
    try:
        voice = get_voice_for_language(language)
        
        # Generar archivo de audio temporal
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
            tmp_path = tmp.name
        
        # Sintetizar voz
        asyncio.run(_synthesize_async(text, voice, tmp_path))
        
        # Reproducir con pygame
        import pygame
        pygame.mixer.init()
        pygame.mixer.music.load(tmp_path)
        pygame.mixer.music.play()
        
        # Esperar a que termine la reproducción
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
        
        pygame.mixer.quit()
        
        # Limpiar archivo temporal
        try:
            os.unlink(tmp_path)
        except Exception:
            pass
            
    except Exception as e:
        print(f"  [Voz] Error al sintetizar o reproducir: {e}")


def speak_async_safe(text: str, language: str = "es"):
    """
    Versión segura para llamar desde contextos con event loops existentes.
    """
    import threading
    thread = threading.Thread(target=speak, args=(text, language), daemon=True)
    thread.start()
    return thread
