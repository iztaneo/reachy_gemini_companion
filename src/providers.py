import re
import json
import logging
import base64
import numpy as np
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

try:
    import cv2
except ImportError:
    cv2 = None

from PIL import Image
from reachy_gemini_companion.src.config import Config

logger = logging.getLogger("LLMProviders")

class BaseLLMProvider(ABC):
    """Unified Abstract Base Provider for all LLMs (Gemini, Claude, Ollama)."""
    
    @abstractmethod
    def generate(self, prompt: str, system_instruction: str, memory_context: str, frame: Optional[np.ndarray] = None, detections: Optional[list] = None) -> Dict[str, Any]:
        """Generates a response from the LLM given prompt, system instruction, memories, and optional camera frame."""
        pass

class GeminiProvider(BaseLLMProvider):
    def __init__(self, config: Config):
        from google import genai
        self.config = config
        self.client = genai.Client(api_key=config.GEMINI_API_KEY)
        self.model_name = config.GEMINI_MODEL

    def generate(self, prompt: str, system_instruction: str, memory_context: str, frame: Optional[np.ndarray] = None, detections: Optional[list] = None) -> Dict[str, Any]:
        full_prompt = f"{system_instruction}\n{memory_context}\n\nUsuario: {prompt}"
        if detections:
            full_prompt += f"\n[Pollen Vision detectó]: {detections}"

        contents = [full_prompt]

        if frame is not None:
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(rgb_frame)
            contents.append(pil_img)

        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=contents
            )
            return {
                "text": response.text,
                "model": self.model_name,
                "provider": "gemini",
                "status": "success",
                "api_status": "200 OK (Gemini)"
            }
        except Exception as e:
            err_str = str(e)
            return {
                "text": f"⚠️ [Gemini Rate Limit / Error]: {err_str}",
                "model": self.model_name,
                "provider": "gemini",
                "status": "rate_limited" if "429" in err_str else "error",
                "api_status": f"Gemini Error: {err_str}"
            }

class ClaudeProvider(BaseLLMProvider):
    def __init__(self, config: Config):
        import anthropic
        self.config = config
        self.client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
        self.model_name = config.CLAUDE_MODEL

    def generate(self, prompt: str, system_instruction: str, memory_context: str, frame: Optional[np.ndarray] = None, detections: Optional[list] = None) -> Dict[str, Any]:
        full_system = f"{system_instruction}\n{memory_context}"
        user_text = prompt
        if detections:
            user_text += f"\n[Pollen Vision detectó]: {detections}"

        messages_payload = []

        # Attach camera frame image if available
        if frame is not None and cv2 is not None:
            _, img_buffer = cv2.imencode('.jpg', frame)
            img_b64 = base64.b64encode(img_buffer.tobytes()).decode('utf-8')
            messages_payload.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/jpeg",
                    "data": img_b64
                }
            })

        messages_payload.append({
            "type": "text",
            "text": user_text
        })

        try:
            response_msg = self.client.messages.create(
                model=self.model_name,
                max_tokens=300,
                system=full_system,
                messages=[{"role": "user", "content": messages_payload}]
            )
            return {
                "text": response_msg.content[0].text,
                "model": self.model_name,
                "provider": "claude",
                "status": "success",
                "api_status": "200 OK (Claude)"
            }
        except Exception as e:
            err_str = str(e)
            return {
                "text": f"⚠️ [Claude Error]: {err_str}",
                "model": self.model_name,
                "provider": "claude",
                "status": "error",
                "api_status": f"Claude Error: {err_str}"
            }

class OllamaProvider(BaseLLMProvider):
    def __init__(self, config: Config):
        import urllib.request
        self.config = config
        self.model_name = config.OLLAMA_MODEL
        self.host = config.OLLAMA_HOST

    def generate(self, prompt: str, system_instruction: str, memory_context: str, frame: Optional[np.ndarray] = None, detections: Optional[list] = None) -> Dict[str, Any]:
        import urllib.request
        full_prompt = f"{system_instruction}\n{memory_context}\n\nUsuario: {prompt}"
        if detections:
            full_prompt += f"\n[Pollen Vision detectó]: {detections}"

        images_b64 = []
        if frame is not None and cv2 is not None:
            _, img_buffer = cv2.imencode('.jpg', frame)
            img_b64 = base64.b64encode(img_buffer.tobytes()).decode('utf-8')
            images_b64.append(img_b64)

        url = f"{self.host}/api/generate"
        payload_dict = {
            "model": self.model_name,
            "prompt": full_prompt,
            "stream": False
        }
        if images_b64:
            payload_dict["images"] = images_b64

        payload = json.dumps(payload_dict).encode("utf-8")
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})

        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                res_data = json.loads(resp.read().decode("utf-8"))
                return {
                    "text": res_data.get("response", ""),
                    "model": self.model_name,
                    "provider": "ollama",
                    "status": "success",
                    "api_status": "200 OK (Ollama)"
                }
        except Exception as e:
            return {
                "text": f"⚠️ [Ollama Error]: {e}",
                "model": self.model_name,
                "provider": "ollama",
                "status": "error",
                "api_status": f"Ollama Error: {e}"
            }

class LLMProviderFactory:
    """Factory to instantiate the appropriate provider based on configuration."""
    
    @staticmethod
    def get_provider(config: Config) -> BaseLLMProvider:
        provider_name = config.LLM_PROVIDER.lower()
        if provider_name == "claude":
            logger.info("Initializing Anthropic Claude LLM Provider...")
            return ClaudeProvider(config)
        elif provider_name == "ollama":
            logger.info("Initializing Ollama Local LLM Provider...")
            return OllamaProvider(config)
        else:
            logger.info("Initializing Google Gemini LLM Provider...")
            return GeminiProvider(config)
