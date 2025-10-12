#!/usr/bin/env python3
"""Test customer UI functions"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """Test that all imports work"""
    try:
        from customer_ui import login, logout, chat, get_docs_list, app_state
        print("✓ All imports successful")
        return True
    except Exception as e:
        print(f"✗ Import failed: {e}")
        return False

def test_login():
    """Test login function"""
    try:
        from customer_ui import login, app_state
        
        # Test empty name
        msg, success, user = login("")
        assert not success, "Empty login should fail"
        print("✓ Empty login correctly rejected")
        
        # Test valid name
        msg, success, user = login("Test User")
        assert success, "Valid login should succeed"
        assert app_state.username == "Test User"
        print("✓ Valid login successful")
        
        return True
    except Exception as e:
        print(f"✗ Login test failed: {e}")
        return False

def test_chat():
    """Test chat function"""
    try:
        from customer_ui import chat, login, app_state
        
        # Login first
        login("Test User")
        
        # Test empty message
        history, error = chat("", [])
        assert error == "", "Empty message should not error"
        print("✓ Empty message handled")
        
        # Test valid message
        history, error = chat("help", [])
        assert len(history) > 0, "Valid message should add to history"
        print("✓ Valid message processed")
        
        return True
    except Exception as e:
        print(f"✗ Chat test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("Testing Customer UI...")
    
    tests = [
        ("Imports", test_imports),
        ("Login", test_login),
        ("Chat", test_chat),
    ]
    
    passed = 0
    for name, test_func in tests:
        print(f"\n--- Testing {name} ---")
        if test_func():
            passed += 1
        else:
            print(f"❌ {name} test failed")
    
    print(f"\n--- Results ---")
    print(f"Passed: {passed}/{len(tests)}")
    
    if passed == len(tests):
        print("🎉 All tests passed!")
        return 0
    else:
        print("⚠️ Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())