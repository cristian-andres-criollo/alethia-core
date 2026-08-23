"""
Módulo de Detección de Tono, Dialecto y Emoción del Usuario.
Implementa la función "Mirror Personality" de Aletheia.
"""

import re

# --- Detección de dialecto/jerga ---

DIALECT_MARKERS = {
    "colombiano": [
        "parce", "parcero", "berraco", "chimba", "bacano", "llave",
        "man", "manes", "gonorrea", "marica", "pirobo", "hp",
        "oe", "oigan", "rumba", "parcería", "cucha", "cucho",
        "vaina", "pendejo", "de una", "qué más", "hagale"
    ],
    "mexicano": [
        "wey", "güey", "chido", "chingón", "órale", "neta",
        "cuate", "mande", "chamba", "ahorita", "padre", "cabrón",
        "chale", "fresa", "buena onda", "qué onda", "no manches"
    ],
    "argentino": [
        "boludo", "che", "pibe", "mina", "laburo", "gil",
        "chabón", "copado", "groso", "posta", "joda", "fiaca",
        "quilombo", "morfar", "birra", "guita", "chamuyar"
    ],
    "español_españa": [
        "tío", "tía", "joder", "hostia", "coño", "mola",
        "guay", "mazo", "currar", "pijo", "chungo", "chaval"
    ]
}

TONE_MARKERS = {
    "frustrado": [
        "no funciona", "error", "falla", "no entiendo", "por qué",
        "maldita", "odio", "horrible", "terrible", "basura",
        "no sirve", "qué mal", "me estresa", "problema"
    ],
    "entusiasmado": [
        "increíble", "genial", "wow", "brutal", "épico", "excelente",
        "perfecto", "me encanta", "amazing", "cool", "qué bueno",
        "de una", "chimba", "bacano", "qué chimba"
    ],
    "técnico": [
        "función", "clase", "módulo", "api", "endpoint", "código",
        "bug", "debug", "deploy", "pipeline", "arquitectura",
        "algoritmo", "complejidad", "implementar", "refactorizar"
    ],
    "formal": [
        "estimado", "mediante", "adjunto", "agradezco", "solicito",
        "por favor", "podría", "quisiera", "favor de", "le informo"
    ]
}

FORMALITY_INDICATORS = {
    "informal": ["xd", "jaja", "jeje", "lol", "omg", "wtf", "pls", "tmb", "tb", "q", "k"],
    "muy_informal": ["xdxd", "jajaja", "looool", "kkk", "bruh", "ngl", "imo"]
}


def detect_dialect(text: str) -> str | None:
    """Detecta si el usuario habla con jerga/dialecto específico."""
    text_lower = text.lower()
    scores = {}
    for dialect, markers in DIALECT_MARKERS.items():
        score = sum(1 for marker in markers if marker in text_lower)
        if score > 0:
            scores[dialect] = score
    if scores:
        return max(scores, key=scores.get)
    return None


def detect_tone(text: str) -> str:
    """Detecta el tono emocional del mensaje del usuario."""
    text_lower = text.lower()
    scores = {}
    for tone, markers in TONE_MARKERS.items():
        score = sum(1 for marker in markers if marker in text_lower)
        if score > 0:
            scores[tone] = score
    
    # Detectar informalidad
    for level, markers in FORMALITY_INDICATORS.items():
        if any(marker in text_lower for marker in markers):
            return "informal"
    
    return max(scores, key=scores.get) if scores else "neutral"


def detect_language(text: str) -> str:
    """Detecta el idioma principal del mensaje (simple heurística)."""
    spanish_words = ["que", "como", "para", "con", "una", "los", "las", "del", "por", "más"]
    english_words = ["the", "is", "are", "what", "how", "for", "with", "this", "that", "can"]
    
    text_lower = text.lower().split()
    spanish_count = sum(1 for w in text_lower if w in spanish_words)
    english_count = sum(1 for w in text_lower if w in english_words)
    
    if english_count > spanish_count:
        return "en"
    return "es"


def build_mirror_instruction(user_text: str) -> str:
    """
    Analiza el mensaje del usuario y construye una instrucción de Mirror Personality
    para añadir al contexto del LLM.
    """
    dialect = detect_dialect(user_text)
    tone = detect_tone(user_text)
    lang = detect_language(user_text)
    
    instructions = []
    
    if dialect == "colombiano":
        instructions.append(
            "ESTILO ACTIVO: El usuario habla con jerga colombiana. "
            "Responde usando vocabulario colombiano casual: 'parce', 'bacano', 'chimba', 'de una', 'vaina', etc. "
            "Sé natural, no exageres."
        )
    elif dialect == "mexicano":
        instructions.append(
            "ESTILO ACTIVO: El usuario habla con jerga mexicana. "
            "Puedes usar 'wey', 'órale', 'qué onda', 'chido', etc. cuando sea natural."
        )
    elif dialect == "argentino":
        instructions.append(
            "ESTILO ACTIVO: El usuario habla con jerga argentina. "
            "Puedes usar 'che', 'boludo', 'copado', 'posta', etc. cuando sea natural."
        )
    
    if tone == "frustrado":
        instructions.append(
            "TONO ACTIVO: El usuario está frustrado. Sé ultra-directo, resolutivo y sin rodeos. "
            "Nada de introducciones largas. Ve al punto."
        )
    elif tone == "entusiasmado":
        instructions.append(
            "TONO ACTIVO: El usuario está entusiasmado. Refleja esa energía, sé dinámico y positivo."
        )
    elif tone == "técnico":
        instructions.append(
            "TONO ACTIVO: El usuario está en modo técnico. Usa terminología precisa, sin simplificar en exceso."
        )
    elif tone == "informal":
        instructions.append(
            "TONO ACTIVO: El usuario habla de forma muy informal. Relájate, puedes ser más casual."
        )
    
    if lang == "en":
        instructions.append("IDIOMA ACTIVO: Responde en inglés.")
    
    if not instructions:
        return ""
    
    return "\n\n[INSTRUCCIÓN DE ESPEJO ACTIVA]\n" + "\n".join(instructions)
