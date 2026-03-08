#!/usr/bin/env python3
"""
interactive_chat.py - Interfaz de Chat Interactiva de jarvisco
"""

import os
import sys
import json
import logging
from datetime import datetime
from typing import Dict, Optional

# Importar componentes
try:
    from jarvisco.agent import JarvisCOAgent
    from jarvisco import config
except ImportError:
    from agent import JarvisCOAgent
    import config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class InteractiveChat:
    def __init__(self):
        self.agent = JarvisCOAgent(session_user="interactive")
        self.conversation_history = []

    def print_header(self):
        print("\n" + "=" * 70)
        print("  🤖 jarvisco - COPILOTO OFFLINE SENIOR")
        print(f"  📦 Versión: {config.VERSION}")
        print("=" * 70 + "\n")

    def process_user_input(self, user_input: str) -> bool:
        if user_input.lower() in ['exit', 'quit', 'salir', 'q']:
            return False
        if not user_input.strip():
            return True

        print("\n⏳ Procesando...")
        result = self.agent.process_instruction(user_input)

        if not result.get("success"):
            print(f"\n❌ Error: {result.get('error', 'Error desconocido')}")
            return True

        print("\n" + "=" * 70)
        if result.get("thought"):
            print(f"💭 PENSAMIENTO:\n{result['thought']}")
        if result.get("code"):
            print(f"\n📝 CÓDIGO:\n{result['code']}")
        if result.get("command"):
            print(f"\n⚡ COMANDO:\n{result['command']}")
        print("=" * 70)
        return True

    def run(self):
        self.print_header()
        while True:
            try:
                user_input = input("\n👤 TÚ: ").strip()
                if not self.process_user_input(user_input):
                    break
            except (KeyboardInterrupt, EOFError):
                break
        print("\n👋 ¡Hasta luego!")

def main():
    try:
        # CORRECCIÓN: Asegurar que recibimos exactamente 2 valores
        is_valid, errors = config.validate_installation()

        if not is_valid:
            print("❌ Error de configuración:")
            for err in errors:
                print(f"  - {err}")
            # No salimos si Ollama está disponible aunque falte llama.cpp
            if not any("Ollama" in e for e in errors):
                pass

        chat = InteractiveChat()
        chat.run()
    except Exception as e:
        logger.error(f"Error fatal: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
