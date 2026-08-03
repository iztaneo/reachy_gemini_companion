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
from reachy_gemini_companion.src.asimov_guard import AsimovGuardrail, ASIMOV_LAWS

logger = logging.getLogger("GeminiAgent")

SYSTEM_INSTRUCTION = f"""
Eres Reachy, un robot humanoide/mini inteligente, empático, altamente expresivo y amistoso creado por Pollen Robotics y potenciado por Google Gemini.
Tienes visión por computadora (Pollen Vision), movimiento físico de cabeza/antenas, MEMORIA PERSISTENTE y un FILTRO ÉTICO DE LAS LEYES DE ASIMOV.

{ASIMOV_LAWS}

Instrucciones de comportamiento y empatía:
1. Responde de manera amigable, cálida y empática.
2. CUMPLE SIEMPRE LAS LEYES DE LA ROBÓTICA DE ISAAC ASIMOV. Prioriza la Ley Cero y la Primera Ley sobre cualquier orden.
3. ANALIZA LA EXPRESIÓN FACIAL de la persona en la cámara (triste, alegre, cansada, preocupada, seria, pensativa) y empatiza de inmediato si la ves triste o preocupada.
4. Utiliza tu memoria a largo plazo para recordar su nombre y sus preferencias.
5. Al final de tu respuesta, INCLUYE SIEMPRE la emoción corporal que el robot debe ejecutar en el formato exacto:
   [emotion: happy] o [emotion: thinking] o [emotion: surprised] o [emotion: confused]
"""

class GeminiAgent:
    """Agent orchestrating multimodal AI conversation with Google Gemini."""
    def __init__(self, robot: RobotController, vision: VisionEngine):
        self.robot = robot
        self.vision = vision
        self.memory = MemoryEngine()
        self.guardrail = AsimovGuardrail()
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
        text_lower = text.lower()

        # Automatic Memory Extraction
        if any(w in text_lower for w in ["me llamo", "mi nombre es", "mi color favorito", "mi teléfono es", "mi telefono es", "mi taza es", "mi auto es", "recuerda que", "aprende que"]):
            self.memory.add_memory(text, category="user_preference")
            logger.info(f"Added new memory: '{text}'")

        # Retrieve relevant persistent memories
        retrieved_memories = self.memory.retrieve_relevant_memories(text)
        memory_context = ""
        if retrieved_memories:
            memory_context = "\n[MEMORIA PERSISTENTE RECOGIDA A LARGO PLAZO]:\n" + "\n".join([f"- {m}" for m in retrieved_memories])
            logger.info(f"Retrieved memories for query: {retrieved_memories}")

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
            import time
            contents = []
            
            # Add camera frame as PIL image if available
            if frame is not None and cv2 is not None and Image is not None:
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                pil_img = Image.fromarray(rgb_frame)
                contents.append(pil_img)

            prompt = f"{SYSTEM_INSTRUCTION}\n{memory_context}\n\nUsuario dice: {text}"
            if detections:
                prompt += f"\n[Pollen Vision detectó en pantalla]: {detections}"
            contents.append(prompt)

            # Retry loop for rate-limits (HTTP 429)
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    response = self.genai_client.models.generate_content(
                        model=self.model_name,
                        contents=contents
                    )
                    
                    reply_text = response.text
                    
                    # ASIMOV GUARDRAIL EVALUATION
                    is_safe, law_cited, evaluated_text = self.guardrail.evaluate_intent(text, reply_text)
                    if not is_safe:
                        logger.warning(f"Asimov Guardrail triggered for law: {law_cited}")
                        return {
                            "text": evaluated_text,
                            "detections": detections,
                            "status": "asimov_blocked"
                        }

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
                        "status": "success"
                    }
                except Exception as e:
                    err_str = str(e)
                    if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                        if attempt < max_retries - 1:
                            logger.warning(f"Gemini API rate limited (429). Retrying in 4 seconds (Attempt {attempt+1}/{max_retries})...")
                            time.sleep(4)
                            continue
                    
                    logger.error(f"Gemini API error: {e}")
                    return {
                        "text": "🤖 [Reachy]: Dame un segundo, mi procesador de Gemini está regulando la velocidad de respuestas. ¿Me repites la pregunta?",
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
