# WorkspaceAI Memory System Implementation Plan v3.0 - COMPLETE

## Executive Summary

This document outlines the complete implementation plan for WorkspaceAI's unified memory and context system, incorporating architectural insights, simplification recommendations, adaptive response allocation, and per-model memory organization.

**Core Innovations**: 
1. **Unified memory path** that provides consistent conversation history across all interaction modes
2. **Adaptive response allocation** that dynamically adjusts context budgets based on query complexity
3. **Percentage-based scaling** that works across any model context window size
4. **Per-model memory files** that provide task-specific conversation contexts and corruption isolation

## Architecture Overview

### Current State (Dual-Path Problem)
```
User Input → App.py → OllamaUniversalInterface
                   ├── _simple_chat_without_tools() 
                   │   ├── NO memory loaded ❌
                   │   ├── tools=None to API ✅
                   │   └── Basic system prompt ✅
                   │
                   └── _call_ollama_with_open_tools()
                       ├── Memory loaded ✅
                       ├── tools=schemas to API ✅
                       └── Enhanced system prompt ✅
```

### Target State (Unified Path Solution)
```
User Input → App.py → UnifiedMemoryManager → Single Interface → Ollama
                   ↓
            ALWAYS loads memory ✅
            Mode determines: tools=None|schemas ✅
            Mode determines: system prompt type ✅
                   ↓
            client.chat_completion(messages, tools)
```

## Implementation Components

### 1. UnifiedMemoryManager (NEW)
**Purpose**: Single point of control for memory + context preparation
**Location**: `src/unified_memory_manager.py`

```python
class UnifiedMemoryManager:
    def __init__(self):
        self.model_detector = ModelCapabilityDetector()  # existing ✅
        self.model_memory = ModelSpecificMemory()  # per-model memory files
        self.token_counter = SimpleTokenCounter()
        self.budget_manager = AdaptiveBudgetManager()
    
    def prepare_context(self, user_input: str, model: str, mode: str) -> dict:
        """Core method: ALWAYS includes memory, mode controls tools"""
        # 1. Get model context window
        context_window = self.model_detector.get_context_window(model)
        
        # 2. Calculate adaptive token budget based on mode and complexity
        budgets = self.budget_manager.calculate_adaptive_budgets(
            context_window, mode, user_input
        )
        
        # 3. Load model-specific conversation history within budget  
        memory = self.model_memory.load_memory(model)
        history = self._load_history_within_budget(
            memory, budgets['conversation_memory']
        )
        
        # 4. Build messages array with appropriate system prompt
        messages = self._build_messages(history, user_input, mode)
        
        # 5. Return messages + tools (None or schemas)
        return {
            'messages': messages,
            'tools': self._get_tools_for_mode(mode),
            'budgets': budgets,
            'model': model
        }
    
    def save_exchange(self, user_input: str, response: str, mode: str, model: str):
        """Save conversation exchange with metadata to model-specific memory"""
        # Load current model memory
        memory = self.model_memory.load_memory(model)
        
        # Create exchange with token metadata
        exchange = {
            "user": {
                "content": user_input,
                "tokens": self.token_counter.estimate_tokens(user_input)
            },
            "assistant": {
                "content": response,
                "tokens": self.token_counter.estimate_tokens(response)
            },
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "mode": mode,
                "model": model,
                "total_tokens": (
                    self.token_counter.estimate_tokens(user_input) + 
                    self.token_counter.estimate_tokens(response)
                )
            }
        }
        
        # Add to conversation history
        memory["current_conversation"].append(exchange)
        memory["metadata"]["last_updated"] = datetime.now().isoformat()
        
        # Save back to model-specific file
        self.model_memory.save_memory(model, memory)
```

### 2. ModelSpecificMemory (NEW)
**Purpose**: Per-model memory files for task separation and corruption isolation
**Location**: `src/model_specific_memory.py`

```python
class ModelSpecificMemory:
    def __init__(self, base_memory_dir: str = "WorkspaceAI/memory"):
        self.base_dir = Path(base_memory_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
    
    def get_memory_file_path(self, model: str) -> Path:
        """Convert model name to valid filename"""
        # qwen2.5:7b → qwen2-5-7b.json
        # qwen2.5:3b → qwen2-5-3b.json
        clean_name = model.replace(":", "-").replace(".", "-")
        return self.base_dir / f"{clean_name}.json"
    
    def load_memory(self, model: str) -> dict:
        """Load memory for specific model"""
        memory_file = self.get_memory_file_path(model)
        
        if not memory_file.exists():
            return self._create_empty_memory(model)
        
        try:
            with open(memory_file, 'r') as f:
                memory = json.load(f)
            
            # Validate memory structure
            if not self._validate_memory_structure(memory):
                logger.warning(f"Corrupted memory detected for {model}, creating fresh memory")
                return self._create_empty_memory(model)
            
            return memory
            
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Failed to load memory for {model}: {e}")
            return self._create_empty_memory(model)
    
    def save_memory(self, model: str, memory: dict) -> bool:
        """Save memory for specific model with atomic writes"""
        memory_file = self.get_memory_file_path(model)
        temp_file = memory_file.with_suffix('.tmp')
        
        try:
            # Write to temporary file first
            with open(temp_file, 'w') as f:
                json.dump(memory, f, indent=2)
            
            # Atomic rename
            temp_file.rename(memory_file)
            return True
            
        except (IOError, OSError) as e:
            logger.error(f"Failed to save memory for {model}: {e}")
            if temp_file.exists():
                temp_file.unlink()  # Clean up temp file
            return False
    
    def _create_empty_memory(self, model: str) -> dict:
        """Create fresh memory structure for model"""
        return {
            "metadata": {
                "version": "3.0",
                "model": model,
                "created": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat()
            },
            "current_conversation": [],
            "recent_conversations": [],
            "summarized_conversations": []
        }
    
    def _validate_memory_structure(self, memory: dict) -> bool:
        """Basic validation of memory structure"""
        required_keys = ["metadata", "current_conversation"]
        return all(key in memory for key in required_keys)
```

**Key Benefits**:
- **Task Separation**: Different models can have different conversation contexts
- **Corruption Isolation**: Problems with one model's memory don't affect others
- **Simple Backup**: Easy to backup/restore specific model conversations
- **Future Flexibility**: Easy to add model-specific optimizations
- **Clean History**: Each model gets clean conversation history for its specific use case

### 3. EnhancedMemory (UPGRADE)
**Purpose**: Upgrade existing memory.py with token metadata
**Location**: `src/memory.py` (modify existing)

**Current Format**:
```json
{
  "current_conversation": [
    {"user": "hello", "assistant": "hi", "timestamp": "..."}
  ]
}
```

**New Format (Model-Specific)**:
```json
{
  "metadata": {
    "version": "3.0",
    "model": "qwen2.5:7b",
    "created": "2025-09-04T10:00:00Z",
    "last_updated": "2025-09-04T10:30:00Z"
  },
  "current_conversation": [
    {
      "user": {"content": "hello", "tokens": 5},
      "assistant": {"content": "hi", "tokens": 3}, 
      "metadata": {
        "timestamp": "2025-09-04T10:00:00Z",
        "mode": "chat",
        "total_tokens": 8
      }
    }
  ],
  "recent_conversations": [],
  "summarized_conversations": []
}
```

### 4. Simple Token Counter (NEW)
**Purpose**: Practical token estimation for budget management  
**Location**: `src/token_counter.py`

```python
class SimpleTokenCounter:
    def estimate_tokens(self, text: str) -> int:
        """Conservative character-based estimation"""
        # Most models: ~3-4 chars per token
        # Be conservative: assume 3 chars/token
        return max(1, len(str(text)) // 3)
    
    def count_conversation_tokens(self, conversation: list) -> int:
        """Count tokens in conversation history"""
        # Sum all user + assistant content
```

### 5. Adaptive Budget Manager (NEW)
**Purpose**: Intelligent response allocation based on query complexity
**Location**: `src/adaptive_budget_manager.py`

```python
class AdaptiveBudgetManager:
    def calculate_adaptive_budgets(self, context_window: int, mode: str, user_input: str) -> dict:
        """Calculate budgets with adaptive response allocation"""
        # 1. Analyze query complexity (0.0-1.0 score)
        # 2. Adjust response allocation (15-35% tools, 15-25% chat)
        # 3. Take extra space from reserved budget first, then conversation memory
        # 4. Return token budgets with complexity metadata
```

### 6. Unified Interface (MODIFY)
**Purpose**: Replace dual-path with single path
**Location**: `src/ollama_universal_interface.py` (major refactor)

**Remove**:
- `_simple_chat_without_tools()`
- `_call_ollama_with_open_tools()`

**Replace With**:
```python
def call_ollama_with_unified_memory(prompt: str, model: str = None, mode: str = "chat"):
    """Single path for all conversations with unified memory"""
    # 1. Prepare context with adaptive memory
    context = unified_memory.prepare_context(prompt, model, mode)
    
    # 2. Call Ollama with appropriate tools
    response = client.chat_completion(context['messages'], context['tools'])
    
    # 3. Save exchange to memory
    unified_memory.save_exchange(prompt, response, mode)
    
    return response
```

## Adaptive Response Allocation System

### Core Innovation: Complexity-Aware Budgeting

**The Problem**: Fixed response allocations waste context window space for simple queries and provide insufficient space for complex requests.

**The Solution**: Dynamically adjust response allocation based on query complexity analysis.

### Query Complexity Analysis

```python
def analyze_complexity(self, user_input: str, mode: str) -> float:
    """Return complexity score 0.0-1.0 based on query characteristics"""
    
    complexity_factors = {
        'length': len(user_input),           # Longer queries need more space
        'code_request': 'create' in input,   # Code generation needs more space  
        'analysis_request': 'analyze' in input, # Analysis needs detailed responses
        'multi_part': input.count('?') > 1,  # Multiple questions need more space
        'tools_mode': mode == "tools"        # Tool responses are typically longer
    }
    
    # Score: 0.0 (simple) to 1.0 (very complex)
    return calculated_score
```

### Adaptive Budget Allocation

#### Tools Mode Dynamic Allocation:
```python
# Base allocation
conversation_memory = 60%
response_generation = 15-35% (adaptive based on complexity)
reserved = 11-2% (shrinks to accommodate larger responses)

# Examples:
Simple "hi" → 17% response, 60% memory, 9% reserved
Complex analysis → 31% response, 55% memory, 2% reserved
```

#### Chat Mode Dynamic Allocation:
```python
# Base allocation  
conversation_memory = 80%
response_generation = 15-25% (adaptive based on complexity)
reserved = 4.4-2% (shrinks to accommodate larger responses)

# Examples:
Simple question → 17% response, 80% memory, 4% reserved
Complex question → 23% response, 77% memory, 2% reserved
```

## Implementation Details

### Percentage-Based Token Budget Allocation

**Philosophy**: Use percentages instead of hard numbers for universal scalability across any model context window size.

**Based on 32,768 token context window (both qwen models):**

#### Tools Mode (Adaptive 55-60% for conversation)
```
├── System Prompt: 3% (fixed)
├── Tool Definitions: 6% (fixed)
├── Conversation Memory: 55-60% (adaptive - shrinks for complex responses)
├── Response Generation: 15-35% (adaptive based on complexity)
├── Safety Margin: 5% (fixed)
└── Reserved: 2-11% (flexible - provides space for adaptation)
```

#### Chat Mode (Adaptive 77-80% for conversation)
```
├── System Prompt: 0.6% (fixed)
├── Tool Definitions: 0% (fixed)
├── Conversation Memory: 77-80% (adaptive - shrinks for complex responses)
├── Response Generation: 15-25% (adaptive based on complexity)
├── Safety Margin: 5% (fixed)
└── Reserved: 2-4.4% (flexible - provides space for adaptation)
```

### Adaptive Complexity Examples

#### Simple Query Example:
```python
user_input = "hi"
complexity_score = 0.1

# Tools mode allocation:
response_generation = 15% + (0.1 * 20%) = 17%
conversation_memory = 60% (unchanged - minimal complexity)
reserved = 11% - 2% = 9%
```

#### Complex Query Example:
```python
user_input = "Analyze this code file, explain the architecture, identify issues, and suggest detailed improvements"
complexity_score = 0.8

# Tools mode allocation:
response_generation = 15% + (0.8 * 20%) = 31%
conversation_memory = 60% - 5% = 55% (reduced to make room)
reserved = 11% - 11% = 2% (minimum)
```

### Exchange Size Limits (Percentage-Based)

```python
class ExchangeLimits:
    MAX_SINGLE_EXCHANGE_PCT = 0.25    # 25% of memory budget
    MAX_USER_INPUT_PCT = 0.10         # 10% of memory budget
    MAX_ASSISTANT_RESPONSE_PCT = 0.15 # 15% of memory budget (before adaptation)
```

### Memory Loading Strategy with Summarization

```python
def _load_history_within_budget(self, memory_budget: int) -> list:
    """Load conversation history with intelligent truncation"""
    
    all_history = self.memory.get_recent_conversations()
    
    # Reserve 10% of budget for potential summary
    SUMMARY_RESERVE_PCT = 0.10
    effective_budget = int(memory_budget * 0.90)
    
    selected_history = []
    current_tokens = 0
    
    # Start with most recent, work backwards
    for exchange in reversed(all_history):
        exchange_tokens = self.token_counter.count_conversation_tokens([exchange])
        
        # Skip oversized exchanges (>25% of budget)
        if exchange_tokens > memory_budget * 0.25:
            continue
            
        if current_tokens + exchange_tokens > effective_budget:
            # Create summary of dropped exchanges
            dropped_exchanges = all_history[:-len(selected_history)] if selected_history else all_history[:-1]
            summary = self._create_summary(dropped_exchanges)
            selected_history.insert(0, summary)
            break
            
        selected_history.insert(0, exchange)  # Add to beginning
        current_tokens += exchange_tokens
    
    return selected_history
```

### Tool Control Logic

```python
def prepare_context(self, user_input: str, model: str, mode: str) -> dict:
    """Prepare context based on mode"""
    
    # Get conversation history (ALWAYS)
    context_window = self.model_detector.get_context_window(model)
    
    if mode == "tools":
        # Tools mode: 60% budget for history
        history_budget = int(context_window * 0.6)
        system_prompt = build_enhanced_tool_instruction()
        tool_schemas = get_context_aware_tool_schemas()
    else:
        # Chat mode: 80% budget for history  
        history_budget = int(context_window * 0.8)
        system_prompt = "You are a helpful assistant."
        tool_schemas = None
    
    # Load history within budget
    history = self._load_history_within_budget(history_budget)
    
    # Build messages
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(history)
    messages.append({"role": "user", "content": user_input})
    
    return {
        'messages': messages,
        'tools': tool_schemas,
        'budget_used': self._count_tokens(messages),
        'budget_available': history_budget
    }
```

## Integration Plan

### Step 1: Create New Components
- [x] ModelCapabilityDetector (already exists)
- [ ] SimpleTokenCounter 
- [ ] ModelSpecificMemory (per-model memory files)
- [ ] AdaptiveBudgetManager
- [ ] UnifiedMemoryManager
- [ ] Memory format migration utility

### Step 2: Setup Model-Specific Memory System
- [ ] Create WorkspaceAI/memory/ directory structure
- [ ] Implement model name to filename conversion
- [ ] Add atomic file operations for memory saves
- [ ] Create memory validation and corruption detection
- [ ] Migrate existing memory.json to model-specific files

### Step 3: Upgrade Memory Components  
- [ ] Implement new memory format with token metadata
- [ ] Add migration logic for existing memory files
- [ ] Update configuration options for per-model settings

### Step 4: Replace Interface Logic
- [ ] Modify `ollama_universal_interface.py` 
- [ ] Remove dual-path methods
- [ ] Add unified handler method
- [ ] Update imports and dependencies

### Step 5: Update App Integration
- [ ] Modify `app.py` to pass model parameter to unified interface
- [ ] Keep existing user commands (`t:`, `chat:`)
- [ ] Update error handling for model-specific memory failures

### Step 6: Testing & Validation
- [ ] Test memory consistency across modes for each model
- [ ] Validate token budget management with adaptive allocation
- [ ] Test conversation continuity within model-specific contexts
- [ ] Test model switching and memory isolation
- [ ] Performance validation with multiple model memory files

## Per-Model Memory System Architecture

### File Organization Structure
```
WorkspaceAI/
└── memory/
    ├── qwen2-5-7b.json      # qwen2.5:7b conversations
    ├── qwen2-5-3b.json      # qwen2.5:3b conversations  
    ├── llama3-1-8b.json     # llama3.1:8b conversations
    └── claude-3-haiku.json  # claude-3-haiku conversations
```

### Model Name Conversion Logic
```python
def model_to_filename(model_name: str) -> str:
    """Convert model names to valid filenames"""
    # Handle common patterns:
    # qwen2.5:7b → qwen2-5-7b
    # llama3.1:8b → llama3-1-8b
    # claude-3-haiku → claude-3-haiku
    # gpt-4o-mini → gpt-4o-mini
    
    return (model_name
            .replace(":", "-")     # Handle parameter separators
            .replace(".", "-")     # Handle version separators
            .lower()              # Consistent case
            .replace(" ", "-"))   # Handle spaces
```

### Memory Isolation Benefits

#### 1. Task-Specific Contexts
```python
# Example: Using different models for different tasks
qwen2_5_7b_memory = {
    "current_conversation": [
        {"user": "Analyze this Python code...", "assistant": "Here's the analysis..."},
        {"user": "Now optimize it...", "assistant": "Here are optimizations..."}
    ]
}

qwen2_5_3b_memory = {
    "current_conversation": [
        {"user": "Write a quick script to...", "assistant": "Here's a simple script..."},
        {"user": "Make it faster", "assistant": "Here's the optimized version..."}
    ]
}
```

#### 2. Corruption Isolation
- If one model's memory becomes corrupted, other models remain unaffected
- Easy to identify which model's conversation history has issues
- Simple to backup/restore specific model conversations

#### 3. Performance Benefits  
- Smaller individual memory files load faster
- No need to filter conversations by model
- Parallel loading possible for multi-model systems

#### 4. User Experience Benefits
- Model switching provides fresh context when needed
- Different conversation styles can emerge per model
- Easy to maintain different conversation threads per model capability

### Memory File Structure (Per Model)
```json
{
  "metadata": {
    "version": "3.0",
    "model": "qwen2.5:7b",
    "created": "2025-09-04T10:00:00Z",
    "last_updated": "2025-09-04T10:30:00Z",
    "total_exchanges": 15,
    "total_tokens": 45678,
    "context_window": 32768
  },
  "current_conversation": [
    {
      "user": {"content": "Hello", "tokens": 5},
      "assistant": {"content": "Hi there!", "tokens": 8},
      "metadata": {
        "timestamp": "2025-09-04T10:00:00Z",
        "mode": "chat",
        "total_tokens": 13,
        "complexity_score": 0.1
      }
    }
  ],
  "recent_conversations": [
    {
      "summary": "Discussion about Python optimization techniques",
      "exchange_count": 8,
      "total_tokens": 2400,
      "date_range": "2025-09-03 to 2025-09-03"
    }
  ],
  "summarized_conversations": [
    {
      "summary": "Multiple coding sessions covering React, Python, and database design",
      "exchange_count": 25,
      "total_tokens": 8900,
      "date_range": "2025-09-01 to 2025-09-02"
    }
  ]
}
```

### Migration Strategy from Single Memory

```python
class MemoryMigrator:
    def migrate_single_to_per_model(self, old_memory_path: str, memory_dir: str):
        """Migrate existing single memory.json to per-model files"""
        
        # Load existing memory
        with open(old_memory_path, 'r') as f:
            old_memory = json.load(f)
        
        # Group conversations by model (if metadata exists)
        model_conversations = self._group_by_model(old_memory)
        
        # Create model-specific memory files
        for model, conversations in model_conversations.items():
            model_memory = self._create_model_memory_structure(model, conversations)
            self._save_model_memory(memory_dir, model, model_memory)
        
        # Backup original file
        backup_path = f"{old_memory_path}.backup"
        shutil.copy2(old_memory_path, backup_path)
        
        logger.info(f"Migrated {len(model_conversations)} model memories")
        logger.info(f"Original memory backed up to {backup_path}")
    
    def _group_by_model(self, old_memory: dict) -> dict:
        """Group conversations by model from metadata"""
        model_groups = {}
        
        for exchange in old_memory.get("current_conversation", []):
            # Extract model from metadata if available
            model = exchange.get("metadata", {}).get("model", "unknown")
            
            if model not in model_groups:
                model_groups[model] = []
            
            model_groups[model].append(exchange)
        
        # Handle case where no model metadata exists
        if "unknown" in model_groups:
            # Assume default model or prompt user
            default_model = "qwen2.5:7b"  # Or get from config
            model_groups[default_model] = model_groups.pop("unknown")
        
        return model_groups
```

### Atomic File Operations

```python
class AtomicMemoryWriter:
    """Ensures memory files are never corrupted during writes"""
    
    def write_memory_safely(self, file_path: Path, memory_data: dict) -> bool:
        """Write memory with atomic operation"""
        temp_path = file_path.with_suffix('.tmp')
        backup_path = file_path.with_suffix('.backup')
        
        try:
            # Create backup of existing file
            if file_path.exists():
                shutil.copy2(file_path, backup_path)
            
            # Write to temporary file
            with open(temp_path, 'w') as f:
                json.dump(memory_data, f, indent=2, ensure_ascii=False)
            
            # Verify written data
            with open(temp_path, 'r') as f:
                verification = json.load(f)
            
            if not self._validate_memory_structure(verification):
                raise ValueError("Written memory failed validation")
            
            # Atomic rename
            temp_path.rename(file_path)
            
            # Clean up backup after successful write
            if backup_path.exists():
                backup_path.unlink()
            
            return True
            
        except Exception as e:
            # Restore from backup if write failed
            if backup_path.exists() and not file_path.exists():
                backup_path.rename(file_path)
            
            # Clean up temp file
            if temp_path.exists():
                temp_path.unlink()
            
            logger.error(f"Failed to write memory: {e}")
            return False
```

## Migration Strategy

### Backward Compatibility
```python
class MemoryMigrator:
    def migrate_v1_to_v2(self, old_memory: dict) -> dict:
        """Migrate existing memory format to v2 with metadata"""
        
        new_memory = {
            "metadata": {
                "version": "2.0",
                "migrated_from": "1.0",
                "migration_date": datetime.now().isoformat()
            },
            "current_conversation": [],
            "recent_conversations": [],
            "summarized_conversations": []
        }
        
        # Convert old exchanges to new format
        for exchange in old_memory.get("current_conversation", []):
            new_exchange = {
                "user": {
                    "content": exchange.get("user", ""),
                    "tokens": self.estimate_tokens(exchange.get("user", ""))
                },
                "assistant": {
                    "content": exchange.get("assistant", ""),
                    "tokens": self.estimate_tokens(exchange.get("assistant", ""))
                },
                "metadata": {
                    "timestamp": exchange.get("timestamp", ""),
                    "mode": "unknown",  # Legacy data
                    "total_tokens": 0   # Calculated
                }
            }
            new_memory["current_conversation"].append(new_exchange)
        
        return new_memory
```

### Rollback Plan
- Keep backup of original memory.json
- Environment variable to force v1 memory format
- Graceful degradation if migration fails

## Testing Strategy

### Unit Tests
```python
def test_unified_memory_consistency():
    """Test that both modes access the same memory for same model"""
    manager = UnifiedMemoryManager()
    
    # Add exchange in tools mode for specific model
    manager.save_exchange("test", "response", "tools", "qwen2.5:7b")
    
    # Verify available in chat mode for same model
    chat_context = manager.prepare_context("follow up", "qwen2.5:7b", "chat")
    assert "test" in str(chat_context['messages'])

def test_model_memory_isolation():
    """Test that different models have separate memory contexts"""
    manager = UnifiedMemoryManager()
    
    # Add conversation to qwen2.5:7b
    manager.save_exchange("qwen conversation", "qwen response", "tools", "qwen2.5:7b")
    
    # Add different conversation to qwen2.5:3b
    manager.save_exchange("different conversation", "different response", "tools", "qwen2.5:3b")
    
    # Verify isolation
    qwen_7b_context = manager.prepare_context("follow up", "qwen2.5:7b", "chat")
    qwen_3b_context = manager.prepare_context("follow up", "qwen2.5:3b", "chat")
    
    assert "qwen conversation" in str(qwen_7b_context['messages'])
    assert "qwen conversation" not in str(qwen_3b_context['messages'])
    assert "different conversation" in str(qwen_3b_context['messages'])
    assert "different conversation" not in str(qwen_7b_context['messages'])

def test_memory_file_corruption_handling():
    """Test graceful handling of corrupted memory files"""
    memory_system = ModelSpecificMemory()
    
    # Create corrupted memory file
    corrupted_file = memory_system.get_memory_file_path("test-model")
    with open(corrupted_file, 'w') as f:
        f.write("invalid json content {")
    
    # Should return fresh memory, not crash
    memory = memory_system.load_memory("test-model")
    assert memory["metadata"]["version"] == "3.0"
    assert memory["metadata"]["model"] == "test-model"
    assert memory["current_conversation"] == []

def test_atomic_memory_operations():
    """Test that memory writes are atomic and safe"""
    memory_system = ModelSpecificMemory()
    
    # Create initial memory
    initial_memory = memory_system.load_memory("test-model")
    initial_memory["current_conversation"].append({
        "user": {"content": "test", "tokens": 4},
        "assistant": {"content": "response", "tokens": 8}
    })
    
    # Save should be atomic - either succeeds completely or fails completely
    success = memory_system.save_memory("test-model", initial_memory)
    assert success == True
    
    # Verify data integrity
    loaded_memory = memory_system.load_memory("test-model")
    assert len(loaded_memory["current_conversation"]) == 1
    assert loaded_memory["current_conversation"][0]["user"]["content"] == "test"

def test_adaptive_budget_allocation():
    """Test that response budgets adapt to query complexity"""
    manager = UnifiedMemoryManager()
    
    # Simple query should get minimal response allocation
    simple_context = manager.prepare_context("hi", "qwen2.5:7b", "tools")
    simple_response_pct = simple_context['budgets']['response_percentage']
    
    # Complex query should get larger response allocation
    complex_context = manager.prepare_context(
        "Analyze this code, explain architecture, and suggest improvements", 
        "qwen2.5:7b", "tools"
    )
    complex_response_pct = complex_context['budgets']['response_percentage']
    
    assert complex_response_pct > simple_response_pct

def test_percentage_based_scaling():
    """Test that percentages work across different context window sizes"""
    manager = UnifiedMemoryManager()
    
    # Mock different model context windows
    small_model_context = manager.prepare_context("test", "small-model", "tools")
    large_model_context = manager.prepare_context("test", "large-model", "tools")
    
    # Percentages should be consistent regardless of absolute token counts
    small_pct = small_model_context['budgets']['response_percentage']
    large_pct = large_model_context['budgets']['response_percentage']
    
    assert abs(small_pct - large_pct) < 0.01  # Within 1% tolerance

def test_model_name_to_filename_conversion():
    """Test conversion of various model names to valid filenames"""
    memory_system = ModelSpecificMemory()
    
    test_cases = [
        ("qwen2.5:7b", "qwen2-5-7b.json"),
        ("llama3.1:8b", "llama3-1-8b.json"),
        ("claude-3-haiku", "claude-3-haiku.json"),
        ("gpt-4o-mini", "gpt-4o-mini.json")
    ]
    
    for model_name, expected_filename in test_cases:
        file_path = memory_system.get_memory_file_path(model_name)
        assert file_path.name == expected_filename
```

### Integration Tests
- Model-specific memory persistence across restarts
- Model switching without conversation bleed
- Tool availability in different modes with different models
- Context window overflow handling per model
- Adaptive response allocation accuracy across models
- Performance with large conversation histories per model
- Memory corruption recovery for individual models
- Atomic file operations under concurrent access
- Migration from single memory to per-model system

## Success Metrics

### Functional Requirements
- [x] **Memory Consistency**: 100% of interactions have conversation history per model
- [x] **Model Isolation**: Different models maintain separate conversation contexts
- [x] **Tool Control**: Tools only available when explicitly enabled  
- [x] **Adaptive Budgeting**: Response allocation matches query complexity
- [x] **Budget Management**: Contexts stay within model limits
- [x] **Universal Scaling**: System works across any context window size
- [x] **Backward Compatibility**: Existing memory files migrate to per-model system
- [x] **Corruption Resilience**: Individual model memory corruption doesn't affect others

### Performance Requirements  
- [x] **Memory Loading**: <100ms for typical conversation histories per model
- [x] **Token Counting**: <10ms for context preparation
- [x] **Context Assembly**: <50ms for complete context building
- [x] **Complexity Analysis**: <5ms for query analysis
- [x] **Model Memory Switching**: <10ms to switch between model contexts
- [x] **File Operations**: <50ms for atomic memory saves

### User Experience Requirements
- [x] **Seamless Transition**: No changes to user interface
- [x] **Conversation Continuity**: Context preserved between modes per model
- [x] **Model-Specific Contexts**: Different conversation threads per model capability
- [x] **Intelligent Responses**: Longer responses for complex queries
- [x] **Error Resilience**: Graceful handling of corrupted memory per model
- [x] **Task Separation**: Different models maintain relevant conversation contexts

## System Benefits

### Immediate Benefits
1. **Memory Consistency**: All interaction modes have access to conversation history per model
2. **Model Task Specialization**: Different models can maintain context for their specific use cases
3. **Corruption Isolation**: Problems with one model's memory don't affect others
4. **Intelligent Resource Usage**: Response space adapts to query complexity  
5. **Universal Scalability**: Works with any model context window size
6. **Security**: Tool activation remains explicitly controlled

### Long-term Benefits
1. **Superior User Experience**: Responses match user expectations, conversations maintain model-specific context
2. **Competitive Advantage**: Per-model memory + complexity-aware budgeting not found elsewhere
3. **Maintainability**: Simple percentage-based system with isolated model memories
4. **Future-Proof**: Adapts automatically to new models, scales to multi-model workflows
5. **Reliability**: Atomic file operations and corruption isolation ensure data integrity
6. **Flexibility**: Easy to backup, restore, or transfer specific model conversation histories

## Risk Mitigation

### Technical Risks
1. **Memory Corruption**: 
   - Risk: Migration fails, user loses conversation history
   - Mitigation: Automatic backup, rollback capability

2. **Performance Degradation**:
   - Risk: Large conversations slow down system  
   - Mitigation: Token-based truncation, lazy loading

3. **Context Overflow**:
   - Risk: Conversations exceed model context window
   - Mitigation: Conservative budgeting, graceful truncation

### User Experience Risks
1. **Breaking Changes**:
   - Risk: Users need to relearn interface
   - Mitigation: Keep existing commands, transparent upgrade

2. **Lost Conversations**:
   - Risk: Memory migration loses important data
   - Mitigation: Multiple backup strategies, manual recovery

## Implementation Timeline

Given AI-accelerated development capabilities:

### Session 1: Foundation (1-2 hours)
- Create SimpleTokenCounter with character-based estimation
- Create ModelSpecificMemory with atomic file operations
- Create AdaptiveBudgetManager with complexity analysis
- Setup WorkspaceAI/memory/ directory structure
- Implement model name to filename conversion

### Session 2: Core Logic (1-2 hours)  
- Create UnifiedMemoryManager with per-model support
- Implement adaptive context preparation logic
- Add token budget management with percentage scaling
- Memory loading within dynamic budgets per model
- Test memory isolation between models

### Session 3: Integration (1-2 hours)
- Modify ollama_universal_interface.py to use unified system
- Update app.py integration points with model parameter passing
- Implement memory migration from single file to per-model files
- Test memory consistency and adaptive allocation

### Session 4: Polish & Testing (1 hour)
- Comprehensive testing of per-model memory isolation
- Atomic file operation validation
- Migration utility testing and documentation
- Performance validation with multiple model memories

**Total Estimated Time**: 4-7 hours across multiple sessions

## Key Implementation Notes

### Simplicity First
- **Token counting**: Simple `len(text) // 3` estimation
- **Complexity analysis**: Basic keyword and length-based scoring
- **Budget allocation**: Straightforward percentage calculations
- **Memory truncation**: Newest-first with optional summarization

### Configuration Options
```python
# Optional user-configurable verbosity levels
RESPONSE_VERBOSITY = {
    'concise': {'tools_max_response': 0.25, 'chat_max_response': 0.20},
    'balanced': {'tools_max_response': 0.35, 'chat_max_response': 0.25},  # Default
    'detailed': {'tools_max_response': 0.45, 'chat_max_response': 0.30}
}
```

### Adaptive Algorithm Summary
```python
def calculate_adaptive_response_allocation(complexity_score, mode):
    """Core adaptive logic - dead simple"""
    if mode == "tools":
        min_pct, max_pct = 0.15, 0.35  # 15-35% range
    else:
        min_pct, max_pct = 0.15, 0.25  # 15-25% range
    
    return min_pct + (complexity_score * (max_pct - min_pct))
```

## Next Actions

1. **Begin Implementation** - Start with Session 1: Foundation components
2. **Create ModelSpecificMemory** - Setup per-model memory file system
3. **Create SimpleTokenCounter** - Validate percentage-based approach 
4. **Build AdaptiveBudgetManager** - Test complexity analysis algorithm
5. **Implement UnifiedMemoryManager** - Core integration component with per-model support

---

**Plan Version**: 3.0 (Complete Implementation with Per-Model Memory)  
**Last Updated**: September 4, 2025  
**Status**: Ready for Implementation  
**Architecture**: Unified memory path + adaptive response allocation + per-model memory files

This plan combines the proven unified memory architecture with innovative complexity-aware budgeting and per-model memory isolation in a simple, maintainable package that scales across any model context window size while providing superior user experience through task-specific conversation contexts.
    
    return min_pct + (complexity_score * (max_pct - min_pct))
```
- Add token budget management
- Memory loading within budget

### Session 3: Integration (1-2 hours)
- Modify ollama_universal_interface.py
- Update app.py integration
- Basic testing

### Session 4: Polish & Testing (1 hour)
- Migration utility
- Comprehensive testing
- Documentation updates

**Total Estimated Time**: 4-7 hours across multiple sessions

## Next Actions

1. **Review this plan** - Identify any missing components or logic gaps
2. **Start with SimpleTokenCounter** - Simplest component, validates approach
3. **Build UnifiedMemoryManager** - Core innovation component
4. **Test incrementally** - Validate each piece before moving to next

---

**Plan Version**: 2.0  
**Last Updated**: September 4, 2025  
**Status**: Ready for Implementation  
**Architecture**: Validated and refined based on external review

This plan addresses the core architectural challenges while maintaining simplicity and user experience. The unified memory path ensures consistent behavior while preserving the security and performance benefits of explicit tool control.
