# MemoryAI - Project Outline

## Vision
A focused, lightweight AI assistant that excels at conversation memory management. Clean architecture, reliable performance, and intelligent context handling without the complexity of universal tool integration.

## Core Value Proposition
- **Smart Memory**: Conversations that remember context across sessions
- **Model Flexibility**: Works with any Ollama model with adaptive optimization
- **Clean Architecture**: Simple, maintainable codebase focused on doing one thing well
- **Performance**: Efficient token management and context optimization

## Architecture Components

### Core Memory System
- `unified_memory_manager.py` - Central memory orchestration
- `model_specific_memory.py` - Per-model conversation storage
- `adaptive_budget_manager.py` - Smart context budgeting
- `token_counter.py` - Accurate token estimation
- `memory_integration.py` - Interface layer for memory operations

### Support Systems
- `config.py` - Configuration and settings management
- `exceptions.py` - Error handling framework
- `safety_validator.py` - Memory validation and safety checks
- `ollama_client.py` - Ollama API communication

### Application Layer
- `main.py` - Simple chat interface
- `app.py` - Core application logic (memory-focused)

### Testing & Quality
- Memory system test suite
- Integration tests
- Performance benchmarks

## Key Features

### 1. Intelligent Memory Management
- **Per-Model Isolation**: Each model gets its own conversation history
- **Adaptive Context**: Dynamic context sizing based on query complexity
- **Token Budgeting**: Prevent context overflow with smart trimming
- **Memory Migration**: Seamless upgrades from legacy memory formats

### 2. Model Optimization
- **Automatic Model Detection**: Discovers available Ollama models
- **Context Window Awareness**: Respects each model's limitations  
- **Performance Tuning**: Optimized for different model characteristics
- **Fallback Handling**: Graceful degradation when models unavailable

### 3. User Experience
- **Session Continuity**: Conversations persist across app restarts
- **Clean Interface**: Simple chat without complexity overhead
- **Performance Feedback**: Memory usage and optimization stats
- **Configuration**: Customizable behavior and preferences

## What's NOT Included (Intentionally)
- Universal tool calling system
- File operation tools
- Code execution capabilities  
- Complex instruction systems
- Multi-agent orchestration
- External API integrations

## Technical Requirements
- Python 3.8+
- Ollama installed locally
- At least one language model (qwen2.5:3b recommended)
- ~50MB storage for memory databases

## Success Metrics
- **Memory Accuracy**: Conversations maintain context appropriately
- **Performance**: Sub-second response times for memory operations
- **Reliability**: No memory corruption or data loss
- **Usability**: Simple setup and intuitive operation
- **Resource Efficiency**: Minimal CPU/memory footprint

## Target Users
- Developers who want reliable local AI with memory
- Privacy-conscious users preferring local models
- Researchers needing consistent conversation context
- Anyone frustrated with AI that "forgets" previous conversations

## Development Philosophy
**Focus > Features**: Better to excel at memory management than struggle with feature bloat. Clean, maintainable code that does its job reliably.

## Migration Path
Users of WorkspaceAI v3.0 can migrate their memory data seamlessly. The memory formats are compatible, just without the tool complexity.
