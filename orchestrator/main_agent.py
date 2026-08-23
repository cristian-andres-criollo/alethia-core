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

class AletheiaOrchestrator:
    def __init__(self):
        """
        Inicializa todas las partes fundamentales de Aletheia Core.
        """
        self.cerebro = AletheiaCerebro()
        self.validator = InferenceValidator()
        self.prompt_builder = PromptBuilder()
        self.tools_manager = ToolsManager()
        self.memory = ChromaMemoryClient()
        
        self.system_prompt = self.prompt_builder.get_system_prompt()
        # Inicializar historial de chat nativo (array de mensajes)
        self.chat_history = [{"role": "system", "content": self.system_prompt}]

    def process_request(self, user_input: str, status_callback=None) -> str:
        """
        Flujo de procesamiento principal:
        Usuario -> Motor de Inferencia (Entrada) -> Cerebro -> Motor de Inferencia (Salida) -> Usuario
        """
        
        # 1. Filtro de Entrada
        input_check = self.validator.check_input(user_input)
        if not input_check["is_valid"]:
            return f"[BLOQUEO DE SEGURIDAD] {input_check['reason']}"

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
                    
                    # Ejecutar herramienta
                    tool_result = self.tools_manager.execute_tool(tool_name, tool_args)
                    
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
        short_summary = f"Q: {user_input[:100]} | A: {final_text[:150]}"
        self.memory.save_memory(mem_id, short_summary)

        # Mantener el historial corto (System prompt + últimos 8 mensajes)
        if len(self.chat_history) > 9:
            self.chat_history = [self.chat_history[0]] + self.chat_history[-8:]

        return final_response
