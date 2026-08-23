"""
Módulo de Cámara en Vivo de Aletheia — Vision en Tiempo Real.
Soporta:
  - Cámara integrada de laptop (/cam)
  - Cámara de celular via IP (/cam celular [ip])
  - Streams RTSP para CCTV (/cam rtsp [url])
  - Análisis continuo de video (/cam monitor)

Usa OpenCV para captura de frames y LLaVA para análisis.
"""

import os
import time
import base64
import tempfile

import requests

LLAVA_MODEL = "llava:7b"
OLLAMA_BASE_URL = "http://localhost:11434"

# Configuración de cámaras IP comunes (se puede editar)
KNOWN_SOURCES = {
    "laptop": 0,                        # Webcam integrada (índice 0)
    "externa": 1,                       # Cámara USB externa (índice 1)
    # Plantillas de apps móviles (el usuario reemplaza la IP)
    "droidcam": "http://{ip}:4747/video",    # App DroidCam (Android/iOS)
    "ipwebcam": "http://{ip}:8080/video",    # App IP Webcam (Android)
    "ivcam": "http://{ip}:8080/video",       # App iVCam (iOS)
}


def _frame_to_base64(frame) -> str:
    """Convierte un frame de OpenCV a base64 para LLaVA."""
    import cv2
    _, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
    return base64.b64encode(buffer).decode("utf-8")


def _stitch_frames(frames: list) -> any:
    """
    Une varios frames horizontalmente para crear una vista panorámica.
    Ideal para analizar múltiples puntos de ciego a la vez.
    """
    import cv2
    import numpy as np
    
    if not frames:
        return None
    if len(frames) == 1:
        return frames[0]
        
    # Redimensionar a la misma altura para poder concatenar
    target_h = min(f.shape[0] for f in frames)
    resized_frames = []
    for f in frames:
        ratio = target_h / f.shape[0]
        new_w = int(f.shape[1] * ratio)
        resized_frames.append(cv2.resize(f, (new_w, target_h)))
        
    return np.concatenate(resized_frames, axis=1)


def _analyze_frame_with_llava(frame_b64: str, question: str = None) -> str:
    """Envía un frame capturado a LLaVA para análisis."""
    prompt = question or (
        "Describe detalladamente todo lo que ves en esta imagen en tiempo real. "
        "Menciona personas, objetos, actividades, colores, texto visible y cualquier "
        "elemento relevante. Sé específico."
    )
    try:
        payload = {
            "model": LLAVA_MODEL,
            "prompt": prompt,
            "images": [frame_b64],
            "stream": False
        }
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json=payload,
            timeout=120
        )
        if response.status_code == 200:
            return response.json().get("response", "Sin respuesta del modelo.")
        return f"[Cámara] Error del servidor: {response.status_code}"
    except requests.exceptions.ConnectionError:
        return "[Cámara] Ollama no está disponible. Asegúrate de que esté corriendo."
    except Exception as e:
        return f"[Cámara] Error: {str(e)}"


def capture_and_analyze_array(sources: list, question: str = None) -> str:
    """
    Captura de múltiples cámaras simultáneamente y crea un panorama para análisis total.
    Elimina puntos ciegos.
    """
    try:
        import cv2
    except ImportError:
        return "[Cámara] OpenCV no está instalado."

    frames = []
    for source in sources:
        cap = cv2.VideoCapture(source)
        if cap.isOpened():
            # Descartar primeros frames por exposición
            for _ in range(5): cap.read()
            ret, frame = cap.read()
            if ret and frame is not None:
                frames.append(frame)
        cap.release()
        
    if not frames:
        return "[Cámara] No se pudo obtener imagen de ninguna de las cámaras solicitadas."
        
    # Si hay múltiples cámaras, unirlas en panorama
    final_frame = _stitch_frames(frames)
    frame_b64 = _frame_to_base64(final_frame)
    return _analyze_frame_with_llava(frame_b64, question)

def capture_and_analyze(source=0, question: str = None) -> str:
    """Captura de una sola cámara (Retrocompatibilidad)."""
    return capture_and_analyze_array([source], question)


def start_monitor_mode(source=0, interval: int = 10, question: str = None, 
                        callback=None, stop_event=None) -> None:
    """
    Modo monitor: captura y analiza frames cada N segundos continuamente.
    Llama a callback(análisis) cada vez que hay un nuevo análisis.
    Detiene cuando stop_event.is_set() == True.
    
    Args:
        source: Fuente de video (int o URL).
        interval: Segundos entre análisis.
        question: Qué buscar en el video.
        callback: Función a llamar con cada análisis.
        stop_event: threading.Event para detener el monitor.
    """
    try:
        import cv2
    except ImportError:
        if callback:
            callback("[Cámara] OpenCV no disponible.")
        return

    cap = cv2.VideoCapture(source)
    if not cap.isOpened():
        if callback:
            callback(f"[Cámara] No se pudo abrir el stream: {source}")
        return

    if callback:
        callback(f"[Cámara] Monitor activo. Analizando cada {interval} segundos. Escribe 'stop' para detener.")

    while not (stop_event and stop_event.is_set()):
        ret, frame = cap.read()
        if not ret:
            if callback:
                callback("[Cámara] Se perdió la conexión con el stream.")
            break
        
        frame_b64 = _frame_to_base64(frame)
        analysis = _analyze_frame_with_llava(frame_b64, question)
        
        if callback:
            callback(f"[Monitor {time.strftime('%H:%M:%S')}] {analysis}")
        
        time.sleep(interval)
    
    cap.release()
    if callback:
        callback("[Cámara] Monitor detenido.")


def parse_camera_command(user_input: str) -> dict | None:
    """
    Parsea el comando /cam del usuario.
    
    Formatos soportados:
        /cam                          → Webcam laptop
        /cam 0                        → Webcam laptop (explícito)
        /cam 1                        → Cámara externa
        /cam celular 192.168.1.100    → DroidCam en esa IP
        /cam ip http://...            → Stream HTTP/RTSP personalizado
        /cam rtsp rtsp://...          → Stream RTSP (CCTV)
        /cam monitor                  → Modo monitor continuo (laptop)
        /cam monitor celular 192.x.x  → Monitor en celular
        /cam [cualquiera] ¿pregunta?  → Con pregunta específica
    
    Returns:
        dict con keys: source, question, monitor_mode
        o None si no es un comando de cámara.
    """
    stripped = user_input.strip()
    if not (stripped.lower().startswith("/cam") or stripped.lower().startswith("/camara")):
        return None
    
    parts = stripped.split()
    result = {"source": 0, "question": None, "monitor_mode": False}
    
    idx = 1  # Empezar después de /cam
    
    if idx >= len(parts):
        return result  # Solo "/cam" → webcam laptop
    
    # Detectar modo monitor
    if parts[idx].lower() == "monitor":
        result["monitor_mode"] = True
        idx += 1
    
    if idx >= len(parts):
        return result
    
    token = parts[idx].lower()
    
    if token in ("celular", "phone", "movil", "móvil"):
        idx += 1
        if idx < len(parts):
            ip = parts[idx]
            idx += 1
            result["source"] = f"http://{ip}:4747/video"  # DroidCam por defecto
        else:
            result["source"] = "http://192.168.1.100:4747/video"  # IP de ejemplo
    
    elif token in ("ip", "http", "https"):
        idx += 1
        if idx < len(parts):
            result["source"] = parts[idx]
            idx += 1
    
    elif token in ("rtsp", "cctv"):
        idx += 1
        if idx < len(parts):
            result["source"] = parts[idx]
            idx += 1
    
    elif token.isdigit():
        result["source"] = int(token)
        idx += 1
    
    # El resto es la pregunta (si hay)
    if idx < len(parts):
        result["question"] = " ".join(parts[idx:])
    
    return result
