"""
Configuration and constants for WorkspaceAI
"""

import platform
import os
import json
import logging
from pathlib import Path
from .exceptions import (
    WorkspaceAIError,
    ConfigurationError,
    handle_exception
)


# Version
VERSION = "3.0"

# ANSI Color codes for terminal output
CYAN = '\033[96m'
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
MAGENTA = '\033[95m'
WHITE = '\033[97m'
BOLD = '\033[1m'
RESET = '\033[0m'

# Application constants
CONSTANTS = {
    'VERSION': VERSION,
    'MODEL': 'qwen2.5:3b',
    'BASE_URL': 'http://127.0.0.1:11434',
    'MEMORY_LOCATION': 'WorkspaceAI/memory',
    'WORKSPACE_LOCATION': 'WorkspaceAI/workspace',
    'CONFIG_FILE': 'WorkspaceAI/config.json',
    'LOG_FILE': 'WorkspaceAI/workspaceai.log',
    'RECENT_CONVERSATIONS': 2,
    'SUMMARIZED_CONVERSATIONS': 8,
    'API_TIMEOUT': 30,
    'API_MAX_RETRIES': 3,
    'SUMMARY_TIMEOUT': 10,
    'MEMORY_CONTEXT_MESSAGES': 10,
    'MAX_RECENT_CONVERSATIONS': 2,
    'MAX_SUMMARIZED_CONVERSATIONS': 20,
    'MAX_FILENAME_LENGTH': 255,
    'PROGRESS_DURATION': 2,
    'SEARCH_MAX_FILE_KB': 1024,
    'SYSTEM_PROMPT': """You are WorkspaceAI, an intelligent file management assistant.

When tools are available and users request file operations, you MUST use the tools immediately.

Your tool selection has been enhanced with advanced intent classification and context weighting. Trust the system's tool recommendations and execute them directly.

For non-file requests (general questions, conversations), respond normally without tools."""
}

# Default application configuration
APP_CONFIG = {
    'model': CONSTANTS['MODEL'],
    'safe_mode': True,
    'ollama_host': 'localhost:11434',
    'search_max_file_kb': CONSTANTS['SEARCH_MAX_FILE_KB'],
    'verbose_output': False
}

def get_config_path():
    """Get the path to the config file"""
    return CONSTANTS['CONFIG_FILE']

def get_workspace_path():
    """Get the path to the workspace directory"""
    return CONSTANTS['WORKSPACE_LOCATION']

def get_memory_path():
    """Get the path to the memory directory"""
    return CONSTANTS['MEMORY_LOCATION']

def get_log_path():
    """Get the path to the log file"""
    return CONSTANTS['LOG_FILE']

def save_config(config):
    """Save configuration to file - backward compatible wrapper"""
    try:
        return _save_config_with_exceptions(config)
    except Exception as e:
        # Log error but don't raise for backward compatibility
        logging.error(f"Config save failed: {e}")
        print(f"Warning: Could not save config: {str(e)}")

def _save_config_with_exceptions(config):
    """Save configuration to file - raises exceptions for validation errors"""
    try:
        os.makedirs(os.path.dirname(get_config_path()), exist_ok=True)
        with open(get_config_path(), 'w', encoding='utf-8') as f:
            json.dump({
                "version": CONSTANTS['VERSION'],
                "settings": config
            }, f, indent=2)
    except PermissionError as e:
        # Use handle_exception for consistent error handling
        error = handle_exception("save_config", e)
        logging.error(f"Config save failed: {error}")
        raise error
    except OSError as e:
        # Handle OS-level errors (disk full, etc.)
        error = handle_exception("save_config", e) 
        logging.error(f"Config save failed: {error}")
        raise error
    except (TypeError, ValueError) as e:
        # Handle JSON serialization errors
        error = ConfigurationError(
            f"Cannot serialize config data: {e}"
        )
        error.context["config_type"] = type(config).__name__
        logging.error(f"Config validation failed: {error}")
        raise error
    except Exception as e:
        converted_error = handle_exception("save_config", e)
        logging.error(f"Config save failed: {converted_error}")
        raise converted_error

def load_config():
    """Load configuration from file - backward compatible wrapper"""
    try:
        return _load_config_with_exceptions()
    except Exception as e:
        # Log error but return default config for backward compatibility
        logging.error(f"Config load failed: {e}")
        print(f"Warning: Could not load config: {str(e)}")
        return APP_CONFIG.copy()

def _load_config_with_exceptions():
    """Load configuration from file - raises exceptions for validation errors"""
    config_path = get_config_path()
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('settings', APP_CONFIG)
        except PermissionError as e:
            # Use handle_exception for consistent error handling
            error = handle_exception("load_config", e)
            logging.error(f"Config load failed: {error}")
            raise error
        except json.JSONDecodeError as e:
            # Handle corrupted config files
            error = ConfigurationError(
                f"Config file is corrupted: {e}"
            )
            error.context["config_path"] = config_path
            logging.error(f"Config corruption detected: {error}")
            raise error
        except KeyError as e:
            # Handle missing required config structure
            error = ConfigurationError(
                f"Config file missing required structure: {e}"
            )
            error.context["config_path"] = config_path
            logging.error(f"Config validation failed: {error}")
            raise error
        except Exception as e:
            converted_error = handle_exception("load_config", e)
            logging.error(f"Config load failed: {converted_error}")
            raise converted_error
    return APP_CONFIG.copy()

def setup_logging():
    """Setup logging configuration - backward compatible wrapper"""
    try:
        return _setup_logging_with_exceptions()
    except Exception as e:
        # Always return a logger even on error for backward compatibility
        print(f"Warning: Could not setup logging: {str(e)}")
        return logging.getLogger(__name__)

def _setup_logging_with_exceptions():
    """Setup logging configuration - raises exceptions for validation errors"""
    try:
        # Load config to check verbose setting
        config = load_config()
        verbose_output = config.get('verbose_output', False)
        
        # Set log level based on verbose setting
        log_level = logging.INFO if verbose_output else logging.WARNING
        
        os.makedirs(os.path.dirname(get_log_path()), exist_ok=True)
        
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(get_log_path(), encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        logger = logging.getLogger(__name__)
        logger.setLevel(log_level)
        return logger
    except PermissionError as e:
        # Use handle_exception for consistent error handling
        error = handle_exception("setup_logging", e)
        raise error
    except OSError as e:
        # Handle OS-level errors (disk full, etc.)
        error = handle_exception("setup_logging", e)
        raise error
    except Exception as e:
        converted_error = handle_exception("setup_logging", e)
        raise converted_error

def update_logging_level(verbose_output: bool):
    """Update logging level based on verbose setting"""
    log_level = logging.INFO if verbose_output else logging.WARNING
    logging.getLogger().setLevel(log_level)
    # Also update all handlers
    for handler in logging.getLogger().handlers:
        handler.setLevel(log_level)
