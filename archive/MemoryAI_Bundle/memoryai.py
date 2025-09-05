#!/usr/bin/env python3
"""
MemoryAI - Simple AI Assistant with Advanced Memory

A focused chat application that excels at conversation memory management
without the complexity of universal tool integration.
"""

import sys
import os
from typing import Optional
import signal

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.memory_integration import MemoryIntegration
from src.ollama_client import OllamaClient
from src.config import Config
from src.exceptions import handle_exception
import logging

class MemoryAI:
    """Simple AI assistant focused on memory management"""
    
    def __init__(self):
        """Initialize MemoryAI"""
        self.config = Config()
        self.memory = MemoryIntegration(self.config.config)
        self.ollama_client = OllamaClient(self.config)
        self.current_model = self.config.get('default_model', 'qwen2.5:3b')
        self.running = True
        
        # Setup signal handling for graceful shutdown
        signal.signal(signal.SIGINT, self._handle_shutdown)
        signal.signal(signal.SIGTERM, self._handle_shutdown)
        
        print("🧠 MemoryAI - AI Assistant with Advanced Memory")
        print(f"📡 Using model: {self.current_model}")
        print("💡 Type 'help' for commands, 'quit' to exit\n")
    
    def _handle_shutdown(self, signum, frame):
        """Handle graceful shutdown"""
        print("\n\n🔄 Shutting down MemoryAI...")
        self.running = False
        
    def chat_loop(self):
        """Main chat interaction loop"""
        while self.running:
            try:
                # Get user input
                user_input = input("You: ").strip()
                
                if not user_input:
                    continue
                    
                # Handle special commands  
                if user_input.lower() in ['quit', 'exit', 'bye']:
                    print("👋 Goodbye!")
                    break
                elif user_input.lower() == 'help':
                    self._show_help()
                    continue
                elif user_input.lower().startswith('model '):
                    self._handle_model_command(user_input)
                    continue
                elif user_input.lower() == 'stats':
                    self._show_memory_stats()
                    continue
                elif user_input.lower() == 'clear':
                    self._clear_conversation()
                    continue
                
                # Add user message to memory
                self.memory.add_message("user", user_input, self.current_model)
                
                # Get context messages for the current model
                context_messages = self.memory.get_context_messages(
                    model=self.current_model,
                    user_input=user_input,
                    interaction_mode="chat"
                )
                
                # Generate response
                print("Assistant: ", end="", flush=True)
                response = self._generate_response(context_messages)
                
                if response:
                    print(response)
                    # Add assistant response to memory
                    self.memory.add_message("assistant", response, self.current_model)
                else:
                    print("Sorry, I couldn't generate a response.")
                    
                print()  # Add spacing
                
            except KeyboardInterrupt:
                print("\n\n🔄 Shutting down MemoryAI...")
                break
            except Exception as e:
                error_msg = handle_exception("chat_loop", e)
                print(f"❌ Error: {error_msg}")
                print()
    
    def _generate_response(self, context_messages) -> Optional[str]:
        """Generate response using Ollama"""
        try:
            # Simple system message for clean chat
            if not any(msg.get('role') == 'system' for msg in context_messages):
                system_msg = {
                    "role": "system", 
                    "content": "You are a helpful AI assistant. Be conversational and remember our previous discussions."
                }
                context_messages = [system_msg] + context_messages
            
            # Make API call
            response = self.ollama_client.chat_completion(
                model=self.current_model,
                messages=context_messages
            )
            
            if hasattr(response, 'message') and hasattr(response.message, 'content'):
                return response.message.content
            elif isinstance(response, dict) and 'message' in response:
                return response['message'].get('content', '')
            else:
                return str(response) if response else None
                
        except Exception as e:
            logging.error(f"Error generating response: {e}")
            return None
    
    def _show_help(self):
        """Show available commands"""
        print("\n🧠 MemoryAI Commands:")
        print("  help       - Show this help message")  
        print("  quit/exit  - Exit MemoryAI")
        print("  model <name> - Switch to different model")
        print("  stats      - Show memory statistics")
        print("  clear      - Clear current conversation")
        print("  Just type normally to chat!")
        print()
    
    def _handle_model_command(self, command: str):
        """Handle model switching command"""
        try:
            parts = command.split(' ', 1)
            if len(parts) < 2:
                print("❌ Usage: model <model_name>")
                return
            
            new_model = parts[1].strip()
            
            # Test if model is available
            test_response = self.ollama_client.chat_completion(
                model=new_model,
                messages=[{"role": "user", "content": "test"}]
            )
            
            if test_response:
                self.current_model = new_model
                print(f"✅ Switched to model: {new_model}")
            else:
                print(f"❌ Model '{new_model}' not available")
                
        except Exception as e:
            print(f"❌ Error switching model: {e}")
    
    def _show_memory_stats(self):
        """Show memory system statistics"""
        try:
            stats = self.memory.get_memory_stats(self.current_model)
            print(f"\n📊 Memory Stats for {self.current_model}:")
            print(f"  Conversations: {stats.get('total_exchanges', 0)}")
            print(f"  Total tokens: {stats.get('total_tokens', 0)}")
            print(f"  Avg exchange size: {stats.get('avg_exchange_tokens', 0):.1f} tokens")
            
            # Show all models with memory
            all_models = self.memory.get_models_with_memory()
            if len(all_models) > 1:
                print(f"  Other models with memory: {', '.join(m for m in all_models if m != self.current_model)}")
                
            print()
            
        except Exception as e:
            print(f"❌ Error getting stats: {e}")
    
    def _clear_conversation(self):
        """Clear current conversation"""
        try:
            confirm = input(f"Clear conversation for {self.current_model}? (y/N): ").strip().lower()
            if confirm == 'y':
                success = self.memory.clear_conversation(self.current_model)
                if success:
                    print("✅ Conversation cleared")
                else:
                    print("❌ Failed to clear conversation")
            else:
                print("Cancelled")
                
        except Exception as e:
            print(f"❌ Error clearing conversation: {e}")

def main():
    """Main entry point"""
    try:
        app = MemoryAI()
        app.chat_loop()
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
