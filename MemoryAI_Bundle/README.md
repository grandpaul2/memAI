# MemoryAI

🧠 **A focused AI assistant that excels at conversation memory management**

MemoryAI is a streamlined local AI assistant that remembers your conversations across sessions. Built around a sophisticated memory system without the complexity of universal tool integration.

## Key Features

- **Smart Memory**: Conversations persist and maintain context across sessions
- **Per-Model Isolation**: Each AI model gets its own conversation history  
- **Adaptive Context**: Dynamic context sizing based on conversation complexity
- **Model Flexibility**: Works with any Ollama model with automatic optimization
- **Clean Interface**: Simple chat focused on conversation, not complexity
- **Privacy First**: Everything runs locally, no data leaves your machine

## Quick Start

### Prerequisites
- Python 3.8+
- [Ollama](https://ollama.ai/) installed locally
- At least one language model (we recommend `qwen2.5:3b`)

### Installation

1. **Install Ollama and a model**:
   ```bash
   # Install Ollama (see https://ollama.ai/)
   curl -fsSL https://ollama.ai/install.sh | sh
   
   # Download a model
   ollama pull qwen2.5:3b
   ```

2. **Setup MemoryAI**:
   ```bash
   # Install dependencies
   pip install -r requirements.txt
   
   # Run MemoryAI
   python memoryai.py
   ```

### Usage

```bash
# Start chatting
python memoryai.py
```

**Available Commands**:
- Just type to chat normally
- `help` - Show commands
- `model <name>` - Switch AI models
- `stats` - Show memory statistics  
- `clear` - Clear current conversation
- `quit` - Exit

## Architecture

MemoryAI uses a sophisticated memory system:

### Core Components
- **Unified Memory Manager**: Central orchestration of memory operations
- **Model-Specific Memory**: Isolated conversation histories per model
- **Adaptive Budget Manager**: Smart context sizing and token management
- **Token Counter**: Accurate token estimation for different models
- **Safety Validator**: Memory validation and corruption prevention

### Memory Features
- **Conversation Persistence**: Chats survive app restarts
- **Context Optimization**: Automatic context trimming to fit model limits
- **Token Budgeting**: Prevents context overflow while preserving important context
- **Memory Migration**: Seamless upgrades and format migrations
- **Performance Monitoring**: Track memory usage and optimization

## Configuration

Edit `config.json` to customize behavior:

```json
{
    "default_model": "qwen2.5:3b",
    "memory_settings": {
        "max_recent_exchanges": 50,
        "max_summarized_conversations": 20
    },
    "ollama_settings": {
        "base_url": "http://localhost:11434",
        "context_window": 32768
    }
}
```

## Memory System Details

### Per-Model Isolation
Each AI model maintains its own conversation history:
- `qwen2.5:3b` conversations are separate from `llama2` conversations
- Switch models without losing context in either
- Optimizations are model-specific

### Adaptive Context Management
- **Simple queries**: Minimal context for fast responses
- **Complex discussions**: Full conversation history loaded
- **Automatic trimming**: Keeps conversations within model limits
- **Token budgeting**: Allocates context space efficiently

### Memory Storage
- Conversations stored in `memory/` directory
- JSON format for easy inspection and backup
- Automatic corruption detection and recovery
- Backup creation before major operations

## Performance

MemoryAI is optimized for:
- **Fast startup**: < 1 second typical startup time
- **Memory efficiency**: < 50MB typical memory usage
- **Response speed**: Context loading in milliseconds
- **Storage efficiency**: Compressed conversation storage

## Troubleshooting

### Common Issues

**"No response from model"**:
- Check that Ollama is running: `ollama list`
- Verify model is available: `ollama run qwen2.5:3b`
- Check Ollama service: `ollama serve`

**"Memory corruption detected"**:
- MemoryAI will automatically reset corrupted memory
- Backup files are created in `memory/backups/`
- Check logs in `memoryai.log` for details

**High memory usage**:
- Use `stats` command to check conversation size
- Use `clear` to reset conversation if needed
- Adjust `max_recent_exchanges` in config

### Debug Mode

Run with debug logging:
```bash
python memoryai.py --debug
```

## Development

### Project Structure
```
MemoryAI/
├── memoryai.py          # Main application
├── config.json         # Configuration
├── requirements.txt    # Dependencies
└── src/                # Core memory system
    ├── unified_memory_manager.py
    ├── model_specific_memory.py
    ├── adaptive_budget_manager.py
    ├── token_counter.py
    ├── memory_integration.py
    ├── config.py
    ├── exceptions.py
    ├── safety_validator.py
    └── ollama_client.py
```

### Key Design Principles
1. **Focus over Features**: Excel at memory, avoid feature bloat
2. **Reliability**: Memory system never loses data
3. **Performance**: Fast responses, efficient resource usage
4. **Simplicity**: Easy to use, easy to maintain

## Migration from WorkspaceAI

If you're coming from WorkspaceAI v3.0, your memory data is compatible:

1. Copy your `WorkspaceAI/memory/` directory to `MemoryAI/memory/`
2. MemoryAI will automatically migrate the format if needed
3. All conversation history will be preserved

## Philosophy

MemoryAI embodies the principle that **doing one thing well** is better than doing many things poorly. We focus exclusively on conversation memory management, delivering a reliable, fast, and intelligent AI assistant that actually remembers your discussions.

No universal tool calling, no complex integrations, no feature bloat. Just smart, persistent conversations with local AI models.

## License

MIT License - see LICENSE file for details.

---

**MemoryAI** - *Remember everything, forget complexity.*
