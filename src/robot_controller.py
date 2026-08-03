import time
import math
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger("RobotController")

class MockReachy:
    """Mock implementation for testing without physical robot hardware."""
    def __init__(self):
        self.head_pose = {"x": 0.0, "y": 0.0, "z": 0.0, "roll": 0.0, "pitch": 0.0, "yaw": 0.0}
        self.antennas = {"left": 0.0, "right": 0.0}
        self.current_emotion = "neutral"
        logger.info("MockReachy initialized (Simulation Mode)")

    def goto_target(self, head=None, duration=1.0):
        logger.info(f"[Mock Robot] Head movement goto: {head} over {duration}s")

    def play_move(self, move_name: str):
        self.current_emotion = move_name
        logger.info(f"[Mock Robot] Playing emotion move: '{move_name}'")

    def set_antennas(self, left_deg: float, right_deg: float):
        self.antennas["left"] = left_deg
        self.antennas["right"] = right_deg
        logger.info(f"[Mock Robot] Set antennas -> Left: {left_deg}°, Right: {right_deg}°")


class RobotController:
    """Unified Controller for Reachy Mini hardware & Mock simulation."""
    def __init__(self, use_mock: bool = True, host: str = "localhost"):
        self.use_mock = use_mock
        self.robot = None
        self.status = "disconnected"
        
        if not use_mock:
            try:
                from reachy_mini import ReachyMini
                self.robot = ReachyMini(host=host)
                self.status = "connected"
                logger.info("Connected to physical Reachy Mini!")
            except Exception as e:
                logger.warning(f"Failed to connect to Reachy Mini ({e}). Falling back to Mock mode.")
                self.robot = MockReachy()
                self.use_mock = True
                self.status = "mock"
        else:
            self.robot = MockReachy()
            self.status = "mock"

    def express_emotion(self, emotion: str) -> str:
        """Trigger an emotional gesture (happy, sad, thinking, surprised, confused)."""
        logger.info(f"Expressing emotion: {emotion}")
        
        # Antenna dynamics based on emotion
        if emotion == "happy":
            self.set_antennas(30.0, 30.0)
        elif emotion == "thinking":
            self.set_antennas(-20.0, 45.0)
        elif emotion == "surprised":
            self.set_antennas(60.0, 60.0)
        elif emotion == "confused":
            self.set_antennas(-45.0, -45.0)
        else: # neutral / default
            self.set_antennas(0.0, 0.0)

        # Attempt to play recorded move if available
        if not self.use_mock and hasattr(self.robot, "play_move"):
            try:
                from reachy_mini.motion.recorded_move import RecordedMoves
                moves = RecordedMoves("pollen-robotics/reachy-mini-emotions-library")
                if emotion in moves.list_moves():
                    self.robot.play_move(moves.get(emotion))
            except Exception as e:
                logger.warning(f"Could not play emotion '{emotion}': {e}")
        else:
            self.robot.play_move(emotion)
            
        return f"Emotion '{emotion}' expressed successfully"

    def look_at(self, x: float, y: float, z: float = 0.0, duration: float = 1.0):
        """Orient head towards relative coordinates."""
        logger.info(f"Looking at coordinates -> x={x:.2f}, y={y:.2f}, z={z:.2f}")
        if not self.use_mock:
            try:
                from reachy_mini.utils import create_head_pose
                pose = create_head_pose(x=x, y=y, z=z, degrees=True, mm=True)
                self.robot.goto_target(head=pose, duration=duration)
            except Exception as e:
                logger.error(f"Error in look_at: {e}")
        else:
            self.robot.goto_target({"x": x, "y": y, "z": z}, duration=duration)

    def set_antennas(self, left_deg: float, right_deg: float):
        """Set left and right antenna angles in degrees."""
        if hasattr(self.robot, "set_antennas"):
            self.robot.set_antennas(left_deg, right_deg)

    def get_camera_frame(self):
        """Unified method to capture camera frames from Physical Reachy or Laptop Webcam."""
        # 1. Physical Reachy Hardware Camera
        if not self.use_mock and hasattr(self.robot, "get_frame"):
            try:
                frame = self.robot.get_frame()
                if frame is not None:
                    return frame
            except Exception as e:
                logger.warning(f"Could not read frame from physical Reachy camera: {e}")

        # 2. Laptop Webcam / Local OpenCV Camera
        try:
            import cv2
            cap = cv2.VideoCapture(0)
            if cap.isOpened():
                ret, frame = cap.read()
                cap.release()
                if ret and frame is not None:
                    return frame
        except Exception as e:
            logger.debug(f"Webcam not available: {e}")

        # 3. Synthetic Fallback Frame
        return None

    def get_status(self) -> Dict[str, Any]:
        return {
            "mode": "simulation" if self.use_mock else "hardware",
            "status": self.status
        }
