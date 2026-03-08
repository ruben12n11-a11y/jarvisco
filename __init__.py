#!/usr/bin/env python3
"""JarvisCO – Copiloto Offline Senior para Termux."""
import sys
import logging
from pathlib import Path

# Importar configuración y componentes del paquete
from . import config
from .interactive_chat import main as interactive_main

# Configurar logging (solo INFO para el usuario)
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def validate_installation():
    """Devuelve (bool, list[str]) indicando si la instalación es válida."""
    errors = []
    if config.USE_OLLAMA:
        if not shutil.which("ollama"):
            errors.append("Ollama no está instalado.")
        else:
            # Verificamos que el modelo exista en Ollama
            result = subprocess.run(
                ["ollama", "list"], capture_output=True, text=True
            )
            if config.OLLAMA_MODEL_NAME not in result.stdout:
                errors.append(f"Modelo {config.OLLAMA_MODEL_NAME} no encontrado en Ollama.")
    else:
        if not shutil.which(str(config.LLAMA_CLI)):
            errors.append("llama-cli no está disponible.")
    return (len(errors) == 0, errors)

def entrypoint():
    """Punto de entrada usado por `console_scripts`."""
    ok, errs = validate_installation()
    if not ok:
        logger.error("Errores de instalación:")
        for e in errs:
            logger.error(f" • {e}")
        sys.exit(1)

    logger.info(f"Usando {'Ollama' if config.USE_OLLAMA else 'llama.cpp'}")
    logger.info(f"Modelo: {config.OLLAMA_MODEL_NAME if config.USE_OLLAMA else config.MODEL_PATH.name}")

    # Lanzar la interfaz interactiva
    interactive_main()

if __name__ == "__main__":
    entrypoint()
