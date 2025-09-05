#!/usr/bin/env python3
"""
Calculate conversation capacity for qwen2.5:3b model
"""

def calculate_conversation_capacity():
    """Calculate how many conversation exchanges qwen2.5:3b can handle"""
    
    # Model parameters
    model = "qwen2.5:3b"
    context_window = 4000  # tokens (conservative for 3b models)
    usable_context = int(context_window * 0.8)  # 20% buffer for system message + current input
    chars_per_token = 3.0
    
    print(f"Model: {model}")
    print(f"Total context window: {context_window:,} tokens")
    print(f"Usable context (80%): {usable_context:,} tokens")
    print(f"Token estimation: {chars_per_token} chars per token")
    print()
    
    # System message estimate
    system_message = "You are a helpful AI assistant. Be conversational and remember our previous discussions."
    system_tokens = len(system_message) // int(chars_per_token)
    
    print(f"System message tokens: ~{system_tokens}")
    print(f"Available for conversations: {usable_context - system_tokens:,} tokens")
    print()
    
    # Typical conversation exchange examples
    conversation_examples = [
        {
            "type": "Short exchange",
            "user": "Hi, I'm Sarah and I work as a software engineer at Google",
            "assistant": "Hi Sarah! Nice to meet you. Working as a software engineer at Google sounds exciting! What kind of projects do you work on?"
        },
        {
            "type": "Medium exchange", 
            "user": "I'm working on a machine learning project about image recognition using TensorFlow",
            "assistant": "That sounds like a fascinating project! Image recognition with TensorFlow is cutting-edge work. Are you focusing on any particular type of images, like medical scans, autonomous vehicle vision, or general object detection? What's been the most challenging aspect so far?"
        },
        {
            "type": "Long exchange",
            "user": "What's my name and job? Can you also tell me about the machine learning project I mentioned?",
            "assistant": "Your name is Sarah, and you work as a software engineer at Google. You mentioned that you're working on a machine learning project focused on image recognition using TensorFlow. This sounds like an exciting and technically challenging project that combines computer vision with deep learning. Image recognition is a rapidly evolving field with applications in everything from medical diagnosis to autonomous vehicles. Since you're using TensorFlow, you're working with one of the most powerful and widely-used machine learning frameworks. How has your experience been with the TensorFlow ecosystem so far?"
        }
    ]
    
    available_tokens = usable_context - system_tokens
    
    for example in conversation_examples:
        user_text = example["user"]
        assistant_text = example["assistant"]
        
        user_tokens = len(user_text) // int(chars_per_token)
        assistant_tokens = len(assistant_text) // int(chars_per_token)
        exchange_tokens = user_tokens + assistant_tokens
        
        max_exchanges = available_tokens // exchange_tokens
        
        print(f"{example['type']}:")
        print(f"  User: {len(user_text)} chars → ~{user_tokens} tokens")
        print(f"  Assistant: {len(assistant_text)} chars → ~{assistant_tokens} tokens")
        print(f"  Total per exchange: ~{exchange_tokens} tokens")
        print(f"  Max exchanges possible: ~{max_exchanges}")
        print(f"  Total conversation lines: ~{max_exchanges * 2} (user + assistant)")
        print()
    
    # Real-world estimate
    print("REALISTIC ESTIMATES:")
    print("="*50)
    
    # Average exchange based on testing data
    avg_user_message = 50  # characters
    avg_assistant_message = 200  # characters  
    avg_exchange_chars = avg_user_message + avg_assistant_message
    avg_exchange_tokens = avg_exchange_chars // int(chars_per_token)
    
    realistic_exchanges = available_tokens // avg_exchange_tokens
    
    print(f"Average user message: {avg_user_message} chars (~{avg_user_message//int(chars_per_token)} tokens)")
    print(f"Average assistant response: {avg_assistant_message} chars (~{avg_assistant_message//int(chars_per_token)} tokens)")
    print(f"Average exchange: {avg_exchange_chars} chars (~{avg_exchange_tokens} tokens)")
    print()
    print(f"🎯 REALISTIC CAPACITY for qwen2.5:3b:")
    print(f"   • ~{realistic_exchanges} conversation exchanges")
    print(f"   • ~{realistic_exchanges * 2} total conversation lines")
    print(f"   • Equivalent to {realistic_exchanges * 2 // 2} back-and-forth interactions")
    
    return realistic_exchanges

if __name__ == "__main__":
    calculate_conversation_capacity()
