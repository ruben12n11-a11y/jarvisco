#!/usr/bin/env python3
"""
adapter.py – Evaluador de riesgos sin IA.
Clasifica comandos y fragmentos de código en cuatro niveles:
LOW, MEDIUM, HIGH, CRITICAL.
"""

import re
import logging
from enum import Enum
from typing import Tuple

# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class RiskLevel(Enum):
    """Niveles de riesgo para comandos y código."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class JarvisCOAdapter:
    """Evaluador de riesgos basado en expresiones regulares y heurística."""

    def __init__(self) -> None:
        logger.info("Inicializando adapter de riesgos...")

        # ------------------------------------------------------------------- #
        # Patrones críticos (pueden destruir el sistema)                     #
        # ------------------------------------------------------------------- #
        self.critical_patterns = [
            r"\bsudo\b",
            r"\bdd\b",
            r"\bmkfs\b",
            r"\bfdisk\b",
            r"\bparted\b",
            r"\bgrub\b",
            r"\bbootloader\b",
            r"\bkill\s+-9\b",
            r"\brm\s+-rf\s+/",
            r"\brm\s+\*",
            r"\bformat\b",
            r"\bwipe\b",
            r"\bshred\b",
            r"\bmount\b",
            r"\bumount\b",
        ]

        # ------------------------------------------------------------------- #
        # Patrones de alto riesgo (pérdida de datos)                         #
        # ------------------------------------------------------------------- #
        self.high_patterns = [
            r"\brm\b",
            r"\bmv\b",
            r"\bchmod\b",
            r"\bchown\b",
            r"\bsystemctl\b",
            r"\bservice\b",
            r"\bkill\b",
            r"\bpkill\b",
            r"\breboot\b",
            r"\bshutdown\b",
            r"\bsync\b",
            r"\bfstab\b",
            r">\s*/dev/",
        ]

        # ------------------------------------------------------------------- #
        # Patrones de riesgo medio (modificaciones de archivos)              #
        # ------------------------------------------------------------------- #
        self.medium_patterns = [
            r"\bmkdir\b",
            r"\btouch\b",
            r"\bcp\b",
            r"\bln\b",
            r"\btar\b",
            r"\bgzip\b",
            r"\bzip\b",
            r"\bunzip\b",
            r"\bsed\s+-i\b",
            r"\bawk\b",
            r"\bfind\b.*-exec\b",
            r"\bxargs\b",
            r">\s*\w+",
        ]

        # ------------------------------------------------------------------- #
        # Patrones seguros (solo lectura)                                    #
        # ------------------------------------------------------------------- #
        self.safe_patterns = [
            r"\bls\b",
            r"\bcat\b",
            r"\becho\b",
            r"\bpwd\b",
            r"\bdate\b",
            r"\bwhoami\b",
            r"\buname\b",
            r"\bdf\b",
            r"\bdu\b",
            r"\bps\b",
            r"\btop\b",
            r"\bfree\b",
            r"\bhistory\b",
            r"\bhead\b",
            r"\btail\b",
            r"\bwc\b",
            r"\bsort\b",
            r"\buniq\b",
            r"\bgrep\b",
            r"\bless\b",
            r"\bmore\b",
        ]

        logger.info("✅ Adapter inicializado con patrones de riesgo")

    # -----------------------------------------------------------------------
    def evaluate_command(self, command: str) -> Tuple[str, str]:
        """
        Evalúa el nivel de riesgo de un comando de shell.
        Devuelve (nivel_riesgo, descripción).
        """
        cmd = command.lower().strip()
        logger.debug(f"Evaluando comando: {cmd}")

        # 1️⃣ Crítico
        for pat in self.critical_patterns:
            if re.search(pat, cmd):
                desc = f"Comando CRÍTICO detectado: {pat}"
                logger.warning(desc)
                return (RiskLevel.CRITICAL.value, desc)

        # 2️⃣ Alto
        for pat in self.high_patterns:
            if re.search(pat, cmd):
                desc = f"Comando de ALTO RIESGO detectado: {pat}"
                logger.warning(desc)
                return (RiskLevel.HIGH.value, desc)

        # 3️⃣ Medio → requiere confirmación
        for pat in self.medium_patterns:
            if re.search(pat, cmd):
                desc = f"Comando de RIESGO MEDIO detectado: {pat}"
                logger.info(desc)
                return (RiskLevel.MEDIUM.value, desc)

        # 4️⃣ Seguro
        desc = "Comando seguro (solo lectura)"
        logger.info(desc)
        return (RiskLevel.LOW.value, desc)

    # -----------------------------------------------------------------------
    def evaluate_code(self, code: str, language: str = "python") -> Tuple[str, str]:
        """
        Evalúa riesgos en fragmentos de código.
        Actualmente soporta Python, Bash y JavaScript.
        """
        code_low = code.lower()

        # ---------- Python ----------
        if language == "python":
            critical_py = [
                r"os\.system\(",
                r"subprocess\.call\(",
                r"subprocess\.run\(",
                r"exec\(",
                r"eval\(",
                r"__import__\(",
                r'open\(.*["\']w["\']',
                r"shutil\.rmtree",
                r"os\.remove",
                r"os\.unlink",
                r"os\.chmod",
                r"os\.rmdir",
            ]
            for pat in critical_py:
                if re.search(pat, code_low):
                    desc = f"Código Python CRÍTICO: {pat}"
                    logger.warning(desc)
                    return (RiskLevel.CRITICAL.value, desc)

        # ---------- Bash ----------
        elif language == "bash":
            critical_bash = [
                r"rm\s+-rf\s+/",
                r"dd\s+if=",
                r"mkfs\b",
                r"\bsudo\b",
                r">\s*/dev/",
            ]
            for pat in critical_bash:
                if re.search(pat, code_low):
                    desc = f"Código Bash CRÍTICO: {pat}"
                    logger.warning(desc)
                    return (RiskLevel.CRITICAL.value, desc)

        # ---------- JavaScript ----------
        elif language == "javascript":
            critical_js = [
                r"eval\(",
                r"exec\(",
                r"child_process",
                r"fs\.unlink",
                r"fs\.rmdir",
            ]
            for pat in critical_js:
                if re.search(pat, code_low):
                    desc = f"Código JavaScript CRÍTICO: {pat}"
                    logger.warning(desc)
                    return (RiskLevel.CRITICAL.value, desc)

        # Si no se detecta nada peligroso → bajo riesgo
        desc = "Código seguro (sin patrones peligrosos detectados)"
        logger.info(desc)
        return (RiskLevel.LOW.value, desc)

    # -----------------------------------------------------------------------
    def should_confirm(self, risk_level: str) -> bool:
        """Decide si se necesita confirmación del usuario."""
        return risk_level in [
            RiskLevel.MEDIUM.value,
            RiskLevel.HIGH.value,
            RiskLevel.CRITICAL.value,
        ]

    # -----------------------------------------------------------------------
    def get_system_info(self) -> dict[str, str]:
        """Obtiene información básica del entorno (pwd, user, OS)."""
        info: dict[str, str] = {}
        try:
            result = subprocess.run(["pwd"], capture_output=True, text=True)
            info["pwd"] = result.stdout.strip()
        except Exception as e:
            info["pwd"] = f"Error: {e}"

        try:
            result = subprocess.run(["whoami"], capture_output=True, text=True)
            info["user"] = result.stdout.strip()
        except Exception as e:
            info["user"] = f"Error: {e}"

        try:
            result = subprocess.run(["uname", "-a"], capture_output=True, text=True)
            info["os"] = result.stdout.strip()
        except Exception as e:
            info["os"] = f"Error: {e}"

        return info
