#!/bin/bash
# memAI Build Script - Creates standalone executables

echo "🚀 Building memAI executables..."
echo ""

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf build/ dist/ *.spec

# Build Linux executable
echo "🐧 Building Linux executable (v1.1.0)..."
~/.local/bin/pyinstaller --onefile --name memAI-v1.1.0-linux-x64 memai.py

echo ""
echo "✅ Linux build complete!"
echo ""
echo "📦 Executable created:"
echo "  - dist/memAI-v1.1.0-linux-x64      (Linux standalone executable)"
echo ""
echo "🎯 Usage:"
echo "  ./dist/memAI-v1.1.0-linux-x64"
echo ""
echo "📁 File is standalone - no Python installation required!"
echo "💾 Size: ~8MB (includes Python runtime)"
echo ""
echo "🪟 For Windows:"
echo "  Windows executables must be built on Windows with:"
echo "  pip install pyinstaller"
echo "  pyinstaller --onefile --name memAI-windows.exe memai.py"
