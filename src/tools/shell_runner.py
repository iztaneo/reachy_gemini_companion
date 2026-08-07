"""
Shell Runner Module for Reachy Autonomous Agent (Claw-style).
Safely executes local python validation scripts and shell commands.
"""
import subprocess
import logging
from typing import Tuple

logger = logging.getLogger("ShellRunner")

class ShellRunner:
    """Executes code verification and terminal commands safely."""

    @staticmethod
    def run_command(command: str, cwd: str = ".") -> Tuple[bool, str]:
        """Execute a shell command and return (success, output)."""
        logger.info(f"ShellRunner: Executing command '{command}' in '{cwd}'")
        try:
            res = subprocess.run(
                command,
                shell=True,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=30
            )
            if res.returncode == 0:
                output = res.stdout.strip() or "Comando ejecutado con éxito."
                return True, output
            else:
                err_msg = res.stderr.strip() or res.stdout.strip()
                return False, f"Error (código {res.returncode}): {err_msg}"
        except Exception as e:
            return False, f"Excepción al ejecutar comando: {e}"
