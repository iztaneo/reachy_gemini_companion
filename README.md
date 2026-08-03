# 🤖🧠👁️ Reachy Gemini Companion

Un proyecto completo que unifica la robótica expresiva de **Reachy Mini**, la visión por computadora zero-shot de **Pollen Vision** y la inteligencia multimodal conversacional de **Google Gemini**.

## 🌟 Características
- **Multimodal Chat con Gemini**: Conversación por voz/texto viendo en vivo lo que ve la cámara del robot.
- **Detección Visual Zero-Shot**: Integración con `Owl-Vit` y `Mobile-SAM` para detectar objetos por texto y hacer que el robot los siga con la cabeza.
- **Expresiones Robóticas**: Control de emociones (alegría, sorpresa, reflexión) y movimiento dinámico de antenas.
- **Soporte Físico y Simulación (Mock)**: Se ejecuta tanto en un robot Reachy Mini/Lite real como en modo simulado para Mac/PC.
- **UI Web Moderna**: Dashboard glassmorphism interactivo con WebSockets.

## 🚀 Inicio Rápido

1. Configura tu API Key de Gemini:
   ```bash
   export GEMINI_API_KEY="tu_clave_api_aqui"
   ```

2. Ejecuta el servidor web:
   ```bash
   python3 -m reachy_gemini_companion.src.web_server
   ```

3. Abre tu navegador en `http://localhost:8000`.
