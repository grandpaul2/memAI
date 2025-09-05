#!/usr/bin/env python3
"""
memAI - AI Assistant with Perfect Memory

A focused chat application that excels at conversation memory management.
Each AI model gets its own conversation history with smart token budgeting.
"""

import sys
import os
import json
import time
import signal
import hashlib
import requests
import threading
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime


class TokenEstimator:
    """Simple, adjustable token estimation"""
    
    def __init__(self):
        # Starting conservative - easily adjustable during testing
        self.chars_per_token = 3.0
        
    def estimate_tokens(self, text: str) -> int:
        """Conservative estimation - easily tunable"""
        if not text:
            return 0
        return max(1, int(len(str(text)) / self.chars_per_token))
    
    def estimate_conversation_tokens(self, exchanges: List[Dict]) -> int:
        """Estimate tokens for a list of conversation exchanges"""
        total = 0
        for exchange in exchanges:
            if 'user' in exchange:
                total += self.estimate_tokens(exchange['user'])
            if 'assistant' in exchange:
                total += self.estimate_tokens(exchange['assistant'])
        return total


class ProgressDots:
    """Animated thinking dots with clean termination"""
    
    def __init__(self):
        self.stop_event = threading.Event()
        self.thread = None
    
    def start(self):
        """Start the animation"""
        if self.thread and self.thread.is_alive():
            return
        
        self.stop_event.clear()
        self.thread = threading.Thread(target=self._animate, daemon=True)
        self.thread.start()
    
    def stop(self):
        """Stop the animation and clear the line"""
        if self.stop_event:
            self.stop_event.set()
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=0.5)
        # Clear the dots line
        print('\r' + ' ' * 20 + '\r', end='', flush=True)
    
    def _animate(self):
        """Animation loop"""
        dots = ['', '.', '..', '...']
        i = 0
        while not self.stop_event.is_set():
            print(f'\r{dots[i % len(dots)]}', end='', flush=True)
            i += 1
            time.sleep(0.5)
    
    def __enter__(self):
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()


class MemoryManager:
    """Per-model conversation memory with token budgeting"""
    
    def __init__(self, memory_dir: str = "./memory"):
        self.memory_dir = Path(memory_dir)
        self.memory_dir.mkdir(exist_ok=True)
        self.token_estimator = TokenEstimator()
    
    def _get_conversation_file(self, model: str) -> Path:
        """Get conversation file path with collision-safe naming"""
        # Hash the model name to handle special characters
        model_hash = hashlib.md5(model.encode()).hexdigest()[:8]
        safe_name = f"{model.replace(':', '_').replace('/', '_')}_{model_hash}.json"
        return self.memory_dir / safe_name
    
    def _load_conversation(self, model: str) -> Dict:
        """Load conversation from file"""
        file_path = self._get_conversation_file(model)
        
        if not file_path.exists():
            return {"exchanges": [], "metadata": {"created": datetime.now().isoformat()}}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            # Corrupted file, start fresh
            return {"exchanges": [], "metadata": {"created": datetime.now().isoformat()}}
    
    def _save_conversation(self, model: str, data: Dict):
        """Atomically save conversation to file"""
        file_path = self._get_conversation_file(model)
        temp_path = file_path.with_suffix('.tmp')
        
        try:
            # Write to temp file first
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            # Atomic move
            temp_path.replace(file_path)
            
        except Exception as e:
            # Clean up temp file if it exists
            if temp_path.exists():
                temp_path.unlink()
            raise e
    
    def add_exchange(self, model: str, user_input: str, ai_response: str, context_window: int):
        """Add new conversation exchange and manage context window"""
        data = self._load_conversation(model)
        
        # Add new exchange
        exchange = {
            "timestamp": datetime.now().isoformat(),
            "user": user_input,
            "assistant": ai_response
        }
        data["exchanges"].append(exchange)
        data["metadata"]["last_updated"] = datetime.now().isoformat()
        
        # Trim to context window if needed
        self._trim_to_context_window(data, context_window)
        
        # Save updated conversation
        self._save_conversation(model, data)
    
    def _trim_to_context_window(self, data: Dict, context_window: int):
        """Keep conversation within token budget"""
        exchanges = data["exchanges"]
        if not exchanges:
            return
        
        # Always keep the most recent exchange
        if len(exchanges) <= 1:
            return
        
        # Estimate tokens and trim from the beginning if needed
        while len(exchanges) > 1:
            total_tokens = self.token_estimator.estimate_conversation_tokens(exchanges)
            
            # Leave room for system message and current exchange (roughly 20% buffer)
            if total_tokens <= context_window * 0.8:
                break
            
            # Remove oldest exchange (but keep at least the most recent one)
            exchanges.pop(0)
        
        data["exchanges"] = exchanges
    
    def get_context_messages(self, model: str, current_input: str, context_window: int) -> List[Dict]:
        """Build context messages for API call"""
        data = self._load_conversation(model)
        exchanges = data["exchanges"]
        
        messages = []
        
        # Add conversation history
        for exchange in exchanges:
            messages.append({"role": "user", "content": exchange["user"]})
            messages.append({"role": "assistant", "content": exchange["assistant"]})
        
        return messages
    
    def get_stats(self, model: str) -> Dict:
        """Get conversation statistics"""
        data = self._load_conversation(model)
        exchanges = data["exchanges"]
        
        if not exchanges:
            return {"exchanges": 0, "tokens": 0, "created": "N/A"}
        
        tokens = self.token_estimator.estimate_conversation_tokens(exchanges)
        created = data["metadata"].get("created", "Unknown")
        
        return {
            "exchanges": len(exchanges),
            "tokens": tokens,
            "created": created
        }
    
    def clear_conversation(self, model: str):
        """Clear conversation history for a model"""
        file_path = self._get_conversation_file(model)
        if file_path.exists():
            file_path.unlink()


class OllamaClient:
    """Clean Ollama API client"""
    
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
    
    def is_available(self) -> bool:
        """Check if Ollama is running"""
        try:
            response = requests.get(f"{self.base_url}/api/version", timeout=5)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False
    
    def get_available_models(self) -> List[str]:
        """Get list of available models"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=10)
            if response.status_code == 200:
                data = response.json()
                return [model["name"] for model in data.get("models", [])]
            return []
        except requests.exceptions.RequestException:
            return []
    
    def get_loaded_models(self) -> List[str]:
        """Get list of currently loaded models"""
        try:
            response = requests.get(f"{self.base_url}/api/ps", timeout=10)
            if response.status_code == 200:
                data = response.json()
                return [model["name"] for model in data.get("models", [])]
            return []
        except requests.exceptions.RequestException:
            return []
    
    def detect_context_window(self, model: str) -> int:
        """Detect context window size for model"""
        # Conservative defaults for common models
        model_lower = model.lower()
        
        if "32k" in model_lower:
            return 32000
        elif "16k" in model_lower:
            return 16000
        elif "8k" in model_lower:
            return 8000
        elif "4k" in model_lower:
            return 4000
        elif "7b" in model_lower or "3b" in model_lower:
            return 4000  # Conservative for smaller models
        elif "14b" in model_lower or "13b" in model_lower:
            return 8000  # Larger models typically have more context
        else:
            return 4000  # Safe default
    
    def ensure_model_loaded(self, model: str) -> bool:
        """Ensure model is loaded in Ollama by sending a test message"""
        try:
            # Send a simple test message to warm up the model
            data = {
                "model": model,
                "messages": [{"role": "user", "content": "test"}],
                "stream": False
            }
            
            response = requests.post(
                f"{self.base_url}/api/chat",
                json=data,
                timeout=60  # Longer timeout for initial load
            )
            
            return response.status_code == 200
                
        except Exception:
            return False

    def chat_completion(self, model: str, messages: List[Dict]) -> Optional[str]:
        """Get response from model with animated dots"""
        try:
            # Prepare request
            data = {
                "model": model,
                "messages": messages,
                "stream": False
            }
            
            # Show thinking dots
            with ProgressDots():
                response = requests.post(
                    f"{self.base_url}/api/chat",
                    json=data,
                    timeout=120
                )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("message", {}).get("content", "").strip()
            else:
                return None
                
        except requests.exceptions.RequestException:
            return None


class MemAI:
    """Main memAI application"""
    
    def __init__(self):
        self.ollama = OllamaClient()
        self.memory = MemoryManager()
        self.current_model = None
        self.running = True
        
        # Setup signal handling for graceful shutdown
        signal.signal(signal.SIGINT, self._handle_shutdown)
        signal.signal(signal.SIGTERM, self._handle_shutdown)
    
    def _handle_shutdown(self, signum, frame):
        """Handle graceful shutdown"""
        print("\nGoodbye!")
        self.running = False
        sys.exit(0)
    
    def start(self):
        """Start the memAI application"""
        # Check Ollama availability
        if not self.ollama.is_available():
            print("Ollama not running")
            print("Start it with: ollama serve")
            return
        
        # Get available and loaded models
        models = self.ollama.get_available_models()
        if not models:
            print("No models available")
            print("Install one with: ollama pull qwen2.5:3b")
            return
        
        loaded_models = self.ollama.get_loaded_models()
        
        # Use loaded model if available, otherwise let user pick
        if loaded_models:
            self.current_model = loaded_models[0]
            # Start chat immediately with loaded model
        else:
            # Show model selection
            for i, model in enumerate(models, 1):
                status = " (loaded)" if model in loaded_models else ""
                print(f"{i}. {model}{status}")
            print()
            
            while True:
                try:
                    choice = input("Choose model: ").strip()
                    
                    # Handle number choice
                    if choice.isdigit():
                        idx = int(choice) - 1
                        if 0 <= idx < len(models):
                            self.current_model = models[idx]
                            break
                    
                    # Handle name choice
                    if choice in models:
                        self.current_model = choice
                        break
                    
                    print(f"Invalid choice. Pick 1-{len(models)} or model name.")
                except KeyboardInterrupt:
                    print("Goodbye!")
                    return
            
            # Load the chosen model if not already loaded
            if self.current_model not in loaded_models:
                with ProgressDots():
                    if not self.ollama.ensure_model_loaded(self.current_model):
                        print("Failed to load model")
                        return
        
        # Start chat loop
        self.chat_loop()
    
    def chat_loop(self):
        """Main conversation loop"""
        while self.running:
            try:
                # Get user input
                user_input = input("You: ").strip()
                
                if not user_input:
                    continue
                
                # Handle commands
                if user_input.lower() in ['quit', 'exit', 'bye']:
                    print("Goodbye!")
                    break
                elif user_input.lower() == 'help':
                    self._show_help()
                    continue
                elif user_input.lower().startswith('model '):
                    self._handle_model_command(user_input)
                    continue
                elif user_input.lower() == 'stats':
                    self._show_stats()
                    continue
                elif user_input.lower() == 'clear':
                    self._clear_conversation()
                    continue
                
                # Get response from AI
                response = self._get_ai_response(user_input)
                
                if response:
                    print(f"memAI: {response}")
                    
                    # Save to memory
                    context_window = self.ollama.detect_context_window(self.current_model)
                    self.memory.add_exchange(self.current_model, user_input, response, context_window)
                else:
                    print("memAI: Sorry, I couldn't generate a response.")
                
                print()  # Add spacing
                
            except KeyboardInterrupt:
                print("\nGoodbye!")
                break
            except Exception as e:
                print(f"Error: {e}")
                print()
    
    def _get_ai_response(self, user_input: str) -> Optional[str]:
        """Get AI response with conversation context"""
        # Get context window for current model
        context_window = self.ollama.detect_context_window(self.current_model)
        
        # Build context messages
        context_messages = self.memory.get_context_messages(
            self.current_model, user_input, context_window
        )
        
        # Add system message if needed
        if not any(msg.get("role") == "system" for msg in context_messages):
            system_msg = {
                "role": "system",
                "content": "You are a helpful AI assistant. Be conversational and remember our previous discussions."
            }
            context_messages.insert(0, system_msg)
        
        # Add current user message
        context_messages.append({"role": "user", "content": user_input})
        
        # Get response from model
        return self.ollama.chat_completion(self.current_model, context_messages)
    
    def _show_help(self):
        """Show available commands"""
        print("\nCommands:")
        print("  help     - Show this help")
        print("  model    - Show current model")
        print("  stats    - Show conversation stats")
        print("  clear    - Clear conversation history")
        print("  quit     - Exit memAI")
        print()
    
    def _handle_model_command(self, command: str):
        """Handle model-related commands"""
        parts = command.split()
        if len(parts) == 1:
            print(f"Current model: {self.current_model}")
        print()
    
    def _show_stats(self):
        """Show conversation statistics"""
        if not self.current_model:
            print("No model selected")
            return
        
        stats = self.memory.get_stats(self.current_model)
        print(f"\nConversation Stats for {self.current_model}:")
        print(f"  Exchanges: {stats['exchanges']}")
        print(f"  Estimated tokens: {stats['tokens']}")
        print(f"  Created: {stats['created']}")
        print()
    
    def _clear_conversation(self):
        """Clear current conversation"""
        if not self.current_model:
            print("No model selected")
            return
        
        self.memory.clear_conversation(self.current_model)
        print(f"Cleared conversation for {self.current_model}")
        print()


def main():
    """Entry point"""
    try:
        app = MemAI()
        app.start()
    except KeyboardInterrupt:
        print("\nGoodbye!")
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
