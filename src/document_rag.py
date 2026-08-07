"""
Document RAG Module for Reachy Gemini Companion.
Parses, indexes, and queries technical schematics, datasheets, and PDF/text documentation.
"""
import os
import json
import logging
from typing import List, Dict, Any

logger = logging.getLogger("DocumentRAG")

class DocumentRAGAssistant:
    """Manages technical documentation, schematic datasheets, and circuit reference indexing."""

    def __init__(self, storage_path: str = "data/documents_index.json"):
        self.storage_path = storage_path
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        self.documents: List[Dict[str, Any]] = self._load_documents()

    def _load_documents(self) -> List[Dict[str, Any]]:
        """Load stored document index from JSON."""
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading document index: {e}")
                return []
        
        # Default hardware datasheets
        default_docs = [
            {
                "title": "Datasheet Motor Controller TB6612FNG",
                "content": "El TB6612FNG opera entre 2.5V y 13.5V DC, con corriente continua de 1.2A por canal (pico 3.2A). Pines clave: VM (Alimentación motor), VCC (Lógica 5V), PWMA/PWMB (Velocidad PWM), AIN1/AIN2 (Dirección motor A), STBY (Habilitación)."
            },
            {
                "title": "Manual de Cinemática Reachy Mini Lite",
                "content": "Reachy Mini Lite utiliza 2 servomotores para las antenas (grados de -45° a +60°) y un cuello cinemático de 3 DOF (x, y, z) controlado por el SDK reachy_mini."
            }
        ]
        return default_docs

    def _save_documents(self):
        try:
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(self.documents, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Error saving document index: {e}")

    def add_document(self, title: str, content: str) -> bool:
        """Add a new technical document or schematic description to RAG index."""
        if not title or not content:
            return False
        
        doc = {"title": title.strip(), "content": content.strip()}
        self.documents.append(doc)
        self._save_documents()
        logger.info(f"Added document to RAG Index: '{title}'")
        return True

    def query_documents(self, query: str, limit: int = 3) -> List[str]:
        """Query technical documentation RAG index."""
        if not self.documents:
            return []

        query_words = set(query.lower().split())
        scored = []

        for doc in self.documents:
            title_lower = doc["title"].lower()
            content_lower = doc["content"].lower()
            
            score = 0
            for word in query_words:
                if len(word) > 2:
                    if word in title_lower:
                        score += 3
                    if word in content_lower:
                        score += 1
            
            if score > 0 or any(kw in query.lower() for kw in ["tb6612", "motor", "circuito", "esquema", "pin", "voltaje", "reachy"]):
                scored.append((score, f"[{doc['title']}]: {doc['content']}"))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [item[1] for item in scored[:limit]]
