#!/usr/bin/env python3
"""Test new document upload and retrieval"""

from memory.rag.indexer import TfidfIndex, DEFAULT_INDEX_PATH, DocMeta, clear_index_cache
from logged_in_bot.tools import handle_logged_in_turn
from datetime import datetime

def test_new_document():
    print("=" * 70)
    print("NEW DOCUMENT TEST")
    print("=" * 70)
    
    # 1. Add a new document
    print("1. Adding new document...")
    test_text = """
    PHYSICS 101 - Introduction to Physics
    
    Professor: Dr. Williams
    Email: williams@university.edu
    Office Hours: Wednesday 10-12 PM
    
    Course Topics:
    - Mechanics
    - Thermodynamics
    - Waves and Optics
    
    Grading:
    - Homework: 25%
    - Lab Reports: 25%
    - Midterm: 25%
    - Final: 25%
    """
    
    idx = TfidfIndex.load(DEFAULT_INDEX_PATH)
    doc_id = f"physics_101_{datetime.now().timestamp()}"
    meta = DocMeta(doc_id=doc_id, source="physics_101.txt", title="Physics 101 Syllabus")
    idx.add_text(doc_id, test_text, meta)
    idx.save(DEFAULT_INDEX_PATH)
    
    # Clear cache
    clear_index_cache(DEFAULT_INDEX_PATH)
    print("   Document added and cache cleared")
    
    # 2. Test chatbot
    print("\n2. Testing chatbot...")
    user = {"id": "physics_test", "name": "physics_test"}
    
    queries = [
        "What are Dr Williams office hours?",
        "Tell me about Physics 101",
        "What are the course topics?",
    ]
    
    for query in queries:
        print(f"\n   User: {query}")
        result = handle_logged_in_turn(query, [], user)
        reply = result['reply']
        
        if "williams" in reply.lower() or "physics" in reply.lower() or "mechanics" in reply.lower():
            print("   ✅ Found Physics 101")
        else:
            print("   ❌ Did not find Physics 101")
        
        print(f"   Bot: {reply[:100]}...")
    
    print(f"\n{'=' * 70}")
    print("✅ Test complete!")

if __name__ == "__main__":
    test_new_document()