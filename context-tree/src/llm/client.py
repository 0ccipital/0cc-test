"""LLM client with streaming support."""

import requests
from typing import List, Dict, Optional, Generator
from llm.streaming import StreamingHandler
from utils.errors import LLMError

class OllamaClient:
    """Ollama client with streaming and error handling."""
    
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url.rstrip('/')
        self.streaming_handler = StreamingHandler()
        
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
            response.raise_for_status()
            
            models_data = response.json()
            return [model["name"] for model in models_data.get("models", [])]
            
        except requests.exceptions.RequestException as e:
            raise LLMError(f"Failed to fetch models: {e}")
        except Exception as e:
            raise LLMError(f"Error getting models: {e}")
    
    def chat_stream(self, messages: List[Dict], model: str) -> Generator[str, None, str]:
        """
        Send chat request with streaming response.
        
        Args:
            messages: List of message dictionaries
            model: Model name to use
            
        Yields:
            str: Content chunks as they arrive
            
        Returns:
            str: Complete response text
        """
        payload = {
            "model": model,
            "messages": messages,
            "stream": True
        }
        
        url = f"{self.base_url}/api/chat"
        return self.streaming_handler.stream_chat(url, payload)
    
    def chat(self, messages: List[Dict], model: str) -> str:
        """
        Send chat request and return complete response.
        
        Args:
            messages: List of message dictionaries
            model: Model name to use
            
        Returns:
            str: Complete response text
        """
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
            response.raise_for_status()
            
            result = response.json()
            return result["message"]["content"]
            
        except requests.exceptions.Timeout:
            raise LLMError("Request timed out. The model might be processing a complex request.")
        except requests.exceptions.ConnectionError:
            raise LLMError("Cannot connect to Ollama. Make sure it's running with 'ollama serve'.")
        except requests.exceptions.RequestException as e:
            raise LLMError(f"Chat request failed: {e}")
        except KeyError as e:
            raise LLMError(f"Invalid response format: missing {e}")
        except Exception as e:
            raise LLMError(f"Chat failed: {e}")
    
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