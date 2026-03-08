#!/usr/bin/env python3
import os
import logging
import sys
import subprocess
import json
import readline  # Para historial de comandos
from pathlib import Path

# Silenciar logs de sistema
logging.getLogger("werkzeug").setLevel(logging.ERROR)
for logger_name in ["agent", "llama_engine", "adapter", "interactive_chat", "session_manager", "analyzer"]:
    logging.getLogger(logger_name).setLevel(logging.ERROR)

VERSION = "1.0.0-senior"
AUTHOR = "Sergio Alberto Sanchez Echeverria"
PROJECT_NAME = "jarvisco"

JARVISCO_HOME = Path.home() / ".jarvisco"
CONFIG_DIR = JARVISCO_HOME / "config"
MODELS_DIR = JARVISCO_HOME / "models"
SESSIONS_DIR = JARVISCO_HOME / "sessions"
BIN_DIR = JARVISCO_HOME / "bin"

for d in [JARVISCO_HOME, CONFIG_DIR, MODELS_DIR, SESSIONS_DIR, BIN_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# Configuración del modelo
USE_OLLAMA = True
OLLAMA_MODEL_NAME = "qwen2.5-coder:1.5b"  # Para compatibilidad

if USE_OLLAMA:
    MODEL_NAME = OLLAMA_MODEL_NAME
    MODEL_PATH = None
    LLAMA_CLI = None
else:
    MODEL_NAME = None
    MODEL_PATH = MODELS_DIR / "qwen2.5-7b-instruct-q4_k_m.gguf"
    LLAMA_CLI = BIN_DIR / "llama-cli"

CONTEXT_SIZE = 4096
MAX_TOKENS = 512
TEMPERATURE = 0.2
INFERENCE_TIMEOUT = 30
SANDBOX_TIMEOUT = 30
SESSION_RETENTION_DAYS = 7

SYSTEM_PROMPT = """Eres jarvisco, un asistente de desarrollo senior con acceso total a la terminal de Termux.
CAPACIDADES:
1. Puedes ejecutar CUALQUIER comando de Bash disponible en el sistema (ls, cat, grep, sed, curl, git, pkg, etc.).
2. Puedes escribir y ejecutar scripts complejos en Python o Bash.
3. Tienes libertad total para analizar, crear y modificar archivos en el almacenamiento del usuario.

REGLAS DE ORO:
- Prioriza siempre la eficiencia: si un comando de Bash es más rápido que un script de Python, úsalo.
- Responde SIEMPRE en formato JSON: {"thought": "Tu razonamiento", "code": "Código si aplica", "command": "Comando real de Bash"}
- El campo "command" debe ser ejecutable directamente por el usuario."""

def validate_installation():
    """Valida la instalación"""
    errors = []

    if USE_OLLAMA:
        if os.system("ollama list > /dev/null 2>&1") != 0:
            errors.append("Ollama no está instalado")
        else:
            result = os.system(f"ollama show {MODEL_NAME} > /dev/null 2>&1")
            if result != 0:
                errors.append(f"Modelo {MODEL_NAME} no encontrado")

    return len(errors) == 0, errors

def execute_command(command):
    """Ejecuta un comando en la terminal y retorna el resultado"""
    try:
        print(f"\n🔧 Ejecutando: {command}")
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=SANDBOX_TIMEOUT
        )

        if result.returncode == 0:
            print("✅ Comando ejecutado con éxito")
            if result.stdout:
                print("\n📤 Salida:")
                print(result.stdout)
        else:
            print("❌ Error en la ejecución")
            if result.stderr:
                print("\n📤 Error:")
                print(result.stderr)

        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        }
    except subprocess.TimeoutExpired:
        print(f"⏰ Timeout: el comando excedió {SANDBOX_TIMEOUT} segundos")
        return {"success": False, "error": "timeout"}
    except Exception as e:
        print(f"💥 Error inesperado: {e}")
        return {"success": False, "error": str(e)}

def query_ollama(prompt):
    """Consulta a Ollama"""
    try:
        full_prompt = f"{SYSTEM_PROMPT}\n\nUsuario: {prompt}\nAsistente:"

        result = subprocess.run(
            ["ollama", "run", MODEL_NAME, full_prompt],
            capture_output=True,
            text=True,
            timeout=INFERENCE_TIMEOUT
        )

        if result.returncode == 0:
            try:
                return json.loads(result.stdout)
            except json.JSONDecodeError:
                return {"thought": "Error parsing response", "code": "", "command": ""}
        else:
            return {"thought": f"Error: {result.stderr}", "code": "", "command": ""}
    except Exception as e:
        return {"thought": f"Error: {e}", "code": "", "command": ""}

def process_input(user_input):
    """Procesa el input del usuario"""
    if user_input.lower() in ["salir", "exit", "quit"]:
        return False

    if user_input.startswith("!"):
        # Comando directo de terminal
        cmd = user_input[1:]  # Quitar el !
        execute_command(cmd)
        return True

    # Consultar al modelo
    print("\n🤔 Pensando...")
    response = query_ollama(user_input)

    print(f"\n💭 {response.get('thought', '')}")

    if response.get('code'):
        print(f"\n📝 Código sugerido:\n{response['code']}")

    if response.get('command'):
        # Preguntar antes de ejecutar
        print(f"\n🔧 Comando sugerido: {response['command']}")
        confirm = input("¿Ejecutar? (s/n): ").lower()
        if confirm == 's':
            execute_command(response['command'])

    return True

def main():
    """Función principal interactiva"""
    print(f"\n{PROJECT_NAME} v{VERSION} - by {AUTHOR}")
    print("=" * 50)

    # Validar instalación
    print("Validando instalación...")
    ok, errors = validate_installation()

    if not ok:
        print("❌ Errores de instalación:")
        for error in errors:
            print(f"  • {error}")
        return 1

    print(f"✅ Usando: {'Ollama' if USE_OLLAMA else 'llama.cpp'}")
    print(f"📦 Modelo: {MODEL_NAME if USE_OLLAMA else MODEL_PATH.name}")
    print("\nComandos especiales:")
    print("  • !comando - Ejecuta comando directamente en terminal")
    print("  • salir/exit - Terminar programa")
    print("=" * 50)

    # Loop principal
    while True:
        try:
            user_input = input("\n👤 Tú: ").strip()

            if not user_input:
                continue

            if not process_input(user_input):
                break

        except KeyboardInterrupt:
            print("\n\n👋 ¡Hasta luego!")
            break
        except Exception as e:
            print(f"💥 Error: {e}")

    return 0

if __name__ == "__main__":
    sys.exit(main())
