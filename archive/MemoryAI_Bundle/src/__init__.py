"""
MemoryAI - Focused Memory System
AI assistant with advanced conversation memory
"""

# Core modules  
from .simple_config import Config, CONSTANTS, get_memory_path, load_config
from .exceptions import MemoryError, handle_exception

# Memory system
from .memory import MemoryManager
from .unified_memory_manager import UnifiedMemoryManager
from .memory_integration import UnifiedMemoryInterface

# Integration layer  
from .ollama_client import OllamaClient

# Create alias for compatibility
MemoryIntegration = UnifiedMemoryInterface

__version__ = "1.0.0"
__author__ = "MemoryAI Team"

__all__ = [
    'Config', 'CONSTANTS', 'MemoryError', 'handle_exception',
    'MemoryManager', 'UnifiedMemoryManager', 'UnifiedMemoryInterface', 'MemoryIntegration',
    'OllamaClient'
]
