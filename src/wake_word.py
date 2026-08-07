"""
Wake Word Detection Module for Reachy Gemini Companion.
Listens for activation phrase ('Oye Reachy' / 'Hola Reachy') to trigger speech input.
"""
import logging
from typing import Tuple

logger = logging.getLogger("WakeWord")

class WakeWordDetector:
    """Detects activation phrases in audio text transcriptions."""

    def __init__(self, wake_phrases: list = None):
        self.wake_phrases = wake_phrases or ["oye reachy", "hola reachy", "hey reachy", "reachy"]

    def check_wake_word(self, text: str) -> Tuple[bool, str]:
        """
        Check if input speech contains wake phrase.
        Returns (is_triggered, cleaned_command).
        """
        if not text:
            return False, ""

        text_lower = text.lower().strip()
        for phrase in self.wake_phrases:
            if phrase in text_lower:
                cleaned = text_lower.replace(phrase, "").strip()
                logger.info(f"Wake Word triggered: '{phrase}' -> Command: '{cleaned}'")
                return True, cleaned

        return False, text
