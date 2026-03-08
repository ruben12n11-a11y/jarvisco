#!/usr/bin/env python3
"""
agent.py – Orquestador principal que coordina LLM, evaluación de riesgos y ejecución.
"""

import logging
import json
import os
import sys
from typing import Dict, Optional

from .llama_engine import LlamaCppEngine
from .session_manager import SessionManager
from .adapter import JarvisCOAdapter
from .sandbox_executor import SandboxExecutor, SandboxResult
from .qwen_handler import QwenHandler
import config

# ---------------------------------------------------------------------------
logger = logging.getLogger(__name__)


class JarvisCOAgent:
    """
    Orquestador que coordina el motor LLM, el adaptador de riesgos,
    el gestor de sesiones y la capacidad real de ejecución.
    """

    def __init__(self, session_user: str = "default", auto_confirm: bool = False):
        self.session_manager = SessionManager()
        self.engine = LlamaCppEngine()
        self.adapter = JarvisCOAdapter()
        self.sandbox = SandboxExecutor()
        self.qwen_handler = QwenHandler()

        self.user_id = session_user
        self.session_id = self.session_manager.create_session()
        self.auto_confirm = auto_confirm

        self.workspace = os.path.expanduser("~/jarvisco_workspace")
        os.makedirs(self.workspace, exist_ok=True)

        logger.info(f"✅ Agente inicializado – Sesión: {self.session_id}")
        logger.info(f"📁 Workspace: {self.workspace}")

    # -----------------------------------------------------------------------
    # ---------- EJECUCIÓN DE COMANDOS ------------------------------------
    def execute_command(self, command: str, risk_level: str) -> Dict:
        """Ejecuta un comando de shell dentro del workspace."""
        logger.info(f"⚙️ Ejecutando comando: {command}")

        try:
            timeout = 5 if risk_level == "LOW" else 30
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=self.workspace,
            )
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
                "command": command,
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": f"Timeout después de {timeout} segundos",
                "command": command,
            }
        except Exception as exc:
            return {"success": False, "error": str(exc), "command": command}

    # -----------------------------------------------------------------------
    # ---------- EJECUCIÓN DE CÓDIGO ---------------------------------------
    def execute_code(self, code: str, language: str = "python") -> Dict:
        """Ejecuta código en el lenguaje indicado mediante el sandbox."""
        logger.info(f"⚙️ Ejecutando código ({language})")
        result: SandboxResult = self.sandbox.execute(code, language)
        return {
            "success": result.success,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.exit_code,
            "execution_time": result.execution_time,
            "error": result.error_message,
            "language": language,
        }

    # -----------------------------------------------------------------------
    # ---------- PROCESADO DE INSTRUCCIONES --------------------------------
    def process_instruction(self, instruction: str) -> Dict:
        """
        Envía la instrucción al LLM, interpreta la respuesta y evalúa riesgos.
        Devuelve un dict con campos:
        thought, code, command, risk_level, risk_description, requires_confirmation
        """
        if not instruction:
            return {"success": False, "error": "Instrucción vacía"}

        # Obtener contexto resumido
        context = self.session_manager.get_context_summary(self.session_id)

        # Llamada al modelo
        llm_response = self.engine.generate_json(prompt=instruction, context_summary=context)

        # Si la respuesta no contiene los campos esperados, intentar repararla
        if not all(k in llm_response for k in ("thought", "code", "command")):
            # usar el reparador del handler
            cleaned = self.qwen_handler.parse_json_response(
                self.qwen_handler.extract_response(str(llm_response))
            )
            llm_response = cleaned

        thought = llm_response.get("thought", "")
        code = llm_response.get("code", "")
        command = llm_response.get("command", "")

        risk_level = "LOW"
        risk_description = ""
        requires_confirmation = False

        if command:
            risk_level, risk_description = self.adapter.evaluate_command(command)
            requires_confirmation = self.adapter.should_confirm(risk_level)
        elif code:
            # Detectar lenguaje (por ahora solo python, bash o js)
            language = "python"
            if "#!/bin/bash" in code:
                language = "bash"
            elif "function" in code and "console.log" in code:
                language = "javascript"
            risk_level, risk_description = self.adapter.evaluate_code(
                code, language=language
            )
            requires_confirmation = self.adapter.should_confirm(risk_level)

        # Guardar interacción completa en la sesión
        self.session_manager.add_interaction(
            self.session_id, instruction, json.dumps(llm_response, ensure_ascii=False)
        )

        return {
            "success": True,
            "thought": thought,
            "code": code,
            "command": command,
            "risk_level": risk_level,
            "risk_description": risk_description,
            "requires_confirmation": requires_confirmation,
        }

    # -----------------------------------------------------------------------
    # ---------- PROCESO COMPLETO (con confirmación y ejecución) ----------
    def process_and_execute(
        self, instruction: str, confirm_callback: Optional[callable] = None
    ) -> Dict:
        """
        1️⃣ Procesa la instrucción (LLM + riesgo)
        2️⃣ Pregunta al usuario si es necesario
        3️⃣ Ejecuta (comando o código) y guarda el resultado
        """
        result = self.process_instruction(instruction)
        if not result.get("success"):
            return result

        # 2️⃣ Confirmación
        if result["requires_confirmation"] and not self.auto_confirm:
            if confirm_callback:
                confirmed = confirm_callback(result)
            else:
                print(f"\n⚠️ {result['risk_description']}")
                answer = input("¿Ejecutar de todas formas? (s/n): ").strip().lower()
                confirmed = answer == "s"

            if not confirmed:
                return {
                    **result,
                    "executed": False,
                    "execution_result": None,
                    "message": "Ejecución cancelada por el usuario",
                }

        # 3️⃣ Ejecución propiamente dicha
        execution_result = None
        if result.get("command"):
            execution_result = self.execute_command(
                result["command"], result["risk_level"]
            )
        elif result.get("code"):
            language = "python"
            if "#!/bin/bash" in result["code"]:
                language = "bash"
            elif "function" in result["code"] and "console.log" in result["code"]:
                language = "javascript"
            execution_result = self.execute_code(result["code"], language)

        # Guardar el resultado de la ejecución en la sesión
        if execution_result is not None:
            self.session_manager.add_interaction(
                self.session_id,
                f"RESULTADO: {json.dumps(execution_result, ensure_ascii=False)}",
                instruction,
            )

        return {
            **result,
            "executed": True,
            "execution_result": execution_result,
        }

    # -----------------------------------------------------------------------
    def finalize(self) -> None:
        """Limpieza de recursos (por ahora solo llama al engine si tiene cleanup)."""
        if hasattr(self.engine, "cleanup"):
            self.engine.cleanup()
