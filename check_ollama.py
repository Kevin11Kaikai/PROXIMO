"""Quick script to check Ollama models."""
import asyncio
import httpx
import json

async def check_ollama():
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get("http://localhost:11434/api/tags")
            if response.status_code == 200:
                data = response.json()
                models = data.get("models", [])
                print(f"\n[OK] Ollama is running at http://localhost:11434")
                print(f"\nAvailable models:")
                for model in models:
                    name = model.get("name", "unknown")
                    size = model.get("size", 0) / (1024**3)  # Convert to GB
                    print(f"  - {name} ({size:.2f} GB)")
                return [m["name"] for m in models]
            else:
                print(f"[ERROR] Ollama returned status {response.status_code}")
                return []
    except Exception as e:
        print(f"[ERROR] Cannot connect to Ollama: {e}")
        return []

if __name__ == "__main__":
    asyncio.run(check_ollama())


