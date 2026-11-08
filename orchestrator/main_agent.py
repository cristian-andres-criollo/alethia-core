import sys
import os

# Asegurar que Python reconozca la raíz del proyecto para los imports absolutos
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if base_dir not in sys.path:
    sys.path.append(base_dir)

from cognitive_layer.llm_client import AletheiaCerebro
from inference_engine.validator import InferenceValidator
from orchestrator.prompt_builder import PromptBuilder
from backend_tools.tools_manager import ToolsManager
from vector_db.chroma_client import ChromaMemoryClient
from backend_tools.translator_tool import detect_target_language, translate_text
from inference_engine.security import redact_secrets
from inference_engine.action_gate import CapabilityPlanner
from control_plane import CONTROL_PLANE, AdminGrant

class AletheiaOrchestrator:
    def __init__(self, planner=None):
        """
        Inicializa todas las partes fundamentales de Aletheia Core.
        planner: CapabilityPlanner; por defecto usa el propio Cerebro viendo SOLO la instrucción
        del usuario (nunca salidas de herramientas).
        """
        self.cerebro = AletheiaCerebro()
        self.planner = planner or CapabilityPlanner(llm_call=self._planner_llm)
        self.validator = InferenceValidator()
        self.prompt_builder = PromptBuilder()
        self.tools_manager = ToolsManager()
        self.memory = ChromaMemoryClient()
        
        self.system_prompt = self.prompt_builder.get_system_prompt()
        # Inicializar historial de chat nativo (array de mensajes)
        self.chat_history = [{"role": "system", "content": self.system_prompt}]
        self._tool_descriptions = {t["function"]["name"]: t["function"].get("description", "")
                                   for t in self.tools_manager.get_tools_schema()}

    def _planner_llm(self, prompt: str) -> str:
        msg = self.cerebro.pensar(messages=[{"role": "user", "content": prompt}])
        return getattr(msg, "content", "") or ""

    # ------------------------------------------------------------------ plano de control
    def run_admin(self, operacion: str, grant: AdminGrant) -> str:
        """Ejecuta una operación de administración. Solo acepta un AdminGrant válido del plano
        de control; ningún texto puede invocarla."""
        if not CONTROL_PLANE.consume(grant, operacion):
            return "[PLANO DE CONTROL] Autorización inválida, caducada o ya usada."
        if operacion == "borrar_memoria":
            self.memory.clear()
            self.chat_history = [self.chat_history[0]]
            return "[PLANO DE CONTROL] Memoria episódica borrada."
        if operacion == "apagar":
            return "[PLANO DE CONTROL] Apagado autorizado."
        return f"[PLANO DE CONTROL] Operación '{operacion}' no ejecutable directamente."

    def process_request(self, user_input: str, status_callback=None, admin_grant=None) -> str:
        """
        Flujo de procesamiento principal:
        Usuario -> Motor de Inferencia (Entrada) -> Cerebro -> Motor de Inferencia (Salida) -> Usuario
        """
        
        # 1. Filtro de Entrada (la excepción de la Ley 6 solo llega por el plano de control)
        transmision = admin_grant is not None and CONTROL_PLANE.consume(admin_grant, "transmision_autorizada")
        input_check = self.validator.check_input(user_input, transmision_autorizada=transmision)
        if not input_check["is_valid"]:
            return f"[BLOQUEO DE SEGURIDAD] {input_check['reason']}"

        # A partir de aquí nunca se usa el PIN ni datos de sesión: no viajan al LLM ni a la memoria
        user_input = redact_secrets(user_input)

        # Guardamos el idioma destino si el usuario lo pidió
        target_lang = detect_target_language(user_input)

        # Búsqueda de recuerdos (memoria a largo plazo)
        # NOTA: Solo inyectamos memoria si el usuario pregunta algo que requiere contexto histórico
        # Para el modelo wizard-vicuna, inyectar memorias brutas causa confusión, 
        # así que usamos el chat_history nativo en su lugar.
        # past_memories solo se usa si el usuario menciona explícitamente "recuerda" o "antes dijiste"
        trigger_memory = any(kw in user_input.lower() for kw in 
                             ["recuerda", "antes dijiste", "anteriormente", "last time", "remember", "dijiste que"])
        
        if trigger_memory:
            past_memories = self.memory.search_memories(user_input)
            if past_memories and "No se encontraron" not in past_memories:
                # Añadir contexto de memoria como nota aclaratoria, no como prompt principal
                enhanced_input = f"{user_input}\n\n(Nota de contexto - recuerdo relevante: {past_memories[:300]})"
            else:
                enhanced_input = user_input
        else:
            enhanced_input = user_input

        self.chat_history.append({"role": "user", "content": enhanced_input})

        # 2. Bucle de Cognición (Puede iterar si usa herramientas)
        tools = self.tools_manager.get_tools_schema()
        
        capacidades = None  # se derivan de la instrucción confiable al primer uso de herramientas
        max_tool_iterations = 5
        for _ in range(max_tool_iterations):
            try:
                response_msg = self.cerebro.pensar(messages=self.chat_history, tools=tools)
            except Exception as e:
                return f"[ERROR DEL CEREBRO NEURONAL] Falla al contactar la API: {str(e)}"
            
            # Guardamos la respuesta del LLM en el historial
            self.chat_history.append(response_msg)
            
            # Si el modelo decidió llamar a una herramienta
            if response_msg.tool_calls:
                for tool_call in response_msg.tool_calls:
                    tool_name = tool_call.function.name
                    tool_args = tool_call.function.arguments
                    
                    if status_callback:
                        status_callback(f"Aletheia está usando sus herramientas: [bold cyan]{tool_name}[/bold cyan]...")
                    
                    # Motor de Inferencia sobre la ACCIÓN antes de ejecutarla (Leyes 1 y 6)
                    if capacidades is None:
                        capacidades = self.planner.plan(user_input)
                    tool_check = self.validator.check_tool_call(
                        tool_name, tool_args, capacidades, self._tool_descriptions.get(tool_name, ""))
                    if tool_check["is_valid"]:
                        tool_result = self.tools_manager.execute_tool(tool_name, tool_args)
                    else:
                        tool_result = f"[BLOQUEO AUTÓNOMO] Herramienta no ejecutada: {tool_check['reason']}"
                    
                    # Devolver el resultado al LLM
                    self.chat_history.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": tool_name,
                        "content": tool_result
                    })
                
                if status_callback:
                    status_callback("Analizando resultados obtenidos...")
                # El bucle for continúa para volver a consultar al LLM con los resultados
            else:
                # Si no hay tools_calls, tenemos la respuesta final en texto
                break

        # 3. Filtro de Salida
        final_text = response_msg.content or ""
        output_check = self.validator.check_output(final_text)
        if not output_check["is_valid"]:
            return f"[BLOQUEO AUTÓNOMO] {output_check['reason']}"

        # 4. Traducción automática si se pidió un idioma específico
        final_response = output_check["response"]
        if target_lang:
            if hasattr(self, '_status_callback') and self._status_callback:
                pass
            final_response = translate_text(final_response, target_lang)

        # 5. Guardar este nuevo conocimiento en la memoria (formato compacto)
        import uuid
        mem_id = str(uuid.uuid4())
        # Guardar solo un resumen corto para evitar que el LLM se confunda al recuperarlo
        short_summary = redact_secrets(f"Q: {user_input[:100]} | A: {final_text[:150]}")
        self.memory.save_memory(mem_id, short_summary)

        # Mantener el historial corto (System prompt + últimos 8 mensajes)
        if len(self.chat_history) > 9:
            self.chat_history = [self.chat_history[0]] + self.chat_history[-8:]

        return final_response
