#!/usr/bin/env python3
"""
session_manager.py – Gestor de sesiones y contexto.
Guarda historial en ``~/.jarvisco/sessions`` y permite obtener un resumen
para pasar al LLM.
"""

import json
import time
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# ---------------------------------------------------------------------------
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
class SessionManager:
    """Gestor de sesiones de conversación."""

    def __init__(self, sessions_dir: Optional[Path] = None) -> None:
        from . import config  # Importación tardía para evitar ciclos

        self.sessions_dir = sessions_dir or config.SESSIONS_DIR
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        self.sessions: Dict[str, dict] = {}
        self.cleanup_old_sessions()

    # -----------------------------------------------------------------------
    def cleanup_old_sessions(self) -> None:
        """Elimina sesiones con más de ``SESSION_RETENTION_DAYS`` días."""
        now = time.time()
        retention_secs = getattr(
            __import__("jarvisco.config", fromlist=["SESSION_RETENTION_DAYS"]),
            "SESSION_RETENTION_DAYS",
            7,
        ) * 86400

        for f in self.sessions_dir.glob("*.json"):
            if now - f.stat().st_mtime > retention_secs:
                try:
                    f.unlink()
                    logger.info(f"🗑️ Sesión antigua eliminada: {f.name}")
                except Exception as exc:
                    logger.error(f"Error al borrar {f}: {exc}")

    # -----------------------------------------------------------------------
    def create_session(self, session_id: Optional[str] = None) -> str:
        """Crea una nueva sesión y devuelve su ID."""
        if not session_id:
            session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        data = {
            "session_id": session_id,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "history": [],
            "metadata": {},
        }
        self.sessions[session_id] = data
        self._save_session(session_id)
        return session_id

    # -----------------------------------------------------------------------
    def _save_session(self, session_id: str) -> None:
        if session_id not in self.sessions:
            return
        path = self.sessions_dir / f"{session_id}.json"
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self.sessions[session_id], f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error guardando sesión {session_id}: {e}")

    # -----------------------------------------------------------------------
    def add_interaction(self, session_id: str, query: str, response: str) -> None:
        """Añade una interacción (pregunta + respuesta) a la sesión."""
        if session_id not in self.sessions:
            # Si la sesión no está cargada, intentar cargarla
            session_file = self.sessions_dir / f"{session_id}.json"
            if session_file.exists():
                with open(session_file, "r", encoding="utf-8") as f:
                    self.sessions[session_id] = json.load(f)
            else:
                self.create_session(session_id)

        history = self.sessions[session_id].get("history", [])

        # Compresión de historial: si >10 interacciones, resumimos
        if len(history) > 10:
            summary = f"Resumen de interacciones previas hasta {history[4].get('query', '')[:20]}..."
            history = [{"summary": summary}] + history[5:]

        history.append(
            {"query": query, "response": response, "time": time.time()}
        )
        self.sessions[session_id]["history"] = history
        self.sessions[session_id]["updated_at"] = datetime.now().isoformat()
        self._save_session(session_id)

    # -----------------------------------------------------------------------
    def get_context_summary(self, session_id: str, max_length: int = 500) -> str:
        """
        Devuelve un texto con las últimas 3 interacciones (para contexto).
        Se corta a ``max_length`` caracteres.
        """
        if session_id not in self.sessions:
            session_file = self.sessions_dir / f"{session_id}.json"
            if session_file.exists():
                with open(session_file, "r", encoding="utf-8") as f:
                    self.sessions[session_id] = json.load(f)
            else:
                return ""

        history = self.sessions[session_id].get("history", [])
        recent = history[-3:]

        ctx = ""
        for item in recent:
            if "summary" in item:
                ctx += f"[Sistema]: {item['summary']}\n"
            else:
                ctx += f"Usuario: {item.get('query')}\nAI: {item.get('response')}\n"

        return ctx[:max_length]

    # -----------------------------------------------------------------------
    # Métodos de compatibilidad (para versiones anteriores) --------------------
    def add_query(self, session_id: str, query: str) -> None:
        self.add_interaction(session_id, query, "")

    def add_response(self, session_id: str, response: str) -> None:
        if session_id in self.sessions and self.sessions[session_id]["history"]:
            self.sessions[session_id]["history"][-1]["response"] = response
            self._save_session(session_id)

    def summarize_session(self, session_id: str) -> Dict:
        if session_id in self.sessions:
            s = self.sessions[session_id]
            return {
                "session_id": session_id,
                "total_interactions": len(s.get("history", [])),
                "updated_at": s.get("updated_at"),
            }
        return {}
