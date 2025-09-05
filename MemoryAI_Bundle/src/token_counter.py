"""
Simple Token Counter with Safety Margins

Provides practical token estimation for budget management with enhanced
accuracy for edge cases like emojis, special characters, and code.
"""

import re
from typing import Optional


class SimpleTokenCounter:
    """Conservative token estimation with safety margins for edge cases"""
    
    def __init__(self, base_ratio: float = 3.0, safety_multiplier: float = 1.2):
        """
        Initialize token counter with configurable parameters
        
        Args:
            base_ratio: Base characters per token ratio (default: 3.0)
            safety_multiplier: Safety margin multiplier (default: 1.2 = 20% margin)
        """
        self.base_ratio = base_ratio
        self.safety_multiplier = safety_multiplier
        
        # Patterns for problematic tokenization cases
        self.emoji_pattern = re.compile(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF\U00002700-\U000027BF\U0001F900-\U0001F9FF\U0001F018-\U0001F270]')
        self.symbol_pattern = re.compile(r'[(){}[\]<>=!@#$%^&*+\-_|\\:;"\',./`~]')
        self.whitespace_pattern = re.compile(r'\s+')
    
    def estimate_tokens(self, text: str) -> int:
        """
        Conservative estimation with safety margins for known problematic patterns
        
        Args:
            text: Input text to estimate tokens for
            
        Returns:
            Estimated token count with safety margins applied
        """
        if not text or not isinstance(text, str):
            return 0
            
        # Base estimation
        base_estimate = max(1, len(text) / self.base_ratio)
        
        # Count problematic patterns that typically use more tokens
        emoji_count = len(self.emoji_pattern.findall(text))
        symbol_count = len(self.symbol_pattern.findall(text))
        
        # Count high-unicode characters (non-ASCII)
        non_ascii_count = len([c for c in text if ord(c) > 127])
        
        # Count very long words (may tokenize into multiple tokens)
        words = text.split()
        long_word_chars = sum(len(word) - 20 for word in words if len(word) > 20)
        long_word_penalty = max(0, long_word_chars) / 10  # Extra tokens for very long words
        
        # Apply adjustments for known problematic patterns
        emoji_adjustment = emoji_count * 2  # Emojis often use 2-4 tokens each
        symbol_adjustment = symbol_count * 0.3  # Some symbols are separate tokens
        unicode_adjustment = (non_ascii_count - emoji_count) * 0.5  # Non-emoji unicode
        
        # Calculate adjusted estimate
        adjusted_estimate = (
            base_estimate + 
            emoji_adjustment + 
            symbol_adjustment + 
            unicode_adjustment + 
            long_word_penalty
        )
        
        # Apply safety multiplier
        final_estimate = int(adjusted_estimate * self.safety_multiplier)
        
        return max(1, final_estimate)
    
    def estimate_tokens_batch(self, texts: list[str]) -> list[int]:
        """
        Estimate tokens for multiple texts efficiently
        
        Args:
            texts: List of text strings
            
        Returns:
            List of estimated token counts
        """
        return [self.estimate_tokens(text) for text in texts]
    
    def estimate_conversation_tokens(self, conversation: list[dict]) -> int:
        """
        Estimate total tokens for a conversation history
        
        Args:
            conversation: List of message dictionaries with 'content' keys
            
        Returns:
            Total estimated token count for conversation
        """
        total_tokens = 0
        
        for message in conversation:
            if isinstance(message, dict):
                # Handle different message formats
                if 'content' in message:
                    content = message['content']
                    if isinstance(content, str):
                        total_tokens += self.estimate_tokens(content)
                elif 'user' in message and 'assistant' in message:
                    # Handle exchange format
                    if isinstance(message['user'], dict) and 'content' in message['user']:
                        total_tokens += self.estimate_tokens(message['user']['content'])
                    if isinstance(message['assistant'], dict) and 'content' in message['assistant']:
                        total_tokens += self.estimate_tokens(message['assistant']['content'])
        
        return total_tokens
    
    def validate_estimation_accuracy(self, text: str, actual_tokens: Optional[int] = None) -> dict:
        """
        Validate estimation accuracy if actual token count is available
        
        Args:
            text: Input text
            actual_tokens: Actual token count from real tokenizer (optional)
            
        Returns:
            Dictionary with estimation metrics
        """
        estimated = self.estimate_tokens(text)
        
        result = {
            'text_length': len(text),
            'estimated_tokens': estimated,
            'characters_per_token': len(text) / max(1, estimated)
        }
        
        if actual_tokens is not None:
            result['actual_tokens'] = actual_tokens
            result['estimation_ratio'] = estimated / max(1, actual_tokens)
            result['estimation_error'] = abs(estimated - actual_tokens)
            result['estimation_error_percent'] = (abs(estimated - actual_tokens) / max(1, actual_tokens)) * 100
        
        return result


class TokenBudgetManager:
    """Manages token budgets using percentage-based allocation"""
    
    def __init__(self, token_counter: SimpleTokenCounter):
        self.token_counter = token_counter
    
    def calculate_percentage_budget(self, context_window: int, percentages: dict) -> dict:
        """
        Calculate absolute token budgets from percentages
        
        Args:
            context_window: Total context window size
            percentages: Dictionary of component -> percentage mappings
            
        Returns:
            Dictionary of component -> token count mappings
        """
        budgets = {}
        
        for component, percentage in percentages.items():
            budgets[component] = int(context_window * (percentage / 100))
        
        return budgets
    
    def validate_budget_allocation(self, budgets: dict, context_window: int) -> dict:
        """
        Validate that budget allocation doesn't exceed context window
        
        Args:
            budgets: Dictionary of component -> token count
            context_window: Total context window size
            
        Returns:
            Validation results with warnings if any
        """
        total_allocated = sum(budgets.values())
        utilization = (total_allocated / context_window) * 100
        
        result = {
            'total_allocated': total_allocated,
            'context_window': context_window,
            'utilization_percent': utilization,
            'remaining_tokens': context_window - total_allocated,
            'is_valid': total_allocated <= context_window,
            'warnings': []
        }
        
        if utilization > 95:
            result['warnings'].append(f"High utilization: {utilization:.1f}%")
        
        if total_allocated > context_window:
            result['warnings'].append(f"Budget exceeds context window by {total_allocated - context_window} tokens")
        
        return result
