"""
Safety Validator

Provides comprehensive validation and safety checks for memory operations,
budget allocations, and system integrity with detailed error reporting.
"""

import json
import time
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from datetime import datetime


class ValidationResult:
    """Structured validation result with severity levels"""
    
    def __init__(self, is_valid: bool = True, component: str = "unknown"):
        self.is_valid = is_valid
        self.component = component
        self.errors = []
        self.warnings = []
        self.info = []
        self.timestamp = datetime.now().isoformat()
    
    def add_error(self, message: str, details: Optional[Dict] = None):
        """Add an error (validation failure)"""
        self.is_valid = False
        self.errors.append({
            'message': message,
            'details': details or {},
            'timestamp': datetime.now().isoformat()
        })
    
    def add_warning(self, message: str, details: Optional[Dict] = None):
        """Add a warning (potential issue)"""
        self.warnings.append({
            'message': message,
            'details': details or {},
            'timestamp': datetime.now().isoformat()
        })
    
    def add_info(self, message: str, details: Optional[Dict] = None):
        """Add informational message"""
        self.info.append({
            'message': message,
            'details': details or {},
            'timestamp': datetime.now().isoformat()
        })
    
    def has_issues(self) -> bool:
        """Check if there are any errors or warnings"""
        return len(self.errors) > 0 or len(self.warnings) > 0
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of validation results"""
        return {
            'component': self.component,
            'is_valid': self.is_valid,
            'timestamp': self.timestamp,
            'error_count': len(self.errors),
            'warning_count': len(self.warnings),
            'info_count': len(self.info),
            'has_issues': self.has_issues()
        }
    
    def get_all_messages(self) -> List[str]:
        """Get all messages as simple list"""
        messages = []
        
        for error in self.errors:
            messages.append(f"ERROR: {error['message']}")
        
        for warning in self.warnings:
            messages.append(f"WARNING: {warning['message']}")
        
        for info in self.info:
            messages.append(f"INFO: {info['message']}")
        
        return messages


class SafetyValidator:
    """Comprehensive validation and safety checks for WorkspaceAI components"""
    
    def __init__(self, strict_mode: bool = False):
        """
        Initialize safety validator
        
        Args:
            strict_mode: If True, warnings are treated as errors
        """
        self.strict_mode = strict_mode
        self.validation_history = []
        
        # Safety thresholds
        self.thresholds = {
            'max_context_utilization': 0.95,  # 95%
            'min_response_allocation': 0.10,  # 10%
            'min_memory_allocation': 0.30,    # 30%
            'max_token_estimation_error': 2.0, # 2x actual
            'min_safety_margin': 0.02,        # 2%
            'max_memory_file_size': 10 * 1024 * 1024,  # 10MB
            'max_conversation_length': 10000,  # exchanges
        }
    
    def validate_token_budgets(self, budgets: Dict[str, int], context_window: int, 
                             complexity_score: float = 0.0) -> ValidationResult:
        """
        Comprehensive budget validation with safety checks
        
        Args:
            budgets: Dictionary of component -> token count
            context_window: Total context window size
            complexity_score: Query complexity score (0.0-1.0)
            
        Returns:
            ValidationResult with detailed analysis
        """
        result = ValidationResult(component="token_budgets")
        
        # Basic validation
        if not budgets or not isinstance(budgets, dict):
            result.add_error("Invalid budgets: not a dictionary", {'budgets': budgets})
            return result
        
        if context_window <= 0:
            result.add_error("Invalid context window", {'context_window': context_window})
            return result
        
        # Calculate totals
        total_allocated = sum(budgets.values())
        utilization = total_allocated / context_window
        
        # Core validation checks
        if total_allocated > context_window:
            excess = total_allocated - context_window
            result.add_error(
                f"Budget exceeds context window by {excess} tokens",
                {
                    'total_allocated': total_allocated,
                    'context_window': context_window,
                    'excess_tokens': excess,
                    'excess_percentage': (excess / context_window) * 100
                }
            )
        
        # Utilization warnings
        if utilization > self.thresholds['max_context_utilization']:
            result.add_warning(
                f"High context utilization: {utilization:.1%}",
                {'utilization': utilization, 'threshold': self.thresholds['max_context_utilization']}
            )
        
        # Component-specific validations
        response_tokens = budgets.get('response_generation', 0)
        memory_tokens = budgets.get('conversation_memory', 0)
        safety_tokens = budgets.get('safety_margin', 0)
        
        # Response allocation checks
        response_ratio = response_tokens / context_window
        if response_ratio < self.thresholds['min_response_allocation']:
            result.add_warning(
                f"Low response allocation: {response_ratio:.1%}",
                {
                    'response_tokens': response_tokens,
                    'response_ratio': response_ratio,
                    'min_threshold': self.thresholds['min_response_allocation']
                }
            )
        
        # Memory allocation checks
        memory_ratio = memory_tokens / context_window
        if memory_ratio < self.thresholds['min_memory_allocation']:
            result.add_warning(
                f"Low memory allocation: {memory_ratio:.1%}",
                {
                    'memory_tokens': memory_tokens,
                    'memory_ratio': memory_ratio,
                    'min_threshold': self.thresholds['min_memory_allocation']
                }
            )
        
        # Safety margin checks
        safety_ratio = safety_tokens / context_window
        if safety_ratio < self.thresholds['min_safety_margin']:
            result.add_warning(
                f"Insufficient safety margin: {safety_ratio:.1%}",
                {
                    'safety_tokens': safety_tokens,
                    'safety_ratio': safety_ratio,
                    'min_threshold': self.thresholds['min_safety_margin']
                }
            )
        
        # Complexity-aware validation
        if complexity_score > 0.7 and response_ratio < 0.20:
            result.add_warning(
                "High complexity query with low response allocation",
                {
                    'complexity_score': complexity_score,
                    'response_ratio': response_ratio,
                    'recommendation': 'Consider increasing response allocation for complex queries'
                }
            )
        
        # Log successful validation
        if result.is_valid:
            result.add_info(
                f"Budget validation passed: {utilization:.1%} utilization",
                {
                    'total_allocated': total_allocated,
                    'utilization': utilization,
                    'component_breakdown': {k: f"{v} tokens ({v/context_window:.1%})" 
                                          for k, v in budgets.items()}
                }
            )
        
        return result
    
    def validate_memory_structure(self, memory_data: Dict, model: str, 
                                file_path: Optional[Path] = None) -> ValidationResult:
        """
        Deep validation of memory structure and content
        
        Args:
            memory_data: Memory dictionary to validate
            model: Model name
            file_path: Optional path to memory file
            
        Returns:
            ValidationResult with detailed analysis
        """
        result = ValidationResult(component="memory_structure")
        
        # Basic structure validation
        if not isinstance(memory_data, dict):
            result.add_error("Memory data is not a dictionary", {'type': type(memory_data)})
            return result
        
        # Required top-level keys
        required_keys = ["metadata", "current_conversation", "summarized_conversations"]
        missing_keys = [key for key in required_keys if key not in memory_data]
        
        if missing_keys:
            result.add_error(
                f"Missing required keys: {missing_keys}",
                {'missing_keys': missing_keys, 'available_keys': list(memory_data.keys())}
            )
        
        # Validate metadata
        if "metadata" in memory_data:
            metadata_result = self._validate_metadata(memory_data["metadata"], model)
            result.errors.extend(metadata_result.errors)
            result.warnings.extend(metadata_result.warnings)
            if not metadata_result.is_valid:
                result.is_valid = False
        
        # Validate conversations
        if "current_conversation" in memory_data:
            conv_result = self._validate_conversation(memory_data["current_conversation"])
            result.errors.extend(conv_result.errors)
            result.warnings.extend(conv_result.warnings)
            if not conv_result.is_valid:
                result.is_valid = False
        
        # File size validation
        if file_path and file_path.exists():
            file_size = file_path.stat().st_size
            if file_size > self.thresholds['max_memory_file_size']:
                result.add_warning(
                    f"Large memory file: {file_size / (1024*1024):.1f}MB",
                    {'file_size': file_size, 'max_size': self.thresholds['max_memory_file_size']}
                )
        
        # Conversation length validation
        if "current_conversation" in memory_data:
            conv_length = len(memory_data["current_conversation"])
            if conv_length > self.thresholds['max_conversation_length']:
                result.add_warning(
                    f"Very long conversation: {conv_length} exchanges",
                    {
                        'conversation_length': conv_length,
                        'max_length': self.thresholds['max_conversation_length'],
                        'recommendation': 'Consider summarizing older exchanges'
                    }
                )
        
        if result.is_valid:
            result.add_info(
                "Memory structure validation passed",
                {
                    'model': model,
                    'conversation_length': len(memory_data.get("current_conversation", [])),
                    'has_summaries': len(memory_data.get("summarized_conversations", [])) > 0
                }
            )
        
        return result
    
    def _validate_metadata(self, metadata: Dict, model: str) -> ValidationResult:
        """Validate memory metadata structure"""
        result = ValidationResult(component="metadata")
        
        if not isinstance(metadata, dict):
            result.add_error("Metadata is not a dictionary", {'type': type(metadata)})
            return result
        
        # Required metadata fields
        required_fields = ["model", "version", "created_at", "last_modified"]
        missing_fields = [field for field in required_fields if field not in metadata]
        
        if missing_fields:
            result.add_warning(
                f"Missing metadata fields: {missing_fields}",
                {'missing_fields': missing_fields}
            )
        
        # Model consistency check
        if metadata.get("model") != model and metadata.get("model") not in [None, "", "unknown"]:
            result.add_warning(
                f"Model mismatch: metadata={metadata.get('model')}, expected={model}",
                {'metadata_model': metadata.get("model"), 'expected_model': model}
            )
        
        # Version check
        if metadata.get("version") != "3.0":
            result.add_info(
                f"Non-standard version: {metadata.get('version')}",
                {'version': metadata.get("version")}
            )
        
        return result
    
    def _validate_conversation(self, conversation: List) -> ValidationResult:
        """Validate conversation structure and content"""
        result = ValidationResult(component="conversation")
        
        if not isinstance(conversation, list):
            result.add_error("Conversation is not a list", {'type': type(conversation)})
            return result
        
        # Validate individual exchanges
        for i, exchange in enumerate(conversation):
            if not isinstance(exchange, dict):
                result.add_error(f"Exchange {i} is not a dictionary", {'index': i, 'type': type(exchange)})
                continue
            
            # Check for required exchange fields
            if "user" not in exchange or "assistant" not in exchange:
                result.add_error(
                    f"Exchange {i} missing user/assistant fields",
                    {'index': i, 'available_keys': list(exchange.keys())}
                )
                continue
            
            # Validate user/assistant structure
            for participant in ["user", "assistant"]:
                participant_data = exchange[participant]
                if not isinstance(participant_data, dict):
                    result.add_warning(
                        f"Exchange {i} {participant} is not a dictionary",
                        {'index': i, 'participant': participant, 'type': type(participant_data)}
                    )
                    continue
                
                if "content" not in participant_data:
                    result.add_warning(
                        f"Exchange {i} {participant} missing content",
                        {'index': i, 'participant': participant}
                    )
        
        return result
    
    def validate_token_estimation_accuracy(self, estimated: int, actual: Optional[int], 
                                         text: str) -> ValidationResult:
        """
        Validate token estimation accuracy against actual counts
        
        Args:
            estimated: Estimated token count
            actual: Actual token count (if available)
            text: Original text
            
        Returns:
            ValidationResult with accuracy analysis
        """
        result = ValidationResult(component="token_estimation")
        
        # Basic validation
        if estimated <= 0:
            result.add_error("Invalid estimated token count", {'estimated': estimated})
            return result
        
        # Length sanity check
        text_length = len(text) if text else 0
        if estimated > text_length:
            result.add_warning(
                "Estimated tokens exceed text length",
                {'estimated': estimated, 'text_length': text_length}
            )
        
        # Accuracy validation (if actual count available)
        if actual is not None:
            if actual <= 0:
                result.add_error("Invalid actual token count", {'actual': actual})
                return result
            
            ratio = estimated / actual
            error_percent = abs(estimated - actual) / actual * 100
            
            if ratio > self.thresholds['max_token_estimation_error']:
                result.add_error(
                    f"Token estimation too high: {ratio:.2f}x actual",
                    {
                        'estimated': estimated,
                        'actual': actual,
                        'ratio': ratio,
                        'error_percent': error_percent
                    }
                )
            elif ratio < 0.5:
                result.add_warning(
                    f"Token estimation very low: {ratio:.2f}x actual",
                    {
                        'estimated': estimated,
                        'actual': actual,
                        'ratio': ratio,
                        'error_percent': error_percent
                    }
                )
            else:
                result.add_info(
                    f"Token estimation reasonable: {ratio:.2f}x actual ({error_percent:.1f}% error)",
                    {
                        'estimated': estimated,
                        'actual': actual,
                        'ratio': ratio,
                        'error_percent': error_percent
                    }
                )
        
        return result
    
    def validate_migration_integrity(self, old_data: Dict, new_data_by_model: Dict[str, Dict]) -> ValidationResult:
        """
        Validate that migration preserved all data
        
        Args:
            old_data: Original memory data
            new_data_by_model: Dictionary of model -> new memory data
            
        Returns:
            ValidationResult with migration integrity analysis
        """
        result = ValidationResult(component="migration_integrity")
        
        # Count original exchanges from all sources
        original_count = 0
        
        # Count from current conversation
        current_conv = old_data.get("current_conversation", [])
        original_count += len(current_conv)
        
        # Count from recent conversations  
        recent_convs = old_data.get("recent_conversations", [])
        for conversation in recent_convs:
            original_count += len(conversation)
        
        # Count migrated exchanges
        migrated_count = 0
        models_created = []
        
        for model, memory_data in new_data_by_model.items():
            model_exchanges = memory_data.get("current_conversation", [])
            migrated_count += len(model_exchanges)
            models_created.append(model)
        
        # Integrity checks
        if migrated_count != original_count:
            result.add_error(
                f"Exchange count mismatch: {original_count} → {migrated_count}",
                {
                    'original_count': original_count,
                    'migrated_count': migrated_count,
                    'difference': migrated_count - original_count
                }
            )
        
        if not models_created:
            result.add_error("No models created during migration")
        
        # Success info
        if result.is_valid:
            result.add_info(
                f"Migration integrity validated: {original_count} exchanges → {len(models_created)} models",
                {
                    'original_exchanges': original_count,
                    'models_created': models_created,
                    'migrated_exchanges': migrated_count
                }
            )
        
        return result
    
    def validate_system_integration(self, components: Dict[str, Any]) -> ValidationResult:
        """
        Validate integration between system components
        
        Args:
            components: Dictionary of component_name -> component_instance
            
        Returns:
            ValidationResult with integration analysis
        """
        result = ValidationResult(component="system_integration")
        
        required_components = [
            'token_counter', 'memory_manager', 'budget_manager'
        ]
        
        # Check required components
        missing_components = [comp for comp in required_components if comp not in components]
        if missing_components:
            result.add_error(
                f"Missing required components: {missing_components}",
                {'missing': missing_components, 'available': list(components.keys())}
            )
        
        # Component interface validation
        for name, component in components.items():
            if hasattr(component, 'validate_self'):
                try:
                    component_result = component.validate_self()
                    if not component_result.is_valid:
                        result.add_warning(
                            f"Component {name} self-validation failed",
                            {'component': name, 'errors': component_result.errors}
                        )
                except Exception as e:
                    result.add_warning(
                        f"Component {name} self-validation error: {e}",
                        {'component': name, 'error': str(e)}
                    )
        
        if result.is_valid:
            result.add_info(
                "System integration validation passed",
                {'components': list(components.keys())}
            )
        
        return result
    
    def log_validation_result(self, result: ValidationResult, 
                            log_level: str = "INFO") -> None:
        """
        Log validation result with appropriate severity
        
        Args:
            result: ValidationResult to log
            log_level: Base log level
        """
        # Store in history
        self.validation_history.append({
            'timestamp': result.timestamp,
            'component': result.component,
            'summary': result.get_summary()
        })
        
        # Keep only recent history (last 100 validations)
        if len(self.validation_history) > 100:
            self.validation_history = self.validation_history[-100:]
        
        # Log messages (in practice, would use proper logging)
        for message in result.get_all_messages():
            print(f"[{log_level}] {result.component}: {message}")
    
    def get_validation_summary(self) -> Dict[str, Any]:
        """Get summary of recent validation activity"""
        if not self.validation_history:
            return {'total_validations': 0, 'components': [], 'recent_issues': []}
        
        recent_validations = self.validation_history[-10:]  # Last 10
        
        components = list(set(v['component'] for v in recent_validations))
        issues = [v for v in recent_validations if v['summary']['has_issues']]
        
        return {
            'total_validations': len(self.validation_history),
            'recent_validations': len(recent_validations),
            'components': components,
            'recent_issues': len(issues),
            'validation_history': recent_validations
        }
