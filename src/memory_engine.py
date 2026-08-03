"""
Memory Engine Module for Reachy Gemini Companion.
Handles persistent long-term semantic memory for facts, user preferences, and observations.
"""
import os
import json
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger("MemoryEngine")

class MemoryEngine:
    """Manages persistent long-term memory stored on disk."""

    def __init__(self, storage_path: str = "data/memory_store.json"):
        self.storage_path = storage_path
        self._ensure_storage_dir()
        self.memories: List[Dict[str, Any]] = self._load_memories()

    def _ensure_storage_dir(self):
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)

    def _load_memories(self) -> List[Dict[str, Any]]:
        """Load stored memories from JSON file."""
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading memory file: {e}")
                return []
        return [
            {"fact": "El robot se llama Reachy y es un asistente robótico amistoso.", "category": "system"},
            {"fact": "Reachy tiene la capacidad de mover su cabeza y antenas 3D y reconocer objetos con Pollen Vision.", "category": "system"}
        ]

    def _save_memories(self):
        """Save memories to JSON file."""
        try:
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(self.memories, f, ensure_ascii=False, indent=2)
            logger.info(f"Saved {len(self.memories)} memories to {self.storage_path}")
        except Exception as e:
            logger.error(f"Failed to save memory file: {e}")

    def add_memory(self, fact: str, category: str = "user_preference") -> bool:
        """Add a new memory fact to persistent storage."""
        cleaned_fact = fact.strip()
        if not cleaned_fact:
            return False

        # Avoid duplicates
        for mem in self.memories:
            if mem.get("fact", "").lower() == cleaned_fact.lower():
                return False

        new_entry = {
            "fact": cleaned_fact,
            "category": category,
            "timestamp": logger.root.handlers[0].formatter.formatTime(logging.LogRecord("", 0, "", 0, "", (), None)) if logger.root.handlers else ""
        }
        self.memories.append(new_entry)
        self._save_memories()
        return True

    def retrieve_relevant_memories(self, query: str, limit: int = 5) -> List[str]:
        """Search and retrieve memories relevant to user query."""
        if not self.memories:
            return []

        query_lower = query.lower()
        query_words = set(query_lower.split())

        scored_memories = []
        for mem in self.memories:
            fact_text = mem.get("fact", "")
            fact_lower = fact_text.lower()
            
            # Simple keyword overlap scoring
            score = 0
            for word in query_words:
                if len(word) > 2 and word in fact_lower:
                    score += 1
                    
            if score > 0 or any(w in query_lower for w in ["quién", "quien", "quienes", "recuerdas", "sabes", "nombre", "preferencia", "taza", "teléfono", "telefono"]):
                scored_memories.append((score, fact_text))

        # Sort by relevance score
        scored_memories.sort(key=lambda x: x[0], reverse=True)
        results = [m[1] for m in scored_memories[:limit]]
        
        # Always include top user memories if query asks about user/identity
        if not results and any(w in query_lower for w in ["recuerdas", "sabes de mi", "quién soy", "quien soy", "mi"]):
            results = [m["fact"] for m in self.memories if m.get("category") == "user_preference"]

        return results

    def get_all_memories(self) -> List[Dict[str, Any]]:
        """Return all stored memories."""
        return self.memories
