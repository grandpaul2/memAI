#!/usr/bin/env python3
"""
MemoryAI System Test

Quick test to verify the memory system is working correctly.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.memory_integration import UnifiedMemoryInterface
from src.simple_config import Config
import json

def test_memory_system():
    """Test basic memory system functionality"""
    print("🧪 Testing MemoryAI Memory System")
    print("=" * 40)
    
    try:
        # Initialize components
        config = Config()
        memory = UnifiedMemoryInterface(config.config)
        test_model = "test-model"
        
        print("✅ Memory system initialized")
        
        # Test adding messages
        memory.add_message("user", "Hello, my name is TestUser", test_model)
        memory.add_message("assistant", "Hello TestUser! Nice to meet you.", test_model)
        
        print("✅ Messages added to memory")
        
        # Test getting context
        context = memory.get_context_messages(
            model=test_model,
            user_input="What's my name?",
            interaction_mode="chat"
        )
        
        print(f"✅ Context retrieved: {len(context)} messages")
        
        # Test memory stats
        stats = memory.get_memory_stats()
        print(f"✅ Memory stats: {json.dumps(stats, indent=2)}")
        
        # Test models with memory
        models = memory.unified_manager.get_models_with_memory()
        print(f"✅ Models with memory: {models}")
        
        # Cleanup test data
        memory.unified_manager.clear_conversation(test_model)
        print("✅ Test data cleaned up")
        
        print("\n🎉 All memory system tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Memory system test failed: {e}")
        return False

def test_config_system():
    """Test configuration system"""
    print("\n🧪 Testing Configuration System")
    print("=" * 40)
    
    try:
        config = Config()
        print(f"✅ Default model: {config.get('default_model')}")
        print(f"✅ Memory settings: {config.get('memory_settings')}")
        print(f"✅ Ollama settings: {config.get('ollama_settings')}")
        
        print("✅ Configuration system working")
        return True
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧠 MemoryAI System Tests")
    print("=" * 50)
    
    tests_passed = 0
    total_tests = 2
    
    if test_config_system():
        tests_passed += 1
        
    if test_memory_system():
        tests_passed += 1
    
    print(f"\n📊 Test Results: {tests_passed}/{total_tests} passed")
    
    if tests_passed == total_tests:
        print("🎉 All systems operational! MemoryAI is ready to use.")
        return True
    else:
        print("❌ Some tests failed. Check your setup.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
