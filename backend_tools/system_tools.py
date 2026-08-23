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

def read_file(path: str) -> str:
    """
    Lee un archivo del sistema local.
    """
    try:
        print(f"\n[Aletheia está leyendo archivo]: {path}")
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        return content
    except Exception as e:
        return f"Error al leer el archivo {path}: {str(e)}"

def write_file(path: str, content: str) -> str:
    """
    Escribe contenido en un archivo local (Lo crea si no existe, o lo sobrescribe).
    """
    try:
        print(f"\n[Aletheia está escribiendo archivo]: {path}")
        # Asegurarse de que el directorio existe
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"Archivo {path} escrito exitosamente."
    except Exception as e:
        return f"Error al escribir el archivo {path}: {str(e)}"
