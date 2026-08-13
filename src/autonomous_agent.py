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
                for idx, email_item in enumerate(unread, 1):
                    sender = email_item.get('from', email_item.get('to', 'Desconocido'))
                    subj = email_item.get('subject', 'Sin asunto')
                    body_snippet = email_item.get('body', '')[:120]
                    summary += f"{idx}. De: {sender} | Asunto: {subj}\n   Resumen: {body_snippet}...\n"

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

        # 4. Terminal Shell Command Execution Intent
        if any(w in prompt_lower for w in ["ejecuta el comando", "corre en la terminal", "ejecuta en la terminal", "comando de terminal", "terminal", "espacio en disco", "listar archivos"]):
            cmd = "df -h"
            if "archivos" in prompt_lower or "listar" in prompt_lower:
                cmd = "ls -la"
            elif "disco" in prompt_lower or "espacio" in prompt_lower:
                cmd = "df -h"
            elif "memoria" in prompt_lower or "procesos" in prompt_lower:
                cmd = "top -l 1 | head -n 10"

            ok, out = self.shell_runner.run_command(cmd)
            return {
                "action": "execute_shell",
                "result": out,
                "text": f"¡Listo César! Ejecuté el comando `{cmd}` en tu Mac. Resultado:\n{out[:250]}",
                "emotion": "thinking"
            }

        # 5. Auto-Generation of New Skills Intent
        if any(w in prompt_lower for w in ["crea un skill", "crea una habilidad", "genera un skill", "genera una habilidad", "nuevo skill"]):
            # Extract skill name from prompt or default to data-analyst
            skill_name = "data-analyst"
            if "pandas" in prompt_lower or "datos" in prompt_lower or "data" in prompt_lower:
                skill_name = "data-analyst"
            elif "vision" in prompt_lower or "imagen" in prompt_lower:
                skill_name = "vision-expert"

            description = f"Skill auto-generado por Reachy para procesamiento especializado de {skill_name}."
            keywords = ["datos", "pandas", "analisis", "tabla", "csv", "grafico", skill_name]
            system_prompt = (
                f"# Skill Auto-Generado: {skill_name} 📊\n\n"
                f"## Rol y Comportamiento\n"
                f"Eres un Analista Experto en {skill_name}.\n"
                f"Proporcionas respuestas analíticas, estructuradas y con código limpio en Python."
            )

            from reachy_gemini_companion.src.skills_engine import SkillsEngine
            skills_engine = SkillsEngine()
            ok, msg = skills_engine.create_skill(skill_name, description, keywords, system_prompt)

            return {
                "action": "create_skill",
                "result": msg,
                "text": f"¡Hecho César! {msg}",
                "emotion": "surprised"
            }

        # 6. Auto-Generation of Custom Prompt Templates Intent
        if any(w in prompt_lower for w in ["crea un prompt", "guarda este prompt", "nuevo prompt", "plantilla de prompt"]):
            prompt_name = "plantilla_explicacion_simple"
            if "resumen" in prompt_lower:
                prompt_name = "plantilla_resumen_ejecutivo"

            prompt_content = (
                "# Plantilla de Prompt: Explicación Sencilla 💡\n\n"
                "Explica el siguiente concepto técnico como si tu oyente tuviera 10 años, "
                "utilizando analogías cotidianas y sin jerga matemática compleja.\n"
            )

            from reachy_gemini_companion.src.skills_engine import SkillsEngine
            skills_engine = SkillsEngine()
            ok, msg = skills_engine.create_prompt(prompt_name, prompt_content)

            return {
                "action": "create_prompt",
                "result": msg,
                "text": f"¡Hecho César! {msg}",
                "emotion": "happy"
            }

        return None
