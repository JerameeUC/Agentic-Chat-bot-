#!/usr/bin/env python3
"""
Graduation Store Demo - Interactive chatbot for graduation products and rules
"""

from logged_in_bot import handle_logged_in_turn

def demo():
    user = {'id': 'demo_student', 'name': 'Demo Student'}
    
    print("\n" + "="*70)
    print("🎓 GRADUATION STORE CHATBOT DEMO")
    print("="*70)
    print("\nAsk me about:")
    print("  • Products (cap & gown, parking passes)")
    print("  • Parking rules")
    print("  • Dress code")
    print("  • FAQs")
    print("\nType 'quit' to exit\n")
    
    history = []
    
    while True:
        try:
            question = input("You: ").strip()
            if not question:
                continue
            if question.lower() in ['quit', 'exit', 'q']:
                print("\n👋 Thanks for using the Graduation Store Chatbot!")
                break
            
            response = handle_logged_in_turn(question, history, user)
            reply = response['reply']
            
            print(f"\nBot: {reply}\n")
            
            history.append([question, reply])
            
        except KeyboardInterrupt:
            print("\n\n👋 Thanks for using the Graduation Store Chatbot!")
            break
        except Exception as e:
            print(f"\n⚠ Error: {e}\n")

if __name__ == "__main__":
    demo()
