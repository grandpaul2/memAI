# memAI Testing Guide

## Quick Start Testing
1. Run test scenarios: `python3 test_scenarios.py`
2. Start memAI: `python3 memai.py`  
3. Work through scenarios systematically
4. Log results in `test_log.json`

## Test Categories

### 🧠 Memory Tests
- **Memory Continuity**: Does it remember basic facts across conversation?
- **Context Window**: How does it handle long conversations?
- **Multi-session**: Does memory persist after restart?

### 💬 Conversation Tests  
- **Natural Flow**: Context switching and topic changes
- **Technical Discussions**: Code, concepts, debugging
- **Complex Reasoning**: Multi-step problem solving

### ⚙️ System Tests
- **Commands**: help, model, stats, clear, quit
- **Edge Cases**: Empty input, long text, Unicode
- **Error Handling**: Network issues, invalid commands

## Testing Checklist

### Before Testing
- [ ] Ollama running (`ollama serve`)
- [ ] Models available (qwen2.5:3b, qwen2.5:7b, qwen3:14b)
- [ ] Clean memory directory or test with existing data
- [ ] Test log template ready

### During Testing
- [ ] Test all model sizes (3b, 7b, 14b)
- [ ] Verify memory accuracy 
- [ ] Check response quality
- [ ] Test command functionality
- [ ] Note UI/UX issues
- [ ] Test Ctrl+C shutdown

### After Testing
- [ ] Fill out test log
- [ ] Check memory files created correctly
- [ ] Verify token estimation working
- [ ] Document any bugs or improvements

## Memory File Inspection

Check generated memory files:
```bash
ls -la memory/
cat memory/qwen2.5_3b_*.json | jq .
```

## Performance Notes

- **3b models**: Fast, good for basic testing
- **7b models**: Balanced speed/quality  
- **14b models**: Slow but highest quality
- **Context limits**: ~4k tokens for smaller models, ~8k for larger

## Common Issues to Watch For

1. **Memory loss**: Information forgotten too quickly
2. **Context overflow**: Poor handling of long conversations  
3. **Token estimation**: Inaccurate context window management
4. **File corruption**: JSON parsing errors in memory files
5. **Model loading**: Failure to load or switch models
6. **UI issues**: Spacing, colors, shutdown problems

## Success Criteria

✅ **Memory System**
- Accurately recalls facts from earlier in conversation
- Handles context window limits gracefully
- Persists memory across app restarts
- Creates clean, readable memory files

✅ **User Experience**  
- Clean, minimal interface
- Proper spacing and colors
- Responsive model loading
- Smooth conversation flow

✅ **Reliability**
- No crashes or hangs
- Proper error handling
- Clean shutdown with Ctrl+C
- Works across different model sizes
