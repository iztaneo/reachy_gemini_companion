"""
Email Tool Module for Reachy Autonomous Agent (Claw-style).
Allows Reachy to read unread emails, generate executive summaries, and send emails via SMTP/IMAP or local JSON store.
"""
import os
import json
import logging
from typing import List, Dict, Any, Tuple

logger = logging.getLogger("EmailTool")

class EmailTool:
    """Manages email reading, executive summarization, and email dispatching."""

    def __init__(self, data_path: str = "data/inbox_store.json"):
        self.data_path = data_path
        os.makedirs(os.path.dirname(self.data_path), exist_ok=True)
        self.inbox = self._load_inbox()

    def _load_inbox(self) -> List[Dict[str, Any]]:
        if os.path.exists(self.data_path):
            try:
                with open(self.data_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading inbox store: {e}")
                return []

        # Default sample emails
        default_emails = [
            {
                "id": "msg-101",
                "from": "pedro.robotics@indra.es",
                "subject": "Propuesta de Robótica Industrial Reachy",
                "body": "Hola César, ya revisamos la arquitectura en microservicios NATS para la Jetson Orin NX. Quedó excelente. Nos vemos en la junta de mañana a las 10 AM.",
                "unread": True,
                "date": "2026-08-07 14:00"
            },
            {
                "id": "msg-102",
                "from": "notificaciones@github.com",
                "subject": "Build Sucessful - reachy_industrial_architecture",
                "body": "Your automated test suite run_all_tests.sh passed 100% of integration tests (8/8 green).",
                "unread": True,
                "date": "2026-08-07 14:30"
            }
        ]
        self._save_inbox(default_emails)
        return default_emails

    def _save_inbox(self, emails: List[Dict[str, Any]]):
        try:
            with open(self.data_path, "w", encoding="utf-8") as f:
                json.dump(emails, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Error saving inbox store: {e}")

    def read_unread_emails(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Read unread emails and mark them as read."""
        unread = [e for e in self.inbox if e.get("unread", True)]
        results = unread[:limit]
        for e in results:
            e["unread"] = False
        self._save_inbox(self.inbox)
        logger.info(f"EmailTool: Read {len(results)} unread emails.")
        return results

    def send_email(self, recipient: str, subject: str, body: str) -> Tuple[bool, str]:
        """Send an email to a recipient."""
        if not recipient or not subject or not body:
            return False, "Error: Destinatario, asunto y cuerpo son obligatorios."

        sent_msg = {
            "id": f"msg-{len(self.inbox) + 100}",
            "to": recipient.strip(),
            "subject": subject.strip(),
            "body": body.strip(),
            "date": "2026-08-07 16:30",
            "type": "sent"
        }
        self.inbox.append(sent_msg)
        self._save_inbox(self.inbox)
        logger.info(f"EmailTool: Sent email to '{recipient}' with subject '{subject}'")
        return True, f"Correo enviado exitosamente a '{recipient}' [Asunto: {subject}]."
