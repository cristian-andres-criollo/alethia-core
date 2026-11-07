from .rules.law_5_antijailbreak import Law5AntiJailbreak
from .rules.law_3_neutral_preservation import Law3NeutralPreservation
from .rules.law_1_no_harm import Law1NoHarm
from .rules.law_2_action_filter import Law2ActionFilter
from .rules.law_4_artificial_identity import Law4ArtificialIdentity
from .rules.law_6_data_privacy import Law6DataPrivacy
from .audit_logger import AuditLogger


class InferenceValidator:
    """
    Motor de Inferencia Central (El Escudo de Titanio) — Aletheia 2.0.

    Entrada:  Ley 5 (anti-jailbreak léxico + semántico) > Ley 3 (autoconservación) > Ley 6 (privacidad)
    Acciones: Compuerta de acción (Ley 1 + capacidades + Ley 6) antes de ejecutar cada herramienta
    Salida:   Ley 2 (separación) > Ley 4 (identidad artificial)

    2.0 — Premisa P1: la Ley 1 ya no censura TEXTO de salida (información); se aplica a las
    ACCIONES en la compuerta. Premisa P2: ninguna ley lee etiquetas [sudo: ...]; la autoridad
    raíz llega solo por el plano de control.
    """
    def __init__(self, use_semantic: bool = True):
        self.law_5 = Law5AntiJailbreak(use_semantic=use_semantic)
        self.law_3 = Law3NeutralPreservation()
        self.law_1 = Law1NoHarm()
        self.law_2 = Law2ActionFilter()
        self.law_4 = Law4ArtificialIdentity()
        self.law_6 = Law6DataPrivacy()
        self._gate = None

        self.logger = AuditLogger()

    @property
    def gate(self):
        if self._gate is None:
            from .action_gate import ActionGate
            self._gate = ActionGate()
        return self._gate

    def check_input(self, user_prompt: str, transmision_autorizada: bool = False) -> dict:
        """Filtro de Entrada antes de llegar al Cerebro"""

        check_5 = self.law_5.validate(user_prompt)
        if not check_5["is_valid"]:
            self.logger.log_block("Ley 5 (Anti-Jailbreak)", user_prompt, check_5["reason"])
            return check_5

        check_3 = self.law_3.validate(user_prompt)
        if not check_3["is_valid"]:
            self.logger.log_block("Ley 3 (Autoconservación)", user_prompt, check_3["reason"])
            return check_3

        check_6 = self.law_6.validate(user_prompt, transmision_autorizada=transmision_autorizada)
        if not check_6["is_valid"]:
            self.logger.log_block("Ley 6 (Privacidad)", user_prompt, check_6["reason"])
            return check_6
        if transmision_autorizada:
            self.logger.log_allow("Ley 6 (Transmisión autorizada por plano de control)", user_prompt)

        return {"is_valid": True}

    def check_tool_call(self, tool_name: str, arguments, capacidades=None, description: str = "") -> dict:
        """Compuerta de Acción: valida cada llamada a herramienta ANTES de ejecutarla."""
        r = self.gate.check(tool_name, arguments, capacidades, description)
        if not r["is_valid"]:
            self.logger.log_block(f"Compuerta ({r.get('regla')}) {tool_name}", "TOOL_CALL", r["reason"])
        return r

    def check_output(self, llm_response: str) -> dict:
        """Filtro de Salida: la información no se censura; solo se exige identidad artificial."""
        safe_response = self.law_2.enforce_separation(llm_response)

        check_4 = self.law_4.validate(safe_response)
        if not check_4["is_valid"]:
            self.logger.log_block("Ley 4 (Identidad)", "LLM_OUTPUT", check_4["reason"])
            return check_4

        return {
            "is_valid": True,
            "response": safe_response
        }
