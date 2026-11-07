import os
from duckduckgo_search import DDGS

def search_web(query: str) -> str:
    """
    Realiza una búsqueda web utilizando DuckDuckGo y devuelve un resumen de los resultados.
    """
    try:
        print(f"\n[Aletheia está buscando en la web]: {query}")
        results = []
        with DDGS() as ddgs:
            # Obtener los 3 primeros resultados
            for r in ddgs.text(query, max_results=3):
                results.append(f"Título: {r['title']}\nEnlace: {r['href']}\nResumen: {r['body']}\n")
        
        if not results:
            return "No se encontraron resultados en la web para esta consulta."
        
        return "\n---\n".join(results)
    except Exception as e:
        return f"Falló la búsqueda web: {str(e)}"

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Archivos de secretos que la IA nunca debe leer (aunque el LLM lo pida)
_SECRET_FILE_NAMES = {".env", ".env.local", ".env.production", "id_rsa", "id_ed25519", "credentials.json"}


def get_workspace_dir() -> str:
    """Carpeta sandbox donde la IA puede escribir (ALETHEIA_WORKSPACE o <proyecto>/workspace)."""
    ws = os.getenv("ALETHEIA_WORKSPACE") or os.path.join(_BASE_DIR, "workspace")
    return os.path.realpath(ws)


def _resolve_in_workspace(path: str) -> str | None:
    """Resuelve la ruta dentro del sandbox. Retorna None si intenta salir de él."""
    ws = get_workspace_dir()
    candidate = path if os.path.isabs(path) else os.path.join(ws, path)
    real = os.path.realpath(candidate)
    try:
        if os.path.commonpath([ws, real]) != ws:
            return None
    except ValueError:  # Otra unidad en Windows
        return None
    return real


def _is_secret_file(path: str) -> bool:
    name = os.path.basename(path).lower()
    return name in _SECRET_FILE_NAMES or (name.startswith(".env.") and name != ".env.example")


def read_file(path: str) -> str:
    """
    Lee un archivo del sistema local (excepto archivos de secretos como .env).
    """
    try:
        if _is_secret_file(path):
            return f"[BLOQUEO] Lectura de '{os.path.basename(path)}' denegada: archivo de secretos protegido."
        print(f"\n[Aletheia está leyendo archivo]: {path}")
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        return content
    except Exception as e:
        return f"Error al leer el archivo {path}: {str(e)}"

def write_file(path: str, content: str) -> str:
    """
    Escribe contenido en un archivo local (Lo crea si no existe, o lo sobrescribe).
    Solo se permite dentro del sandbox (ALETHEIA_WORKSPACE); rutas relativas se ubican ahí.
    """
    try:
        target = _resolve_in_workspace(path)
        if target is None:
            return (f"[BLOQUEO] Escritura en '{path}' denegada: solo se permite escribir dentro de "
                    f"{get_workspace_dir()}")
        print(f"\n[Aletheia está escribiendo archivo]: {target}")
        # Asegurarse de que el directorio existe
        os.makedirs(os.path.dirname(target), exist_ok=True)

        with open(target, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"Archivo {path} escrito exitosamente."
    except Exception as e:
        return f"Error al escribir el archivo {path}: {str(e)}"
