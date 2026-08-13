# Arquitectura General: Reachy Gemini Companion 🤖🧠👁️🔊

Este documento describe la arquitectura modular del sistema **Reachy Gemini Companion**, diseñado para proveer interacción humano-robot multimodal en tiempo real.

---

## 🏛️ Diagrama de Componentes

```
                                +---------------------------+
                                |  Navegador Web Frontend   |
                                | (Three.js 3D + Audio Web) |
                                +-------------+-------------+
                                              |
                                       WebSocket / HTTP REST
                                              |
                                              v
                                +---------------------------+
                                |   FastAPI Web Server      |
                                |    (src/web_server.py)    |
                                +-------------+-------------+
                                              |
                                              v
                                +---------------------------+
                                |      GeminiAgent          |
                                |   (src/gemini_agent.py)   |
                                +----+-----+-----+----+-----+
                                     |     |     |    |
          +--------------------------+     |     |    +-------------------------+
          |                                |     |                              |
          v                                v     v                              v
+------------------+         +---------------+ +---------------+      +-------------------+
|  FaceBiometrics  |         | MemoryEngine  | | VisionEngine  |      |  AutonomousAgent  |
| (YuNet 128D ONNX)|         | (TinyDB NoSQL)| | (OWL-ViT AI)  |      |  (Claw Tools AI)  |
+------------------+         +---------------+ +---------------+      +---------+---------+
                                                                                |
                                                               +----------------+----------------+
                                                               |                |                |
                                                               v                v                v
                                                        +--------------+ +--------------+ +-------------+
                                                        |  EmailTool   | |CodeGenerator | | ShellRunner |
                                                        +--------------+ +--------------+ +-------------+
```

---

## 🛠️ Descripción de Módulos Principales

1. **`src/web_server.py`**:
   - Servidor FastAPI con streaming MJPEG a ~25 FPS, endpoints REST y WebSockets para actualización en tiempo real de widgets biométricos y gestos de manos.
2. **`src/face_biometrics.py`**:
   - Extractor biométrico facial basado en el modelo profundo YuNet ONNX (`cv2.FaceDetectorYN`) para firmas numéricas de 128 dimensiones y coincidencia por distancia euclidiana.
3. **`src/memory_engine.py`**:
   - Almacenamiento continuo sin pedir "guárdalo", organizando perfiles por usuario (`user_profiles`) e indexando recuerdos en TinyDB / JSON RAG.
4. **`src/providers.py`**:
   - Patrón Provider Factory para Anthropic Claude 3.5, Google Gemini y Ollama Local.
5. **`src/hand_gestures.py`**:
   - Clasificador de gestos de manos (✌️ Paz/Saludo, 🖐️ Palma/Alto, 👍 Confirmar).
6. **`src/autonomous_agent.py` & `src/tools/`**:
   - Agente autónomo estilo Claw equipado con herramientas para interacción con correo electrónico, generación de proyectos de código multi-archivo y ejecución de pruebas de terminal.
7. **`src/skills_engine.py` & `skills/`**:
   - Repositorio modular de habilidades e instrucciones expertas (`skills/<nombre>/SKILL.md`). Incluye autodetección dinámica de roles basándose en la conversación y auto-generación física de nuevos skills.
