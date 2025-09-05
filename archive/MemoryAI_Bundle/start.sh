#!/bin/bash
# MemoryAI Launch Script

echo "🧠 MemoryAI - AI Assistant with Advanced Memory"
echo "=============================================="

# Check if setup has been run
if [ ! -f "config.json" ]; then
    echo "⚠️  First time setup required..."
    python3 setup.py
    if [ $? -ne 0 ]; then
        echo "❌ Setup failed. Please check the errors above."
        exit 1
    fi
    echo ""
fi

echo "🚀 Starting MemoryAI..."
python3 memoryai.py
