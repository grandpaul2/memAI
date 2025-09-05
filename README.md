# memAI - Memory-Enhanced AI Assistant

A lightweight, single-file AI assistant with excellent conversation memory management. Built for Ollama local AI models.

## Features

- **Persistent Memory**: Conversations saved per-model with automatic context window management
- **Adaptive Scaling**: Memory capacity scales with model context window (4k-20k tokens)
- **Simple Interface**: Clean CLI with animated progress indicators
- **Zero Dependencies**: Only requires Python 3.8+ and `requests` library
- **Production Ready**: Comprehensive testing with 390+ automated scenarios

## Quick Start

```bash
# Install requirements
pip install -r requirements.txt

# Run memAI
python3 memai.py

# Select a model and start chatting!
```

## Commands

- `help` - Show available commands
- `model` - Switch AI model
- `stats` - Show conversation statistics
- `clear` - Clear conversation history
- `quit` - Exit memAI

## Memory Management

- **Per-model storage**: Each model gets its own conversation file
- **Smart truncation**: Keeps recent exchanges when context window fills
- **Collision-safe**: Hash-based filenames prevent conflicts
- **Performance cap**: Max 20k tokens (~500 exchanges) even for massive models

## Project Structure

```
memAI/
├── memai.py           # Main application (single file)
├── requirements.txt   # Python dependencies
├── docs/             # Documentation and project notes
├── tests/            # Comprehensive test suite
└── archive/          # Historical files and backups
```

## Testing

The project includes comprehensive testing:

```bash
cd tests/
python3 large_scale_test.py    # 390 automated scenarios
python3 simple_test.py         # Quick validation
python3 conversation_capacity.py  # Memory analysis
```

## License

Open source - feel free to use and modify!
