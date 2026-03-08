#!/usr/bin/env python3
"""
sandbox_executor.py – Ejecuta código en un entorno aislado y con límites.
Soporta Python, Bash y JavaScript (Node.js).
"""

import subprocess
import tempfile
import time
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

import config

# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
@dataclass
class SandboxResult:
    """Resultado de la ejecución aislada."""

    success: bool
    stdout: str
    stderr: str
    exit_code: int
    execution_time: float
    language: str
    error_message: Optional[str] = None


# ---------------------------------------------------------------------------
class SandboxExecutor:
    """Ejecutor que lanza subprocesses con timeout y límites de recursos."""

    def __init__(self, timeout: Optional[int] = None) -> None:
        self.timeout = timeout or config.SANDBOX_TIMEOUT
        self.workdir = Path.home() / ".jarvisco_workspace"
        self.workdir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Sandbox inicializada en {self.workdir} (timeout={self.timeout}s)")

    # -----------------------------------------------------------------------
    def _run_subprocess(self, argv: List[str], cwd: Path, lang: str) -> SandboxResult:
        """
        Helper que ejecuta ``subprocess.run`` con límites de CPU/memoria.
        """
        try:
            import resource

            def limit_resources():
                # 200 MiB de RAM
                resource.setrlimit(resource.RLIMIT_AS, (200 * 1024 * 1024, 200 * 1024 * 1024))
                # máximo 10 procesos simultáneos
                resource.setrlimit(resource.RLIMIT_NPROC, (10, 10))

            start = time.time()
            proc = subprocess.run(
                argv,
                cwd=str(cwd),
                capture_output=True,
                text=True,
                timeout=self.timeout,
                preexec_fn=limit_resources,
                env={"PATH": "/usr/bin:/bin"},
            )
            exec_time = time.time() - start
            return SandboxResult(
                success=(proc.returncode == 0),
                stdout=proc.stdout,
                stderr=proc.stderr,
                exit_code=proc.returncode,
                execution_time=exec_time,
                language=lang,
            )
        except subprocess.TimeoutExpired:
            return SandboxResult(
                success=False,
                stdout="",
                stderr="",
                exit_code=-1,
                execution_time=self.timeout,
                language=lang,
                error_message=f"Timeout después de {self.timeout}s",
            )
        except Exception as exc:
            return SandboxResult(
                success=False,
                stdout="",
                stderr="",
                exit_code=-1,
                execution_time=0,
                language=lang,
                error_message=str(exc),
            )

    # -----------------------------------------------------------------------
    def execute_python(self, code: str) -> SandboxResult:
        """Ejecuta código Python en un archivo temporal."""
        with tempfile.NamedTemporaryFile(
            "w",
            suffix=".py",
            dir=self.workdir,
            delete=False,
        ) as f:
            f.write(code)
            temp_path = Path(f.name)

        result = self._run_subprocess(
            ["python3", str(temp_path)], cwd=self.workdir, lang="python"
        )
        temp_path.unlink(missing_ok=True)
        return result

    # -----------------------------------------------------------------------
    def execute_bash(self, code: str) -> SandboxResult:
        """Ejecuta script Bash."""
        with tempfile.NamedTemporaryFile(
            "w",
            suffix=".sh",
            dir=self.workdir,
            delete=False,
        ) as f:
            f.write("#!/bin/bash\n")
            f.write(code)
            temp_path = Path(f.name)

        # Convertir en ejecutable
        os.chmod(temp_path, 0o755)

        result = self._run_subprocess(
            [str(temp_path)], cwd=self.workdir, lang="bash"
        )
        temp_path.unlink(missing_ok=True)
        return result

    # -----------------------------------------------------------------------
    def execute_javascript(self, code: str) -> SandboxResult:
        """Ejecuta código JavaScript usando Node.js."""
        with tempfile.NamedTemporaryFile(
            "w",
            suffix=".js",
            dir=self.workdir,
            delete=False,
        ) as f:
            f.write(code)
            temp_path = Path(f.name)

        result = self._run_subprocess(
            ["node", str(temp_path)], cwd=self.workdir, lang="javascript"
        )
        temp_path.unlink(missing_ok=True)
        return result

    # -----------------------------------------------------------------------
    def execute(self, code: str, language: str) -> SandboxResult:
        """Dispatcher único."""
        lang = language.lower()
        if lang in ("python", "py"):
            return self.execute_python(code)
        if lang in ("bash", "sh", "shell"):
            return self.execute_bash(code)
        if lang in ("javascript", "js", "node"):
            return self.execute_javascript(code)
        return SandboxResult(
            success=False,
            stdout="",
            stderr="",
            exit_code=-1,
            execution_time=0,
            language=lang,
            error_message=f"Lenguaje no soportado: {language}",
        )
