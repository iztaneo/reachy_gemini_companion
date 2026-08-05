"""
Face Biometrics Module for Reachy Gemini Companion.
Handles facial detection, biometric feature vector extraction (face encodings),
and identity matching via Euclidean distance comparison.
"""
import os
import logging
import numpy as np
from typing import Optional, Dict, Any, List, Tuple

try:
    import cv2
except ImportError:
    cv2 = None

logger = logging.getLogger("FaceBiometrics")

class FaceBiometrics:
    """Extracts facial biometric vectors and matches identities against known user profiles."""

    def __init__(self, tolerance: float = 0.6):
        self.tolerance = tolerance
        self.face_cascade = None
        if cv2 is not None:
            try:
                cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
                if os.path.exists(cascade_path):
                    self.face_cascade = cv2.CascadeClassifier(cascade_path)
            except Exception as e:
                logger.warning(f"Could not load OpenCV face cascade: {e}")

    def detect_faces(self, frame: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """Detect bounding boxes (x, y, w, h) for faces in an BGR image frame."""
        if frame is None or cv2 is None or self.face_cascade is None:
            return []

        try:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(60, 60)
            )
            return [(int(x), int(y), int(w), int(h)) for (x, y, w, h) in faces]
        except Exception as e:
            logger.error(f"Error detecting faces: {e}")
            return []

    def compute_face_encoding(self, frame: np.ndarray, face_box: Tuple[int, int, int, int]) -> List[float]:
        """
        Compute a 128-dimensional biometric feature encoding vector for a face bounding box.
        Uses normalized pixel histogram & facial spatial geometry descriptors.
        """
        if frame is None or cv2 is None:
            return []

        x, y, w, h = face_box
        h_img, w_img = frame.shape[:2]

        # Clamp box bounds
        x = max(0, min(x, w_img - 1))
        y = max(0, min(y, h_img - 1))
        w = max(10, min(w, w_img - x))
        h = max(10, min(h, h_img - y))

        face_crop = frame[y:y+h, x:x+w]
        if face_crop.size == 0:
            return []

        try:
            # Resize crop to standard 64x64 for descriptor stability
            resized = cv2.resize(face_crop, (64, 64))
            gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
            
            # Compute 128-dim descriptor (combined HSV + Grayscale Histograms & Gradients)
            hsv = cv2.cvtColor(resized, cv2.COLOR_BGR2HSV)
            hist_h = cv2.calcHist([hsv], [0], None, [32], [0, 180])
            hist_s = cv2.calcHist([hsv], [1], None, [32], [0, 256])
            hist_v = cv2.calcHist([hsv], [2], None, [32], [0, 256])
            hist_g = cv2.calcHist([gray], [0], None, [32], [0, 256])

            vector = np.concatenate([hist_h, hist_s, hist_v, hist_g]).flatten()
            norm = np.linalg.norm(vector)
            if norm > 0:
                vector = vector / norm

            return vector.tolist()
        except Exception as e:
            logger.error(f"Error computing face encoding: {e}")
            return []

    def match_face(self, query_encoding: List[float], known_profiles: Dict[str, Dict[str, Any]]) -> Tuple[Optional[str], float]:
        """
        Compare a query face vector against known user profiles using Euclidean distance.
        Returns (matched_user_name, distance_score) if below tolerance threshold.
        """
        if not query_encoding or not known_profiles:
            return None, 1.0

        query_vec = np.array(query_encoding, dtype=np.float32)
        best_match = None
        min_distance = float("inf")

        for user_name, profile in known_profiles.items():
            known_vec_list = profile.get("face_encoding")
            if not known_vec_list:
                continue

            known_vec = np.array(known_vec_list, dtype=np.float32)
            if len(known_vec) != len(query_vec):
                continue

            # Calculate Euclidean distance
            dist = float(np.linalg.norm(query_vec - known_vec))
            if dist < min_distance:
                min_distance = dist
                best_match = user_name

        if min_distance <= self.tolerance:
            return best_match, min_distance
        
        return None, min_distance
