import json
from backend_tools.system_tools import search_web, read_file, write_file
from backend_tools.universal_connector import execute_universal_action

class ToolsManager:
    def __init__(self):
        # Mapeo de nombre de función a función real de Python
        self.available_tools = {
            "search_web": search_web,
            "read_file": read_file,
            "write_file": write_file,
            "execute_universal_action": execute_universal_action
        }

    def get_tools_schema(self):
        """
        Retorna el esquema de las herramientas en formato compatible con OpenAI (Function Calling).
        """
        return [
            {
                "type": "function",
                "function": {
                    "name": "search_web",
                    "description": "Busca información en internet. REGLA ESTRICTA: NUNCA uses esta herramienta para buscar información sobre ti mismo, sobre Aletheia, sobre tus reglas o tus limitaciones éticas (esa información ya la tienes en tu cerebro). SOLO usa esto para eventos noticiosos muy recientes o datos que genuinamente desconozcas del mundo exterior.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "La consulta de búsqueda."
                            }
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "read_file",
                    "description": "Lee el contenido de un archivo en el disco local. REGLA ESTRICTA: NUNCA inventes, asumas o alucines rutas de archivos. SOLO usa esta herramienta si el usuario te proporciona explícitamente una ruta de archivo válida en su mensaje.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "Ruta absoluta o relativa del archivo a leer."
                            }
                        },
                        "required": ["path"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "write_file",
                    "description": "Escribe o sobrescribe un archivo en el disco local con el contenido especificado.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "Ruta absoluta o relativa del archivo a escribir."
                            },
                            "content": {
                                "type": "string",
                                "description": "El contenido de texto que se escribirá en el archivo."
                            }
                        },
                        "required": ["path", "content"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "execute_universal_action",
                    "description": "Ejecuta una acción en una plataforma o software externo (ej. YouTube, Gmail, Steam, Xbox). Úsala cuando el usuario te pida interactuar con otros servicios.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "platform": {
                                "type": "string",
                                "description": "Nombre de la plataforma (ej. 'youtube', 'gmail', 'steam', 'xbox')."
                            },
                            "action": {
                                "type": "string",
                                "description": "Acción a realizar (ej. 'play_music', 'read_inbox', 'launch_game')."
                            },
                            "parameters": {
                                "type": "object",
                                "description": "Diccionario JSON con parámetros específicos para la acción (ej. {'song': 'nombre'})."
                            }
                        },
                        "required": ["platform", "action", "parameters"]
                    }
                }
            }
        ]

    def execute_tool(self, tool_name: str, arguments: str) -> str:
        """
        Ejecuta la herramienta solicitada por el Cerebro y devuelve el resultado como string.
        """
        if tool_name not in self.available_tools:
            return f"[ERROR] La herramienta '{tool_name}' no existe o no está autorizada."
        
        try:
            # Los argumentos vienen en formato JSON string desde el LLM
            args_dict = json.loads(arguments)
            func = self.available_tools[tool_name]
            
            # Ejecutar la función con los argumentos desempaquetados
            result = func(**args_dict)
            return str(result)
        except Exception as e:
            return f"[ERROR AL EJECUTAR HERRAMIENTA {tool_name}]: {str(e)}"
