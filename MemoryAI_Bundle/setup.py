#!/usr/bin/env python3
"""
MemoryAI Setup Script

Quick setup and verification for MemoryAI.
"""

import sys
import os
import subprocess
import json
from pathlib import Path

def check_python_version():
    """Check Python version compatibility"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8+ required")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro}")
    return True

def check_ollama():
    """Check if Ollama is installed and running"""
    try:
        result = subprocess.run(['ollama', 'list'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            models = [line.split()[0] for line in result.stdout.strip().split('\n')[1:] 
                     if line.strip() and not line.startswith('NAME')]
            print(f"✅ Ollama running with {len(models)} models")
            if models:
                print(f"   Available models: {', '.join(models)}")
            return True, models
        else:
            print("❌ Ollama not responding")
            return False, []
    except FileNotFoundError:
        print("❌ Ollama not installed")
        return False, []

def install_dependencies():
    """Install Python dependencies"""
    try:
        print("📦 Installing dependencies...")
        result = subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'],
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Dependencies installed")
            return True
        else:
            print(f"❌ Failed to install dependencies: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error installing dependencies: {e}")
        return False

def setup_config():
    """Setup configuration if needed"""
    config_path = Path('config.json')
    if config_path.exists():
        print("✅ Configuration file exists")
        return True
    
    try:
        # Create default config
        default_config = {
            "default_model": "qwen2.5:3b",
            "verbose_output": False,
            "memory_settings": {
                "max_recent_exchanges": 50,
                "max_summarized_conversations": 20,
                "auto_summarize_threshold": 100
            },
            "ollama_settings": {
                "base_url": "http://localhost:11434",
                "timeout": 30,
                "context_window": 32768
            },
            "logging": {
                "level": "INFO",
                "file": "memoryai.log"
            }
        }
        
        with open(config_path, 'w') as f:
            json.dump(default_config, f, indent=4)
        
        print("✅ Configuration file created")
        return True
        
    except Exception as e:
        print(f"❌ Failed to create config: {e}")
        return False

def create_directories():
    """Create necessary directories"""
    dirs = ['memory', 'logs']
    for dir_name in dirs:
        os.makedirs(dir_name, exist_ok=True)
    print("✅ Directories created")

def run_system_test():
    """Run system test"""
    try:
        result = subprocess.run([sys.executable, 'test_system.py'],
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ System test passed")
            return True
        else:
            print(f"❌ System test failed:\n{result.stdout}\n{result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error running system test: {e}")
        return False

def main():
    """Main setup process"""
    print("🧠 MemoryAI Setup")
    print("=" * 30)
    
    # Check prerequisites
    if not check_python_version():
        sys.exit(1)
    
    ollama_ok, models = check_ollama()
    if not ollama_ok:
        print("\n⚠️  Please install Ollama first:")
        print("   curl -fsSL https://ollama.ai/install.sh | sh")
        print("   ollama pull qwen2.5:3b")
        sys.exit(1)
    
    # Setup process
    steps = [
        ("Installing dependencies", install_dependencies),
        ("Setting up configuration", setup_config),
        ("Creating directories", create_directories),
        ("Running system test", run_system_test)
    ]
    
    for step_name, step_func in steps:
        print(f"\n{step_name}...")
        if not step_func():
            print(f"❌ Setup failed at: {step_name}")
            sys.exit(1)
    
    print("\n🎉 MemoryAI setup complete!")
    print("\nTo start using MemoryAI:")
    print("  python memoryai.py")
    
    if models:
        print(f"\nRecommended model: {models[0] if 'qwen2.5:3b' not in models else 'qwen2.5:3b'}")

if __name__ == "__main__":
    main()
