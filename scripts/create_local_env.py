"""
Create .env file for local Ollama development.
"""

import asyncio
import httpx
from pathlib import Path

async def get_available_models():
    """Get available Ollama models."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get("http://localhost:11434/api/tags")
            if response.status_code == 200:
                data = response.json()
                return [m["name"] for m in data.get("models", [])]
    except Exception:
        pass
    return []

def create_env_file():
    """Create .env file for local development."""
    env_file = Path(".env")
    
    # Check available models
    models = asyncio.run(get_available_models())
    
    if models:
        # Use first available model
        model_name = models[0]
        print(f"[INFO] Using available model: {model_name}")
    else:
        model_name = "llama3.1:8b"
        print(f"[WARN] Cannot detect models, using default: {model_name}")
        print(f"[INFO] To download: ollama pull {model_name}")
    
    env_content = f"""# Application settings
DEBUG=false
HOST=0.0.0.0
PORT=8000

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# For local development (not Docker)
REDIS_URL=redis://localhost:6379
QDRANT_URL=http://localhost:6333
OLLAMA_URL=http://localhost:11434

# LLM
OLLAMA_BASE_URL=http://localhost:11434

# Model settings
MODEL_PATH=./models
MODEL_NAME={model_name}

# Simulation settings
SIMULATION_DURATION_DAYS=30
TIME_COMPRESSION_FACTOR=24

# Data storage
DATA_DIR=./data
RESULTS_DIR=./data/results

# CORS settings
CORS_ORIGINS=["*"]
"""
    
    try:
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write(env_content)
        print(f"[OK] Created .env file")
        print(f"[OK] OLLAMA_URL=http://localhost:11434")
        print(f"[OK] MODEL_NAME={model_name}")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to create .env file: {e}")
        return False

if __name__ == "__main__":
    create_env_file()


