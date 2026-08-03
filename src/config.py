import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

class Config:
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    
    # Robot configuration
    REACHY_HOST: str = os.getenv("REACHY_HOST", "localhost")
    USE_MOCK_ROBOT: bool = os.getenv("USE_MOCK_ROBOT", "true").lower() in ("true", "1", "yes")
    
    # Vision configuration (False = usa la cámara web real de la laptop / robot)
    USE_MOCK_VISION: bool = os.getenv("USE_MOCK_VISION", "false").lower() in ("true", "1", "yes")

config = Config()
