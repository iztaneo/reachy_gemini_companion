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


# Camera Frame Generator
def generate_camera_frames():
    """Generate camera frames (Real Laptop Webcam / Physical Robot Camera / Synthetic Fallback)."""
    cap = None
    if not config.USE_MOCK_VISION and cv2 is not None:
        try:
            cap = cv2.VideoCapture(0)
        except Exception as e:
            logger.warning(f"Could not open webcam: {e}")
            cap = None

    angle = 0
    while True:
        frame = None
        if cap and cap.isOpened():
            success, read_frame = cap.read()
            if success and read_frame is not None:
                frame = read_frame

        if frame is None:
            # Create a synthetic 640x480 dark frame with robot overlay for testing
            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            # Add grid pattern
            for i in range(0, 640, 40):
                cv2.line(frame, (i, 0), (i, 480), (15, 25, 40), 1)
            for j in range(0, 480, 40):
                cv2.line(frame, (0, j), (640, j), (15, 25, 40), 1)
                
            timestamp = time.strftime("%H:%M:%S")
            cv2.putText(frame, f"REACHY CAM + POLLEN VISION AI - {timestamp}", (20, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 242, 254), 1)

            # --- Simulated Objects for Pollen Vision demonstration ---
            # Object 1: Coffee Cup (Taza)
            cv2.rectangle(frame, (400, 220), (520, 340), (0, 255, 128), 2)
            cv2.rectangle(frame, (400, 195), (520, 220), (0, 255, 128), -1)
            cv2.putText(frame, "Owl-Vit: Taza (95%)", (405, 212), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 0), 1)
            cv2.circle(frame, (460, 280), 4, (0, 255, 128), -1)

            # Object 2: Phone (Teléfono)
            cv2.rectangle(frame, (120, 140), (220, 280), (79, 172, 254), 2)
            cv2.rectangle(frame, (120, 115), (220, 140), (79, 172, 254), -1)
            cv2.putText(frame, "Owl-Vit: Telefono (91%)", (125, 132), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 0), 1)
            cv2.circle(frame, (170, 210), 4, (79, 172, 254), -1)

            # Orbiting Robot Head Direction Reticle
            angle = (angle + 0.04) % (2 * math.pi)
            cx = int(320 + 100 * math.cos(angle))
            cy = int(240 + 60 * math.sin(angle))
            
            # Crosshair reticle for head tracking
            cv2.circle(frame, (cx, cy), 14, (255, 0, 255), 1)
            cv2.line(frame, (cx - 20, cy), (cx + 20, cy), (255, 0, 255), 1)
            cv2.line(frame, (cx, cy - 20), (cx, cy + 20), (255, 0, 255), 1)
            cv2.putText(frame, "Head Vector", (cx + 18, cy + 5), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 0, 255), 1)

        # Encode frame to JPEG
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
    """Handle chat messages from web user."""
    frame = None
    if not config.USE_MOCK_VISION:
        try:
            cap = cv2.VideoCapture(0)
            ret, frame = cap.read()
            cap.release()
        except Exception:
            frame = None

    response = gemini_agent.process_message(request.message, frame)
    return response


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
