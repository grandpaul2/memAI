"""
Integration Layer for Unified Memory System

Provides backward-compatible interface that integrates the new UnifiedMemoryManager
with the existing WorkspaceAI system while maintaining all current functionality.
"""

import logging
from typing import Optional, Dict, Any, List

from .unified_memory_manager import UnifiedMemoryManager
from .config import load_config
from .exceptions import handle_exception, MemoryError


logger = logging.getLogger(__name__)


class UnifiedMemoryInterface:
    """
    Backward-compatible interface that bridges the old memory system
    with the new UnifiedMemoryManager
    """
    
    def __init__(self, config=None):
        """Initialize the unified memory interface"""
        try:
            self.config = config or load_config()
            self.unified_manager = UnifiedMemoryManager(self.config)
            self._migrated = False
            
            # Perform automatic migration on first use
            self._ensure_migration()
            
            logger.info("UnifiedMemoryInterface initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize UnifiedMemoryInterface: {e}")
            raise MemoryError(f"Memory interface initialization failed: {e}") from e
    
    def _ensure_migration(self):
        """Ensure legacy memory has been migrated to new format"""
        if not self._migrated:
            try:
                success = self.unified_manager.migrate_legacy_memory()
                if success:
                    logger.info("Legacy memory migration completed successfully")
                else:
                    logger.warning("Legacy memory migration encountered issues")
                self._migrated = True
            except Exception as e:
                logger.error(f"Migration failed: {e}")
                # Continue anyway - system should work without migration
                self._migrated = True
    
    def get_context_messages(self, model: Optional[str] = None, 
                           user_input: Optional[str] = None,
                           interaction_mode: str = "chat",
                           context_window: int = 32768) -> List[Dict[str, Any]]:
        """
        Get context messages for a model, optimized for the current query
        
        Args:
            model: Model name (uses default if None)
            user_input: Current user input for complexity analysis
            interaction_mode: "chat" or "tools"
            context_window: Model's context window size
            
        Returns:
            List of context messages ready for chat completion
        """
        try:
            # Use default model if none specified
            if model is None:
                model = self.config.get('default_model', 'unknown-model')
            
            # If no user input provided, just get recent conversation
            if user_input is None:
                return self._get_simple_context(model, context_window)
            
            # Use full context preparation with adaptive budgets
            context_result = self.unified_manager.prepare_context_for_model(
                model=model,
                user_input=user_input,
                interaction_mode=interaction_mode,
                context_window=context_window
            )
            
            return context_result['context_messages']
            
        except Exception as e:
            logger.error(f"Error getting context messages: {e}")
            # Fallback to empty context
            return []
    
    def add_message(self, role: str, content: str, model: Optional[str] = None,
                   tokens: Optional[int] = None):
        """
        Add a message to conversation history
        
        Args:
            role: "user" or "assistant"  
            content: Message content
            model: Model name (uses default if None)
            tokens: Pre-calculated token count (estimated if None)
        """
        try:
            if model is None:
                model = self.config.get('default_model', 'unknown-model')
            
            # Store in temporary buffer until we have a complete exchange
            if not hasattr(self, '_pending_exchange'):
                self._pending_exchange = {}
            
            if role == "user":
                self._pending_exchange['user'] = {
                    'content': content,
                    'tokens': tokens
                }
                self._pending_exchange['model'] = model
            elif role == "assistant":
                if 'user' in self._pending_exchange:
                    # Complete exchange - add to memory
                    user_data = self._pending_exchange['user']
                    
                    success = self.unified_manager.add_exchange(
                        model=self._pending_exchange.get('model', model),
                        user_content=user_data['content'],
                        assistant_content=content,
                        user_tokens=user_data.get('tokens'),
                        assistant_tokens=tokens
                    )
                    
                    if success:
                        logger.debug(f"Added complete exchange to {model}")
                    else:
                        logger.warning(f"Failed to add exchange to {model}")
                    
                    # Clear pending exchange
                    self._pending_exchange = {}
                else:
                    # Assistant message without user message - store as pending
                    self._pending_exchange['assistant'] = {
                        'content': content,
                        'tokens': tokens
                    }
                    self._pending_exchange['model'] = model
            
        except Exception as e:
            logger.error(f"Error adding message: {e}")
    
    def save_memory_async(self):
        """
        Compatibility method - memory is saved automatically in new system
        """
        # The new system saves automatically, so this is just for compatibility
        logger.debug("save_memory_async called - memory saves automatically in new system")
    
    def reset_memory(self, model: Optional[str] = None):
        """
        Reset conversation memory for a model
        
        Args:
            model: Model name (uses default if None)
        """
        try:
            if model is None:
                model = self.config.get('default_model', 'unknown-model')
            
            success = self.unified_manager.clear_conversation(model)
            if success:
                logger.info(f"Reset memory for {model}")
            else:
                logger.warning(f"Failed to reset memory for {model}")
            
        except Exception as e:
            logger.error(f"Error resetting memory: {e}")
    
    def get_conversation_summary(self, model: Optional[str] = None, 
                               max_exchanges: int = 10) -> List[Dict]:
        """
        Get a summary of recent conversation
        
        Args:
            model: Model name (uses default if None)
            max_exchanges: Maximum exchanges to return
            
        Returns:
            List of recent exchanges
        """
        try:
            if model is None:
                model = self.config.get('default_model', 'unknown-model')
            
            return self.unified_manager.get_conversation_history(
                model=model,
                max_exchanges=max_exchanges
            )
            
        except Exception as e:
            logger.error(f"Error getting conversation summary: {e}")
            return []
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get comprehensive memory statistics"""
        try:
            return self.unified_manager.get_memory_stats()
        except Exception as e:
            logger.error(f"Error getting memory stats: {e}")
            return {'error': str(e)}
    
    def _get_simple_context(self, model: str, context_window: int) -> List[Dict[str, Any]]:
        """Get simple context without complexity analysis"""
        try:
            # Allocate 80% of context to conversation memory
            memory_budget = int(context_window * 0.8)
            
            conversation = self.unified_manager.get_conversation_history(
                model=model,
                max_tokens=memory_budget
            )
            
            # Convert to message format
            messages = []
            for exchange in conversation:
                if 'user' in exchange and exchange['user'].get('content'):
                    messages.append({
                        'role': 'user',
                        'content': exchange['user']['content']
                    })
                
                if 'assistant' in exchange and exchange['assistant'].get('content'):
                    messages.append({
                        'role': 'assistant',
                        'content': exchange['assistant']['content']
                    })
            
            return messages
            
        except Exception as e:
            logger.error(f"Error getting simple context: {e}")
            return []


# Create global instance for backward compatibility
try:
    unified_memory = UnifiedMemoryInterface()
    logger.info("Global unified memory interface created")
except Exception as e:
    logger.error(f"Failed to create global unified memory interface: {e}")
    # Create a fallback that won't crash the system
    unified_memory = None


def get_unified_memory() -> Optional[UnifiedMemoryInterface]:
    """Get the global unified memory interface"""
    return unified_memory


def prepare_context_with_adaptive_budgets(model: str, user_input: str,
                                        interaction_mode: str = "chat",
                                        context_window: int = 32768) -> Dict[str, Any]:
    """
    High-level function to prepare context with adaptive budget allocation
    
    Args:
        model: Model name
        user_input: User's query for complexity analysis
        interaction_mode: "chat" or "tools"
        context_window: Model's context window size
        
    Returns:
        Dictionary with context messages and budget information
    """
    try:
        if unified_memory is None:
            logger.error("Unified memory interface not available")
            return {
                'context_messages': [],
                'error': 'Memory interface not available'
            }
        
        return unified_memory.unified_manager.prepare_context_for_model(
            model=model,
            user_input=user_input,
            interaction_mode=interaction_mode,
            context_window=context_window
        )
        
    except Exception as e:
        logger.error(f"Error preparing context with adaptive budgets: {e}")
        return {
            'context_messages': [],
            'error': str(e)
        }


def add_conversation_exchange(model: str, user_content: str, assistant_content: str,
                            user_tokens: Optional[int] = None, 
                            assistant_tokens: Optional[int] = None) -> bool:
    """
    High-level function to add a complete conversation exchange
    
    Args:
        model: Model name
        user_content: User message content
        assistant_content: Assistant response content
        user_tokens: Optional user token count
        assistant_tokens: Optional assistant token count
        
    Returns:
        True if successful, False otherwise
    """
    try:
        if unified_memory is None:
            logger.error("Unified memory interface not available")
            return False
        
        return unified_memory.unified_manager.add_exchange(
            model=model,
            user_content=user_content,
            assistant_content=assistant_content,
            user_tokens=user_tokens,
            assistant_tokens=assistant_tokens
        )
        
    except Exception as e:
        logger.error(f"Error adding conversation exchange: {e}")
        return False


def get_system_health() -> Dict[str, Any]:
    """Get comprehensive system health information"""
    try:
        if unified_memory is None:
            return {
                'status': 'unhealthy',
                'error': 'Unified memory interface not available'
            }
        
        health = unified_memory.unified_manager.validate_system_health()
        health['status'] = 'healthy' if health.get('integration_validation', {}).get('is_valid', False) else 'degraded'
        
        return health
        
    except Exception as e:
        logger.error(f"Error getting system health: {e}")
        return {
            'status': 'unhealthy',
            'error': str(e)
        }
