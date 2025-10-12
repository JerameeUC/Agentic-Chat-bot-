#!/usr/bin/env python3
"""
Test Gemini API integration
"""
import os
from agenticcore.providers_unified import generate_text, analyze_sentiment

def test_gemini():
    # Check if Gemini API key is set
    if not os.getenv("GEMINI_API_KEY"):
        print("❌ GEMINI_API_KEY not set. Please set it to test Gemini integration.")
        print("Get your API key from: https://aistudio.google.com/app/apikey")
        return
    
    print("🧪 Testing Gemini API integration...")
    
    # Test text generation
    print("\n1. Testing text generation:")
    result = generate_text("What is the capital of France?", max_tokens=50)
    print(f"Provider: {result.get('provider')}")
    print(f"Response: {result.get('text', 'No response')}")
    
    # Test sentiment analysis
    print("\n2. Testing sentiment analysis:")
    result = analyze_sentiment("I love this chatbot! It's amazing!")
    print(f"Provider: {result.get('provider')}")
    print(f"Sentiment: {result.get('label')} (score: {result.get('score')})")
    
    print("\n✅ Gemini integration test complete!")

if __name__ == "__main__":
    test_gemini()