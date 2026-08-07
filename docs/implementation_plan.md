# Plan de Implementación: Agente Autónomo Ejecutivo estilo Claw (Opción A Nativa)

Este documento establece la arquitectura e implementación del **Módulo de Agente Autónomo con Herramientas Ejecutables (Tool Use / Function Calling)** en el repositorio `reachy_gemini_companion`.

---

## User Review Required

> [!IMPORTANT]
> Se implementarán 3 herramientas ejecutivas nativas que Reachy invocará de forma autónoma al conversar contigo:
> 1. **📧 Herramienta de Correo Electrónico (`src/tools/email_tool.py`)**: Lectura de correos, resúmenes ejecutivos y envío de mensajes (con almacenamiento y configuración local).
> 2. **💻 Generador de Proyectos de Código (`src/tools/code_generator.py`)**: Creación automática de carpetas, archivos y proyectos completos de código (ej. FastAPI, Python scripts).
> 3. **⚙️ Ejecutor de Comandos y Pruebas (`src/tools/shell_runner.py`)**: Ejecución de pruebas y comandos de terminal de forma segura.

---

## Proposed Changes

### [Nuevos Módulos de Herramientas Ejecutivas]

#### [NEW] [email_tool.py](file:///Users/indra/.gemini/antigravity/scratch/reachy_gemini_companion/src/tools/email_tool.py)
- Módulo para consultar bandejas de entrada, hacer resúmenes ejecutivos de correos y enviar mensajes redactados.

#### [NEW] [code_generator.py](file:///Users/indra/.gemini/antigravity/scratch/reachy_gemini_companion/src/tools/code_generator.py)
- Módulo para estructurar y escribir proyectos multi-archivo de código en una carpeta de destino (ej. `generated_projects/mi_app`).

#### [NEW] [shell_runner.py](file:///Users/indra/.gemini/antigravity/scratch/reachy_gemini_companion/src/tools/shell_runner.py)
- Módulo seguro de ejecución de comandos de terminal para probar código y verificar sintaxis.

#### [NEW] [autonomous_agent.py](file:///Users/indra/.gemini/antigravity/scratch/reachy_gemini_companion/src/autonomous_agent.py)
- Orquestador del bucle de razonamiento autónomo (Thought → Tool Action → Observation) integrado con Anthropic Claude / Gemini Tool Calling.

---

### [Capa de Integración]

#### [MODIFY] [providers.py](file:///Users/indra/.gemini/antigravity/scratch/reachy_gemini_companion/src/providers.py)
- Soporte para esquemas de herramientas (Tools/Functions) en `ClaudeProvider` y `GeminiProvider`.

#### [MODIFY] [gemini_agent.py](file:///Users/indra/.gemini/antigravity/scratch/reachy_gemini_companion/src/gemini_agent.py)
- Inyección del bucle del agente autónomo cuando el usuario solicite tareas de correo, programación o ejecución de comandos.

---

### [Pruebas Unitarias]

#### [MODIFY] [test_agent_and_vision.py](file:///Users/indra/.gemini/antigravity/scratch/reachy_gemini_companion/tests/test_agent_and_vision.py)
- Incorporación de pruebas automáticas para verificar el funcionamiento de `EmailTool`, `CodeGenerator` y `AutonomousAgent`.

---

## Verification Plan

### Automated Tests
- Ejecución de la batería de pruebas unitarias:
  ```bash
  PYTHONPATH=/Users/indra/.gemini/antigravity/scratch /Users/indra/.gemini/antigravity/scratch/reachy_gemini_companion/.venv/bin/python3 -m unittest reachy_gemini_companion.tests.test_agent_and_vision
  ```

### Manual Verification
- Solicitar a Reachy por voz/chat: *"Reachy, créame una API en Python en la carpeta generated_projects/mi_api"* y verificar la creación física del proyecto de código.
