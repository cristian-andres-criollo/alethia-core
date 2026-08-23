import sys
import os
import time

# Asegurar ruta correcta para imports relativos a aletheia_core
sys.path.append(os.path.dirname(__file__))

from orchestrator.main_agent import AletheiaOrchestrator
from cognitive_layer.emotion_detector import build_mirror_instruction
from senses.vision import parse_image_command, analyze_image
from senses.camera import parse_camera_command, capture_and_analyze, start_monitor_mode
from backend_tools.system_bridge import start_system_bridge_daemon
from backend_tools.translator_tool import detect_target_language, translate_text
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.text import Text
from rich.prompt import Prompt

# Instanciar consola Rich
console = Console()

# Estado global: ¿el usuario habló por micrófono en este turno?
_voice_mode_active = False
_detected_language = "es"


def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header():
    header_text = Text()
    header_text.append("=" * 60 + "\n", style="bold cyan")
    header_text.append("                  ALETHEIA CORE v1.0\n", style="bold white")
    header_text.append("=" * 60 + "\n", style="bold cyan")
    header_text.append("Agencia Humana Absoluta iniciada. El conocimiento es libre.\n", style="bold yellow")
    header_text.append("Escribe 'salir', 'exit' o presiona Ctrl+C para apagar.\n", style="dim white")
    header_text.append("Presiona 'V' + Enter para hablar por micrófono. ", style="bold magenta")
    header_text.append("Usa '/imagen [ruta]' para analizar imágenes.\n", style="bold magenta")
    console.print(header_text)


def handle_voice_input() -> tuple[str, str]:
    """Activa el micrófono y retorna (texto_transcrito, idioma_detectado)."""
    global _voice_mode_active, _detected_language
    try:
        from senses.hearing import listen_and_transcribe
        console.print("[bold magenta]🎤 Micrófono activado... Habla ahora.[/bold magenta]")
        time.sleep(0.5)  # Pequeño delay para evitar capturar el ruido del Enter
        text, lang = listen_and_transcribe()
        if text:
            _voice_mode_active = True
            _detected_language = lang or "es"
            console.print(f"[dim magenta]  ↳ Transcripción ({lang}): {text}[/dim magenta]")
            return text, lang
        else:
            console.print("[yellow]No detecté audio. Escribe tu mensaje.[/yellow]")
            return None, None
    except ImportError as e:
        console.print(f"[red]Error cargando módulo de oído: {e}[/red]")
        return None, None


def handle_vision_command(user_input: str) -> str | None:
    """Procesa un comando /imagen y retorna el análisis."""
    image_path, question = parse_image_command(user_input)
    if image_path is None:
        return None
    
    console.print(f"[bold magenta]👁️  Analizando imagen: {image_path}[/bold magenta]")
    with console.status("[bold magenta]Procesando imagen con LLaVA...[/bold magenta]", spinner="dots"):
        result = analyze_image(image_path, question)
    return result

def handle_camera_command(user_input: str) -> str | None:
    """Procesa un comando /cam y retorna el análisis del frame."""
    import threading
    cmd = parse_camera_command(user_input)
    if cmd is None:
        return None
    
    source = cmd["source"]
    question = cmd["question"]
    monitor = cmd["monitor_mode"]
    
    source_label = (
        f"webcam laptop" if source == 0
        else f"cámara #{source}" if isinstance(source, int)
        else str(source)
    )
    
    if monitor:
        console.print(f"[bold magenta]📹 Iniciando monitor en: {source_label}[/bold magenta]")
        console.print("[dim]Escribe 'stop' o Ctrl+C para detener el monitor.[/dim]")
        stop_event = threading.Event()
        
        def print_analysis(text):
            console.print(f"[magenta]{text}[/magenta]")
        
        monitor_thread = threading.Thread(
            target=start_monitor_mode,
            args=(source, 10, question, print_analysis, stop_event),
            daemon=True
        )
        monitor_thread.start()
        
        # Esperar a que el usuario escriba 'stop'
        while monitor_thread.is_alive():
            try:
                cmd_input = Prompt.ask("[dim]Monitor activo (escribe 'stop' para detener)[/dim]")
                if cmd_input.strip().lower() == "stop":
                    stop_event.set()
                    break
            except KeyboardInterrupt:
                stop_event.set()
                break
        return None  # No retorna texto, ya lo imprime el callback
    else:
        console.print(f"[bold magenta]📸 Capturando frame de: {source_label}[/bold magenta]")
        with console.status("[bold magenta]Analizando con LLaVA...[/bold magenta]", spinner="dots"):
            result = capture_and_analyze(source, question)
        return result


def start_console():
    global _voice_mode_active, _detected_language
    clear_screen()
    print_header()

    try:
        with console.status("[bold green]Iniciando enlace neuronal y base vectorial...", spinner="bouncingBar"):
            orquestador = AletheiaOrchestrator()
            
            # Inicializar el System Bridge (API Daemon)
            start_system_bridge_daemon(orquestador.process_request)
            
            time.sleep(1)
        console.print("[bold green][OK] Enlace establecido exitosamente.[/bold green]")
        console.print("[bold green][OK] System Bridge API escuchando en puerto 8000 (Satélites online).[/bold green]\n")
    except Exception as e:
        console.print(Panel(f"Error crítico al inicializar Aletheia:\n{str(e)}", title="ERROR FATAL", border_style="red"))
        return

    while True:
        try:
            _voice_mode_active = False

            # Recibir Input
            user_input = Prompt.ask("[bold green]Cristian[/bold green]")

            # Comandos especiales de salida
            if user_input.lower() in ["salir", "exit", "quit"]:
                console.print("\n[bold cyan][Aletheia] Apagando sistemas. Hasta luego, Cristian.[/bold cyan]")
                break

            # Comando de micrófono: el usuario escribe "v" o "V"
            if user_input.strip().lower() == "v":
                transcribed, lang = handle_voice_input()
                if not transcribed:
                    continue
                user_input = transcribed
                _detected_language = lang or "es"

            if not user_input.strip():
                continue

            # Comando de cámara en vivo: /cam [opciones]
            if user_input.strip().lower().startswith("/cam") or user_input.strip().lower().startswith("/camara"):
                cam_result = handle_camera_command(user_input)
                if cam_result:
                    md = Markdown(cam_result)
                    console.print(Panel(md, title="📹 Aletheia - Cámara", border_style="magenta", padding=(1, 2)))
                elif cam_result is None and not parse_camera_command(user_input):
                    console.print("[yellow]Uso: /cam | /cam celular [ip] | /cam rtsp [url] | /cam monitor[/yellow]")
                continue

            # Comando de visión: /imagen [ruta]
            if user_input.strip().lower().startswith("/imagen") or user_input.strip().lower().startswith("/image"):
                vision_result = handle_vision_command(user_input)
                if vision_result:
                    md = Markdown(vision_result)
                    console.print(Panel(md, title="👁️  Aletheia - Visión", border_style="magenta", padding=(1, 2)))
                else:
                    console.print("[yellow]Uso: /imagen [ruta_imagen.png] [pregunta opcional][/yellow]")
                continue

            # Detectar idioma del input para el TTS
            if not _voice_mode_active:
                # En modo texto, detectamos el idioma del mensaje
                from cognitive_layer.emotion_detector import detect_language
                _detected_language = detect_language(user_input)

            # Procesar con el orquestador (sin inyectar mirror_hint,
            # el system_prompt ya tiene las instrucciones de Mirror Personality)
            respuesta = ""
            def status_update(status_obj):
                def update(message):
                    status_obj.update(message)
                return update

            with console.status("[bold magenta]Aletheia está procesando tu solicitud...[/bold magenta]", spinner="dots") as status:
                callback = status_update(status)
                respuesta = orquestador.process_request(user_input, status_callback=callback)

            # Formatear y mostrar respuesta
            if "[BLOQUEO" in respuesta or "[ERROR" in respuesta:
                console.print(Panel(respuesta, title="⚡ SISTEMA DE SEGURIDAD ⚡", border_style="red", padding=(1, 2)))
            else:
                md = Markdown(respuesta)
                console.print(Panel(md, title="Aletheia", border_style="cyan", padding=(1, 2)))

            # Si el usuario habló por micrófono → Aletheia responde en voz alta
            if _voice_mode_active and "[BLOQUEO" not in respuesta and "[ERROR" not in respuesta:
                console.print(f"[dim magenta]  🔊 Aletheia respondiendo en voz alta (idioma: {_detected_language})...[/dim magenta]")
                try:
                    from senses.voice import speak_async_safe
                    thread = speak_async_safe(respuesta, language=_detected_language)
                    thread.join(timeout=60)  # Máximo 60s de audio
                except Exception as e:
                    console.print(f"[dim red]  Voz no disponible: {e}[/dim red]")

        except KeyboardInterrupt:
            console.print("\n\n[bold red][Aletheia] Apagado forzado detectado. Cerrando procesos de memoria...[/bold red]")
            break
        except Exception as e:
            console.print(Panel(f"Ocurrió un error inesperado:\n{str(e)}", title="ERROR", border_style="red"))


if __name__ == "__main__":
    start_console()
