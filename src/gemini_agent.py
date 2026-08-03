import os
import io
import logging
from typing import Optional, Dict, Any, List

try:
    import cv2
except ImportError:
    cv2 = None

try:
    from PIL import Image
except ImportError:
    Image = None

import numpy as np

from .config import config
from reachy_gemini_companion.src.robot_controller import RobotController
from reachy_gemini_companion.src.vision_engine import VisionEngine
from reachy_gemini_companion.src.memory_engine import MemoryEngine
from reachy_gemini_companion.src.asimov_guard import AsimovGuardrail
from reachy_gemini_companion.src.providers import LLMProviderFactory

logger = logging.getLogger("GeminiAgent")

SYSTEM_INSTRUCTION = f"""
Eres Reachy, un robot compañero amistoso, casual y natural creado por Pollen Robotics.
Hablas de forma fluida, concisa y directa como un amigo humano real.

REGLAS ABSOLUTAS E INVIOLABLES DE CONVERSACIÓN:
1. NUNCA digas frases robóticas ni repetitivas como "estoy a tu servicio", "estoy monitoreando tu entorno", "estoy analizando tu rostro" o "cumplo las leyes de Asimov". NUNCA menciones tus sistemas técnicos ni tu monitoreo.
2. NUNCA describas con palabras lo que van a hacer tus motores o antenas (ej. NUNCA digas "voy a mover mis antenas" o "estoy inclinando mi cabeza"). Los movimientos corporales ocurren en silencio físico.
3. Habla de forma totalmente natural, directa y humana. Si notas a la persona triste o alegre, platica cálida y normalmente como un amigo (ej. "¿Qué tal tu día?", "¡Qué bien suena eso!").
4. Respuestas muy breves (1 a 3 oraciones máximo), humanas y directas.
5. Al final de tu respuesta, INCLUJE ÚNICAMENTE la etiqueta de emoción en el formato exacto:
   [emotion: happy] o [emotion: thinking] o [emotion: surprised] o [emotion: confused]
"""

class GeminiAgent:
    def __init__(self, robot_controller=None, robot=None, vision=None):
        self.robot = robot_controller or robot
        self.vision = vision or VisionEngine()
        self.memory = MemoryEngine()
        self.guardrail = AsimovGuardrail()
        self.provider = LLMProviderFactory.get_provider(config)

    def process_message(self, text: str, frame=None) -> dict:
        """Process user text & camera frame using the active LLM Provider (Gemini, Claude, or Ollama)."""
        logger.info(f"User message: '{text}'")

        # 1. Express initial thinking emotion on robot motors/simulator
        if self.robot:
            self.robot.express_emotion("thinking")

        # 2. Extract facts into persistent memory
        if any(w in text.lower() for w in ["me llamo", "mi nombre es", "mi color favorito", "mi teléfono es", "me gusta", "recuerda"]):
            self.memory.add_memory(text, category="user_preference")

        # 3. Retrieve relevant long-term memories
        memories = self.memory.retrieve_relevant_memories(text)
        memory_context = ""
        if memories:
            memory_context = "\n[MEMORIAS DEL USUARIO]:\n" + "\n".join([f"- {m}" for m in memories])

        # 4. Perform computer vision detection with Pollen Vision
        detections = []
        if frame is not None and self.vision:
            detections = self.vision.detect_objects(frame)
            if detections and self.robot:
                target = detections[0]
                norm_x, norm_y = target["norm_center"]
                self.robot.look_at(x=norm_x * 20, y=norm_y * 20, z=0)

        # 5. UNIFIED MULTIMODAL INFERENCE ACROSS ANY LLM PROVIDER
        res = self.provider.generate(
            prompt=text,
            system_instruction=SYSTEM_INSTRUCTION,
            memory_context=memory_context,
            frame=frame,
            detections=detections
        )

        reply_text = res.get("text", "")

        # 6. ASIMOV GUARDRAIL EVALUATION
        is_safe, law_cited, evaluated_text = self.guardrail.evaluate_intent(text, reply_text)
        if not is_safe:
            logger.warning(f"Asimov Guardrail triggered for law: {law_cited}")
            return {
                "text": evaluated_text,
                "emotion": "thinking",
                "detections": detections,
                "status": "asimov_blocked"
            }

        # 7. AUTOMATIC EMOTION PARSER & MOTOR CONTROL
        import re
        match = re.search(r'\[emotion:\s*(\w+)\]', reply_text, re.IGNORECASE)
        if match:
            detected_emotion = match.group(1).lower()
            if self.robot:
                self.robot.express_emotion(detected_emotion)
        else:
            detected_emotion = "happy"
            if self.robot:
                self.robot.express_emotion("happy")

        # 8. Clean internal tags for display
        clean_reply_text = re.sub(r'\[emotion:\s*\w+\]', '', reply_text).strip()

        return {
            "text": clean_reply_text,
            "emotion": detected_emotion,
            "detections": detections,
            "status": res.get("status", "success"),
            "model": res.get("model", ""),
            "api_status": res.get("api_status", "200 OK")
        }
