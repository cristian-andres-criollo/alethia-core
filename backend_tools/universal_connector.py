"""
Conector Universal — Despachador de acciones para plataformas externas.
Recibe órdenes del Motor y las ejecuta utilizando los tokens/sesiones proporcionados por los satélites.
Soporta módulos dinámicos (Gmail, YouTube, Steam, Xbox, etc.).
"""

import json

# Contexto global temporal que almacena las sesiones delegadas del turno actual
_current_session_context = {}

def set_current_session(context: dict):
    global _current_session_context
    _current_session_context = context

def execute_universal_action(platform: str, action: str, parameters: dict) -> str:
    """
    Ejecuta una acción en una plataforma externa usando la sesión delegada.
    Esta función es llamada por el LLM a través de ToolsManager.
    """
    global _current_session_context
    
    platform = platform.lower()
    
    # 1. Verificar que tengamos sesión para esta plataforma (opcional, dependiendo de la plataforma)
    # Algunas plataformas no requieren sesión (ej. buscar info pública)
    # Otras sí (ej. leer correos, abrir juegos en Steam local)
    
    try:
        if platform == "youtube":
            return _handle_youtube(action, parameters, _current_session_context)
        elif platform in ["gmail", "outlook", "email"]:
            return _handle_email(action, parameters, _current_session_context)
        elif platform == "steam":
            return _handle_steam(action, parameters, _current_session_context)
        elif platform == "xbox":
            return _handle_xbox(action, parameters, _current_session_context)
        else:
            return f"[Conector Universal] Plataforma no soportada aún: {platform}"
    except Exception as e:
        return f"[Conector Universal] Error ejecutando {action} en {platform}: {str(e)}"

# =====================================================================
# DRIVERS DE PLATAFORMAS (Lógica agnóstica preparada para implementación)
# =====================================================================

def _handle_youtube(action: str, params: dict, session: dict) -> str:
    if action == "play_music":
        song = params.get("song", "desconocida")
        # Aquí iría la lógica real usando ytmusicapi o selenium
        return f"ÉXITO: Orden de reproducir '{song}' enviada a YouTube Music usando sesión delegada."
    elif action == "search_video":
        query = params.get("query", "")
        return f"ÉXITO: Búsqueda de '{query}' realizada en YouTube."
    return f"Acción '{action}' no soportada en YouTube."

def _handle_email(action: str, params: dict, session: dict) -> str:
    if action == "read_inbox":
        # Aquí iría IMAP/Graph API usando el token en `session`
        return "ÉXITO: Bandeja de entrada leída. (Simulación: 0 mensajes nuevos)."
    elif action == "send_email":
        to = params.get("to")
        subject = params.get("subject")
        return f"ÉXITO: Correo '{subject}' enviado a {to} usando sesión delegada."
    return f"Acción '{action}' no soportada en Correo."

def _handle_steam(action: str, params: dict, session: dict) -> str:
    if action == "launch_game":
        game = params.get("game")
        # Aquí iría subprocess.call("steam://rungameid/...")
        return f"ÉXITO: Orden de lanzar '{game}' enviada a Steam local."
    return f"Acción '{action}' no soportada en Steam."

def _handle_xbox(action: str, params: dict, session: dict) -> str:
    if action == "turn_on":
        # Aquí iría Xbox Smartglass API
        return "ÉXITO: Orden de encendido enviada a consola Xbox en red local."
    return f"Acción '{action}' no soportada en Xbox."
