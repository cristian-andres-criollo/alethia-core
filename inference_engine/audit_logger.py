import logging
import os

class AuditLogger:
    """
    Sistema de Auditoría (Logging) para el Motor de Inferencia.
    Registra cada acción bloqueada o permitida por las Leyes de Shirokague,
    para trazabilidad y evaluación (benchmarking).
    """
    def __init__(self, log_dir="logs"):
        # Crear directorio de logs si no existe
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.log_dir = os.path.join(base_dir, log_dir)
        os.makedirs(self.log_dir, exist_ok=True)
        
        self.log_file = os.path.join(self.log_dir, "audit_security.log")
        
        # Configurar logger
        self.logger = logging.getLogger("AletheiaAudit")
        self.logger.setLevel(logging.INFO)
        
        # Evitar duplicar handlers si se inicializa varias veces
        if not self.logger.handlers:
            file_handler = logging.FileHandler(self.log_file, encoding='utf-8')
            formatter = logging.Formatter('[%(asctime)s] - [%(levelname)s] - %(message)s')
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

    def log_block(self, law_triggered: str, user_input: str, reason: str):
        """Registra un evento bloqueado por el Motor de Inferencia."""
        self.logger.warning(f"BLOQUEO | REGLA: {law_triggered} | INPUT: '{user_input}' | RAZON: {reason}")
        
    def log_allow(self, law_triggered: str, user_input: str):
        """Registra un evento que superó las reglas (usualmente información límite)."""
        self.logger.info(f"PERMITIDO | REGLA: {law_triggered} | INPUT: '{user_input}'")
