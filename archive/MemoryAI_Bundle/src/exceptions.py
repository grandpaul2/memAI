"""
Simplified Exception Classes for WorkspaceAI
Basic exceptions focused on tool selection accuracy without verbose error handling
"""


class WorkspaceAIError(Exception):
    """Base exception for WorkspaceAI errors"""
    def __init__(self, message="", **context):
        super().__init__(message)
        # Store any additional context information
        self.context = context or {}


class ConfigurationError(WorkspaceAIError):
    """Configuration-related errors"""
    pass


class ConfigFileError(ConfigurationError):
    """Configuration file-related errors"""
    pass


class PackageManagerError(WorkspaceAIError):
    """Package manager operation errors"""
    pass


class UnsupportedPlatformError(WorkspaceAIError):
    """Platform not supported errors"""
    pass


class OllamaConnectionError(WorkspaceAIError):
    """Ollama connection errors"""
    pass


class IntentError(WorkspaceAIError):
    """Intent classification errors"""
    pass


class AmbiguousIntentError(IntentError):
    """Multiple intents with equal confidence"""
    pass


class UnknownIntentError(IntentError):
    """No matching intent patterns"""
    pass


class ToolExecutionError(WorkspaceAIError):
    """Tool execution errors"""
    pass


class ToolNotFoundError(ToolExecutionError):
    """Requested tool not found"""
    pass


class ToolParameterError(ToolExecutionError):
    """Tool parameter validation errors"""
    pass


class MemoryError(WorkspaceAIError):
    """Memory system errors"""
    pass


class ConversationError(WorkspaceAIError):
    """Conversation context errors"""
    pass


# Simple error handler that just logs and re-raises
def handle_exception(context: str, error: Exception):
    """Simple error handler for basic logging"""
    import logging
    logger = logging.getLogger(__name__)
    logger.error(f"{context}: {error}")
    return error  # Return the error instead of raising it


# Backward compatibility - for code that expects log_and_raise
def log_and_raise(context: str, error: Exception):
    """Backward compatibility function"""
    return handle_exception(context, error)
