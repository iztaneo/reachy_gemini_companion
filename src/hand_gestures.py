"""
Hand Gestures Recognition Module for Reachy Gemini Companion.
Detects hand gestures (✌️ Victory/Salute, 🖐️ Open Palm/Pause, 👍 Thumbs Up/Confirm)
using OpenCV contour geometry and spatial landmark analysis.
"""
import logging
import numpy as np
from typing import Optional, Dict, Any, List, Tuple

try:
    import cv2
except ImportError:
    cv2 = None

logger = logging.getLogger("HandGestures")

class HandGestureRecognizer:
    """Classifies hand gestures from BGR image frames."""

    def __init__(self):
        logger.info("HandGestureRecognizer initialized.")

    def detect_hand_gesture(self, frame: np.ndarray, face_box: Optional[Tuple[int, int, int, int]] = None) -> Tuple[Optional[str], float, Optional[Tuple[int, int, int, int]]]:
        """
        Classify hand gesture in frame:
        - 'victory' (✌️ Peace / Salute) -> Triggers happy dance & greeting
        - 'palm' (🖐️ Open Palm) -> Triggers listening pause
        - 'thumbs_up' (👍 Thumbs Up) -> Triggers memory saving confirmation
        Returns (gesture_name, confidence, bounding_box).
        """
        if frame is None or cv2 is None:
            return None, 0.0, None

        try:
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            # Skin color mask in HSV space
            lower_skin = np.array([0, 25, 60], dtype=np.uint8)
            upper_skin = np.array([20, 255, 255], dtype=np.uint8)
            mask = cv2.inRange(hsv, lower_skin, upper_skin)

            # Mask out face bounding box region so face/head skin is excluded from hand detection
            if face_box:
                fx, fy, fw, fh = face_box
                # Expand face mask slightly to cover chin and neck
                pad_x = int(fw * 0.2)
                pad_y = int(fh * 0.4)
                my_h, my_w = mask.shape[:2]
                x1 = max(0, fx - pad_x)
                y1 = max(0, fy - pad_y)
                x2 = min(my_w, fx + fw + pad_x)
                y2 = min(my_h, fy + fh + pad_y)
                mask[y1:y2, x1:x2] = 0

            # Apply Gaussian Blur and Morphology
            mask = cv2.GaussianBlur(mask, (5, 5), 0)
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if not contours:
                return None, 0.0, None

            # Find largest skin contour (hand candidate)
            max_contour = max(contours, key=cv2.contourArea)
            area = cv2.contourArea(max_contour)
            if area < 6000: # Filter small background noise
                return None, 0.0, None

            x, y, w, h = cv2.boundingRect(max_contour)
            aspect_ratio = float(w) / h
            hull = cv2.convexHull(max_contour)
            hull_area = cv2.contourArea(hull)
            solidity = float(area) / hull_area if hull_area > 0 else 0

            # Convexity Defects to count extended fingers
            hull_indices = cv2.convexHull(max_contour, returnPoints=False)
            finger_count = 0

            if hull_indices is not None and len(hull_indices) > 3:
                try:
                    defects = cv2.convexityDefects(max_contour, hull_indices)
                    if defects is not None:
                        for i in range(defects.shape[0]):
                            row = defects[i]
                            if len(row.shape) > 1:
                                s, e, f, d = row[0]
                            else:
                                s, e, f, d = row

                            start = tuple(max_contour[int(s)][0])
                            end = tuple(max_contour[int(e)][0])
                            far = tuple(max_contour[int(f)][0])

                            # Calculate angle of defect triangle
                            a = np.sqrt((end[0] - start[0])**2 + (end[1] - start[1])**2)
                            b = np.sqrt((far[0] - start[0])**2 + (far[1] - start[1])**2)
                            c = np.sqrt((end[0] - far[0])**2 + (end[1] - far[1])**2)
                            angle = np.arccos(np.clip((b**2 + c**2 - a**2) / (2 * b * c + 1e-5), -1.0, 1.0)) * (180 / np.pi)

                            # Deep defect angle < 90 deg indicates finger separation
                            if angle <= 90 and float(d) > 800:
                                finger_count += 1
                except Exception as ex:
                    logger.debug(f"Defects calculation debug: {ex}")

            # Gesture classification logic (strict criteria to prevent false positives)
            gesture = None
            confidence = 0.92

            # Open Palm 🖐️: 4-5 fingers extended, area > 10000
            if finger_count in [3, 4, 5] and area > 8000 and solidity < 0.75:
                gesture = "palm"
            # Victory ✌️: Exactly 1-2 finger separation defects, vertical orientation
            elif finger_count in [1, 2] and area > 6000 and solidity < 0.70 and h > w * 0.9:
                gesture = "victory"
            # Thumbs Up 👍: 0 finger separation defects, high aspect ratio
            elif finger_count == 0 and aspect_ratio < 0.75 and area > 7000:
                gesture = "thumbs_up"

            if gesture:
                logger.info(f"Detected Hand Gesture: '{gesture}' (Fingers: {finger_count}, Area: {area:.0f})")
                return gesture, confidence, (x, y, w, h)

        except Exception as e:
            logger.error(f"Error in hand gesture recognition: {e}")

        return None, 0.0, None
