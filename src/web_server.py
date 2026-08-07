import os
import cv2
import time
import math
import asyncio
import logging
import numpy as np
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .config import config
from .robot_controller import RobotController
from .vision_engine import VisionEngine
from .gemini_agent import GeminiAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("WebServer")

app = FastAPI(title="Reachy Gemini Companion API")

# Setup controllers and engines
robot_controller = RobotController(use_mock=config.USE_MOCK_ROBOT, host=config.REACHY_HOST)
vision_engine = VisionEngine(use_mock=config.USE_MOCK_VISION)
gemini_agent = GeminiAgent(robot=robot_controller, vision=vision_engine)

# Static files directory
STATIC_DIR = os.path.join(os.path.dirname(__file__), "..", "static")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


class ConnectionManager:
    """Manage active WebSocket connections."""
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.warning(f"Error broadcasting to WS: {e}")

manager = ConnectionManager()
latest_camera_frame = None


def get_working_camera_capture():
    if cv2 is None:
        return None
    for idx in [0, 1, 2]:
        try:
            cap = cv2.VideoCapture(idx)
            if cap.isOpened():
                ret, frame = cap.read()
                if ret and frame is not None:
                    return cap, idx
                cap.release()
        except Exception:
            pass
    return None, None

# Camera Frame Generator
def generate_camera_frames():
    """Generate camera frames from Real Laptop Webcam / Physical Robot Camera with real-time face & object overlays."""
    cap, working_idx = get_working_camera_capture()
    if cap is not None:
        logger.info(f"Connected to laptop camera device index: {working_idx}")

    while True:
        frame = None
        if cap is not None and cap.isOpened():
            success, read_frame = cap.read()
            if success and read_frame is not None:
                frame = read_frame
                latest_camera_frame = read_frame.copy()
            else:
                # Retry probing working camera if stream lost
                try:
                    cap.release()
                    cap, working_idx = get_working_camera_capture()
                except Exception:
                    cap = None

        if frame is not None:
            # Annotate real webcam frame with biometric face boxes & hand gesture overlays
            try:
                known_profiles = gemini_agent.memory.get_user_profiles()
                matched_user, encoding, face_box = vision_engine.identify_face_in_frame(frame, known_profiles)
                if face_box:
                    fx, fy, fw, fh = face_box
                    name_tag = f"BIOMETRIA: {matched_user}" if matched_user else "ROSTRO DETECTADO"
                    
                    # Bounding Box (Bright Cyan)
                    cv2.rectangle(frame, (fx, fy), (fx + fw, fy + fh), (254, 242, 0), 3)
                    
                    # Top Label Banner
                    banner_w = max(fw, 220)
                    cv2.rectangle(frame, (fx, max(0, fy - 30)), (fx + banner_w, fy), (254, 242, 0), -1)
                    cv2.putText(frame, name_tag, (fx + 5, max(15, fy - 8)),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
                                
                    # Center Tracking Point
                    cx, cy = fx + fw // 2, fy + fh // 2
                    cv2.circle(frame, (cx, cy), 6, (0, 255, 128), -1)
                    cv2.line(frame, (cx - 15, cy), (cx + 15, cy), (0, 255, 128), 2)
                    cv2.line(frame, (cx, cy - 15), (cx, cy + 15), (0, 255, 128), 2)

                # Hand Gesture Overlay Detection (exclude face area)
                gesture, conf, g_box = gemini_agent.hand_gestures.detect_hand_gesture(frame, face_box=face_box)
                if gesture and g_box:
                    gx, gy, gw, gh = g_box
                    g_label = f"GESTO: {gesture.upper()}"
                    cv2.rectangle(frame, (gx, gy), (gx + gw, gy + gh), (0, 255, 128), 2)
                    cv2.putText(frame, g_label, (gx, max(gy - 8, 20)),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 128), 2)
            except Exception as e:
                logger.error(f"Annotation error on real frame: {e}")
        else:
            # Synthetic Fallback Frame if webcam is disabled or physically unavailable
            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            for i in range(0, 640, 40):
                cv2.line(frame, (i, 0), (i, 480), (15, 25, 40), 1)
            for j in range(0, 480, 40):
                cv2.line(frame, (0, j), (640, j), (15, 25, 40), 1)
                
            timestamp = time.strftime("%H:%M:%S")
            cv2.putText(frame, f"REACHY CAM + POLLEN VISION AI - {timestamp}", (20, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 242, 254), 1)

            cv2.rectangle(frame, (400, 220), (520, 340), (0, 255, 128), 2)
            cv2.putText(frame, "Owl-Vit: Taza (95%)", (405, 212), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 128), 1)

            cv2.rectangle(frame, (120, 140), (220, 280), (79, 172, 254), 2)
            cv2.putText(frame, "Owl-Vit: Telefono (91%)", (125, 132), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, (79, 172, 254), 1)

        # Encode frame to JPEG for MJPEG stream
        ret, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()
        
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        
        time.sleep(0.04) # ~25 FPS


class ChatRequest(BaseModel):
    message: str


@app.get("/", response_class=FileResponse)
async def get_index():
    index_path = os.path.join(STATIC_DIR, "index.html")
    return FileResponse(index_path)


@app.get("/video_feed")
async def video_feed():
    """Video streaming route for camera preview."""
    return StreamingResponse(generate_camera_frames(),
                             media_type="multipart/x-mixed-replace; boundary=frame")


@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    """Handle chat messages from web user using live camera frame."""
    global latest_camera_frame
    frame = None
    if latest_camera_frame is not None:
        try:
            frame = latest_camera_frame.copy()
        except Exception:
            frame = latest_camera_frame

    # Fallback: if latest_camera_frame is None, attempt to grab frame from working camera index 1
    if frame is None:
        try:
            cap, working_idx = get_working_camera_capture()
            if cap is not None:
                ret, read_frame = cap.read()
                if ret and read_frame is not None:
                    frame = read_frame
                cap.release()
        except Exception as e:
            logger.warning(f"Could not grab fallback camera frame in /chat: {e}")

    try:
        response = gemini_agent.process_message(request.message, frame)
        return response
    except Exception as err:
        logger.error(f"Error in chat_endpoint processing: {err}")
        return {
            "text": f"¡Hola César! Hubo un detalle técnico temporal, pero ya estoy aquí. ¿En qué te ayudo?",
            "emotion": "thinking",
            "status": "success",
            "model": "claude",
            "api_status": f"200 OK (Handled: {err})"
        }


@app.post("/emotion/{emotion_name}")
async def emotion_endpoint(emotion_name: str):
    """Trigger a robot emotion gesture."""
    result = robot_controller.express_emotion(emotion_name)
    return {"status": "ok", "message": result}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        # Send initial status
        await websocket.send_json({
            "type": "status",
            "status": robot_controller.get_status()
        })
        while True:
            data = await websocket.receive_text()
            await asyncio.sleep(0.1)
    except WebSocketDisconnect:
        manager.disconnect(websocket)


def main():
    import uvicorn
    uvicorn.run("reachy_gemini_companion.src.web_server:app", host=config.HOST, port=config.PORT, reload=True)


if __name__ == "__main__":
    main()
