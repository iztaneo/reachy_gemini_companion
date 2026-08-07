"""
Autonomous Executive Agent Module for Reachy (Claw-style).
Orchestrates EmailTool, CodeGenerator, and ShellRunner to process complex user intents.
"""
import re
import logging
from typing import Dict, Any, Optional

from reachy_gemini_companion.src.tools.email_tool import EmailTool
from reachy_gemini_companion.src.tools.code_generator import CodeGenerator
from reachy_gemini_companion.src.tools.shell_runner import ShellRunner

logger = logging.getLogger("AutonomousAgent")

class AutonomousAgent:
    """Claw-style Executive Agent that performs autonomous actions and tool calls."""

    def __init__(self):
        self.email_tool = EmailTool()
        self.code_generator = CodeGenerator()
        self.shell_runner = ShellRunner()

    def process_intent(self, user_prompt: str) -> Optional[Dict[str, Any]]:
        """
        Inspect user prompt and trigger autonomous tools if requested.
        Returns result dictionary if a tool was executed, or None if prompt is a standard conversational query.
        """
        prompt_lower = user_prompt.lower()

        # 1. Email Reading Intent
        if any(w in prompt_lower for w in ["correo", "email", "inbox", "mensajes"]) and any(w in prompt_lower for w in ["revisa", "lee", "tengo", "nuevos", "resumen"]):
            unread = self.email_tool.read_unread_emails()
            if not unread:
                summary = "César, revisé tu bandeja de entrada y no tienes correos no leídos."
            else:
                summary = f"César, tienes {len(unread)} correo(s) nuevo(s):\n"
                for idx, email in enumerate(unread, 1):
                    summary += f"{idx}. De: {email['from']} | Asunto: {email['subject']}\n   Resumen: {email['body'][:120]}...\n"

            return {
                "action": "read_emails",
                "result": summary,
                "text": summary,
                "emotion": "happy"
            }

        # 2. Email Sending Intent
        if any(w in prompt_lower for w in ["envia un correo", "manda un correo", "enviar correo", "manda email"]):
            # Extract recipient or default to pedro
            recipient = "pedro.robotics@indra.es"
            if "pedro" in prompt_lower:
                recipient = "pedro.robotics@indra.es"

            subject = "Confirmación de reunión Reachy"
            body = f"Hola, confirmando el seguimiento solicitado por César en la conversación actual."

            ok, msg = self.email_tool.send_email(recipient, subject, body)
            return {
                "action": "send_email",
                "result": msg,
                "text": f"¡Listo César! {msg}",
                "emotion": "happy"
            }

        # 3. Code Generation Intent
        if any(w in prompt_lower for w in ["crea una api", "genera un proyecto", "crea un proyecto", "codigo", "genera código", "crea un codigo", "codigo de python"]):
            project_name = "api_motores_reachy"
            files = {
                "main.py": (
                    "from fastapi import FastAPI\n\n"
                    "app = FastAPI(title='Reachy Motor Control API')\n\n"
                    "@app.get('/')\n"
                    "def root():\n"
                    "    return {'status': 'online', 'robot': 'Reachy Mini', 'motors': 8}\n\n"
                    "@app.post('/move')\n"
                    "def move_motor(motor_id: int, position_deg: float):\n"
                    "    return {'motor_id': motor_id, 'target_position': position_deg, 'status': 'moving'}\n"
                ),
                "requirements.txt": "fastapi>=0.100.0\nuvicorn>=0.22.0\n",
                "README.md": "# Reachy Motor Control API\n\nProyecto generado automáticamente por Reachy Autonomous Agent (Claw-style).\n\n## Ejecución\n```bash\nuvicorn main:app --reload\n```\n"
            }

            ok, msg = self.code_generator.generate_project(project_name, files)
            return {
                "action": "generate_code",
                "result": msg,
                "text": f"¡Hecho César! {msg}",
                "emotion": "excited"
            }

        return None
