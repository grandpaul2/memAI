# memAI v1.1.0 Release Notes

## 🚀 What's New in v1.1.0

### Enhanced Chat Interface
- **Arrow Key Navigation**: Full cursor movement support within chat input
- **Command History**: Navigate through previous messages with up/down arrows
- **Persistent History**: Chat history saved across sessions in `~/.memai_history`
- **Input Editing**: Edit and modify messages before sending

### Smart Connection Management  
- **Auto Port Detection**: Automatically handles Ollama connection issues
- **Custom Port Support**: Enter custom ports when default fails
- **Port Persistence**: Automatically saves working ports to source code
- **Friendly Prompts**: Clear instructions for connection troubleshooting

### Improved User Experience
- **Text Wrapping**: Smart word-boundary wrapping prevents text overflow
- **Better Readability**: 78-character width for optimal terminal display
- **Version Command**: New `version` command to check current release
- **Updated Branding**: Refined to "Local model interface with chat memory"

## 🛠️ Technical Improvements

### Code Quality
- Added `readline` module for enhanced terminal input handling
- Graceful fallback for systems without readline support
- Version tracking with `__version__ = "1.1.0"` variable
- Improved error handling and user feedback

### Build System
- Updated build script with versioned executable naming
- Created `memAI-v1.1.0-linux-x64` standalone executable
- 8.2MB self-contained binary with Python runtime included

## 📦 Downloads

### Linux
- **memAI-v1.1.0-linux-x64** (8.2MB)
  - Standalone executable for Linux x64 systems
  - No Python installation required
  - Usage: `./memAI-v1.1.0-linux-x64`

## 🔧 Commands

All previous commands plus:
- `version` - Display current memAI version
- `help` - Updated help with version command
- Arrow keys for input navigation and history
- Tab completion (foundation for future enhancements)

## 🚀 Upgrade Instructions

1. Download the new `memAI-v1.1.0-linux-x64` executable
2. Make executable: `chmod +x memAI-v1.1.0-linux-x64`
3. Run: `./memAI-v1.1.0-linux-x64`
4. Enjoy enhanced chat experience with arrow key support!

## 🔄 Compatibility

- **Requirements**: Linux x64 systems
- **Dependencies**: None (standalone executable)
- **Ollama**: Compatible with all Ollama versions
- **Models**: Works with any Ollama-compatible model

## 🐛 Bug Fixes

- Fixed word splitting in long chat responses
- Improved connection error handling
- Better terminal input handling across different systems
- More robust port configuration process

---

**Full Changelog**: [v1.0.0...v1.1.0](https://github.com/grandpaul2/memAI/compare/v1.0.0...v1.1.0)
