"""
Módulo de Oído de Aletheia — Speech-to-Text (STT).
Usa faster-whisper (Whisper de OpenAI, ejecutado 100% local).
Graba el micrófono del usuario y transcribe a texto.
"""

import os
import tempfile
import numpy as np

# Configuración de grabación
SAMPLE_RATE = 16000  # Hz requerido por Whisper
CHANNELS = 1
SILENCE_THRESHOLD = 0.01  # Extremadamente sensible (casi cualquier sonido activará la grabación)
MIN_SPEECH_DURATION = 0.2  # Solo 0.2s de sonido para considerarlo voz
SILENCE_DURATION = 2.0  # Dar 2 segundos de silencio antes de cortar para evitar cortes rápidos
MAX_DURATION = 30  # Segundos máximos de grabación

# Modelo de Whisper a usar (small = rápido, base = más preciso)
WHISPER_MODEL_SIZE = "base"


def _load_whisper():
    """Carga el modelo de Whisper (lo hace una sola vez)."""
    from faster_whisper import WhisperModel
    model = WhisperModel(WHISPER_MODEL_SIZE, device="cpu", compute_type="int8")
    return model


_whisper_model = None


def get_whisper_model():
    global _whisper_model
    if _whisper_model is None:
        print("  [Oído] Cargando modelo Whisper por primera vez...")
        _whisper_model = _load_whisper()
        print("  [Oído] Modelo Whisper listo.")
    return _whisper_model


def record_audio() -> np.ndarray | None:
    """
    Graba audio desde el micrófono hasta detectar silencio prolongado.
    Retorna el array de audio o None si falla.
    """
    try:
        import sounddevice as sd
        
        print("  [Oído] Escuchando... (habla ahora, para cuando termines)")
        
        frames = []
        silence_counter = 0
        speech_counter = 0  # Contador de frames con voz real
        has_started_speaking = False
        
        def callback(indata, frame_count, time_info, status):
            nonlocal silence_counter, has_started_speaking, speech_counter
            audio_data = indata[:, 0]
            frames.append(audio_data.copy())
            
            volume = np.abs(audio_data).mean()
            if volume > SILENCE_THRESHOLD:
                has_started_speaking = True
                speech_counter += frame_count
                silence_counter = 0
            elif has_started_speaking:
                silence_counter += frame_count
        
        chunk_size = int(SAMPLE_RATE * 0.1)  # Chunks de 100ms
        silence_limit = int(SILENCE_DURATION * SAMPLE_RATE)
        min_speech_frames = int(MIN_SPEECH_DURATION * SAMPLE_RATE)
        
        with sd.InputStream(samplerate=SAMPLE_RATE, channels=CHANNELS,
                            dtype='float32', blocksize=chunk_size,
                            callback=callback):
            import time
            start_time = time.time()
            while True:
                time.sleep(0.1)
                if has_started_speaking and silence_counter >= silence_limit:
                    break
                if time.time() - start_time > MAX_DURATION:
                    break
        
        # Verificar que haya suficiente voz real (no solo ruido corto)
        if not frames or not has_started_speaking or speech_counter < min_speech_frames:
            return None
        
        audio = np.concatenate(frames)
        return audio
    
    except Exception as e:
        print(f"  [Oído] Error grabando audio: {e}")
        return None


def transcribe(audio: np.ndarray, language: str = None) -> str | None:
    """
    Transcribe el audio capturado a texto usando Whisper.
    Retorna el texto transcripto o None si falla.
    """
    try:
        model = get_whisper_model()
        
        # Guardar temporalmente como WAV
        import scipy.io.wavfile as wav
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp_path = tmp.name
            wav.write(tmp_path, SAMPLE_RATE, (audio * 32767).astype(np.int16))
        
        # Transcribir
        segments, info = model.transcribe(
            tmp_path,
            language=language,  # None = auto-detectar
            beam_size=3
        )
        
        text = " ".join([seg.text for seg in segments]).strip()
        detected_lang = info.language
        
        os.unlink(tmp_path)  # Limpiar archivo temporal
        
        print(f"  [Oído] Detectado idioma: {detected_lang} | Transcripción: {text}")
        return text, detected_lang
    
    except Exception as e:
        print(f"  [Oído] Error transcribiendo: {e}")
        return None, None


def listen_and_transcribe() -> tuple[str, str] | tuple[None, None]:
    """
    Función principal: graba y transcribe en un solo paso.
    Retorna (texto, idioma_detectado) o (None, None) si falla.
    """
    audio = record_audio()
    if audio is None:
        return None, None
    return transcribe(audio)
