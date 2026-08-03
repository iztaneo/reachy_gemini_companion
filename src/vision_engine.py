try:
    import cv2
except ImportError:
    cv2 = None

import numpy as np
import logging
from typing import List, Dict, Any, Tuple, Optional

logger = logging.getLogger("VisionEngine")

class VisionEngine:
    """Vision processing engine integrating Pollen Vision zero-shot detection."""
    def __init__(self, use_mock: bool = False):
        self.use_mock = use_mock
        self.owl_vit = None
        self.sam = None
        
        if not use_mock:
            try:
                from pollen_vision.vision_models.object_detection import OwlVitWrapper
                self.owl_vit = OwlVitWrapper()
                logger.info("Pollen Vision OwlVitWrapper loaded successfully!")
            except Exception as e:
                logger.warning(f"Could not load Pollen Vision OwlVitWrapper ({e}). Using mock/fallback vision.")
                self.use_mock = True

    def detect_objects(self, frame: np.ndarray, queries: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Perform zero-shot object detection for given text queries."""
        if frame is None or len(frame) == 0:
            return []

        if queries is None:
            queries = ["person", "face", "object"]

        h, w, _ = frame.shape
        detected = []

        if not self.use_mock and self.owl_vit is not None:
            try:
                predictions = self.owl_vit.infer(frame, queries)
                for pred in predictions:
                    # pred: box [x1, y1, x2, y2], score, label
                    box = pred.get("box", [0, 0, 0, 0])
                    label = pred.get("label", "object")
                    score = pred.get("score", 0.0)
                    
                    x1, y1, x2, y2 = map(int, box)
                    cx = (x1 + x2) // 2
                    cy = (y1 + y2) // 2
                    
                    detected.append({
                        "label": label,
                        "score": float(score),
                        "bbox": [x1, y1, x2, y2],
                        "center": [cx, cy],
                        "norm_center": [(cx / w) * 2 - 1, (cy / h) * 2 - 1] # [-1, 1] range
                    })
            except Exception as e:
                logger.error(f"Error during Pollen Vision inference: {e}")
        else:
            # Fallback / Mock detection for demonstration
            for query in queries:
                # Generate a mock bounding box around center for testing
                cx, cy = w // 2, h // 2
                x1, y1 = cx - 80, cy - 80
                x2, y2 = cx + 80, cy + 80
                detected.append({
                    "label": query,
                    "score": 0.92,
                    "bbox": [x1, y1, x2, y2],
                    "center": [cx, cy],
                    "norm_center": [0.0, 0.0]
                })

        return detected

    def annotate_frame(self, frame: np.ndarray, detections: List[Dict[str, Any]]) -> np.ndarray:
        """Draw bounding boxes and labels onto the image frame."""
        if frame is None or cv2 is None:
            return frame

        annotated = frame.copy()
        for det in detections:
            x1, y1, x2, y2 = det["bbox"]
            label = det["label"]
            score = det["score"]
            
            # Green bounding box
            cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 255, 128), 2)
            
            # Label banner
            text = f"{label}: {score:.2f}"
            cv2.putText(annotated, text, (x1, max(y1 - 10, 20)), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 128), 2)
            
            # Center point
            cx, cy = det["center"]
            cv2.circle(annotated, (cx, cy), 5, (0, 0, 255), -1)
            
        return annotated
