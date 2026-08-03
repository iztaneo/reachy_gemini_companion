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
    
    # LLM Provider configuration ("gemini" for Cloud or "ollama" for Local)
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "gemini").lower()
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "gemma4:latest")
    OLLAMA_HOST: str = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    
    # Robot configuration (False = usa la cámara web real de la laptop / robot)
    REACHY_HOST: str = os.getenv("REACHY_HOST", "localhost")
    USE_MOCK_ROBOT: bool = os.getenv("USE_MOCK_ROBOT", "true").lower() in ("true", "1", "yes")
    
    # Vision configuration
    USE_MOCK_VISION: bool = os.getenv("USE_MOCK_VISION", "false").lower() in ("true", "1", "yes")

config = Config()
