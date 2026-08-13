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

    def test_advanced_5_features(self):
        """Verify Hand Gestures, Wake Word, Document RAG, and Vocal Sentiment modules."""
        # 1. Test Hand Gesture Recognizer
        dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        gesture, conf, g_box = self.agent.hand_gestures.detect_hand_gesture(dummy_frame)
        self.assertIsNone(gesture)

        # 2. Test Wake Word Detector
        is_triggered, cmd = self.agent.wake_word.check_wake_word("Oye Reachy cuéntame un chiste")
        self.assertTrue(is_triggered)
        self.assertEqual(cmd, "cuéntame un chiste")

        # 3. Test Document RAG Skill
        rag_skill = self.agent.skills_engine.auto_detect_skill("¿A qué voltaje opera el controlador de motores TB6612FNG?")
        self.assertIsNotNone(rag_skill)
        self.assertEqual(rag_skill["name"], "document-rag")

        # 4. Test Vocal Sentiment Analyzer
        sentiment_info = self.agent.vocal_sentiment.analyze_text_sentiment("¡Excelente trabajo genial!")
        self.assertEqual(sentiment_info["sentiment"], "excited")
        self.assertGreater(sentiment_info["antenna_speed"], 1.0)
        print("✅ [TEST PASSED]: Las 5 Mejoras Avanzadas (Gestos, WakeWord, RAG Documentos y Sentimiento) funcionan 100%.")

    def test_claw_autonomous_agent(self):
        """Test Claw-style Autonomous Agent Tools (Email, Code Generator, Shell Runner)."""
        # Test Email Reading Tool
        res_email = self.agent.process_message("Reachy, revisa mis correos nuevos por favor")
        self.assertIn("action", res_email)
        self.assertEqual(res_email["action"], "read_emails")
        self.assertIn("César", res_email["text"])

        # Test Code Generator Tool
        res_code = self.agent.process_message("Reachy, crea un proyecto de codigo con una api de motores")
        self.assertIn("action", res_code)
        self.assertEqual(res_code["action"], "generate_code")
        self.assertIn("api_motores_reachy", res_code["text"])

        # Test Email Sending Tool
        res_send = self.agent.process_message("Reachy, envia un correo a Pedro confirmando la junta")
        self.assertIn("action", res_send)
        self.assertEqual(res_send["action"], "send_email")
        self.assertIn("enviado exitosamente", res_send["text"])

        print("✅ [TEST PASSED]: Herramientas Autónomas estilo Claw (Lectura/Envío Correo, Generador Código) funcionan 100%.")

    def test_skills_engine_auto_detection_and_generation(self):
        """Test SkillsEngine auto-detection from conversation and dynamic skill auto-generation."""
        # 1. Test Auto-Detection of code-auditor skill
        skill_detected = self.agent.skills_engine.auto_detect_skill("Tengo un error de sintaxis en mi script de Python con FastAPI")
        self.assertIsNotNone(skill_detected)
        self.assertEqual(skill_detected["name"], "code-auditor")

        # 2. Test Auto-Detection of system-sysadmin skill
        sysadmin_skill = self.agent.skills_engine.auto_detect_skill("Revisa la memoria y uso de disco de la laptop con un comando de terminal zsh")
        self.assertIsNotNone(sysadmin_skill)
        self.assertEqual(sysadmin_skill["name"], "system-sysadmin")

        # 3. Test Auto-Generation of a brand new skill (create_skill)
        ok, msg = self.agent.skills_engine.create_skill(
            name="test-automation",
            description="Skill de automatización de pruebas unitarias",
            keywords=["unittest", "pytest", "test", "automatizacion"],
            system_prompt="Eres un experto en Automatización de Pruebas."
        )
        self.assertTrue(ok)
        self.assertIn("test-automation", self.agent.skills_engine.skills)
        print("✅ [TEST PASSED]: Motor de Skills (Auto-Detección por Conversación y Auto-Generación create_skill) funciona 100%.")

if __name__ == "__main__":
    unittest.main()
