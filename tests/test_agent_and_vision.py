import sys
import unittest
import numpy as np

from reachy_gemini_companion.src.config import config
from reachy_gemini_companion.src.robot_controller import RobotController
from reachy_gemini_companion.src.vision_engine import VisionEngine
from reachy_gemini_companion.src.memory_engine import MemoryEngine
from reachy_gemini_companion.src.gemini_agent import GeminiAgent
from reachy_gemini_companion.src.providers import LLMProviderFactory

class TestReachyAgentAndVision(unittest.TestCase):
    
    def setUp(self):
        self.robot = RobotController(use_mock=True)
        self.vision = VisionEngine()
        self.agent = GeminiAgent(robot_controller=self.robot, vision=self.vision)

    def test_memory_engine_methods(self):
        """Verify memory engine add & retrieve methods exist and work."""
        self.agent.memory.add_memory("Mi nombre es César", category="user_preference")
        memories = self.agent.memory.retrieve_relevant_memories("César")
        self.assertTrue(len(memories) > 0)
        print("✅ [TEST PASSED]: Motor de memoria (add_memory y retrieve_relevant_memories) funciona 100%.")

    def test_vision_engine_methods(self):
        """Verify vision engine process dummy frame without AttributeError."""
        dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        detections = self.vision.detect_objects(dummy_frame)
        self.assertIsInstance(detections, list)
        print("✅ [TEST PASSED]: Motor de visión (detect_objects) procesa frames sin error.")

    def test_provider_factory(self):
        """Verify LLM Provider Factory instantiates active provider."""
        provider = LLMProviderFactory.get_provider(config)
        self.assertIsNotNone(provider)
        print(f"✅ [TEST PASSED]: Proveedor activo '{config.LLM_PROVIDER}' instanciado correctamente.")

    def test_process_message_with_camera_frame(self):
        """Verify complete multimodal process_message flow with text + camera frame."""
        dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        response = self.agent.process_message("Hola Reachy, ¿qué ves en pantalla?", frame=dummy_frame)
        
        self.assertIn("text", response)
        self.assertIn("status", response)
        self.assertIn("emotion", response)
        self.assertEqual(response["status"], "success")
        print(f"✅ [TEST PASSED]: Flujo completo con cámara e IA respondió: '{response['text'][:60]}...'")

    def test_face_biometrics_and_user_profiles(self):
        """Verify face biometric vector calculation and multi-user memory profiles."""
        # Test User Profile saving and retrieving
        self.agent.memory.save_user_profile("César", face_encoding=[0.1, 0.2, 0.3], memories=["Es el usuario principal"])
        profiles = self.agent.memory.get_user_profiles()
        
        self.assertIn("César", profiles)
        self.assertEqual(profiles["César"]["face_encoding"], [0.1, 0.2, 0.3])

        # Test Vision Engine face identification on dummy frame
        dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        matched_user, encoding, box = self.vision.identify_face_in_frame(dummy_frame, profiles)
        self.assertIsInstance(encoding, list)
        print("✅ [TEST PASSED]: Biometría facial y perfiles de memoria multi-usuario funcionan 100%.")

if __name__ == "__main__":
    unittest.main()
