#!/usr/bin/env python3
"""
memAI Test Runner - Execute Generated Scenarios

Simple test runner that executes the generated scenarios by creating
test input files that can be piped into memAI for systematic testing.
"""

import json
import time
import subprocess
import sys
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

class MemAITestRunner:
    """Execute automated tests against memAI"""
    
    def __init__(self):
        self.results = []
        
    def create_test_script(self, scenarios: List[Dict], model_choice: str = "3") -> str:
        """Create a test script that can be piped to memAI"""
        script_lines = [model_choice]  # Start with model selection
        
        for scenario in scenarios:
            script_lines.append(f"# Starting scenario: {scenario['id']}")
            
            # Add all inputs from the scenario
            for input_msg in scenario["inputs"]:
                if input_msg.strip():  # Skip empty inputs for now
                    script_lines.append(input_msg)
            
            # Add a separator
            script_lines.append("# Scenario complete")
        
        # End with quit command
        script_lines.append("quit")
        
        return "\n".join(script_lines)
    
    def run_batch_test(self, scenarios: List[Dict], batch_size: int = 10) -> Dict:
        """Run a batch of scenarios for testing"""
        print(f"Running batch test with {len(scenarios)} scenarios...")
        
        # Create test script
        test_script = self.create_test_script(scenarios)
        
        # Save test script
        script_file = f"test_batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(script_file, 'w', encoding='utf-8') as f:
            f.write(test_script)
        
        print(f"Test script saved to: {script_file}")
        print(f"To run manually: cat {script_file} | python3 memai.py")
        
        # Return batch info
        return {
            "script_file": script_file,
            "scenario_count": len(scenarios),
            "total_inputs": sum(len(s["inputs"]) for s in scenarios),
            "estimated_time_minutes": sum(len(s["inputs"]) for s in scenarios) / 60  # 1 second per input
        }
    
    def analyze_memory_file(self, model_name: str = "qwen2.5_3b") -> Dict:
        """Analyze the memory file created by memAI after testing"""
        memory_dir = Path("memory")
        memory_files = list(memory_dir.glob(f"{model_name}_*.json"))
        
        if not memory_files:
            return {"error": "No memory files found"}
        
        # Use the most recent memory file
        memory_file = max(memory_files, key=lambda x: x.stat().st_mtime)
        
        try:
            with open(memory_file, 'r', encoding='utf-8') as f:
                memory_data = json.load(f)
            
            exchanges = memory_data.get("exchanges", [])
            
            analysis = {
                "memory_file": str(memory_file),
                "total_exchanges": len(exchanges),
                "conversation_length": len(exchanges),
                "first_exchange": exchanges[0] if exchanges else None,
                "last_exchange": exchanges[-1] if exchanges else None,
                "metadata": memory_data.get("metadata", {}),
                "token_estimate": sum(len(ex.get("user", "")) + len(ex.get("assistant", "")) for ex in exchanges) // 3
            }
            
            return analysis
            
        except Exception as e:
            return {"error": f"Could not analyze memory file: {str(e)}"}

def load_scenarios(filename: str = "automated_test_scenarios.json") -> List[Dict]:
    """Load scenarios from JSON file"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data.get("scenarios", [])
    except FileNotFoundError:
        print(f"Scenario file {filename} not found. Run scenario_generator.py first.")
        return []
    except Exception as e:
        print(f"Error loading scenarios: {e}")
        return []

def main():
    """Main test execution"""
    print("memAI Automated Test Runner")
    print("=" * 40)
    
    # Load scenarios
    scenarios = load_scenarios()
    if not scenarios:
        print("No scenarios loaded. Exiting.")
        return
    
    print(f"Loaded {len(scenarios)} test scenarios")
    
    # Create test runner
    runner = MemAITestRunner()
    
    # Get user choices
    print("\nTest Options:")
    print("1. Quick test (first 10 scenarios)")
    print("2. Category test (50 scenarios)")
    print("3. Full test (all scenarios)")
    print("4. Custom batch size")
    
    choice = input("Choose option (1-4): ").strip()
    
    if choice == "1":
        test_scenarios = scenarios[:10]
    elif choice == "2":
        test_scenarios = scenarios[:50]
    elif choice == "3":
        test_scenarios = scenarios
    elif choice == "4":
        batch_size = int(input("Enter batch size: "))
        test_scenarios = scenarios[:batch_size]
    else:
        print("Invalid choice. Using quick test.")
        test_scenarios = scenarios[:10]
    
    # Run batch test
    batch_info = runner.run_batch_test(test_scenarios)
    
    print(f"\nBatch Test Created:")
    print(f"  Script file: {batch_info['script_file']}")
    print(f"  Scenarios: {batch_info['scenario_count']}")
    print(f"  Total inputs: {batch_info['total_inputs']}")
    print(f"  Estimated time: {batch_info['estimated_time_minutes']:.1f} minutes")
    
    print(f"\nTo execute the test:")
    print(f"  cat {batch_info['script_file']} | python3 memai.py")
    
    print(f"\nAfter running, analyze results with:")
    print(f"  python3 -c \"from test_runner import MemAITestRunner; r = MemAITestRunner(); print(r.analyze_memory_file())\"")

if __name__ == "__main__":
    main()
