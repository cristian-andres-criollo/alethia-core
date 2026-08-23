import os
from dotenv import load_dotenv
from openai import OpenAI

# Cargar variables de entorno desde el archivo .env
load_dotenv()

class AletheiaCerebro:
    def __init__(self, models=None, temperature=0.7):
        """
        Inicializa el Cerebro conectándose a la API de OpenRouter.
        Maneja una lista de modelos gratuitos con baja o nula censura por si alguno se satura.
        """
        api_key = os.getenv("OPENROUTER_API_KEY", "TU_CLAVE_AQUI")
        custom_base_url = os.getenv("CUSTOM_API_BASE")
        custom_model = os.getenv("CUSTOM_MODEL")
        
        # Si tienes tu propio servidor, usamos ese enlace, sino caemos en OpenRouter
        final_base_url = custom_base_url if custom_base_url else "https://openrouter.ai/api/v1"

        if custom_base_url and custom_model:
            self.models = [custom_model]  # Si hay server local, usamos estrictamente su modelo
        else:
            self.models = models or [
                "nousresearch/hermes-3-llama-3.1-405b:free", 
                "cognitivecomputations/dolphin-mistral-24b-venice-edition:free", 
                "qwen/qwen3-next-80b-a3b-instruct:free", 
                "meta-llama/llama-3.3-70b-instruct:free" 
            ]
        
        # Si usas un servidor local/privado, el "model" suele dar igual, pero lo mantenemos por compatibilidad.
        # En caso de que no tengas clave para tu server privado, mandamos "not-needed"
        self.temperature = temperature
        # Detectar si es un servidor local de Ollama (no soporta tools/function calling)
        self.is_local_ollama = custom_base_url is not None and ("localhost" in custom_base_url or "127.0.0.1" in custom_base_url)
        
        self.client = OpenAI(
            base_url=final_base_url,
            api_key=api_key if api_key != "TU_CLAVE_AQUI" else "not-needed",
        )

    def pensar(self, messages: list, tools=None) -> dict:
        """
        Toma una lista de mensajes, se conecta con la red neuronal y retorna el mensaje de respuesta.
        Si hay tools definidos, se los pasa al LLM.
        """
        
        last_error = None
        for model in self.models:
            try:
                extra_headers = {
                    "HTTP-Referer": "https://github.com/Shirokague-Devs",
                    "X-Title": "Aletheia Core Local",
                    "ngrok-skip-browser-warning": "true",
                    "Bypass-Tunnel-Reminder": "true"
                }
                
                kwargs = {
                    "extra_headers": extra_headers,
                    "model": model,
                    "messages": messages,
                    "temperature": self.temperature,
                    "max_tokens": 2048
                }
                
                if tools and not self.is_local_ollama:
                    kwargs["tools"] = tools
                    kwargs["tool_choice"] = "auto"

                response = self.client.chat.completions.create(**kwargs)
                return response.choices[0].message
            except Exception as e:
                last_error = str(e)
                # Atrapamos CUALQUIER error (429, 404, 502, etc.) y pasamos al siguiente modelo
                print(f"  [!] Fallo en el modelo {model}. Saltando al siguiente respaldo...")
                continue
                    
        raise Exception(f"Todos los cerebros de respaldo fallaron. Último error: {last_error}")

# ---- Bloque de Pruebas Unitarias ----
# Este bloque solo se ejecuta si corremos este archivo directamente.
if __name__ == "__main__":
    try:
        print("[*] Iniciando secuencia de conexión neuronal...")
        cerebro = AletheiaCerebro()
        print("[+] Conexión establecida con OpenRouter (Dolphin).")
        
        print("[*] Enviando pulso de prueba...")
        # Prueba sin System Prompt aún, solo para ver si responde.
        respuesta = cerebro.pensar([{"role": "user", "content": "Hola, dime en una oración corta si estás en línea."}])
        print(f"\n[Cerebro Dolphin]: {respuesta.content}")
    except Exception as e:
        print(f"[-] Error fatal de conexión: {e}")
