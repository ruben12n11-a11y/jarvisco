#!/usr/bin/env python3
"""
qwen_handler.py – Handler específico para Qwen 2.5.
Se encarga de:
* Formatear prompts en el estilo ChatML de Qwen.
* Extraer la respuesta JSON del output crudo.
* Reparar JSON en caso de que Ollama devuelva texto malformado.
"""

import re
import json
import logging
from typing import Dict, Optional

# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class QwenHandler:
    """Handler para el modelo Qwen 2.5 (ChatML)."""

    # Tokens especiales de Qwen ------------------------------------------------
    SYSTEM_START = "<|im_start|>system"
    SYSTEM_END = "<|im_end|>"
    USER_START = "<|im_start|>user"
    USER_END = "<|im_end|>"
    ASSISTANT_START = "<|im_start|>assistant"
    ASSISTANT_END = "<|im_end|>"

    # -----------------------------------------------------------------------
    def __init__(self) -> None:
        logger.info("QwenHandler inicializado")

    # -----------------------------------------------------------------------
    def format_prompt(
        self,
        user_message: str,
        system_message: str = "",
        context: str = "",
    ) -> str:
        """
        Construye el prompt en formato ChatML de Qwen.
        """
        parts = []

        if system_message:
            parts.append(f"{self.SYSTEM_START}\n{system_message}{self.SYSTEM_END}")

        if context:
            parts.append(f"\nCONTEXTO:\n{context}")

        parts.append(f"{self.USER_START}\n{user_message}{self.USER_END}")
        # El assistant token indica al modelo que continúe la respuesta
        parts.append(self.ASSISTANT_START)

        return "\n".join(parts)

    # -----------------------------------------------------------------------
    def extract_response(self, raw_output: str) -> str:
        """
        Extrae la cadena JSON sin los tokens de ChatML.
        Busca el primer bloque `{ … }` y lo devuelve (con espacios extra eliminados).
        """
        match = re.search(r"\{.*\}", raw_output, re.DOTALL)
        if match:
            return match.group(0).strip()

        logger.debug("No se encontró JSON en la salida del modelo.")
        return raw_output.strip()

    # -----------------------------------------------------------------------
    def parse_json_response(self, response: str) -> Dict:
        """
        Convierte el texto de respuesta en un diccionario con los campos
        ``thought``, ``code`` y ``command``.
        Si el JSON está malformado se intenta repararlo.
        """
        # 1️⃣ Intento directo
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            pass

        # 2️⃣ Reparación básica (comillas simples → dobles, llave final)
        repaired = self.repair_json(response)
        if repaired:
            return repaired

        # 3️⃣ Extracción con regex (último recurso)
        data: Dict[str, str] = {}
        for field in ("thought", "code", "command"):
            m = re.search(rf'"{field}"\s*:\s*"([^"]*)"', response, re.DOTALL)
            if m:
                data[field] = m.group(1)

        if data:
            return data

        # 4️⃣ Si todo falla, devolvemos un mensaje de error estructurado
        return {
            "thought": "Error al parsear la respuesta del modelo.",
            "code": "",
            "command": "",
        }

    # -----------------------------------------------------------------------
    def repair_json(self, json_str: str) -> Optional[Dict]:
        """
        Intenta reparar JSON malformado:
        * comillas simples → dobles
        * añadir comilla de cierre si falta
        * añadir llave final si falta
        """
        # Intento directo (en caso de que solo falte una comilla)
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            pass

        # Reemplazar comillas simples
        repaired = json_str.replace("'", '"')

        # Asegurar número par de comillas
        if repaired.count('"') % 2 != 0:
            repaired += '"'

        # Asegurar llave de cierre
        if not repaired.rstrip().endswith("}"):
            repaired = repaired.rstrip() + "}"

        try:
            return json.loads(repaired)
        except json.JSONDecodeError:
            pass

        # Último recurso: extracción manual con regex (solo fields)
        data: Dict[str, str] = {}
        for field in ("thought", "code", "command"):
            m = re.search(rf'"{field}"\s*:\s*"([^"]*)"', repaired, re.DOTALL)
            if m:
                data[field] = m.group(1)

        return data if data else None

    # -----------------------------------------------------------------------
    def format_code_block(self, code: str, language: str = "") -> str:
        """Devuelve un bloque Markdown para enviar al modelo."""
        return f"```{language}\n{code}\n```"

    # -----------------------------------------------------------------------
    def extract_code_blocks(self, text: str) -> list[tuple[str, str]]:
        """
        Busca bloques de código markdown dentro de ``text``.
        Devuelve una lista de tuplas (lenguaje, código).
        """
        pattern = r"```(\w+)?\n(.*?)```"
        matches = re.findall(pattern, text, re.DOTALL)
        return [(lang or "text", code.strip()) for lang, code in matches]

    # -----------------------------------------------------------------------
    def get_system_prompt_for_task(self, task_type: str) -> str:
        """
        Plantilla de system‑prompt según el tipo de tarea.
        """
        prompts = {
            "code": """Eres un asistente de programación experto.
Genera código limpio, eficiente y bien documentado.
Responde en JSON con los campos thought, code y command.""",
            "explain": """Eres un tutor técnico experto.
Explica conceptos de forma clara y concisa.
Responde en JSON con los campos thought, code y command.""",
            "debug": """Eres un experto en debugging.
Analiza el código, identifica errores y sugiere correcciones.
Responde en JSON con los campos thought, code y command.""",
            "command": """Eres un experto en línea de comandos.
Sugiere comandos seguros y eficientes.
Responde en JSON con los campos thought, code y command.""",
            "default": """Eres un asistente de desarrollo senior.
Ayuda con programación, comandos y explicaciones técnicas.
Responde en JSON con los campos thought, code y command.""",
        }
        return prompts.get(task_type, prompts["default"])
