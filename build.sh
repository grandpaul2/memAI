#!/bin/bash
# memAI Build Script - Creates standalone executables

echo "🚀 Building memAI executables..."
echo ""

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf build/ dist/ *.spec

# Build Linux executable
echo "🐧 Building Linux executable..."
~/.local/bin/pyinstaller --onefile --name memAI-linux memai.py

# Build Windows executable (cross-compile attempt)
echo "🪟 Building Windows executable..."
~/.local/bin/pyinstaller --onefile --name memAI-windows.exe memai.py

echo ""
echo "✅ Build complete!"
echo ""
echo "📦 Executables created:"
echo "  - dist/memAI-linux      (Linux standalone executable)"
echo "  - dist/memAI-windows.exe (Windows standalone executable)"
echo ""
echo "🎯 Usage:"
echo "  Linux:   ./dist/memAI-linux"
echo "  Windows: .\\dist\\memAI-windows.exe"
echo ""
echo "📁 Files are standalone - no Python installation required!"
echo "💾 Size: ~10-15MB each (includes Python runtime)"
