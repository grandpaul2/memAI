"""
Core Ollama API client for WorkspaceAI

Handles basic API communication, connection testing, and request/response cycles.
"""

import json
import logging
import requests
import time
from typing import Dict, List, Optional, Any
import threading

from .config import APP_CONFIG, CONSTANTS, load_config
from .exceptions import (
    OllamaConnectionError, 
    WorkspaceAIError, 
    handle_exception
)
from .progress import show_progress

logger = logging.getLogger(__name__)


class OllamaClient:
    """Core Ollama API client with connection management and retry logic"""
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize the Ollama client with configuration"""
        if config is None:
            config = load_config()
        
        self.config = config or {}
        self.model = self.config.get('model', CONSTANTS['MODEL'])
        self.base_url = f"http://{self.config.get('ollama_host', 'localhost:11434')}"
        self.timeout = CONSTANTS['API_TIMEOUT']
        self.max_retries = CONSTANTS['API_MAX_RETRIES']
        
    def get_running_models(self) -> List[str]:
        """Get list of currently running models"""
        try:
            response = requests.get(f"{self.base_url}/api/ps", timeout=5)
            if response.status_code == 200:
                data = response.json()
                models = data.get("models", [])
                return [model.get("name", "") for model in models if model.get("name")]
            return []
        except Exception as e:
            logger.debug(f"Could not get running models: {e}")
            return []
    
    def check_and_use_running_model(self) -> bool:
        """
        Check if any models are already running and use one if available.
        Returns True if switched to a running model, False otherwise.
        """
        try:
            running_models = self.get_running_models()
            if running_models:
                # Use the first running model
                running_model = running_models[0]
                logger.info(f"Found running model: {running_model}, using it instead of {self.model}")
                print(f"🔄 Using already running model: {running_model}")
                self.model = running_model
                return True
            return False
        except Exception as e:
            logger.debug(f"Error checking running models: {e}")
            return False
        
    def verify_connection(self) -> Dict[str, Any]:
        """
        Verify connection to Ollama server and return detailed status.
        Raises exceptions on failure.
        
        Returns:
            Dict with connection status and available models
        """
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code != 200:
                raise WorkspaceAIError(
                    f"Ollama server returned status {response.status_code}"
                )
            
            try:
                data = response.json()
            except json.JSONDecodeError as e:
                raise WorkspaceAIError(
                    f"Invalid JSON response from Ollama at {self.base_url}",
                    # response_content=response.text[:500] if hasattr(response, 'text') else "",
                    # original_error=e
                )
            
            models = data.get("models", [])
            model_names = [model["name"] for model in models]
            
            return {
                "connected": True,
                "model_available": self.model in model_names,
                "available_models": model_names,
                "requested_model": self.model
            }
                
        except requests.exceptions.ConnectionError as e:
            raise OllamaConnectionError(
                f"Connection refused to Ollama at {self.base_url}",
                # host=self.base_url,
                # original_error=e
            )
        except requests.exceptions.Timeout as e:
            raise WorkspaceAIError(
                f"Connection timeout to Ollama at {self.base_url}",
                # timeout_seconds=5.0,
                # original_error=e
            )
        except (WorkspaceAIError, WorkspaceAIError):
            # Re-raise our custom exceptions
            raise
        except Exception as e:
            converted_error = handle_exception("verify_connection", e)
            raise converted_error
        
    def test_connection(self) -> bool:
        """Test connection to Ollama server and check for running models"""
        try:
            # First, check if any models are already running and use one if available
            if self.check_and_use_running_model():
                return True
            
            # If no models are running, proceed with normal connection test
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get("models", [])
                model_names = [model["name"] for model in models]
                
                if self.model in model_names:
                    print(f"✅ Connected to Ollama - {self.model} is available")
                    logger.info(f"Ollama connection successful, model {self.model} available")
                    return True
                else:
                    available = ", ".join(model_names) if model_names else "none"
                    print(f"⚠️ Connected to Ollama but {self.model} not found")
                    print(f"Available models: {available}")
                    print(f"Run: ollama pull {self.model}")
                    logger.warning(f"Model {self.model} not available. Available: {available}")
                    return False
            else:
                print(f"❌ Ollama responded with status {response.status_code}")
                logger.error(f"Ollama connection failed with status {response.status_code}")
                return False
                
        except requests.exceptions.ConnectionError as e:
            print("❌ Cannot connect to Ollama")
            print("Make sure Ollama is running: ollama serve")
            logger.error(f"Connection refused to Ollama at {self.base_url}: {e}")
            return False
        except requests.exceptions.Timeout as e:
            print("❌ Ollama connection timeout")
            logger.error(f"Connection timeout to Ollama at {self.base_url}: {e}")
            return False
        except json.JSONDecodeError as e:
            print("❌ Invalid response from Ollama")
            logger.error(f"Invalid JSON response from Ollama at {self.base_url}: {e}")
            return False
        except Exception as e:
            print(f"❌ Ollama connection error: {e}")
            logger.error(f"Unexpected Ollama connection error: {e}")
            return False
    
    def make_request(self, endpoint: str, data: Dict, retry_count: int = 0) -> Optional[requests.Response]:
        """Make HTTP request to Ollama with retry logic"""
        try:
            return self._make_request_with_exceptions(endpoint, data, retry_count)
        except (OllamaConnectionError, WorkspaceAIError, WorkspaceAIError):
            # For backward compatibility, return None instead of raising
            return None
        except Exception:
            # For backward compatibility, return None for unexpected errors
            return None
    
    def _make_request_with_exceptions(self, endpoint: str, data: Dict, retry_count: int = 0) -> requests.Response:
        """Make HTTP request to Ollama with retry logic - raises exceptions on failure"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = requests.post(url, json=data, timeout=self.timeout)
            response.raise_for_status()
            return response
            
        except requests.exceptions.Timeout as e:
            if retry_count < self.max_retries:
                wait_time = 2 ** retry_count  # Exponential backoff
                logger.warning(f"Request timeout, retrying in {wait_time}s (attempt {retry_count + 1}/{self.max_retries})")
                time.sleep(wait_time)
                return self._make_request_with_exceptions(endpoint, data, retry_count + 1)
            else:
                logger.error("Request failed after maximum retries due to timeout")
                raise WorkspaceAIError(
                    f"Request to {url} timed out after {self.max_retries} retries",
                    # timeout_seconds=self.timeout,
                    # original_error=e
                )
                
        except requests.exceptions.ConnectionError as e:
            if retry_count < self.max_retries:
                wait_time = 2 ** retry_count
                logger.warning(f"Connection error, retrying in {wait_time}s (attempt {retry_count + 1}/{self.max_retries})")
                time.sleep(wait_time)
                return self._make_request_with_exceptions(endpoint, data, retry_count + 1)
            else:
                logger.error("Request failed after maximum retries due to connection error")
                raise OllamaConnectionError(
                    f"Connection to {url} failed after {self.max_retries} retries",
                    # host=self.base_url,
                    # original_error=e
                )
                
        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code if e.response else 0
            if status_code >= 500:
                raise WorkspaceAIError(
                    f"Ollama server error at {url}: HTTP {status_code}",
                    # original_error=e
                )
            else:
                logger.error(f"HTTP error: {e}")
                converted_error = handle_exception("make_request", e)
                raise converted_error
            
        except Exception as e:
            logger.error(f"Unexpected error in request: {e}")
            converted_error = handle_exception("make_request", e)
            raise converted_error
    
    def chat_completion(self, messages: List[Dict], tools: Optional[List[Dict]] = None, stream: bool = False) -> Optional[Dict]:
        """Perform chat completion with optional tools"""
        try:
            data = {
                "model": self.model,
                "messages": messages,
                "stream": stream
            }
            
            if tools:
                data["tools"] = tools
            
            # Show progress indicator while waiting for response
            with show_progress("", animated=True):
                response = self.make_request("/api/chat", data)
            
            if response and response.status_code == 200:
                try:
                    return response.json()
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse JSON response: {e}")
                    return None
            
            return None
            
        except Exception as e:
            logger.error(f"Error in chat_completion: {e}")
            return None
    
    def simple_chat(self, prompt: str) -> Optional[str]:
        """Simple chat without tools or memory"""
        try:
            messages = [{"role": "user", "content": prompt}]
            result = self.chat_completion(messages)
            
            if result and "message" in result:
                return result["message"].get("content", "")
            
            return None
            
        except Exception as e:
            logger.error(f"Error in simple_chat: {e}")
            return None


# Global client instance for backward compatibility
_default_client = None

def get_default_client() -> OllamaClient:
    """Get or create the default Ollama client"""
    global _default_client
    if _default_client is None:
        _default_client = OllamaClient()
    return _default_client
