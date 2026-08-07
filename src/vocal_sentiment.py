"""
Vocal Sentiment Analysis Module for Reachy Gemini Companion.
Analyzes speech rhythm, sentiment keywords, and tone to adjust robot antenna speed and empathy.
"""
import logging
from typing import Dict, Any

logger = logging.getLogger("VocalSentiment")

class VocalSentimentAnalyzer:
    """Analyzes speech sentiment to modulate Reachy's antenna speed and emotional posture."""

    def __init__(self):
        self.excited_words = ["excelente", "genial", "fantástico", "increíble", "súper", "vamos", "buenísimo", "me encanta"]
        self.calm_words = ["tranquilo", "despacio", "calma", "pausa", "relajado", "poco a poco"]

    def analyze_text_sentiment(self, text: str) -> Dict[str, Any]:
        """
        Analyze sentiment tone of input text:
        Returns {'sentiment': 'excited'|'calm'|'neutral', 'antenna_speed': float}
        """
        if not text:
            return {"sentiment": "neutral", "antenna_speed": 1.0}

        text_lower = text.lower()
        excited_count = sum(1 for w in self.excited_words if w in text_lower)
        calm_count = sum(1 for w in self.calm_words if w in text_lower)

        if excited_count > calm_count:
            logger.info("Vocal Sentiment: Excited detected -> Increasing antenna speed.")
            return {"sentiment": "excited", "antenna_speed": 1.8}
        elif calm_count > excited_count:
            logger.info("Vocal Sentiment: Calm detected -> Lowering antenna speed.")
            return {"sentiment": "calm", "antenna_speed": 0.6}

        return {"sentiment": "neutral", "antenna_speed": 1.0}
