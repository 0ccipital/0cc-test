"""Streaming response handling with memory management."""

import json
import requests
from typing import Iterator, Generator
from collections import deque
from utils.errors import StreamingError, LLMError

class StreamingHandler:
    """Handle streaming responses with memory management."""
    
    def __init__(self, buffer_size: int = 1024):
        self._buffer_size = buffer_size
        self._response_buffer = deque(maxlen=buffer_size)
    
    def stream_chat(self, url: str, payload: dict, timeout: int = 60) -> Generator[str, None, str]:
        """
        Stream chat response with memory-efficient buffering.
        
        Yields:
            str: Content chunks as they arrive
            
        Returns:
            str: Complete response text
        """
        self._response_buffer.clear()
        
        try:
            response = requests.post(
                url,
                json=payload,
                stream=True,
                timeout=timeout
            )
            response.raise_for_status()
            
            for line in response.iter_lines(decode_unicode=True):
                if line:
                    try:
                        chunk = json.loads(line)
                        content = chunk.get('message', {}).get('content', '')
                        
                        if content:
                            self._response_buffer.append(content)
                            yield content
                            
                        # Check if streaming is done
                        if chunk.get('done', False):
                            break
                            
                    except json.JSONDecodeError:
                        # Skip malformed JSON lines
                        continue
                        
        except requests.exceptions.Timeout:
            raise StreamingError("Request timed out. The model might be processing a complex request.")
        except requests.exceptions.ConnectionError:
            raise StreamingError("Cannot connect to Ollama. Make sure it's running with 'ollama serve'.")
        except requests.exceptions.RequestException as e:
            raise StreamingError(f"Request failed: {e}")
        except Exception as e:
            raise StreamingError(f"Streaming failed: {e}")
        
        # Return complete response
        return ''.join(self._response_buffer)
    
    def get_buffer_size(self) -> int:
        """Get current buffer size."""
        return len(self._response_buffer)
    
    def clear_buffer(self) -> None:
        """Clear response buffer."""
        self._response_buffer.clear()