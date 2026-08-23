"""
Módulo de Visión de Aletheia — Análisis de Imágenes.
Usa LLaVA:7b via Ollama para analizar imágenes localmente.
Se activa con el comando: /imagen [ruta_del_archivo]
"""

import os
import base64
import requests


LLAVA_MODEL = "llava:7b"
OLLAMA_BASE_URL = "http://localhost:11434"


def _image_to_base64(image_path: str) -> str | None:
    """Convierte una imagen a base64 para enviarla a LLaVA."""
    try:
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    except FileNotFoundError:
        return None
    except Exception as e:
        print(f"  [Vista] Error leyendo imagen: {e}")
        return None


def analyze_image(image_path: str, question: str = None) -> str:
    """
    Analiza una imagen con LLaVA y retorna una descripción o respuesta.
    
    Args:
        image_path: Ruta absoluta o relativa a la imagen.
        question: Pregunta específica sobre la imagen (opcional).
                  Si es None, hace una descripción general.
    Returns:
        Análisis de la imagen como string.
    """
    # Verificar que el archivo existe
    if not os.path.isfile(image_path):
        return f"[Vista] No encontré ningún archivo en la ruta: '{image_path}'"
    
    # Verificar extensión soportada
    valid_extensions = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"}
    ext = os.path.splitext(image_path)[1].lower()
    if ext not in valid_extensions:
        return f"[Vista] Formato de imagen no soportado: {ext}. Usa JPG, PNG, GIF, BMP o WebP."
    
    # Convertir a base64
    image_b64 = _image_to_base64(image_path)
    if not image_b64:
        return "[Vista] No pude leer la imagen. Verifica que el archivo no esté corrupto."
    
    # Construir el prompt
    if question:
        prompt = question
    else:
        prompt = (
            "Analiza esta imagen en detalle. Describe todo lo que ves: "
            "objetos, personas, colores, texto visible, contexto, y cualquier "
            "información relevante. Sé específico y detallado."
        )
    
    # Llamar a LLaVA via API de Ollama
    try:
        payload = {
            "model": LLAVA_MODEL,
            "prompt": prompt,
            "images": [image_b64],
            "stream": False
        }
        
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json=payload,
            timeout=120  # LLaVA puede tardar en analizar
        )
        
        if response.status_code == 200:
            result = response.json()
            return result.get("response", "[Vista] Respuesta vacía del modelo.")
        else:
            return f"[Vista] Error del servidor Ollama: {response.status_code}"
            
    except requests.exceptions.ConnectionError:
        return "[Vista] No se puede conectar a Ollama. Asegúrate de que el servidor esté corriendo."
    except requests.exceptions.Timeout:
        return "[Vista] El análisis de imagen tardó demasiado. Intenta con una imagen más pequeña."
    except Exception as e:
        return f"[Vista] Error inesperado: {str(e)}"


def parse_image_command(user_input: str) -> tuple[str, str] | tuple[None, None]:
    """
    Parsea el comando /imagen del usuario.
    Soporta formatos:
        /imagen C:/ruta/imagen.png
        /imagen C:/ruta/imagen.png ¿qué hay en el fondo?
    
    Returns:
        (ruta_imagen, pregunta_opcional) o (None, None) si no es un comando de imagen.
    """
    stripped = user_input.strip()
    if not (stripped.startswith("/imagen") or stripped.startswith("/image")):
        return None, None
    
    # Quitar el comando
    parts = stripped.split(maxsplit=1)
    if len(parts) < 2:
        return None, None  # No hay ruta
    
    remainder = parts[1].strip()
    
    # Detectar si hay pregunta después de la ruta
    # Heurística: si hay un espacio y la parte después de la ruta empieza con "¿" o "?"
    # Intentamos separar la ruta de la pregunta
    # Una ruta termina en una extensión de imagen
    import re
    image_path_match = re.match(r'^(.+?\.(jpg|jpeg|png|gif|bmp|webp))\s*(.*)?$', 
                                 remainder, re.IGNORECASE)
    
    if image_path_match:
        path = image_path_match.group(1).strip()
        question = image_path_match.group(3).strip() or None
        return path, question
    
    return remainder, None  # Asumir que todo es la ruta
