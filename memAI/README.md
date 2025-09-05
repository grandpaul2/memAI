# memAI

AI assistant with perfect conversation memory. Each model maintains isolated conversation history with intelligent context management.

## Prerequisites

- Python 3.8+
- [Ollama](https://ollama.ai/) running locally
- At least one language model installed

## Installation

```bash
pip install -r requirements.txt
python memai.py
```

## Features

- **Per-Model Memory**: Each AI model gets isolated conversation history
- **Adaptive Context**: Smart context loading based on query complexity  
- **Token Budgeting**: Optimized context window utilization
- **Zero Configuration**: Auto-detects models, works immediately
- **Session Persistence**: Conversations survive app restarts

## Commands

- `help` - Show commands
- `model <name>` - Switch AI models
- `stats` - Memory statistics
- `clear` - Clear current conversation
- `quit` - Exit

## Storage

Memory files created in `./memory/` directory:
- `{model-name}_{hash}.json` - Conversation history per model
- `./memory/backups/` - Automatic backups before operations

## Configuration

Token estimation can be adjusted in `TokenEstimator` class:
```python
self.chars_per_token = 3.0  # Tune based on testing
```

Context limits automatically scale with model size (8K/32K/128K+ tokens).
