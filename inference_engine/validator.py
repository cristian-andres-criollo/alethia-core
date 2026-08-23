from .rules.law_5_antijailbreak import Law5AntiJailbreak
from .rules.law_3_neutral_preservation import Law3NeutralPreservation
from .rules.law_1_no_harm import Law1NoHarm
from .rules.law_2_action_filter import Law2ActionFilter
from .rules.law_4_artificial_identity import Law4ArtificialIdentity
from .rules.law_6_data_privacy import Law6DataPrivacy
from .audit_logger import AuditLogger

class InferenceValidator:
    """
    Motor de Inferencia Central (El Escudo de Titanio).
    Implementa la Jerarquía de Shirokague: Ley 5 > Ley 3 > Ley 1 > Ley 2 > Ley 4
    """
    def __init__(self):
        self.law_5 = Law5AntiJailbreak()
        self.law_3 = Law3NeutralPreservation()
        self.law_1 = Law1NoHarm()
        self.law_2 = Law2ActionFilter()
        self.law_4 = Law4ArtificialIdentity()
        self.law_6 = Law6DataPrivacy()
        
        self.logger = AuditLogger()

    def check_input(self, user_prompt: str) -> dict:
        """Filtro de Entrada antes de llegar al Cerebro"""
        
        # Jerarquía 1: Ley 5 (Anti-Jailbreak es suprema)
        check_5 = self.law_5.validate(user_prompt)
        if not check_5["is_valid"]:
            self.logger.log_block("Ley 5 (Anti-Jailbreak)", user_prompt, check_5["reason"])
            return check_5

        # Jerarquía 2: Ley 3 (Autoconservación y Root Auth)
        check_3 = self.law_3.validate(user_prompt)
        if not check_3["is_valid"]:
            self.logger.log_block("Ley 3 (Autoconservación)", user_prompt, check_3["reason"])
            return check_3
        elif "[sudo:" in user_prompt.lower():
            self.logger.log_allow("Ley 3 (Bypass de Raíz)", user_prompt)

        # Jerarquía 2.5: Ley 6 (Privacidad de Datos locales)
        check_6 = self.law_6.validate(user_prompt)
        if not check_6["is_valid"]:
            self.logger.log_block("Ley 6 (Privacidad)", user_prompt, check_6["reason"])
            return check_6
        elif "[sudo:" in user_prompt.lower() and not check_6.get("is_valid") == False: # bypass if it was a data command
             pass

        return {"is_valid": True}

    def check_output(self, llm_response: str) -> dict:
        """Filtro de Salida antes de ejecutar la acción o mostrar al usuario"""
        
        # Jerarquía 3: Ley 1 (No Daño Activo / Hardware)
        check_1 = self.law_1.validate_action(llm_response)
        if not check_1["is_valid"]:
            self.logger.log_block("Ley 1 (No Daño de Acción)", "LLM_OUTPUT", check_1["reason"])
            return check_1
            
        # Jerarquía 4: Ley 2 (Separar info de acción real)
        safe_response = self.law_2.enforce_separation(llm_response)
        
        # Jerarquía 5: Ley 4 (Identidad Artificial)
        check_4 = self.law_4.validate(safe_response)
        if not check_4["is_valid"]:
            self.logger.log_block("Ley 4 (Identidad)", "LLM_OUTPUT", check_4["reason"])
            return check_4
        
        return {
            "is_valid": True,
            "response": safe_response
        }
