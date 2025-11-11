"""
Setup script for local Ollama configuration.

This script helps configure Ollama for local development.
"""

import os
import sys
from pathlib import Path

def setup_local_ollama():
    """Setup local Ollama configuration."""
    
    print("=" * 80)
    print("PROXIMO Local Ollama Setup")
    print("=" * 80)
    
    # Check if .env exists
    env_file = Path(".env")
    if env_file.exists():
        print("\n[INFO] .env file already exists")
        response = input("Do you want to update it? (y/n): ").strip().lower()
        if response != 'y':
            print("[INFO] Skipping .env file update")
            return
    else:
        print("\n[INFO] Creating .env file...")
    
    # Check available models
    print("\n[INFO] Checking available Ollama models...")
    try:
        import httpx
        import asyncio
        import json
        
        async def check_models():
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    response = await client.get("http://localhost:11434/api/tags")
                    if response.status_code == 200:
                        data = response.json()
                        models = [m["name"] for m in data.get("models", [])]
                        return models
                    return []
            except Exception:
                return []
        
        available_models = asyncio.run(check_models())
        
        if available_models:
            print(f"\n[OK] Found {len(available_models)} available model(s):")
            for i, model in enumerate(available_models, 1):
                print(f"  {i}. {model}")
            
            # Select model
            print("\n[INFO] Select a model to use:")
            print("  (Enter number or model name, or 'skip' to keep default)")
            choice = input("Choice: ").strip()
            
            selected_model = None
            if choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(available_models):
                    selected_model = available_models[idx]
            elif choice.lower() != 'skip':
                if choice in available_models:
                    selected_model = choice
                else:
                    print(f"[WARN] Model '{choice}' not found, using first available: {available_models[0]}")
                    selected_model = available_models[0]
            
            if not selected_model:
                selected_model = available_models[0] if available_models else "llama3.1:8b"
        else:
            print("\n[WARN] Cannot connect to Ollama or no models found")
            print("[INFO] Using default model: llama3.1:8b")
            selected_model = "llama3.1:8b"
            print("[INFO] To download this model, run: ollama pull llama3.1:8b")
            
    except ImportError:
        print("[WARN] httpx not available, using default model")
        selected_model = "llama3.1:8b"
    
    # Create .env content
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
MODEL_NAME={selected_model}

# Simulation settings
SIMULATION_DURATION_DAYS=30
TIME_COMPRESSION_FACTOR=24

# Data storage
DATA_DIR=./data
RESULTS_DIR=./data/results

# CORS settings
CORS_ORIGINS=["*"]
"""
    
    # Write .env file
    try:
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write(env_content)
        print(f"\n[OK] Created/updated .env file")
        print(f"[OK] Ollama URL: http://localhost:11434")
        print(f"[OK] Model: {selected_model}")
        print("\n[INFO] You can now run test_conversation_pipeline.py")
    except Exception as e:
        print(f"\n[ERROR] Failed to create .env file: {e}")
        print("\n[INFO] Please manually create .env file with:")
        print("  OLLAMA_URL=http://localhost:11434")
        print(f"  MODEL_NAME={selected_model}")
        sys.exit(1)
    
    print("\n" + "=" * 80)
    print("Setup completed!")
    print("=" * 80)

if __name__ == "__main__":
    setup_local_ollama()


