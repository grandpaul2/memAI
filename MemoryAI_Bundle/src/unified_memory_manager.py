"""
Unified Memory Manager

Orchestrates all memory system components to provide a single, consistent
interface for conversation memory management with per-model organization
and adaptive budget allocation.
"""

import os
import json
import shutil
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from pathlib import Path

from .token_counter import SimpleTokenCounter, TokenBudgetManager
from .model_specific_memory import ModelSpecificMemory
from .adaptive_budget_manager import AdaptiveBudgetManager, InteractionMode
from .safety_validator import SafetyValidator
from .config import get_memory_path
from .exceptions import handle_exception, MemoryError


logger = logging.getLogger(__name__)


class UnifiedMemoryManager:
    """
    Single point of control for all memory operations
    
    Provides unified interface that:
    - Manages per-model conversation histories
    - Calculates adaptive token budgets based on query complexity
    - Validates all operations for safety
    - Handles migration from legacy memory format
    """
    
    def __init__(self, config=None):
        """
        Initialize unified memory manager
        
        Args:
            config: Optional configuration dictionary
        """
        if config is None:
            from .config import APP_CONFIG
            config = APP_CONFIG
            
        self.config = config
        
        # Initialize core components
        self.token_counter = SimpleTokenCounter()
        self.budget_manager = TokenBudgetManager(self.token_counter)
        self.memory_manager = ModelSpecificMemory(get_memory_path())
        self.adaptive_budget = AdaptiveBudgetManager()
        self.validator = SafetyValidator(strict_mode=config.get('strict_validation', False))
        
        # Cache for current session
        self._current_model = None
        self._last_budgets = {}
        self._session_stats = {
            'exchanges_added': 0,
            'validations_run': 0,
            'migrations_performed': 0
        }
        
        logger.info("UnifiedMemoryManager initialized successfully")
    
    def prepare_context_for_model(self, model: str, user_input: str, 
                                interaction_mode: str = "chat",
                                context_window: int = 32768,
                                minimum_exchanges: int = 0) -> Dict[str, Any]:
        """
        Prepare optimized context for a specific model and query
        
        Args:
            model: Model name/identifier
            user_input: User's input query
            interaction_mode: "chat" or "tools"
            context_window: Model's context window size
            minimum_exchanges: Minimum conversation exchanges to include
            
        Returns:
            Dictionary with prepared context and budget information
        """
        try:
            self._current_model = model
            
            # Step 1: Analyze query complexity
            complexity_score = self.adaptive_budget.analyze_complexity(user_input, interaction_mode)
            
            # Step 2: Calculate adaptive budgets
            budgets = self.adaptive_budget.calculate_adaptive_budgets(
                context_window=context_window,
                mode=interaction_mode,
                user_input=user_input
            )
            
            # Step 3: Validate budget allocation
            budget_validation = self.validator.validate_token_budgets(
                budgets, context_window, complexity_score
            )
            
            if not budget_validation.is_valid:
                logger.warning(f"Budget validation failed for {model}: {budget_validation.errors}")
            
            # Step 4: Load conversation history within budget
            conversation_history = self._get_conversation_within_budget(
                model=model,
                budget=budgets.get('conversation_memory', 0),
                minimum_exchanges=minimum_exchanges
            )
            
            # Step 5: Prepare context messages
            context_messages = self._build_context_messages(
                conversation_history=conversation_history,
                model=model
            )
            
            # Step 6: Final validation
            actual_memory_tokens = self.token_counter.estimate_conversation_tokens(context_messages)
            memory_budget = budgets.get('conversation_memory', 0)
            
            if actual_memory_tokens > memory_budget:
                logger.warning(
                    f"Memory exceeds budget: {actual_memory_tokens} > {memory_budget} tokens"
                )
                # Trim conversation to fit budget
                context_messages = self._trim_conversation_to_budget(
                    context_messages, memory_budget
                )
            
            # Cache results
            self._last_budgets = budgets
            self._session_stats['validations_run'] += 1
            
            result = {
                'context_messages': context_messages,
                'budgets': budgets,
                'complexity_score': complexity_score,
                'validation': budget_validation,
                'stats': {
                    'conversation_exchanges': len(conversation_history),
                    'estimated_memory_tokens': actual_memory_tokens,
                    'memory_budget': memory_budget,
                    'response_budget': budgets.get('response_generation', 0),
                    'utilization_percent': (sum(budgets.values()) / context_window) * 100
                }
            }
            
            logger.info(f"Context prepared for {model}: {len(context_messages)} messages, "
                       f"{complexity_score:.3f} complexity, {result['stats']['utilization_percent']:.1f}% utilization")
            
            return result
            
        except Exception as e:
            error_msg = f"Failed to prepare context for {model}: {str(e)}"
            logger.error(error_msg)
            raise MemoryError(error_msg) from e
    
    def add_exchange(self, model: str, user_content: str, assistant_content: str,
                    user_tokens: Optional[int] = None, assistant_tokens: Optional[int] = None) -> bool:
        """
        Add a conversation exchange to model-specific memory
        
        Args:
            model: Model name/identifier  
            user_content: User message content
            assistant_content: Assistant response content
            user_tokens: Optional pre-calculated user token count
            assistant_tokens: Optional pre-calculated assistant token count
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Estimate tokens if not provided
            if user_tokens is None:
                user_tokens = self.token_counter.estimate_tokens(user_content)
            if assistant_tokens is None:
                assistant_tokens = self.token_counter.estimate_tokens(assistant_content)
            
            # Validate exchange before adding
            exchange_validation = self._validate_exchange(
                user_content, assistant_content, user_tokens, assistant_tokens
            )
            
            if not exchange_validation.is_valid:
                logger.warning(f"Exchange validation failed: {exchange_validation.errors}")
                if self.validator.strict_mode:
                    return False
            
            # Add to model-specific memory
            success = self.memory_manager.add_exchange(
                model=model,
                user_content=user_content,
                assistant_content=assistant_content,
                user_tokens=user_tokens,
                assistant_tokens=assistant_tokens
            )
            
            if success:
                self._session_stats['exchanges_added'] += 1
                logger.info(f"Added exchange to {model}: {user_tokens}+{assistant_tokens} tokens")
            else:
                logger.error(f"Failed to add exchange to {model}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error adding exchange to {model}: {str(e)}")
            return False
    
    def get_conversation_history(self, model: str, max_exchanges: Optional[int] = None,
                               max_tokens: Optional[int] = None) -> List[Dict]:
        """
        Get conversation history for a model with optional limits
        
        Args:
            model: Model name/identifier
            max_exchanges: Maximum number of exchanges to return
            max_tokens: Maximum token budget for returned conversation
            
        Returns:
            List of conversation exchanges
        """
        try:
            # Get raw conversation history
            history = self.memory_manager.get_conversation_history(model, max_exchanges)
            
            # Apply token budget if specified
            if max_tokens is not None:
                history = self._trim_conversation_to_budget(history, max_tokens)
            
            return history
            
        except Exception as e:
            logger.error(f"Error getting conversation history for {model}: {str(e)}")
            return []
    
    def clear_conversation(self, model: str) -> bool:
        """
        Clear conversation history for a model
        
        Args:
            model: Model name/identifier
            
        Returns:
            True if successful, False otherwise
        """
        try:
            success = self.memory_manager.clear_conversation(model)
            if success:
                logger.info(f"Cleared conversation for {model}")
            return success
            
        except Exception as e:
            logger.error(f"Error clearing conversation for {model}: {str(e)}")
            return False
    
    def migrate_legacy_memory(self, legacy_memory_path: Optional[str] = None) -> bool:
        """
        Migrate legacy memory.json to per-model format
        
        Args:
            legacy_memory_path: Path to legacy memory file (auto-detected if None)
            
        Returns:
            True if successful or no migration needed, False if failed
        """
        try:
            # Auto-detect legacy memory file
            if legacy_memory_path is None:
                legacy_memory_path = os.path.join(get_memory_path(), "memory.json")
            
            if not os.path.exists(legacy_memory_path):
                logger.info("No legacy memory file found, migration not needed")
                return True
            
            # Load legacy memory
            with open(legacy_memory_path, 'r') as f:
                legacy_data = json.load(f)
            
            # Extract conversation data
            current_conversation = legacy_data.get('current_conversation', [])
            recent_conversations = legacy_data.get('recent_conversations', [])
            
            if not current_conversation and not recent_conversations:
                logger.info("Legacy memory file is empty, migration not needed")
                return True
            
            # Group exchanges by model (or assign to default model)
            default_model = self.config.get('default_model', 'unknown-model')
            migrated_exchanges = 0
            
            # Migrate current conversation
            for exchange in current_conversation:
                model = self._extract_model_from_exchange(exchange, default_model)
                
                if 'user' in exchange and 'assistant' in exchange:
                    user_data = exchange['user']
                    assistant_data = exchange['assistant']
                    
                    success = self.memory_manager.add_exchange(
                        model=model,
                        user_content=user_data.get('content', ''),
                        assistant_content=assistant_data.get('content', ''),
                        user_tokens=user_data.get('tokens'),
                        assistant_tokens=assistant_data.get('tokens')
                    )
                    
                    if success:
                        migrated_exchanges += 1
            
            # Migrate recent conversations
            for conversation in recent_conversations:
                if isinstance(conversation, list):
                    for exchange in conversation:
                        model = self._extract_model_from_exchange(exchange, default_model)
                        
                        if 'user' in exchange and 'assistant' in exchange:
                            user_data = exchange['user']
                            assistant_data = exchange['assistant']
                            
                            success = self.memory_manager.add_exchange(
                                model=model,
                                user_content=user_data.get('content', ''),
                                assistant_content=assistant_data.get('content', ''),
                                user_tokens=user_data.get('tokens'),
                                assistant_tokens=assistant_data.get('tokens')
                            )
                            
                            if success:
                                migrated_exchanges += 1
            
            # Validate migration
            migration_validation = self.validator.validate_migration_integrity(
                legacy_data, {default_model: self.memory_manager.load_memory(default_model)}
            )
            
            if migration_validation.is_valid:
                # Create backup of legacy file
                backup_path = f"{legacy_memory_path}.migrated.{int(datetime.now().timestamp())}"
                shutil.copy2(legacy_memory_path, backup_path)
                
                logger.info(f"Migration successful: {migrated_exchanges} exchanges migrated")
                logger.info(f"Legacy memory backed up to: {backup_path}")
                
                self._session_stats['migrations_performed'] += 1
                return True
            else:
                logger.error(f"Migration validation failed: {migration_validation.errors}")
                return False
            
        except Exception as e:
            logger.error(f"Migration failed: {str(e)}")
            return False
    
    def get_models_with_memory(self) -> List[str]:
        """Get list of all models that have conversation history"""
        try:
            return self.memory_manager.list_models_with_memory()
        except Exception as e:
            logger.error(f"Error listing models with memory: {str(e)}")
            return []
    
    def get_memory_stats(self, model: Optional[str] = None) -> Dict[str, Any]:
        """
        Get comprehensive memory statistics
        
        Args:
            model: Specific model to get stats for (all models if None)
            
        Returns:
            Dictionary with memory statistics
        """
        try:
            if model:
                # Stats for specific model
                model_stats = self.memory_manager.get_memory_stats(model)
                return {
                    'model_stats': model_stats,
                    'session_stats': self._session_stats.copy(),
                    'last_budgets': self._last_budgets.copy()
                }
            else:
                # Stats for all models
                all_models = self.get_models_with_memory()
                model_stats = {}
                
                for model_name in all_models:
                    model_stats[model_name] = self.memory_manager.get_memory_stats(model_name)
                
                return {
                    'all_models': model_stats,
                    'total_models': len(all_models),
                    'session_stats': self._session_stats.copy(),
                    'last_budgets': self._last_budgets.copy()
                }
                
        except Exception as e:
            logger.error(f"Error getting memory stats: {str(e)}")
            return {'error': str(e)}
    
    def validate_system_health(self) -> Dict[str, Any]:
        """
        Perform comprehensive system health validation
        
        Returns:
            Dictionary with validation results and recommendations
        """
        try:
            # Validate system integration
            components = {
                'token_counter': self.token_counter,
                'memory_manager': self.memory_manager,
                'budget_manager': self.budget_manager,
                'adaptive_budget': self.adaptive_budget,
                'validator': self.validator
            }
            
            integration_result = self.validator.validate_system_integration(components)
            
            # Get validation summary
            validation_summary = self.validator.get_validation_summary()
            
            # System health metrics
            health_metrics = {
                'models_with_memory': len(self.get_models_with_memory()),
                'session_exchanges': self._session_stats['exchanges_added'],
                'session_validations': self._session_stats['validations_run'],
                'current_model': self._current_model,
                'last_budgets_valid': bool(self._last_budgets),
                'integration_valid': integration_result.is_valid
            }
            
            return {
                'integration_validation': integration_result,
                'validation_summary': validation_summary,
                'health_metrics': health_metrics,
                'recommendations': self._generate_health_recommendations(health_metrics)
            }
            
        except Exception as e:
            logger.error(f"System health validation failed: {str(e)}")
            return {'error': str(e), 'health_status': 'unhealthy'}
    
    # Private helper methods
    
    def _get_conversation_within_budget(self, model: str, budget: int, 
                                      minimum_exchanges: int = 0) -> List[Dict]:
        """Get conversation history that fits within token budget"""
        full_history = self.memory_manager.get_conversation_history(model)
        
        if not full_history:
            return []
        
        # Ensure minimum exchanges if possible
        if len(full_history) <= minimum_exchanges:
            return full_history
        
        # Trim to budget, but keep at least minimum_exchanges
        trimmed = self._trim_conversation_to_budget(full_history, budget)
        
        if len(trimmed) < minimum_exchanges and len(full_history) >= minimum_exchanges:
            # Take the most recent minimum_exchanges even if over budget
            return full_history[-minimum_exchanges:]
        
        return trimmed
    
    def _trim_conversation_to_budget(self, conversation: List[Dict], budget: int) -> List[Dict]:
        """Trim conversation to fit within token budget, keeping most recent exchanges"""
        if not conversation or budget <= 0:
            return []
        
        # Work backwards from most recent
        trimmed = []
        current_tokens = 0
        
        for exchange in reversed(conversation):
            exchange_tokens = self._estimate_exchange_tokens(exchange)
            
            if current_tokens + exchange_tokens <= budget:
                trimmed.insert(0, exchange)  # Insert at beginning to maintain order
                current_tokens += exchange_tokens
            else:
                break
        
        return trimmed
    
    def _estimate_exchange_tokens(self, exchange: Dict) -> int:
        """Estimate tokens for a single exchange"""
        total_tokens = 0
        
        if 'user' in exchange:
            user_data = exchange['user']
            if 'tokens' in user_data:
                total_tokens += user_data['tokens']
            elif 'content' in user_data:
                total_tokens += self.token_counter.estimate_tokens(user_data['content'])
        
        if 'assistant' in exchange:
            assistant_data = exchange['assistant']
            if 'tokens' in assistant_data:
                total_tokens += assistant_data['tokens']
            elif 'content' in assistant_data:
                total_tokens += self.token_counter.estimate_tokens(assistant_data['content'])
        
        return total_tokens
    
    def _build_context_messages(self, conversation_history: List[Dict], model: str) -> List[Dict]:
        """Build context messages in chat completion format"""
        messages = []
        
        for exchange in conversation_history:
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
    
    def _validate_exchange(self, user_content: str, assistant_content: str,
                          user_tokens: int, assistant_tokens: int):
        """Validate a conversation exchange"""
        from .safety_validator import ValidationResult
        
        result = ValidationResult(component="exchange_validation")
        
        # Content validation
        if not user_content or not isinstance(user_content, str):
            result.add_error("Invalid user content")
        
        if not assistant_content or not isinstance(assistant_content, str):
            result.add_error("Invalid assistant content")
        
        # Token validation
        if user_tokens <= 0:
            result.add_warning("User token count is zero or negative")
        
        if assistant_tokens <= 0:
            result.add_warning("Assistant token count is zero or negative")
        
        # Reasonable token estimates
        estimated_user = self.token_counter.estimate_tokens(user_content)
        estimated_assistant = self.token_counter.estimate_tokens(assistant_content)
        
        if abs(user_tokens - estimated_user) > estimated_user * 0.5:
            result.add_warning(f"User token count seems off: {user_tokens} vs estimated {estimated_user}")
        
        if abs(assistant_tokens - estimated_assistant) > estimated_assistant * 0.5:
            result.add_warning(f"Assistant token count seems off: {assistant_tokens} vs estimated {estimated_assistant}")
        
        return result
    
    def _extract_model_from_exchange(self, exchange: Dict, default_model: str) -> str:
        """Extract model name from exchange metadata or return default"""
        if isinstance(exchange, dict):
            metadata = exchange.get('metadata', {})
            if isinstance(metadata, dict):
                model = metadata.get('model')
                if model and isinstance(model, str):
                    return model
        
        return default_model
    
    def _generate_health_recommendations(self, health_metrics: Dict) -> List[str]:
        """Generate system health recommendations"""
        recommendations = []
        
        if health_metrics['models_with_memory'] == 0:
            recommendations.append("No models have conversation history - consider adding some test exchanges")
        
        if health_metrics['session_exchanges'] == 0:
            recommendations.append("No exchanges added this session - system may not be receiving conversations")
        
        if not health_metrics['integration_valid']:
            recommendations.append("Component integration validation failed - check logs for details")
        
        if not health_metrics['last_budgets_valid']:
            recommendations.append("No budget calculations performed - system may not be processing contexts")
        
        if not recommendations:
            recommendations.append("System health looks good - all components functioning normally")
        
        return recommendations
