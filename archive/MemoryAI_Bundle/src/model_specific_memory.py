"""
Model-Specific Memory Management

Provides per-model memory file organization with atomic operations,
corruption protection, and collision-safe filename conversion.
"""

import json
import hashlib
import tempfile
import shutil
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime


class ModelSpecificMemory:
    """Per-model memory files for task separation and corruption isolation"""
    
    def __init__(self, base_memory_dir: str = "WorkspaceAI/memory"):
        """
        Initialize model-specific memory manager
        
        Args:
            base_memory_dir: Base directory for all memory files
        """
        self.base_dir = Path(base_memory_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
        # Memory file structure
        self.memory_template = {
            "metadata": {
                "model": "",
                "created_at": "",
                "last_modified": "",
                "version": "3.0",
                "total_exchanges": 0
            },
            "current_conversation": [],
            "summarized_conversations": []
        }
    
    def _model_to_filename(self, model: str) -> str:
        """
        Convert model name to safe filename with collision detection
        
        Args:
            model: Model name (e.g., "qwen2.5:7b", "model-v1:2b")
            
        Returns:
            Safe filename with hash suffix for uniqueness
        """
        if not model:
            model = "unknown"
        
        # Replace problematic characters with safe alternatives
        safe_name = model.replace(":", "-").replace("/", "-").replace("\\", "-")
        safe_name = safe_name.replace(" ", "_").replace(".", "-")
        
        # Remove any remaining problematic characters
        safe_chars = []
        for char in safe_name:
            if char.isalnum() or char in "-_":
                safe_chars.append(char)
            else:
                safe_chars.append("_")
        
        safe_name = "".join(safe_chars)
        
        # Add hash suffix to prevent collisions
        model_hash = hashlib.md5(model.encode()).hexdigest()[:8]
        filename = f"{safe_name}_{model_hash}.json"
        
        return filename
    
    def _get_memory_path(self, model: str) -> Path:
        """Get the full path for a model's memory file"""
        filename = self._model_to_filename(model)
        return self.base_dir / filename
    
    def _validate_memory_structure(self, memory_data: dict, model: str) -> bool:
        """
        Validate memory structure and fix common issues
        
        Args:
            memory_data: Memory dictionary to validate
            model: Model name for validation
            
        Returns:
            True if valid/fixable, False if corrupted beyond repair
        """
        try:
            # Check top-level structure
            required_keys = ["metadata", "current_conversation", "summarized_conversations"]
            for key in required_keys:
                if key not in memory_data:
                    memory_data[key] = self.memory_template[key].copy()
            
            # Validate metadata
            if not isinstance(memory_data["metadata"], dict):
                memory_data["metadata"] = self.memory_template["metadata"].copy()
            
            metadata = memory_data["metadata"]
            if "model" not in metadata or not metadata["model"]:
                metadata["model"] = model
            if "version" not in metadata:
                metadata["version"] = "3.0"
            if "total_exchanges" not in metadata:
                metadata["total_exchanges"] = len(memory_data.get("current_conversation", []))
            
            # Validate conversation arrays
            if not isinstance(memory_data["current_conversation"], list):
                memory_data["current_conversation"] = []
            if not isinstance(memory_data["summarized_conversations"], list):
                memory_data["summarized_conversations"] = []
            
            # Validate individual exchanges
            valid_exchanges = []
            for exchange in memory_data["current_conversation"]:
                if isinstance(exchange, dict) and "user" in exchange and "assistant" in exchange:
                    valid_exchanges.append(exchange)
            
            memory_data["current_conversation"] = valid_exchanges
            memory_data["metadata"]["total_exchanges"] = len(valid_exchanges)
            
            return True
            
        except Exception as e:
            print(f"Memory validation failed for {model}: {e}")
            return False
    
    def load_memory(self, model: str) -> dict:
        """
        Load memory for a specific model with validation and error recovery
        
        Args:
            model: Model name
            
        Returns:
            Memory dictionary (creates new if doesn't exist or corrupted)
        """
        memory_path = self._get_memory_path(model)
        
        # Return new memory if file doesn't exist
        if not memory_path.exists():
            return self._create_new_memory(model)
        
        try:
            # Load existing memory
            with open(memory_path, 'r', encoding='utf-8') as f:
                memory_data = json.load(f)
            
            # Validate and fix structure if needed
            if self._validate_memory_structure(memory_data, model):
                # Update last accessed time
                memory_data["metadata"]["last_accessed"] = datetime.now().isoformat()
                return memory_data
            else:
                print(f"Memory corrupted for {model}, creating backup and new memory")
                return self._handle_corrupted_memory(memory_path, model)
                
        except (json.JSONDecodeError, IOError, KeyError) as e:
            print(f"Failed to load memory for {model}: {e}")
            return self._handle_corrupted_memory(memory_path, model)
    
    def save_memory(self, model: str, memory_data: dict) -> bool:
        """
        Atomically save memory for a specific model
        
        Args:
            model: Model name
            memory_data: Memory dictionary to save
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Validate structure before saving
            if not self._validate_memory_structure(memory_data, model):
                print(f"Cannot save invalid memory structure for {model}")
                return False
            
            # Update metadata
            memory_data["metadata"]["model"] = model
            memory_data["metadata"]["last_modified"] = datetime.now().isoformat()
            memory_data["metadata"]["total_exchanges"] = len(memory_data.get("current_conversation", []))
            
            memory_path = self._get_memory_path(model)
            
            # Atomic write using temporary file
            with tempfile.NamedTemporaryFile(
                mode='w', 
                encoding='utf-8', 
                dir=self.base_dir, 
                delete=False,
                suffix='.tmp'
            ) as temp_file:
                json.dump(memory_data, temp_file, indent=2, ensure_ascii=False)
                temp_path = temp_file.name
            
            # Atomic move to final location
            shutil.move(temp_path, memory_path)
            
            return True
            
        except Exception as e:
            print(f"Failed to save memory for {model}: {e}")
            
            # Clean up temporary file if it exists
            try:
                if 'temp_path' in locals() and Path(temp_path).exists():
                    Path(temp_path).unlink()
            except:
                pass
            
            return False
    
    def _create_new_memory(self, model: str) -> dict:
        """Create new memory structure for a model"""
        import copy
        memory = copy.deepcopy(self.memory_template)
        memory["metadata"]["model"] = model
        memory["metadata"]["created_at"] = datetime.now().isoformat()
        memory["metadata"]["last_modified"] = datetime.now().isoformat()
        
        return memory
    
    def _handle_corrupted_memory(self, memory_path: Path, model: str) -> dict:
        """
        Handle corrupted memory by creating backup and new memory
        
        Args:
            memory_path: Path to corrupted memory file
            model: Model name
            
        Returns:
            New memory dictionary
        """
        try:
            # Create backup of corrupted file
            timestamp = int(time.time())
            backup_path = memory_path.with_suffix(f'.corrupted.{timestamp}')
            shutil.copy2(memory_path, backup_path)
            print(f"Corrupted memory backed up to: {backup_path}")
            
        except Exception as e:
            print(f"Failed to backup corrupted memory: {e}")
        
        # Return new memory
        return self._create_new_memory(model)
    
    def add_exchange(self, model: str, user_content: str, assistant_content: str, 
                    user_tokens: Optional[int] = None, assistant_tokens: Optional[int] = None) -> bool:
        """
        Add a conversation exchange to model memory
        
        Args:
            model: Model name
            user_content: User message content
            assistant_content: Assistant response content
            user_tokens: Optional token count for user message
            assistant_tokens: Optional token count for assistant response
            
        Returns:
            True if successful, False otherwise
        """
        try:
            memory = self.load_memory(model)
            
            # Estimate tokens if not provided (rough estimation)
            if user_tokens is None:
                user_tokens = max(1, len(user_content) // 4)  # Simple fallback estimation
            if assistant_tokens is None:
                assistant_tokens = max(1, len(assistant_content) // 4)  # Simple fallback estimation
            
            exchange = {
                "timestamp": datetime.now().isoformat(),
                "user": {
                    "content": user_content,
                    "tokens": user_tokens
                },
                "assistant": {
                    "content": assistant_content,
                    "tokens": assistant_tokens
                }
            }
            
            memory["current_conversation"].append(exchange)
            
            return self.save_memory(model, memory)
            
        except Exception as e:
            print(f"Failed to add exchange for {model}: {e}")
            return False
    
    def get_conversation_history(self, model: str, max_exchanges: Optional[int] = None) -> List[dict]:
        """
        Get conversation history for a model
        
        Args:
            model: Model name
            max_exchanges: Maximum number of recent exchanges to return
            
        Returns:
            List of conversation exchanges
        """
        memory = self.load_memory(model)
        conversation = memory.get("current_conversation", [])
        
        if max_exchanges is not None and max_exchanges > 0:
            return conversation[-max_exchanges:]
        
        return conversation
    
    def clear_conversation(self, model: str) -> bool:
        """
        Clear conversation history for a model (keeps metadata)
        
        Args:
            model: Model name
            
        Returns:
            True if successful, False otherwise
        """
        try:
            memory = self.load_memory(model)
            
            # Move current conversation to summarized if it exists
            if memory["current_conversation"]:
                summary_entry = {
                    "summarized_at": datetime.now().isoformat(),
                    "exchange_count": len(memory["current_conversation"]),
                    "date_range": {
                        "start": memory["current_conversation"][0].get("timestamp", "unknown"),
                        "end": memory["current_conversation"][-1].get("timestamp", "unknown")
                    }
                }
                memory["summarized_conversations"].append(summary_entry)
            
            # Clear current conversation
            memory["current_conversation"] = []
            
            return self.save_memory(model, memory)
            
        except Exception as e:
            print(f"Failed to clear conversation for {model}: {e}")
            return False
    
    def list_models_with_memory(self) -> List[str]:
        """
        List all models that have memory files
        
        Returns:
            List of model names that have existing memory
        """
        models = []
        
        try:
            for memory_file in self.base_dir.glob("*.json"):
                try:
                    with open(memory_file, 'r', encoding='utf-8') as f:
                        memory_data = json.load(f)
                    
                    model_name = memory_data.get("metadata", {}).get("model")
                    if model_name:
                        models.append(model_name)
                        
                except Exception:
                    # Skip corrupted files
                    continue
                    
        except Exception as e:
            print(f"Failed to list models: {e}")
        
        return sorted(models)
    
    def get_memory_stats(self, model: str) -> dict:
        """
        Get statistics about a model's memory
        
        Args:
            model: Model name
            
        Returns:
            Dictionary with memory statistics
        """
        try:
            memory = self.load_memory(model)
            
            stats = {
                "model": model,
                "total_exchanges": len(memory.get("current_conversation", [])),
                "summarized_conversations": len(memory.get("summarized_conversations", [])),
                "created_at": memory.get("metadata", {}).get("created_at"),
                "last_modified": memory.get("metadata", {}).get("last_modified"),
                "memory_file": str(self._get_memory_path(model))
            }
            
            # Calculate conversation date range
            conversation = memory.get("current_conversation", [])
            if conversation:
                stats["conversation_date_range"] = {
                    "start": conversation[0].get("timestamp"),
                    "end": conversation[-1].get("timestamp")
                }
            
            return stats
            
        except Exception as e:
            return {
                "model": model,
                "error": str(e),
                "memory_file": str(self._get_memory_path(model))
            }
