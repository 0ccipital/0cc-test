"""Ollama API client for LLM communication."""

import requests
import json
from typing import List, Dict, Optional
from config import OLLAMA_BASE_URL

class OllamaClient:
    def __init__(self, base_url: str = OLLAMA_BASE_URL):
        self.base_url = base_url.rstrip('/')
        
    def is_connected(self) -> bool:
        """Check if Ollama is accessible."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except Exception:
            return False
    
    def get_available_models(self) -> List[str]:
        """Get list of available models from Ollama."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=10)
            if response.status_code == 200:
                models_data = response.json()
                return [model["name"] for model in models_data.get("models", [])]
            else:
                return []
        except Exception as e:
            print(f"Error fetching models: {e}")
            return []
    
    def chat(self, messages: List[Dict], model: str) -> str:
        """Send chat request to Ollama."""
        try:
            payload = {
                "model": model,
                "messages": messages,
                "stream": False
            }
            
            response = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                return result["message"]["content"]
            else:
                raise Exception(f"Ollama API error: {response.status_code} - {response.text}")
                
        except requests.exceptions.Timeout:
            raise Exception("Request timed out. The model might be processing a complex request.")
        except requests.exceptions.ConnectionError:
            raise Exception("Cannot connect to Ollama. Make sure it's running with 'ollama serve'.")
        except Exception as e:
            raise Exception(f"Chat request failed: {str(e)}")
    
    def unload_model(self, model: str) -> bool:
        """Unload model from memory to clear context."""
        try:
            response = requests.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": model,
                    "messages": [],
                    "keep_alive": 0
                },
                timeout=10
            )
            return response.status_code == 200
        except Exception:
            return False
    
    def check_model_loaded(self, model: str) -> bool:
        """Check if a model is currently loaded."""
        try:
            # Try a minimal request to see if model responds quickly
            response = requests.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": "hi"}],
                    "stream": False
                },
                timeout=5
            )
            return response.status_code == 200
        except Exception:
            return False