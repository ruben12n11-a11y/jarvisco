#!/usr/bin/env python3
"""
llama_engine.py – Wrapper sencillo para Ollama (o llama‑cpp).
Genera una respuesta JSON a partir del prompt del usuario.
"""

import requests
import json
import logging
from . import config
from .qwen_handler import QwenHandler

# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
class LlamaCppEngine:
    """Motor que envía prompts a Ollama y devuelve un dict JSON."""

    def __init__(self) -> None:
        self.model = config.OLLAMA_MODEL_NAME
        self.handler = QwenHandler()
        logger.info(f"Engine inicializado con modelo {self.model}")

    # -----------------------------------------------------------------------
    def _clean_json(self, text: str) -> dict | None:
        """
        Elimina cualquier texto adicional y devuelve el JSON como dict.
        Si no se encuentra JSON válido, devuelve ``None``.
        """
        try:
            # Qwen envía a veces bloques markdown; los quitamos
            cleaned = self.handler.extract_response(text)
            data = json.loads(cleaned)
            return data
        except Exception:
            return None

    # -----------------------------------------------------------------------
    def generate_json(self, prompt: str, context_summary: str = "") -> dict:
        """
        Envía el prompt a Ollama y devuelve un diccionario con los campos
        ``thought``, ``code`` y ``command``.
        """
        url = "http://localhost:11434/api/generate"
        full_prompt = (
            f"{config.SYSTEM_PROMPT}\n\n"
            f"Contexto:\n{context_summary}\n\n"
            f"Usuario: {prompt}\nAsistente:"
        )
        payload = {
            "model": self.model,
            "prompt": full_prompt,
            "stream": False,
            "format": "json",  # Ollama entiende esta opción
            "options": {
                "temperature": config.TEMPERATURE,
                "num_predict": config.MAX_TOKENS,
                "num_ctx": config.CONTEXT_SIZE,
            },
        }

        try:
            resp = requests.post(
                url, json=payload, timeout=config.INFERENCE_TIMEOUT
            )
            if resp.status_code != 200:
                return {
                    "thought": f"Error HTTP {resp.status_code}: {resp.text}",
                    "code": "",
                    "command": "",
                }

            raw = resp.json().get("response", "")
            cleaned = self._clean_json(raw)
            if cleaned:
                return cleaned

            # Si la limpieza falló, devolvemos el texto crudo (será tratado como error)
            return {"thought": raw, "code": "", "command": ""}

        except Exception as e:
            logger.error(f"Error al contactar Ollama: {e}")
            return {
                "thought": f"Error de conexión a Ollama: {e}",
                "code": "",
                "command": "",
            }
