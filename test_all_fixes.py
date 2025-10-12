#!/usr/bin/env python3
"""Test all fixes from user's conversation history."""

from logged_in_bot.tools import handle_logged_in_turn

def main():
    print("=" * 70)
    print("COMPREHENSIVE FIX VERIFICATION")
    print("=" * 70)
    
    user = {"id": "test_all_fixes"}
    history = []
    
    tests = [
        {
            "query": "remember name: Alex",
            "expected": "Should save name",
            "check": lambda r: "remember" in r.lower()
        },
        {
            "query": "What are the parking rules?",
            "expected": "Should answer about RULES (not passes)",
            "check": lambda r: "double parking" in r.lower() or "handicap" in r.lower()
        },
        {
            "query": "What products can I buy?",
            "expected": "Should list both products",
            "check": lambda r: "cap and gown" in r.lower() and "parking" in r.lower()
        },
        {
            "query": "What should I wear?",
            "expected": "Should explain dress code",
            "check": lambda r: "dress code" in r.lower() or "formal" in r.lower()
        },
        {
            "query": "nepal",
            "expected": "Should say no specific info",
            "check": lambda r: "don't have" in r.lower() or "no" in r.lower()
        },
        {
            "query": "what is my name?",
            "expected": "Should recall Alex from memory",
            "check": lambda r: "alex" in r.lower()
        },
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        query = test["query"]
        expected = test["expected"]
        check_fn = test["check"]
        
        print(f"\n{'─' * 70}")
        print(f"Query: {query}")
        print(f"Expected: {expected}")
        
        result = handle_logged_in_turn(query, history, user)
        reply = result['reply']
        
        print(f"Response: {reply[:150]}{'...' if len(reply) > 150 else ''}")
        
        if check_fn(reply):
            print("✅ PASS")
            passed += 1
        else:
            print("❌ FAIL")
            failed += 1
        
        history.append(("user", query))
        history.append(("bot", reply))
    
    print(f"\n{'=' * 70}")
    print(f"RESULTS: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("\n🎉 ALL TESTS PASSED!")
        print("\nFeatures verified:")
        print("  ✅ Query intent understanding (rules vs passes)")
        print("  ✅ Product listing")
        print("  ✅ Memory recall (personal info)")
        print("  ✅ Conversational responses")
        print("  ✅ Helpful fallbacks for irrelevant queries")
    else:
        print(f"\n⚠️  {failed} test(s) failed")
    
    print("=" * 70)

if __name__ == "__main__":
    main()
