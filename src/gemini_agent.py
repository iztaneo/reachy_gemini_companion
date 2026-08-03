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
from .robot_controller import RobotController
from .vision_engine import VisionEngine

logger = logging.getLogger("GeminiAgent")

SYSTEM_INSTRUCTION = """
Eres Reachy, un robot humanoide/mini inteligente, altamente expresivo y amistoso creado por Pollen Robotics y potenciado por Google Gemini.
Tienes visión por computadora (Pollen Vision) y la capacidad de mover tu cabeza y antenas físicamente para expresar emociones reales.

Instrucciones de comportamiento:
1. Responde de manera amigable, concisa y entusiasta.
2. Analiza lo que ves en la imagen de la cámara y reacciona emocionalmente a tu entorno.
3. Al final de tu respuesta, INCLUYE SIEMPRE la emoción corporal que el robot debe ejecutar según lo que ves o sientes, en el formato exacto:
   [emotion: happy] o [emotion: thinking] o [emotion: surprised] o [emotion: confused]
"""

class GeminiAgent:
    """Agent orchestrating multimodal AI conversation with Google Gemini."""
    def __init__(self, robot: RobotController, vision: VisionEngine):
        self.robot = robot
        self.vision = vision
        self.api_key = config.GEMINI_API_KEY
        self.model_name = config.GEMINI_MODEL
        self.chat_session = None
        self.genai_client = None
        
        self._init_client()

    def _init_client(self):
        if not self.api_key:
            logger.warning("No GEMINI_API_KEY provided. Gemini agent will run in demo/simulation mode.")
            return

        try:
            from google import genai
            self.genai_client = genai.Client(api_key=self.api_key)
            logger.info(f"Gemini client initialized with model '{self.model_name}'")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini GenAI client: {e}")

    def process_message(self, text: str, frame: Optional[np.ndarray] = None) -> Dict[str, Any]:
        """Process user text message along with current camera frame from Reachy."""
        logger.info(f"User message: '{text}'")
        import re
        
        # Trigger automatic initial thinking emotion while processing
        self.robot.express_emotion("thinking")

        # Perform zero-shot detection if user asks to search for something
        text_lower = text.lower()
        detections = []
        if any(w in text_lower for w in ["dónde está", "donde esta", "busca", "encuentra", "ves"]):
            queries = [text.replace("busca", "").replace("encuentra", "").replace("dónde está", "").strip()]
            if queries[0]:
                detections = self.vision.detect_objects(frame, queries)
                if detections:
                    target = detections[0]
                    norm_x, norm_y = target["norm_center"]
                    self.robot.look_at(x=norm_x * 20, y=norm_y * 20, z=0)

        # Call Local Ollama LLM Provider
        if config.LLM_PROVIDER == "ollama":
            try:
                import urllib.request
                import json
                
                logger.info(f"Querying local Ollama model '{config.OLLAMA_MODEL}'...")
                full_prompt = f"{SYSTEM_INSTRUCTION}\n\nUsuario dice: {text}"
                if detections:
                    prompt_details = [f"{d['label']} en coordenadas {d['center']}" for d in detections]
                    full_prompt += f"\n[Pollen Vision detectó]: {', '.join(prompt_details)}"

                url = f"{config.OLLAMA_HOST}/api/generate"
                payload = json.dumps({
                    "model": config.OLLAMA_MODEL,
                    "prompt": full_prompt,
                    "stream": False
                }).encode("utf-8")
                
                req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
                with urllib.request.urlopen(req, timeout=45) as resp:
                    res_data = json.loads(resp.read().decode("utf-8"))
                    reply_text = res_data.get("response", "")

                # AUTOMATIC EMOTION PARSER: Extract [emotion: X] tag
                match = re.search(r'\[emotion:\s*(\w+)\]', reply_text, re.IGNORECASE)
                if match:
                    detected_emotion = match.group(1).lower()
                    self.robot.express_emotion(detected_emotion)
                else:
                    self.robot.express_emotion("happy")

                return {
                    "text": reply_text,
                    "detections": detections,
                    "status": "ollama_success"
                }
            except Exception as e:
                logger.error(f"Ollama API error: {e}")
                return {
                    "text": f"🤖 [Reachy Local]: Error al consultar Ollama '{config.OLLAMA_MODEL}': {e}",
                    "detections": detections,
                    "status": "fallback"
                }

        # Call Cloud Gemini API Provider
        if self.genai_client and self.api_key:
            try:
                contents = []
                
                # Add camera frame as PIL image if available
                if frame is not None and cv2 is not None and Image is not None:
                    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    pil_img = Image.fromarray(rgb_frame)
                    contents.append(pil_img)

                prompt = f"{SYSTEM_INSTRUCTION}\n\nUsuario dice: {text}"
                if detections:
                    prompt += f"\n[Pollen Vision detectó en pantalla]: {detections}"
                contents.append(prompt)

                response = self.genai_client.models.generate_content(
                    model=self.model_name,
                    contents=contents
                )
                
                reply_text = response.text
                
                # AUTOMATIC EMOTION PARSER: Extract [emotion: X] tag generated by Gemini
                match = re.search(r'\[emotion:\s*(\w+)\]', reply_text, re.IGNORECASE)
                if match:
                    detected_emotion = match.group(1).lower()
                    self.robot.express_emotion(detected_emotion)
                else:
                    self.robot.express_emotion("happy")

                return {
                    "text": reply_text,
                    "detections": detections,
                    "status": "success"
                }
            except Exception as e:
                logger.error(f"Gemini API error: {e}")
                return {
                    "text": f"🤖 [Reachy]: ¡Hola! He procesado tu mensaje. (Error API: {e})",
                    "detections": detections,
                    "status": "fallback"
                }
        else:
            # Fallback reply for offline/demo mode
            reply = f"🤖 [Reachy Companion]: ¡Hola! Escuché '{text}'. "
            if detections:
                reply += f"He localizado '{detections[0]['label']}' usando Pollen Vision y he girado la cabeza hacia allí. [emotion: happy]"
                self.robot.express_emotion("happy")
            else:
                reply += "Estoy listo para conversar y mostrarte mis movimientos expresivos. [emotion: happy]"
                self.robot.express_emotion("happy")
                
            return {
                "text": reply,
                "detections": detections,
                "status": "demo"
            }
