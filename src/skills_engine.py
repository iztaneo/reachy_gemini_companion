"""
Skills Engine Module for Reachy.
Scans the skills/ repository, auto-detects expert skills from conversation context,
and supports dynamic auto-generation of new SKILL.md files.
"""
import os
import re
import logging
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger("SkillsEngine")

class SkillsEngine:
    """Manages skill scanning, prompt template repository, semantic auto-detection, and auto-generation."""

    def __init__(self, skills_dir: str = "skills", prompts_dir: str = "prompts"):
        self.skills_dir = skills_dir
        self.prompts_dir = prompts_dir
        os.makedirs(self.skills_dir, exist_ok=True)
        os.makedirs(self.prompts_dir, exist_ok=True)
        self.skills: Dict[str, Dict[str, Any]] = {}
        self.prompts: Dict[str, str] = {}
        self.reload_skills()
        self.reload_prompts()

    def reload_prompts(self) -> int:
        """Scan prompts/ directory and index all available .txt / .md prompt files."""
        self.prompts.clear()
        if not os.path.exists(self.prompts_dir):
            return 0

        for item in os.listdir(self.prompts_dir):
            item_path = os.path.join(self.prompts_dir, item)
            if os.path.isfile(item_path) and (item.endswith(".txt") or item.endswith(".md")):
                prompt_name = os.path.splitext(item)[0]
                try:
                    with open(item_path, "r", encoding="utf-8") as f:
                        self.prompts[prompt_name] = f.read().strip()
                except Exception as e:
                    logger.error(f"Error loading prompt '{item}': {e}")

        logger.info(f"SkillsEngine: Indexed {len(self.prompts)} custom prompts: {list(self.prompts.keys())}")
        return len(self.prompts)

    def reload_skills(self) -> int:
        """Scan skills/ directory and index all available SKILL.md files."""
        self.skills.clear()
        if not os.path.exists(self.skills_dir):
            return 0

        for item in os.listdir(self.skills_dir):
            item_path = os.path.join(self.skills_dir, item)
            if os.path.isdir(item_path):
                skill_file = os.path.join(item_path, "SKILL.md")
                if os.path.exists(skill_file):
                    skill_data = self._parse_skill_file(skill_file)
                    if skill_data:
                        self.skills[skill_data["name"]] = skill_data

        logger.info(f"SkillsEngine: Indexed {len(self.skills)} skills: {list(self.skills.keys())}")
        return len(self.skills)

    def _parse_skill_file(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Parse frontmatter metadata and body instructions from a SKILL.md file."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            metadata = {}
            body_str = content

            frontmatter_match = re.search(r"^---\s*\n(.*?)\n---\s*\n(.*)$", content, re.DOTALL)
            if frontmatter_match:
                header = frontmatter_match.group(1)
                body_str = frontmatter_match.group(2)
                for line in header.split("\n"):
                    if ":" in line:
                        k, v = line.split(":", 1)
                        k = k.strip()
                        v = v.strip()
                        if v.startswith("[") and v.endswith("]"):
                            v = [x.strip(" '\"") for x in v[1:-1].split(",") if x.strip()]
                        metadata[k] = v

            name = metadata.get("name", os.path.basename(os.path.dirname(file_path)))
            description = metadata.get("description", "")
            keywords = metadata.get("keywords", [])
            if isinstance(keywords, str):
                keywords = [k.strip() for k in keywords.split(",") if k.strip()]

            return {
                "name": name,
                "description": description,
                "keywords": keywords,
                "system_prompt": body_str.strip(),
                "file_path": file_path
            }
        except Exception as e:
            logger.error(f"Error parsing skill file '{file_path}': {e}")
            return None

    def auto_detect_skill(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Auto-detect active skill from conversation context by matching text against skill metadata & keywords.
        Returns the best matching skill dict if score threshold met, or None.
        """
        if not text or not self.skills:
            return None

        text_lower = text.lower()
        best_skill = None
        highest_score = 0

        for name, skill in self.skills.items():
            score = 0
            # 1. Check keyword matches
            keywords = skill.get("keywords", [])
            for kw in keywords:
                if kw.lower() in text_lower:
                    score += 3

            # 2. Check name and description matches
            if name.lower() in text_lower:
                score += 5

            desc_words = [w for w in skill.get("description", "").lower().split() if len(w) > 4]
            for dw in desc_words:
                if dw in text_lower:
                    score += 1

            if score > highest_score and score >= 3:
                highest_score = score
                best_skill = skill

        if best_skill:
            logger.info(f"SkillsEngine: Auto-detected skill '{best_skill['name']}' (Score: {highest_score})")

        return best_skill

    def create_skill(self, name: str, description: str, keywords: List[str], system_prompt: str) -> Tuple[bool, str]:
        """
        Auto-generate a new SKILL.md file physically on disk and reload skills index.
        """
        if not name:
            return False, "Error: El nombre de la habilidad es obligatorio."

        clean_name = re.sub(r"[^a-zA-Z0-9_-]", "", name.lower().replace(" ", "-"))
        skill_dir = os.path.join(self.skills_dir, clean_name)
        os.makedirs(skill_dir, exist_ok=True)

        skill_file = os.path.join(skill_dir, "SKILL.md")

        kw_str = "[" + ", ".join([f"'{k.strip()}'" for k in keywords if k.strip()]) + "]"
        full_content = (
            f"---\n"
            f"name: {clean_name}\n"
            f"description: {description.strip()}\n"
            f"keywords: {kw_str}\n"
            f"---\n\n"
            f"{system_prompt.strip()}\n"
        )

        try:
            with open(skill_file, "w", encoding="utf-8") as f:
                f.write(full_content)

            self.reload_skills()
            logger.info(f"SkillsEngine: Auto-generated new skill '{clean_name}' at '{skill_file}'")
            return True, f"Skill '{clean_name}' auto-generado exitosamente en '{skill_file}'."
        except Exception as e:
            return False, f"Excepción al crear el skill '{clean_name}': {e}"

    def create_prompt(self, name: str, content: str) -> Tuple[bool, str]:
        """
        Auto-generate a new custom prompt template file in prompts/ directory.
        """
        if not name or not content:
            return False, "Error: Nombre y contenido del prompt son requeridos."

        clean_name = re.sub(r"[^a-zA-Z0-9_-]", "", name.lower().replace(" ", "_"))
        prompt_file = os.path.join(self.prompts_dir, f"{clean_name}.md")

        try:
            with open(prompt_file, "w", encoding="utf-8") as f:
                f.write(content.strip() + "\n")

            self.reload_prompts()
            logger.info(f"SkillsEngine: Saved prompt '{clean_name}' at '{prompt_file}'")
            return True, f"Prompt '{clean_name}' guardado exitosamente en '{prompt_file}'."
        except Exception as e:
            return False, f"Excepción al guardar prompt '{clean_name}': {e}"
