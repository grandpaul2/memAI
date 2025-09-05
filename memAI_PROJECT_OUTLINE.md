# memAI - Complete Project Outline

## Executive Summary

**memAI** is a focused, ground-up rebuild of an AI assistant that excels at conversation memory management. Unlike complex multi-feature AI tools, memAI does one thing exceptionally well: maintaining intelligent, persistent conversations with local AI models through Ollama.

**Core Innovation**: Per-model memory isolation with adaptive context management - each AI model gets its own conversation history with smart token budgeting that adapts to query complexity.

## Project Vision

### Primary Goal
Create the definitive local AI conversation assistant that "remembers everything" across sessions while maintaining a clean, minimal architecture.

### Value Proposition
- **Zero Configuration**: Auto-detects models, starts conversations immediately
- **Perfect Memory**: Never lose conversation context, works across app restarts  
- **Smart & Fast**: Adapts to simple/complex queries with optimal context loading
- **Model Flexibility**: Works with any Ollama model, each with isolated conversations
- **Privacy First**: Everything local, no external services, no data collection

## Core Architecture

### Design Philosophy
1. **Single Purpose Excellence**: Master conversation memory, ignore everything else
2. **Ground-Up Simplicity**: Clean rebuild without legacy complexity
3. **Modular When Needed**: Start with single file, split when warranted
4. **Zero Friction Setup**: Works immediately after Ollama installation

### Technical Architecture

#### Option A: Single File (Preferred Start)
```
memAI/
├── memai.py              # Complete application (500-800 lines)
├── requirements.txt      # Just: requests
└── memory/              # Auto-created conversation storage
    ├── qwen2-5-3b_a1b2c3d4.json
    ├── llama2_e5f6g7h8.json
    └── ...
```

#### Option B: Modular (If Growth Warrants)
```
memAI/
├── memai.py              # Main application & CLI
├── memory_manager.py     # Core memory system
├── ollama_client.py      # Ollama communication
├── requirements.txt      # Minimal dependencies
└── memory/              # Conversation storage
```

## Core Features

### 1. Intelligent Memory System

**Per-Model Isolation**:
- Each model gets its own JSON conversation file
- File naming: `{model_name}_{hash}.json` (collision-safe)
- Example: `qwen2-5-3b_a1b2c3d4.json`, `llama2_e5f6g7h8.json`

**Adaptive Context Loading**:
- **Simple queries** ("hi", "what's the weather?"): Load minimal context, fast response
- **Complex queries** ("explain quantum computing"): Load full conversation history
- **Token budgeting**: 75% context memory, 20% response, 5% safety margin

**Smart File Size Management**:
- **Small context models** (8k tokens): Max 50 exchanges
- **Medium context models** (32k tokens): Max 200 exchanges  
- **Large context models** (128k+ tokens): Max 500 exchanges
- **Auto-summarization**: Older conversations get AI-summarized when limits hit

### 2. Automatic Model Detection & Management

**Zero Configuration Startup**:
```python
# App detects available models automatically
available_models = get_ollama_models()
if not available_models:
    print("No models found. Run: ollama pull qwen2.5:3b")
    exit()

# Use first available or let user pick
current_model = available_models[0]
print(f"Using model: {current_model}")
```

**Smart Model Switching**:
- `model <name>` command with auto-completion
- Conversation history preserved per model
- Context window auto-detected per model

### 3. Perfect CLI Experience

**Animated Progress Dots** (The Key Feature to Keep):
```python
def show_thinking():
    """The perfectly implemented animated dots"""
    for i in range(3):
        sys.stdout.write('.')
        sys.stdout.flush()
        time.sleep(0.3)
    sys.stdout.write('\r' + ' ' * 3 + '\r')  # Clear dots
```

**Clean Command Interface**:
- Natural conversation (just type)
- `help` - Show commands
- `model <name>` - Switch models  
- `stats` - Memory usage
- `clear` - Clear current conversation
- `quit` - Exit gracefully

**Minimal UI Noise**:
- No emoji spam (just the dots!)
- Clean startup message
- Error messages without stack traces
- No logging chatter

### 4. Smart Memory Management

**JSON Storage Format**:
```json
{
  "model": "qwen2.5:3b",
  "context_window": 32768,
  "created": "2025-09-05T10:00:00Z",
  "exchanges": [
    {
      "user": "Hello, how are you?",
      "assistant": "I'm doing well, thank you for asking!",
      "timestamp": "2025-09-05T10:00:00Z",
      "tokens": {"user": 12, "assistant": 18}
    }
  ],
  "summary": "User greeted AI assistant, friendly conversation started"
}
```

**Automatic Summarization Mechanism**:
- When file reaches size limit, summarize oldest 25% of conversations
- Use the current model to create summaries
- Keep 2-3 sentence summaries of old conversations
- Maintain conversation flow with summarized context

**Context Window Adaptation**:
```python
# Hardcoded after testing - no user config needed
CONTEXT_LIMITS = {
    "small": {"max_tokens": 8192, "max_exchanges": 50},
    "medium": {"max_tokens": 32768, "max_exchanges": 200}, 
    "large": {"max_tokens": 131072, "max_exchanges": 500}
}

def get_model_limits(model_name):
    """Auto-detect context window and set appropriate limits"""
    context_window = detect_context_window(model_name)
    if context_window <= 8192:
        return CONTEXT_LIMITS["small"]
    elif context_window <= 32768:
        return CONTEXT_LIMITS["medium"]
    else:
        return CONTEXT_LIMITS["large"]
```

## Technical Implementation

### Dependencies
**Minimal**: Only `requests` for Ollama API communication
**Python**: 3.8+ (broad compatibility)
**Storage**: JSON files (human-readable, model-compatible)

### Core Components

#### 1. Memory Manager
```python
class MemoryManager:
    """Handles per-model conversation storage and retrieval"""
    
    def __init__(self):
        self.memory_dir = Path("memory")
        self.memory_dir.mkdir(exist_ok=True)
    
    def get_conversation(self, model: str) -> List[Dict]:
        """Load conversation history for model"""
        
    def add_exchange(self, model: str, user_msg: str, assistant_msg: str):
        """Add new conversation exchange"""
        
    def should_summarize(self, model: str) -> bool:
        """Check if conversation needs summarization"""
        
    def summarize_old_exchanges(self, model: str):
        """Create AI summary of oldest exchanges"""
```

#### 2. Ollama Client
```python
class OllamaClient:
    """Simple Ollama API communication"""
    
    def get_available_models(self) -> List[str]:
        """List available Ollama models"""
        
    def detect_context_window(self, model: str) -> int:
        """Auto-detect model context window size"""
        
    def chat_completion(self, model: str, messages: List[Dict]) -> str:
        """Get response from model with animated dots"""
```

#### 3. Context Builder
```python
class ContextBuilder:
    """Smart context assembly with token budgeting"""
    
    def analyze_complexity(self, user_input: str) -> float:
        """Simple complexity scoring (0.0-1.0)"""
        # Length, question words, technical terms
        
    def build_context(self, model: str, user_input: str) -> List[Dict]:
        """Assemble optimal context within token budget"""
```

### Token Management Strategy

**Simple Token Estimation**:
```python
def estimate_tokens(text: str) -> int:
    """Conservative estimation: ~3 chars per token"""
    return max(1, len(text) // 3)
```

**Budget Allocation** (75/20/5 rule):
- **75% Conversation Memory**: Recent exchanges that fit
- **20% Response Generation**: Space for AI response  
- **5% Safety Margin**: Buffer for estimation errors

**Adaptive Loading**:
- **Simple queries**: Load last 5-10 exchanges (fast)
- **Complex queries**: Load full available context (comprehensive)
- **Auto-trim**: Remove oldest exchanges to fit budget

## User Experience

### Startup Flow
```
$ python memai.py

memAI - AI Assistant with Perfect Memory
🤖 Detected models: qwen2.5:3b, llama2:7b
📱 Using: qwen2.5:3b (type 'model <name>' to switch)
💬 Ready to chat! (type 'help' for commands)

You: hello
   ...   (animated dots while thinking)
Assistant: Hello! I'm ready to help you with anything you'd like to discuss.

You: 
```

### Model Switching
```
You: model llama2:7b
✅ Switched to llama2:7b 
📚 Conversation history: 23 exchanges
💭 Context ready

You: what did we discuss before?
   ...
Assistant: I can see we haven't chatted yet with this model. Each model maintains its own conversation memory, so this is a fresh start!
```

### Memory Stats
```
You: stats
📊 Memory Statistics for qwen2.5:3b:
   Exchanges: 47
   Total tokens: ~12,400
   Context usage: 68% of available
   Memory file: 8.2 KB
   
🤖 Other models with memory: llama2:7b (23 exchanges)
```

## File Structure & Storage

### Memory File Organization
```
memory/
├── qwen2-5-3b_a1b2c3d4.json      # Primary model conversations
├── llama2-7b_e5f6g7h8.json       # Secondary model conversations  
├── codellama_f9g8h7i6.json       # Code-focused conversations
└── backups/                      # Auto-created safety backups
    ├── qwen2-5-3b_a1b2c3d4_backup_20250905.json
    └── ...
```

### Collision Prevention
```python
def model_to_filename(model: str) -> str:
    """Convert model name to safe filename with hash"""
    safe_name = re.sub(r'[^\w\-]', '-', model)  # Clean special chars
    model_hash = hashlib.md5(model.encode()).hexdigest()[:8]
    return f"{safe_name}_{model_hash}.json"
```

## Automatic Setup & Recovery

### Ollama Integration
```python
def ensure_ollama_ready():
    """Check Ollama status and guide user if needed"""
    if not is_ollama_running():
        print("❌ Ollama not running")
        print("💡 Start it with: ollama serve")
        return False
        
    models = get_available_models()
    if not models:
        print("❌ No models available")  
        print("💡 Install one with: ollama pull qwen2.5:3b")
        return False
        
    return True
```

### Memory Corruption Recovery
```python
def validate_memory_file(filepath: Path) -> bool:
    """Check if memory file is valid JSON with required structure"""
    try:
        with open(filepath) as f:
            data = json.load(f)
        return "model" in data and "exchanges" in data
    except:
        return False

def recover_corrupted_memory(filepath: Path):
    """Attempt to recover from backup or reset"""
    backup_path = find_most_recent_backup(filepath)
    if backup_path and validate_memory_file(backup_path):
        shutil.copy(backup_path, filepath)
        print(f"✅ Recovered memory from backup")
    else:
        create_fresh_memory_file(filepath)
        print(f"🔄 Reset corrupted memory file")
```

## Performance Targets

### Response Times
- **Startup**: < 2 seconds (model detection + memory loading)
- **Context Loading**: < 100ms (typical conversation)
- **Memory Saving**: < 50ms (atomic write operations)
- **Model Switching**: < 200ms (context change)

### Resource Usage
- **Memory**: < 30MB typical usage
- **Storage**: ~1-5KB per conversation exchange
- **CPU**: Minimal background usage

### Scalability
- **Max models**: Unlimited (limited by disk space)
- **Max exchanges per model**: 50-500 (based on context window)
- **Max total storage**: User's available disk space

## Development Plan

### Phase 1: Core Implementation (Week 1)
1. **Single file implementation** (`memai.py`)
2. **Basic memory management** (JSON storage)
3. **Ollama client integration** (model detection, chat)
4. **CLI interface** (commands, animated dots)
5. **Per-model isolation** (filename generation, loading)

### Phase 2: Smart Features (Week 2)  
1. **Token budgeting system** (context limits)
2. **Adaptive context loading** (simple vs complex queries)
3. **Auto-summarization** (when memory files get large)
4. **Error handling & recovery** (corrupted files, Ollama issues)

### Phase 3: Polish & Testing (Week 3)
1. **Edge case handling** (network issues, model switching)
2. **Performance optimization** (fast loading, efficient storage)
3. **User experience refinement** (clear messages, help system)
4. **Documentation** (README, usage examples)

## Quality Assurance

### Testing Strategy
- **Manual testing** with multiple Ollama models
- **Memory persistence testing** (app restart scenarios)
- **Error condition testing** (network failures, corrupted files)
- **Performance testing** (large conversation histories)

### Success Metrics
- ✅ **Sub-second response times** for typical queries
- ✅ **Zero data loss** across app restarts
- ✅ **Seamless model switching** with conversation isolation
- ✅ **Intuitive user experience** requiring no documentation to use
- ✅ **Reliable operation** with various Ollama models

## Future Considerations

### Potential Enhancements (Post-MVP)
1. **Export/Import**: Save conversations to readable formats
2. **Search**: Find specific exchanges across conversation history  
3. **Themes**: Different conversation styles per model
4. **Analytics**: Usage patterns and model performance stats
5. **Sync**: Optional backup to cloud storage (user-controlled)

### Architecture Evolution
- **Stay single-file** as long as possible (< 1000 lines)
- **Split selectively** only when complexity warrants it
- **Maintain simplicity** as core principle
- **Resist feature creep** - "memAI does memory, period"

---

## Questions for External Validation

### Technical Architecture
1. Is the single-file approach optimal for initial development?
2. Are the token budgeting percentages (75/20/5) appropriate?
3. Should we implement more sophisticated summarization beyond basic AI summaries?

### User Experience  
1. Is the zero-configuration approach viable, or do users need more control?
2. Are the CLI commands sufficient, or should we add more advanced features?
3. Is per-model memory isolation intuitive for end users?

### Market Positioning
1. Does the "one thing well" approach differentiate sufficiently?
2. Is local-only operation a significant competitive advantage?
3. Should we target developers specifically or broader audiences?

### Implementation Priorities
1. Which Phase should be demonstrated first for stakeholder buy-in?
2. Are there specific Ollama models we should optimize for initially?
3. Should Windows/Mac compatibility be prioritized over Linux-first development?

---

**memAI Project Outline v1.0**  
**Prepared**: September 5, 2025  
**Status**: Ready for External Consultation Review  
**Next Step**: Stakeholder validation and implementation approval
