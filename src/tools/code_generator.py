"""
Code Generator Module for Reachy Autonomous Agent (Claw-style).
Generates multi-file code projects, creates directories, and saves clean code files.
"""
import os
import logging
from typing import Dict, Any, Tuple

logger = logging.getLogger("CodeGenerator")

class CodeGenerator:
    """Generates structured code projects into local directory workspace."""

    def __init__(self, base_output_dir: str = "generated_projects"):
        self.base_output_dir = base_output_dir
        os.makedirs(self.base_output_dir, exist_ok=True)

    def generate_project(self, project_name: str, files: Dict[str, str]) -> Tuple[bool, str]:
        """
        Generate a multi-file code project.
        files: Dictionary where key is relative file path (e.g. 'main.py') and value is code string.
        """
        if not project_name or not files:
            return False, "Error: Nombre de proyecto y archivos son requeridos."

        proj_dir = os.path.join(self.base_output_dir, project_name)
        os.makedirs(proj_dir, exist_ok=True)

        created_files = []
        for rel_path, code in files.items():
            full_path = os.path.join(proj_dir, rel_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(code.strip() + "\n")
            created_files.append(rel_path)

        logger.info(f"CodeGenerator: Created project '{project_name}' with {len(created_files)} files.")
        return True, f"Proyecto '{project_name}' generado exitosamente en '{proj_dir}' con {len(created_files)} archivos: {', '.join(created_files)}"
