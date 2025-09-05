#!/usr/bin/env python3
"""
Simple Batch Test Runner for memAI

Executes test scenarios by spawning memAI process and feeding inputs.
"""

import subprocess
import time
import json
import sys
from pathlib import Path

def run_simple_test():
    """Run a simple focused test"""
    print("Starting simple memAI test...")
    
    # Test inputs
    test_inputs = [
        "3",  # Choose model 3 (qwen2.5:3b)
        "Hi, I'm Sarah and I work as a software engineer at Google",
        "I'm working on a machine learning project about image recognition", 
        "What's my name and job?",
        "What project am I working on?",
        "I live in San Francisco and work remotely",
        "Where do I live and what's my work setup?",
        "help",
        "stats", 
        "quit"
    ]
    
    try:
        # Start memAI process
        process = subprocess.Popen(
            ["python3", "memai.py"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd="/home/grandpaul/memAI_project/memAI"
        )
        
        print("memAI process started, feeding inputs...")
        
        # Send all inputs
        for i, input_text in enumerate(test_inputs):
            print(f"Sending input {i+1}: {input_text}")
            process.stdin.write(input_text + "\n")
            process.stdin.flush()
            time.sleep(2)  # Wait between inputs
        
        # Wait for completion
        print("Waiting for process to complete...")
        stdout, stderr = process.communicate(timeout=30)
        
        print("Test completed!")
        print(f"Return code: {process.returncode}")
        
        if stdout:
            print("STDOUT:")
            print(stdout)
        
        if stderr:
            print("STDERR:")
            print(stderr)
            
        return True
        
    except Exception as e:
        print(f"Test failed: {e}")
        if process:
            process.terminate()
        return False

def analyze_memory_after_test():
    """Analyze memory files created during test"""
    memory_dir = Path("/home/grandpaul/memAI_project/memAI/memory")
    
    if not memory_dir.exists():
        print("No memory directory found")
        return
    
    memory_files = list(memory_dir.glob("*.json"))
    print(f"Found {len(memory_files)} memory files:")
    
    for memory_file in memory_files:
        print(f"  {memory_file.name}")
        
        try:
            with open(memory_file, 'r') as f:
                data = json.load(f)
            
            exchanges = data.get("exchanges", [])
            print(f"    Exchanges: {len(exchanges)}")
            
            if exchanges:
                print(f"    First: {exchanges[0].get('user', 'N/A')[:50]}...")
                print(f"    Last: {exchanges[-1].get('user', 'N/A')[:50]}...")
                
        except Exception as e:
            print(f"    Error reading: {e}")

if __name__ == "__main__":
    print("memAI Simple Test Runner")
    print("=" * 30)
    
    success = run_simple_test()
    
    if success:
        print("\nAnalyzing memory files...")
        analyze_memory_after_test()
    else:
        print("Test failed!")
        
    print("\nTest complete!")
