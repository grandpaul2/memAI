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
        # Start            
            # Load the chosen model if not already loaded
            if self.current_model not in loaded_models:
                with ProgressDots():
                    if not self.ollama.ensure_model_loaded(self.current_model):
                        print("Failed to load model")
                        returne - easily adjustable during testing
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
    """Perfect animated dots implementation"""
    
    def __init__(self):
        self.running = False
        self.thread = None
        
    def start(self):
        """Start animated dots"""
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._animate, daemon=True)
        self.thread.start()
        
    def stop(self):
        """Stop and clear dots"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=0.5)
        # Clear the dots
        sys.stdout.write('\r   \r')
        sys.stdout.flush()
        
    def _animate(self):
        """Internal animation loop"""
        dots = 0
        while self.running:
            sys.stdout.write('\r' + '.' * (dots + 1) + ' ' * (3 - dots - 1))
            sys.stdout.flush()
            dots = (dots + 1) % 3
            time.sleep(0.4)
            
    def __enter__(self):
        self.start()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()


class MemoryManager:
    """Per-model conversation storage and retrieval"""
    
    def __init__(self):
        self.memory_dir = Path("memory")
        self.memory_dir.mkdir(exist_ok=True)
        self.backup_dir = self.memory_dir / "backups"
        self.backup_dir.mkdir(exist_ok=True)
        self.token_estimator = TokenEstimator()
        
        # Context limits based on model size
        self.CONTEXT_LIMITS = {
            "small": {"max_tokens": 8192, "max_exchanges": 50},
            "medium": {"max_tokens": 32768, "max_exchanges": 200}, 
            "large": {"max_tokens": 131072, "max_exchanges": 500}
        }
    
    def _model_to_filename(self, model: str) -> str:
        """Convert model name to safe filename with collision prevention"""
        # Clean model name for filename
        safe_name = "".join(c if c.isalnum() or c in '-_' else '-' for c in model)
        safe_name = safe_name.strip('-_')[:50]  # Limit length
        
        # Add hash for collision prevention
        model_hash = hashlib.md5(model.encode()).hexdigest()[:8]
        return f"{safe_name}_{model_hash}.json"
    
    def _get_memory_path(self, model: str) -> Path:
        """Get path for model's memory file"""
        return self.memory_dir / self._model_to_filename(model)
    
    def _create_fresh_memory(self, model: str, context_window: int = 32768) -> Dict:
        """Create new memory structure for model"""
        return {
            "model": model,
            "context_window": context_window,
            "created": datetime.now().isoformat(),
            "last_modified": datetime.now().isoformat(),
            "exchanges": [],
            "summary": ""
        }
    
    def _get_model_limits(self, context_window: int) -> Dict:
        """Get appropriate limits based on context window size"""
        if context_window <= 8192:
            return self.CONTEXT_LIMITS["small"]
        elif context_window <= 32768:
            return self.CONTEXT_LIMITS["medium"]
        else:
            return self.CONTEXT_LIMITS["large"]
    
    def _backup_memory(self, model: str):
        """Create backup of memory file"""
        memory_path = self._get_memory_path(model)
        if memory_path.exists():
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{self._model_to_filename(model).replace('.json', '')}_{timestamp}.json"
            backup_path = self.backup_dir / backup_name
            
            try:
                import shutil
                shutil.copy2(memory_path, backup_path)
            except Exception:
                pass  # Backup failed, but continue
    
    def load_memory(self, model: str, context_window: int = 32768) -> Dict:
        """Load or create memory for model"""
        memory_path = self._get_memory_path(model)
        
        if memory_path.exists():
            try:
                with open(memory_path, 'r', encoding='utf-8') as f:
                    memory = json.load(f)
                
                # Validate structure
                if all(key in memory for key in ["model", "exchanges"]):
                    return memory
                else:
                    print(f"⚠️  Corrupted memory for {model}, creating fresh")
            except (json.JSONDecodeError, IOError):
                print(f"⚠️  Could not read memory for {model}, creating fresh")
        
        # Create fresh memory
        return self._create_fresh_memory(model, context_window)
    
    def save_memory(self, model: str, memory: Dict):
        """Save memory to file with atomic write"""
        memory_path = self._get_memory_path(model)
        temp_path = memory_path.with_suffix('.tmp')
        
        try:
            # Update timestamp
            memory["last_modified"] = datetime.now().isoformat()
            
            # Write to temp file first
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(memory, f, indent=2, ensure_ascii=False)
            
            # Atomic move
            temp_path.replace(memory_path)
            
        except Exception as e:
            print(f"⚠️  Failed to save memory for {model}: {e}")
            if temp_path.exists():
                temp_path.unlink()
    
    def add_exchange(self, model: str, user_msg: str, assistant_msg: str, context_window: int = 32768):
        """Add conversation exchange to memory"""
        memory = self.load_memory(model, context_window)
        
        # Add new exchange
        exchange = {
            "user": user_msg,
            "assistant": assistant_msg,
            "timestamp": datetime.now().isoformat(),
            "tokens": {
                "user": self.token_estimator.estimate_tokens(user_msg),
                "assistant": self.token_estimator.estimate_tokens(assistant_msg)
            }
        }
        
        memory["exchanges"].append(exchange)
        
        # Check if we need to summarize old exchanges
        limits = self._get_model_limits(context_window)
        if len(memory["exchanges"]) > limits["max_exchanges"]:
            self._summarize_old_exchanges(memory, limits["max_exchanges"])
        
        self.save_memory(model, memory)
    
    def _summarize_old_exchanges(self, memory: Dict, max_exchanges: int):
        """Summarize oldest exchanges when limit is reached"""
        exchanges = memory["exchanges"]
        
        if len(exchanges) <= max_exchanges:
            return
        
        # Keep the most recent exchanges
        keep_count = int(max_exchanges * 0.75)  # Keep 75% of limit
        to_summarize = exchanges[:-keep_count]
        to_keep = exchanges[-keep_count:]
        
        # Create simple summary of old exchanges
        if to_summarize:
            summary_text = f"Previous conversation ({len(to_summarize)} exchanges): "
            
            # Sample a few key exchanges for summary
            sample_size = min(3, len(to_summarize))
            sample_exchanges = [to_summarize[0]]  # First
            if len(to_summarize) > 2:
                sample_exchanges.append(to_summarize[len(to_summarize)//2])  # Middle
            if len(to_summarize) > 1:
                sample_exchanges.append(to_summarize[-1])  # Last
            
            topics = []
            for exchange in sample_exchanges:
                user_msg = exchange.get("user", "")[:100]  # First 100 chars
                if user_msg:
                    topics.append(user_msg)
            
            summary_text += " | ".join(topics)
            memory["summary"] = summary_text
        
        # Update exchanges to keep only recent ones
        memory["exchanges"] = to_keep
    
    def get_context_messages(self, model: str, user_input: str, context_window: int = 32768) -> List[Dict]:
        """Get conversation context optimized for current query"""
        memory = self.load_memory(model, context_window)
        exchanges = memory["exchanges"]
        
        if not exchanges:
            return []
        
        # Analyze query complexity (simple heuristic)
        complexity = self._analyze_complexity(user_input)
        
        # Budget allocation: 75% memory, 20% response, 5% safety
        memory_budget = int(context_window * 0.75)
        
        # Adaptive loading based on complexity
        if complexity < 0.3:  # Simple query
            # Load recent exchanges only
            max_recent = min(10, len(exchanges))
            context_exchanges = exchanges[-max_recent:]
        else:  # Complex query
            # Load as much as budget allows
            context_exchanges = self._load_within_budget(exchanges, memory_budget)
        
        # Convert to chat format
        messages = []
        
        # Add summary if available
        if memory.get("summary"):
            messages.append({
                "role": "system",
                "content": f"Previous context: {memory['summary']}"
            })
        
        # Add conversation exchanges
        for exchange in context_exchanges:
            messages.append({"role": "user", "content": exchange["user"]})
            messages.append({"role": "assistant", "content": exchange["assistant"]})
        
        return messages
    
    def _analyze_complexity(self, user_input: str) -> float:
        """Simple complexity analysis (0.0-1.0)"""
        if not user_input:
            return 0.0
        
        complexity = 0.0
        
        # Length factor
        length_score = min(1.0, len(user_input) / 200)
        complexity += length_score * 0.3
        
        # Question words
        question_words = ['what', 'why', 'how', 'when', 'where', 'explain', 'describe', 'analyze']
        question_score = sum(1 for word in question_words if word in user_input.lower()) / len(question_words)
        complexity += question_score * 0.4
        
        # Technical terms (simple heuristic)
        if any(term in user_input.lower() for term in ['code', 'program', 'algorithm', 'function', 'data']):
            complexity += 0.3
        
        return min(1.0, complexity)
    
    def _load_within_budget(self, exchanges: List[Dict], budget: int) -> List[Dict]:
        """Load exchanges that fit within token budget, newest first"""
        if not exchanges:
            return []
        
        selected = []
        current_tokens = 0
        
        # Work backwards from newest
        for exchange in reversed(exchanges):
            exchange_tokens = self.token_estimator.estimate_tokens(
                exchange.get("user", "") + exchange.get("assistant", "")
            )
            
            if current_tokens + exchange_tokens <= budget:
                selected.insert(0, exchange)  # Insert at beginning to maintain order
                current_tokens += exchange_tokens
            else:
                break
        
        return selected
    
    def get_memory_stats(self, model: str) -> Dict:
        """Get memory statistics for model"""
        memory = self.load_memory(model)
        exchanges = memory["exchanges"]
        
        total_tokens = self.token_estimator.estimate_conversation_tokens(exchanges)
        
        return {
            "model": model,
            "exchanges": len(exchanges),
            "total_tokens": total_tokens,
            "avg_tokens_per_exchange": total_tokens // max(1, len(exchanges)),
            "memory_file_size": self._get_memory_path(model).stat().st_size if self._get_memory_path(model).exists() else 0,
            "last_modified": memory.get("last_modified", "Unknown")
        }
    
    def clear_conversation(self, model: str) -> bool:
        """Clear conversation for model"""
        try:
            self._backup_memory(model)  # Backup before clearing
            memory_path = self._get_memory_path(model)
            if memory_path.exists():
                memory_path.unlink()
            return True
        except Exception:
            return False
    
    def list_models_with_memory(self) -> List[str]:
        """Get list of models that have memory files"""
        models = []
        for memory_file in self.memory_dir.glob("*.json"):
            try:
                with open(memory_file, 'r') as f:
                    data = json.load(f)
                model_name = data.get("model")
                if model_name:
                    models.append(model_name)
            except:
                continue
        return sorted(models)


class OllamaClient:
    """Simple Ollama API communication"""
    
    def __init__(self):
        self.base_url = "http://localhost:11434"
        self.timeout = 30
        
    def is_available(self) -> bool:
        """Check if Ollama is running"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def get_available_models(self) -> List[str]:
        """Get list of available models"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                data = response.json()
                models = data.get("models", [])
                return [model["name"] for model in models]
            return []
        except:
            return []
    
    def get_loaded_models(self) -> List[str]:
        """Get list of currently loaded/running models"""
        try:
            response = requests.get(f"{self.base_url}/api/ps", timeout=5)
            if response.status_code == 200:
                data = response.json()
                models = data.get("models", [])
                return [model["name"] for model in models if model.get("name")]
            return []
        except:
            return []
    
    def detect_context_window(self, model: str) -> int:
        """Detect context window size for model (simplified)"""
        # Simple heuristic based on model name
        model_lower = model.lower()
        
        if "3b" in model_lower or "7b" in model_lower:
            return 32768
        elif "13b" in model_lower or "70b" in model_lower:
            return 32768
        else:
            return 32768  # Default assumption
    
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
                    timeout=self.timeout
                )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("message", {}).get("content", "")
            else:
                return None
                
        except Exception as e:
            print(f"⚠️  Error communicating with model: {e}")
            return None


class MemAI:
    """Main memAI application"""
    
    def __init__(self):
        self.memory = MemoryManager()
        self.ollama = OllamaClient()
        self.current_model = None
        self.running = True
        
        # Setup signal handling for graceful shutdown
        signal.signal(signal.SIGINT, self._handle_shutdown)
        signal.signal(signal.SIGTERM, self._handle_shutdown)
    
    def _handle_shutdown(self, signum, frame):
        """Handle graceful shutdown"""
        print("\n\nShutting down memAI...")
        self.running = False
    
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
            
            # Load the chosen model
            print(f"� Loading {self.current_model}...")
            if self.ollama.ensure_model_loaded(self.current_model):
                print("💬 Ready to chat! (type 'help' for commands)")
            else:
                print("❌ Failed to load model")
                return
        
        # Auto-load the selected model
        if self.ollama.ensure_model_loaded(self.current_model):
            print("💬 Ready to chat! (type 'help' for commands)")
        else:
            print("⚠️  Model loading failed, but you can still try chatting")
        print()
        
        # Start chat loop
        self.chat_loop()
    
    def _show_model_status(self, available_models: List[str], loaded_models: List[str]):
        """Show clear distinction between loaded and available models"""
        print("🤖 Model Status:")
        
        if loaded_models:
            print(f"   ✅ Loaded: {', '.join(loaded_models)}")
        
        unloaded = [m for m in available_models if m not in loaded_models]
        if unloaded:
            print(f"   💤 Available: {', '.join(unloaded)}")
        
        if not loaded_models and not unloaded:
            print("   ❌ No models found")
    
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
                print("\n\nShutting down memAI...")
                break
            except Exception as e:
                print(f"⚠️  Error: {e}")
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
        
        # Get response
        return self.ollama.chat_completion(self.current_model, context_messages)
    
    def _show_help(self):
        """Show available commands"""
        print()
        print("memAI Commands:")
        print("  help                 - Show this help")
        print("  model <name>         - Switch to different model")
        print("  stats                - Show memory statistics")
        print("  clear                - Clear current conversation")
        print("  quit/exit            - Exit memAI")
        print("  Just type normally to chat!")
        print()
    
    def _handle_model_command(self, command: str):
        """Handle model switching"""
        parts = command.split(' ', 1)
        if len(parts) < 2:
            print("Usage: model <model_name>")
            available = self.ollama.get_available_models()
            loaded = self.ollama.get_loaded_models()
            
            if available or loaded:
                print("Models:")
                if loaded:
                    print(f"   ✅ Loaded: {', '.join(loaded)}")
                unloaded = [m for m in available if m not in loaded]
                if unloaded:
                    print(f"   💤 Available: {', '.join(unloaded)}")
            return
        
        new_model = parts[1].strip()
        available_models = self.ollama.get_available_models()
        
        if new_model in available_models:
            # Load the new model
            if self.ollama.ensure_model_loaded(new_model):
                self.current_model = new_model
                print(f"✅ Switched to: {new_model}")
                
                # Show memory info for new model
                stats = self.memory.get_memory_stats(new_model)
                if stats["exchanges"] > 0:
                    print(f"📚 Conversation history: {stats['exchanges']} exchanges")
                else:
                    print("📝 Fresh conversation - no previous history")
            else:
                print(f"❌ Failed to load {new_model}")  
        else:
            print(f"❌ Model '{new_model}' not available")
            print(f"Available models: {', '.join(available_models)}")
    
    def _show_stats(self):
        """Show memory statistics"""
        print()
        stats = self.memory.get_memory_stats(self.current_model)
        
        print(f"📊 Memory Statistics for {self.current_model}:")
        print(f"   Exchanges: {stats['exchanges']}")
        print(f"   Total tokens: ~{stats['total_tokens']:,}")
        print(f"   Avg per exchange: {stats['avg_tokens_per_exchange']} tokens")
        print(f"   Memory file: {stats['memory_file_size'] / 1024:.1f} KB")
        
        # Show other models with memory
        other_models = [m for m in self.memory.list_models_with_memory() 
                       if m != self.current_model]
        if other_models:
            print(f"   Other models with memory: {', '.join(other_models)}")
        
        print()
    
    def _clear_conversation(self):
        """Clear current model's conversation"""
        confirm = input(f"Clear conversation for {self.current_model}? (y/N): ").strip().lower()
        if confirm == 'y':
            if self.memory.clear_conversation(self.current_model):
                print("✅ Conversation cleared")
            else:
                print("❌ Failed to clear conversation")
        else:
            print("Cancelled")


def main():
    """Main entry point"""
    try:
        app = MemAI()
        app.start()
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
