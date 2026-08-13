# Plan de Implementación: Auto-Generación de Skills y Auto-Detección Dinámica (`skills/`)

Este plan describe la arquitectura del **Motor de Auto-Detección y Auto-Generación Dinámica de Skills (`src/skills_engine.py`)** en `reachy_gemini_companion`, el cual le permite a Reachy no solo auto-detectar roles según la conversación, sino también **crearse y auto-generarse nuevos skills** (archivos `skills/<nombre>/SKILL.md`) cuando se detecte una necesidad o por comando directo del usuario.

---

## User Review Required

> [!IMPORTANT]
> Se implementará la **Auto-Generación de Nuevos Skills (`create_skill`)**:
> 1. **✨ Auto-Generación por Comando o Necesidad**: Al decirle *"Reachy, crea un nuevo skill para análisis de datos de Pandas"* o cuando detecte una tarea experta sin skill existente, Reachy generará automáticamente un nuevo archivo `skills/<nombre_skill>/SKILL.md` con metadatos, reglas expertas y metaprompt.
> 2. **🔍 Auto-Escaneo y Carga Inmediata**: Una vez auto-generado el skill, `SkillsEngine` lo indexa en tiempo real sin reiniciar el servidor.
> 3. **🤖 Auto-Detección Basada en la Conversación**: Reachy compara la conversación contra el catálogo de skills (incluyendo los auto-generados), selecciona el rol más apto y conmuta su metaprompt de forma fluida.

---

## Proposed Changes

### [Nuevos Módulos y Carpeta de Skills]

#### [NEW] [skills_engine.py](file:///Users/indra/.gemini/antigravity/scratch/reachy_gemini_companion/src/skills_engine.py)
- Módulo encargado de escanear la carpeta `skills/`, parsear metadatos de cada `SKILL.md`, auto-detectar el rol según la conversación (`auto_detect_skill_for_conversation()`) y **auto-generar nuevos skills** (`create_skill()`).

#### [NEW] [skills/code-auditor/SKILL.md](file:///Users/indra/.gemini/antigravity/scratch/reachy_gemini_companion/skills/code-auditor/SKILL.md)
- Skill con metadatos y prompt especializado en auditoría de calidad de software, análisis estático de código, refactorización y detección de bugs.

#### [NEW] [skills/industrial-rpa/SKILL.md](file:///Users/indra/.gemini/antigravity/scratch/reachy_gemini_companion/skills/industrial-rpa/SKILL.md)
- Skill con metadatos y prompt experto en automatización industrial, robótica NATS/Jetson Orin y propuestas tecnológicas Indra.

#### [NEW] [skills/system-sysadmin/SKILL.md](file:///Users/indra/.gemini/antigravity/scratch/reachy_gemini_companion/skills/system-sysadmin/SKILL.md)
- Skill con metadatos y prompt experto en administración de sistemas macOS/Linux, comandos de terminal zsh y monitoreo de recursos.

---

### [Capa de Integración]

#### [MODIFY] [autonomous_agent.py](file:///Users/indra/.gemini/antigravity/scratch/reachy_gemini_companion/src/autonomous_agent.py)
- Inserción del intent de auto-generación de skills (`create_skill`) para que Reachy cree físicamente nuevas carpetas y archivos `SKILL.md` por comando.

#### [MODIFY] [gemini_agent.py](file:///Users/indra/.gemini/antigravity/scratch/reachy_gemini_companion/src/gemini_agent.py)
- Integración de `SkillsEngine` en `GeminiAgent.process_message()` para auto-detectar el rol e inyectar el metaprompt activo antes de consultar la IA.

#### [MODIFY] [docs/architecture.md](file:///Users/indra/.gemini/antigravity/scratch/reachy_gemini_companion/docs/architecture.md)
- Actualización del diagrama de arquitectura para reflejar el motor `SkillsEngine`, la autodetección y la auto-generación de habilidades.

---

### [Pruebas Unitarias]

#### [MODIFY] [test_agent_and_vision.py](file:///Users/indra/.gemini/antigravity/scratch/reachy_gemini_companion/tests/test_agent_and_vision.py)
- Inclusión de los tests `test_skills_engine_auto_detection` y `test_skills_engine_auto_generation` para verificar la autodetección y la auto-creación física de nuevos skills en la suite de pruebas unitarias.

---

## Verification Plan

### Automated Tests
- Ejecución de la suite completa de pruebas unitarias:
  ```bash
  PYTHONPATH=/Users/indra/.gemini/antigravity/scratch /Users/indra/.gemini/antigravity/scratch/reachy_gemini_companion/.venv/bin/python3 -m unittest reachy_gemini_companion.tests.test_agent_and_vision
  ```

### Manual Verification
- Decir a Reachy: *"Reachy, crea un nuevo skill llamado data-analyst para análisis de datos"* y verificar que crea físicamente `skills/data-analyst/SKILL.md`.
- Enviar una consulta sobre errores de código y verificar en los logs: `[SkillsEngine] Auto-detected active skill: 'code-auditor'`.
