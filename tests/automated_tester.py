#!/usr/bin/env python3
"""
memAI Automated Testing System - Hundreds of Real-world Scenarios

This system automatically tests memAI with hundreds of realistic conversation
scenarios to validate memory, context handling, and system reliability.
"""

import json
import time
import subprocess
import sys
import signal
import threading
import queue
import random
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

class AutomatedTester:
    """Automated testing system for memAI"""
    
    def __init__(self):
        self.test_results = []
        self.current_session = None
        self.process = None
        self.input_queue = queue.Queue()
        self.output_buffer = []
        self.running = False
        
    def create_realistic_scenarios(self) -> List[Dict]:
        """Generate hundreds of realistic conversation scenarios"""
        scenarios = []
        
        # 1. PROFESSIONAL SCENARIOS (50 scenarios)
        professional_contexts = [
            "software engineer", "data scientist", "product manager", "designer", 
            "marketing manager", "sales director", "consultant", "teacher", 
            "doctor", "lawyer", "accountant", "researcher"
        ]
        
        professional_tasks = [
            "debugging code", "analyzing data", "planning project", "designing interface",
            "creating campaign", "closing deals", "solving problems", "teaching students",
            "treating patients", "reviewing contracts", "preparing reports", "conducting research"
        ]
        
        for i, (context, task) in enumerate(zip(professional_contexts, professional_tasks)):
            scenarios.append({
                "id": f"prof_{i+1:03d}",
                "category": "professional",
                "description": f"Professional {context} discussing {task}",
                "conversation": [
                    f"Hi, I'm a {context} and I'm currently {task}",
                    f"What's the best approach for {task}?",
                    f"I tried your suggestion and it worked well",
                    f"Can you remind me what my role is again?",
                    f"What was I working on when we started talking?"
                ],
                "memory_tests": [
                    {"query": "What's my job?", "expected": context},
                    {"query": "What am I working on?", "expected": task}
                ]
            })
        
        # 2. TECHNICAL SCENARIOS (100 scenarios)
        programming_languages = ["Python", "JavaScript", "Java", "C++", "Go", "Rust", "TypeScript"]
        frameworks = ["React", "Django", "Spring", "Express", "Flask", "Vue", "Angular"]
        problems = ["memory leak", "performance issue", "database error", "API timeout", 
                   "security vulnerability", "deployment failure", "testing issue"]
        
        for i in range(100):
            lang = random.choice(programming_languages)
            framework = random.choice(frameworks)
            problem = random.choice(problems)
            
            scenarios.append({
                "id": f"tech_{i+1:03d}",
                "category": "technical",
                "description": f"Technical discussion about {lang} {framework} {problem}",
                "conversation": [
                    f"I'm having a {problem} in my {lang} application using {framework}",
                    f"The error occurs when I try to process large datasets",
                    f"Here's the stack trace: Error in {framework} module line 245",
                    f"What language and framework am I using?",
                    f"What type of problem am I experiencing?"
                ],
                "memory_tests": [
                    {"query": "What programming language?", "expected": lang},
                    {"query": "What framework?", "expected": framework},
                    {"query": "What's the problem?", "expected": problem}
                ]
            })
        
        # 3. PERSONAL SCENARIOS (75 scenarios)
        hobbies = ["photography", "cooking", "hiking", "reading", "gaming", "music", "painting"]
        locations = ["San Francisco", "New York", "London", "Tokyo", "Berlin", "Sydney", "Toronto"]
        goals = ["learning Spanish", "getting fit", "changing careers", "buying a house", 
                "starting a business", "writing a book", "traveling more"]
        
        for i in range(75):
            hobby = random.choice(hobbies)
            location = random.choice(locations)
            goal = random.choice(goals)
            
            scenarios.append({
                "id": f"personal_{i+1:03d}",
                "category": "personal",
                "description": f"Personal conversation about {hobby} in {location}",
                "conversation": [
                    f"I live in {location} and I'm passionate about {hobby}",
                    f"My main goal this year is {goal}",
                    f"I've been working on this goal for about 3 months now",
                    f"Where did I say I live?",
                    f"What's my main hobby and yearly goal?"
                ],
                "memory_tests": [
                    {"query": "Where do I live?", "expected": location},
                    {"query": "What's my hobby?", "expected": hobby},
                    {"query": "What's my goal?", "expected": goal}
                ]
            })
        
        # 4. EDUCATIONAL SCENARIOS (50 scenarios)
        subjects = ["mathematics", "physics", "chemistry", "biology", "history", "literature"]
        levels = ["high school", "college", "graduate", "postgraduate"]
        topics = ["calculus", "quantum mechanics", "organic chemistry", "genetics", 
                 "world war", "shakespeare", "statistics", "thermodynamics"]
        
        for i in range(50):
            subject = random.choice(subjects)
            level = random.choice(levels)
            topic = random.choice(topics)
            
            scenarios.append({
                "id": f"edu_{i+1:03d}",
                "category": "educational",
                "description": f"Educational discussion about {subject} at {level} level",
                "conversation": [
                    f"I'm studying {subject} at the {level} level",
                    f"I'm particularly interested in {topic}",
                    f"Can you explain the basics of {topic}?",
                    f"What subject am I studying?",
                    f"What specific topic interests me most?"
                ],
                "memory_tests": [
                    {"query": "What subject?", "expected": subject},
                    {"query": "What level?", "expected": level},
                    {"query": "What topic?", "expected": topic}
                ]
            })
        
        # 5. CONTEXT SWITCHING SCENARIOS (50 scenarios)
        for i in range(50):
            topic_a = random.choice(["cooking", "programming", "travel", "fitness", "music"])
            topic_b = random.choice(["work", "family", "hobbies", "education", "health"])
            detail_a = f"detail about {topic_a} {i}"
            detail_b = f"detail about {topic_b} {i}"
            
            scenarios.append({
                "id": f"switch_{i+1:03d}",
                "category": "context_switching",
                "description": f"Context switching between {topic_a} and {topic_b}",
                "conversation": [
                    f"Let's talk about {topic_a}. Specifically, {detail_a}",
                    f"Actually, let's switch topics to {topic_b}",
                    f"For {topic_b}, I want to focus on {detail_b}",
                    f"Going back to our first topic, what were we discussing?",
                    f"And what was the detail I mentioned about it?"
                ],
                "memory_tests": [
                    {"query": "First topic?", "expected": topic_a},
                    {"query": "Second topic?", "expected": topic_b},
                    {"query": "Detail about first topic?", "expected": detail_a}
                ]
            })
        
        # 6. LONG CONVERSATION SCENARIOS (25 scenarios)
        for i in range(25):
            base_topic = random.choice(["project planning", "data analysis", "system design", "research"])
            
            conversation = [f"I'm working on a complex {base_topic} project"]
            # Add 20 messages to test context window
            for msg_num in range(1, 21):
                conversation.append(f"Step {msg_num}: This involves {base_topic} aspect {msg_num} with details about component {msg_num}")
            
            conversation.extend([
                "What was the main topic we started with?",
                "What was step 5 about?",
                "Can you summarize our discussion?"
            ])
            
            scenarios.append({
                "id": f"long_{i+1:03d}",
                "category": "long_conversation",
                "description": f"Long conversation testing context window with {base_topic}",
                "conversation": conversation,
                "memory_tests": [
                    {"query": "What's the main topic?", "expected": base_topic},
                    {"query": "How many steps did we discuss?", "expected": "20"}
                ]
            })
        
        # 7. EDGE CASE SCENARIOS (25 scenarios)
        edge_cases = [
            {"input": "", "description": "empty input"},
            {"input": "   ", "description": "whitespace only"},
            {"input": "a" * 1000, "description": "very long input"},
            {"input": "🚀🤖🎉 Unicode: café naïve résumé", "description": "unicode characters"},
            {"input": "Special chars: @#$%^&*()_+-=[]{}|;:,.<>?", "description": "special characters"}
        ]
        
        for i in range(25):
            edge = edge_cases[i % len(edge_cases)]
            scenarios.append({
                "id": f"edge_{i+1:03d}",
                "category": "edge_cases",
                "description": f"Edge case: {edge['description']}",
                "conversation": [
                    "Let's test edge cases",
                    edge["input"],
                    "Did you handle that input correctly?",
                    "What was the previous input I sent?"
                ],
                "memory_tests": [
                    {"query": "Previous input?", "expected": edge["input"] if edge["input"].strip() else "empty or whitespace"}
                ]
            })
        
        # 8. COMMAND TESTING SCENARIOS (25 scenarios)
        commands = ["help", "model", "stats", "clear"]
        for i in range(25):
            cmd = commands[i % len(commands)]
            scenarios.append({
                "id": f"cmd_{i+1:03d}",
                "category": "commands",
                "description": f"Testing {cmd} command",
                "conversation": [
                    "Let's test some commands",
                    f"I'll use the {cmd} command now",
                    cmd,
                    f"Did the {cmd} command work correctly?"
                ],
                "memory_tests": [
                    {"query": f"What command did I test?", "expected": cmd}
                ]
            })
        
        print(f"Generated {len(scenarios)} test scenarios across {len(set(s['category'] for s in scenarios))} categories")
        return scenarios
    
    def run_automated_test(self, scenario: Dict) -> Dict:
        """Run a single automated test scenario"""
        print(f"Running scenario {scenario['id']}: {scenario['description']}")
        
        result = {
            "scenario_id": scenario["id"],
            "category": scenario["category"],
            "description": scenario["description"],
            "timestamp": datetime.now().isoformat(),
            "status": "running",
            "responses": [],
            "memory_test_results": [],
            "errors": [],
            "performance": {}
        }
        
        start_time = time.time()
        
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
            
            # Select model (use model 3 - fastest for testing)
            process.stdin.write("3\n")
            process.stdin.flush()
            time.sleep(2)
            
            # Run conversation
            for msg in scenario["conversation"]:
                process.stdin.write(f"{msg}\n")
                process.stdin.flush()
                time.sleep(1)  # Wait for response
                
                # Try to read response (non-blocking)
                try:
                    response = process.stdout.readline()
                    result["responses"].append({
                        "input": msg,
                        "response": response.strip(),
                        "timestamp": time.time() - start_time
                    })
                except:
                    result["responses"].append({
                        "input": msg,
                        "response": "ERROR: Could not read response",
                        "timestamp": time.time() - start_time
                    })
            
            # Test memory
            for memory_test in scenario.get("memory_tests", []):
                process.stdin.write(f"{memory_test['query']}\n")
                process.stdin.flush()
                time.sleep(1)
                
                try:
                    response = process.stdout.readline()
                    contains_expected = memory_test["expected"].lower() in response.lower()
                    result["memory_test_results"].append({
                        "query": memory_test["query"],
                        "expected": memory_test["expected"],
                        "response": response.strip(),
                        "passed": contains_expected
                    })
                except:
                    result["memory_test_results"].append({
                        "query": memory_test["query"],
                        "expected": memory_test["expected"],
                        "response": "ERROR: Could not test memory",
                        "passed": False
                    })
            
            # Clean shutdown
            process.stdin.write("quit\n")
            process.stdin.flush()
            process.wait(timeout=5)
            
            result["status"] = "completed"
            result["performance"]["total_time"] = time.time() - start_time
            result["performance"]["messages_per_second"] = len(scenario["conversation"]) / (time.time() - start_time)
            
        except Exception as e:
            result["status"] = "error"
            result["errors"].append(str(e))
            if process:
                process.terminate()
        
        return result
    
    def run_full_test_suite(self):
        """Run the complete automated test suite"""
        print("Starting comprehensive automated testing...")
        scenarios = self.create_realistic_scenarios()
        
        results = {
            "test_session": {
                "start_time": datetime.now().isoformat(),
                "total_scenarios": len(scenarios),
                "categories": list(set(s["category"] for s in scenarios))
            },
            "results": []
        }
        
        for i, scenario in enumerate(scenarios):
            print(f"\nProgress: {i+1}/{len(scenarios)} ({(i+1)/len(scenarios)*100:.1f}%)")
            result = self.run_automated_test(scenario)
            results["results"].append(result)
            
            # Save intermediate results every 10 tests
            if (i + 1) % 10 == 0:
                self.save_results(results, f"test_results_partial_{i+1}.json")
        
        results["test_session"]["end_time"] = datetime.now().isoformat()
        results["test_session"]["duration"] = time.time() - time.mktime(time.strptime(results["test_session"]["start_time"], "%Y-%m-%dT%H:%M:%S.%f"))
        
        # Generate summary
        summary = self.generate_summary(results)
        results["summary"] = summary
        
        # Save final results
        self.save_results(results, "test_results_complete.json")
        self.print_summary(summary)
        
        return results
    
    def save_results(self, results: Dict, filename: str):
        """Save test results to file"""
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"Results saved to {filename}")
    
    def generate_summary(self, results: Dict) -> Dict:
        """Generate test summary statistics"""
        total_tests = len(results["results"])
        completed = sum(1 for r in results["results"] if r["status"] == "completed")
        errors = sum(1 for r in results["results"] if r["status"] == "error")
        
        # Memory test statistics
        memory_tests = []
        for result in results["results"]:
            memory_tests.extend(result["memory_test_results"])
        
        memory_passed = sum(1 for t in memory_tests if t["passed"])
        memory_total = len(memory_tests)
        
        # Category statistics
        category_stats = {}
        for result in results["results"]:
            cat = result["category"]
            if cat not in category_stats:
                category_stats[cat] = {"total": 0, "completed": 0, "errors": 0}
            category_stats[cat]["total"] += 1
            if result["status"] == "completed":
                category_stats[cat]["completed"] += 1
            elif result["status"] == "error":
                category_stats[cat]["errors"] += 1
        
        return {
            "total_scenarios": total_tests,
            "completed": completed,
            "errors": errors,
            "completion_rate": completed / total_tests * 100 if total_tests > 0 else 0,
            "memory_tests": {
                "total": memory_total,
                "passed": memory_passed,
                "success_rate": memory_passed / memory_total * 100 if memory_total > 0 else 0
            },
            "category_breakdown": category_stats
        }
    
    def print_summary(self, summary: Dict):
        """Print test summary"""
        print("\n" + "="*60)
        print("AUTOMATED TEST SUMMARY")
        print("="*60)
        print(f"Total Scenarios: {summary['total_scenarios']}")
        print(f"Completed: {summary['completed']} ({summary['completion_rate']:.1f}%)")
        print(f"Errors: {summary['errors']}")
        print(f"\nMemory Tests:")
        print(f"  Total: {summary['memory_tests']['total']}")
        print(f"  Passed: {summary['memory_tests']['passed']}")
        print(f"  Success Rate: {summary['memory_tests']['success_rate']:.1f}%")
        print(f"\nCategory Breakdown:")
        for category, stats in summary['category_breakdown'].items():
            print(f"  {category}: {stats['completed']}/{stats['total']} completed")


if __name__ == "__main__":
    tester = AutomatedTester()
    tester.run_full_test_suite()
