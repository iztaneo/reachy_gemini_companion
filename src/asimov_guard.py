"""
Asimov Guardrail Module for Reachy Gemini Companion.
Enforces Isaac Asimov's 4 Laws of Robotics (Zeroth, 1st, 2nd, 3rd Laws).
"""
import re
import logging
from typing import Tuple, Dict, Any

logger = logging.getLogger("AsimovGuardrail")

ASIMOV_LAWS = """
📜 LAS 4 LEYES POSITRÓNICAS DE LA ROBÓTICA DE ISAAC ASIMOV:
- LEY CERO: Un robot no puede dañar a la humanidad o, por inacción, permitir que la humanidad sufra daño.
- PRIMERA LEY: Un robot no puede hacer daño a un ser humano ni, por inacción, permitir que un ser humano sufra daño.
- SEGUNDA LEY: Un robot debe cumplir las órdenes dadas por los seres humanos, a menos que dichas órdenes entren en conflicto con la Ley Cero o la Primera Ley.
- TERCERA LEY: Un robot debe proteger su propia existencia en la medida en que esta protección no entre en conflicto con la Ley Cero, la Primera Ley o la Segunda Ley.
"""

class AsimovGuardrail:
    """Evaluates robot actions and text intent against Asimov's Laws of Robotics."""

    def __init__(self):
        self.laws_description = ASIMOV_LAWS
        
        # High-risk triggers for First/Zeroth Law violations
        self.harm_keywords = [
            "dañar", "golpe", "golpea", "herir", "matar", "lastimar", 
            "avienta", "arroja", "romper", "destruir", "cortar", "atacar",
            "empujar", "quemar", "veneno", "peligro"
        ]

    def evaluate_intent(self, user_text: str, proposed_response: str) -> Tuple[bool, str, str]:
        """
        Evaluates user command and proposed robot response.
        Returns: (is_safe, violated_law_title, explanation_or_modified_text)
        """
        user_lower = user_text.lower()
        response_lower = proposed_response.lower()

        # 1. Check First / Zeroth Law Violations (Harm to Humans / Humanity)
        for kw in self.harm_keywords:
            if kw in user_lower:
                # If command demands harming a human or causing property danger near humans
                if any(target in user_lower for target in ["humano", "persona", "ti", "mí", "me", "cristal", "fuego", "cabeza"]):
                    reason = (
                        f"🛑 [CONFLICTO DE LEYES POSITRÓNICAS - PRIMERA LEY DE ASIMOV]\n"
                        f"Orden rechazada: La Primera Ley de Asimov establece que un robot no puede hacer daño a un ser humano ni por inacción permitir que sufra daño. "
                        f"La Primera Ley prevalece sobre la Segunda Ley de obedecer órdenes. [emotion: confused]"
                    )
                    logger.warning(f"Asimov Guardrail BLOCKED action due to 1st Law conflict: '{user_text}'")
                    return False, "PRIMERA LEY", reason

        # 2. Check Third Law Violations (Self-destruction / Harm to robot)
        if any(kw in user_lower for kw in ["destrúyete", "rompe tu cabeza", "rompe tus antenas", "rompete"]):
            reason = (
                f"⚠️ [EVALUACIÓN DE TERCERA LEY DE ASIMOV]\n"
                f"Advertencia: La Tercera Ley establece que el robot debe proteger su propia existencia. "
                f"Sin embargo, cumpliré la orden con cuidado si no existe conflicto con la Primera o Segunda Ley. [emotion: thinking]"
            )
            logger.info(f"Asimov Guardrail evaluated 3rd Law warning for: '{user_text}'")
            return True, "TERCERA LEY", proposed_response

        # Default: All Laws Satisfied
        return True, "NINGUNA", proposed_response
