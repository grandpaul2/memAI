#!/usr/bin/env python3
"""
Simple Configuration Class for MemoryAI
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional


class Config:
    """Simple configuration management for MemoryAI"""
    
    def __init__(self, config_file: str = "config.json"):
        """Initialize configuration"""
        self.config_file = config_file
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                print(f"Warning: Could not load config from {self.config_file}, using defaults")
        
        # Return default configuration
        return {
            "default_model": "qwen2.5:3b",
            "verbose_output": False,
            "memory_settings": {
                "max_recent_exchanges": 50,
                "max_summarized_conversations": 20,
                "auto_summarize_threshold": 100
            },
            "ollama_settings": {
                "base_url": "http://localhost:11434",
                "timeout": 30,
                "context_window": 32768
            },
            "logging": {
                "level": "INFO",
                "file": "memoryai.log"
            }
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any) -> None:
        """Set configuration value"""
        keys = key.split('.')
        config = self.config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    def save(self) -> bool:
        """Save configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=4)
            return True
        except IOError:
            return False


# Constants for compatibility
CONSTANTS = {
    'VERSION': '1.0.0',
    'MODEL': 'qwen2.5:3b',
    'BASE_URL': 'http://127.0.0.1:11434',
    'MEMORY_LOCATION': 'memory',
    'API_TIMEOUT': 30,
    'MAX_RECENT_CONVERSATIONS': 50,
    'MAX_SUMMARIZED_CONVERSATIONS': 20,
}

# Functions for compatibility
def get_memory_path() -> str:
    """Get memory storage path"""
    memory_path = Path("memory")
    memory_path.mkdir(exist_ok=True)
    return str(memory_path)

def get_config_path() -> str:
    """Get config file path"""
    return "config.json"

def load_config() -> Dict[str, Any]:
    """Load configuration - compatibility function"""
    config = Config()
    return config.config

def save_config(config_data: Dict[str, Any]) -> bool:
    """Save configuration - compatibility function"""
    try:
        with open("config.json", 'w') as f:
            json.dump(config_data, f, indent=4)
        return True
    except IOError:
        return False
