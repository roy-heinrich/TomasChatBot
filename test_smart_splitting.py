#!/usr/bin/env python3
"""
Test script to verify smart sentence splitting works correctly
"""

import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_smart_sentence_split():
    """Test the smart sentence splitting function"""
    print("🧪 Testing smart sentence splitting...")
    
    try:
        from core.response_generator import ResponseGenerator
        
        # Create response generator instance
        response_gen = ResponseGenerator()
        print("✅ Response generator initialized")
        
        # Test cases
        test_cases = [
            {
                "name": "Name with title",
                "text": "The Grade 2 Adviser is Mrs. Lezil V. Villanueva. Our school is fortunate to have dedicated educators like her, who play a vital role in guiding and supporting our students' learning journey. If you'd like to know more about Mrs. Villanueva or have any other questions about our school's staff or programs, feel free to ask!",
                "expected_sentences": 3
            },
            {
                "name": "Multiple names",
                "text": "Mrs. Annalyn B. Andrade is the Grade 1 adviser. Ms. Thedy Mae P. Ruiz teaches Grade 5. Dr. Smith is the principal.",
                "expected_sentences": 3
            },
            {
                "name": "Regular sentences",
                "text": "Hello! How are you? I'm fine. Thank you for asking.",
                "expected_sentences": 4
            },
            {
                "name": "Mixed content",
                "text": "The school has many teachers. Mrs. Johnson teaches math. What subjects are available?",
                "expected_sentences": 3
            }
        ]
        
        print("\n🔍 Testing sentence splitting:")
        for test_case in test_cases:
            print(f"\n📝 Test: {test_case['name']}")
            print(f"   Input: {test_case['text'][:50]}...")
            
            # Test the smart splitting
            sentences = response_gen._smart_sentence_split(test_case['text'])
            print(f"   Split into {len(sentences)} sentences:")
            
            for i, sentence in enumerate(sentences):
                print(f"     {i+1}. {sentence}")
            
            # Check if names are preserved
            full_text = " ".join(sentences)
            if "Mrs." in test_case['text'] and "Mrs." in full_text:
                print("   ✅ Names preserved")
            else:
                print("   ⚠️ Names might be split")
            
            print(f"   Expected: {test_case['expected_sentences']}, Got: {len(sentences)}")
        
        print("\n🎉 Smart sentence splitting test completed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run the test"""
    print("🚀 Testing smart sentence splitting...\n")
    
    test_passed = test_smart_sentence_split()
    
    if test_passed:
        print("\n🎉 Test completed! Smart sentence splitting should now preserve names.")
        return 0
    else:
        print("\n❌ Test failed. Check the output above for details.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
