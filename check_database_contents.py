#!/usr/bin/env python3
"""
Check what's inside the Supabase database and create test questions based on actual data
"""

import os
from supabase import create_client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

def check_database_contents():
    """Check what's currently in the database"""
    
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("❌ Error: SUPABASE_URL and SUPABASE_KEY must be set in .env file")
        return
    
    try:
        # Create Supabase client
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("✅ Connected to Supabase")
        
        # Get all records from chatbot_prompts table
        result = supabase.table('chatbot_prompts').select('*').execute()
        
        if not result.data:
            print("❌ No data found in chatbot_prompts table")
            return
        
        print(f"📊 Found {len(result.data)} records in the database")
        print("=" * 80)
        
        # Categorize the data
        categories = {
            'greetings': [],
            'school_info': [],
            'staff_info': [],
            'financial': [],
            'location': [],
            'makeup': [],
            'general': []
        }
        
        for item in result.data:
            keywords = item.get('keywords', '').lower()
            response = item.get('response', '')
            
            # Categorize based on keywords
            if any(word in keywords for word in ['hello', 'hi', 'kumusta', 'good morning', 'good afternoon']):
                categories['greetings'].append(item)
            elif any(word in keywords for word in ['head teacher', 'principal', 'teacher', 'staff', 'adviser']):
                categories['staff_info'].append(item)
            elif any(word in keywords for word in ['fee', 'tuition', 'cost', 'price', 'payment']):
                categories['financial'].append(item)
            elif any(word in keywords for word in ['address', 'location', 'where', 'hours', 'store']):
                categories['location'].append(item)
            elif any(word in keywords for word in ['makeup', 'cosmetic', 'lipstick', 'foundation', 'mascara', 'eyeshadow']):
                categories['makeup'].append(item)
            elif any(word in keywords for word in ['school', 'grade', 'enrollment', 'student']):
                categories['school_info'].append(item)
            else:
                categories['general'].append(item)
        
        # Display categorized data
        for category, items in categories.items():
            if items:
                print(f"\n📁 {category.upper()} ({len(items)} items):")
                print("-" * 50)
                for item in items[:5]:  # Show first 5 items
                    keywords = item.get('keywords', 'No keywords')
                    response = item.get('response', 'No response')
                    print(f"Q: {keywords}")
                    print(f"A: {response[:100]}...")
                    print()
                if len(items) > 5:
                    print(f"... and {len(items) - 5} more items")
        
        # Generate test questions based on actual data
        print("\n" + "=" * 80)
        print("🧪 GENERATED TEST QUESTIONS BASED ON DATABASE:")
        print("=" * 80)
        
        generate_test_questions(result.data)
        
    except Exception as e:
        print(f"❌ Error: {e}")

def generate_test_questions(data):
    """Generate test questions based on actual database content"""
    
    test_questions = []
    
    for item in data:
        keywords = item.get('keywords', '')
        response = item.get('response', '')
        
        # Create variations of the original question
        if keywords:
            # Direct question
            test_questions.append({
                'question': keywords,
                'expected_response': response[:100] + "..." if len(response) > 100 else response,
                'category': 'direct'
            })
            
            # Create variations
            if 'head teacher' in keywords.lower():
                test_questions.append({
                    'question': 'Who is the head teacher?',
                    'expected_response': response[:100] + "..." if len(response) > 100 else response,
                    'category': 'variation'
                })
                test_questions.append({
                    'question': 'Sino ang head teacher?',
                    'expected_response': response[:100] + "..." if len(response) > 100 else response,
                    'category': 'tagalog'
                })
            
            elif 'fee' in keywords.lower() or 'tuition' in keywords.lower():
                test_questions.append({
                    'question': 'How much are the school fees?',
                    'expected_response': response[:100] + "..." if len(response) > 100 else response,
                    'category': 'variation'
                })
                test_questions.append({
                    'question': 'Magkano ang tuition?',
                    'expected_response': response[:100] + "..." if len(response) > 100 else response,
                    'category': 'tagalog'
                })
            
            elif 'address' in keywords.lower() or 'location' in keywords.lower():
                test_questions.append({
                    'question': 'Where is the school located?',
                    'expected_response': response[:100] + "..." if len(response) > 100 else response,
                    'category': 'variation'
                })
                test_questions.append({
                    'question': 'Saan ang paaralan?',
                    'expected_response': response[:100] + "..." if len(response) > 100 else response,
                    'category': 'tagalog'
                })
            
            elif 'makeup' in keywords.lower() or 'cosmetic' in keywords.lower():
                test_questions.append({
                    'question': 'What makeup products do you have?',
                    'expected_response': response[:100] + "..." if len(response) > 100 else response,
                    'category': 'variation'
                })
    
    # Display test questions
    categories = {}
    for q in test_questions:
        cat = q['category']
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(q)
    
    for category, questions in categories.items():
        print(f"\n📝 {category.upper()} TEST QUESTIONS:")
        print("-" * 40)
        for i, q in enumerate(questions[:10], 1):  # Show first 10
            print(f"{i}. Q: {q['question']}")
            print(f"   Expected: {q['expected_response']}")
            print()
    
    # Save test questions to file
    save_test_questions_to_file(test_questions)

def save_test_questions_to_file(test_questions):
    """Save test questions to a file for easy testing"""
    
    with open('database_based_test_questions.py', 'w', encoding='utf-8') as f:
        f.write('#!/usr/bin/env python3\n')
        f.write('"""\n')
        f.write('Test questions generated from actual database content\n')
        f.write('"""\n\n')
        f.write('TEST_QUESTIONS = [\n')
        
        for q in test_questions:
            f.write(f'    {{\n')
            f.write(f'        "question": "{q["question"]}",\n')
            f.write(f'        "category": "{q["category"]}",\n')
            f.write(f'        "expected_keywords": ["{q["question"].split()[0].lower()}", "database"]\n')
            f.write(f'    }},\n')
        
        f.write(']\n\n')
        f.write('def get_test_questions():\n')
        f.write('    """Return all test questions"""\n')
        f.write('    return TEST_QUESTIONS\n\n')
        f.write('def get_questions_by_category(category):\n')
        f.write('    """Return questions filtered by category"""\n')
        f.write('    return [q for q in TEST_QUESTIONS if q["category"] == category]\n')
    
    print(f"\n💾 Test questions saved to: database_based_test_questions.py")
    print(f"📊 Total test questions generated: {len(test_questions)}")

if __name__ == "__main__":
    print("🔍 Checking Supabase Database Contents")
    print("=" * 50)
    check_database_contents()
