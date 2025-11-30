"""
Language Bug Fix - Testing Script
Tests English/Tagalog/Aklanon language detection and response generation
"""

import asyncio
import json
from typing import Dict, List, Tuple
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from chatbot_refactored import ChatBot
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class LanguageTestSuite:
    """Comprehensive language detection and response testing"""
    
    def __init__(self):
        """Initialize the test suite"""
        groq_key = os.getenv("GROQ_API_KEY")
        if not groq_key:
            raise ValueError("GROQ_API_KEY not set in environment variables")
        
        self.chatbot = ChatBot(groq_key)
        self.test_results = []
        self.passed = 0
        self.failed = 0
    
    async def test_query(
        self, 
        query: str, 
        expected_language: str,
        test_name: str,
        category: str = "basic"
    ) -> Dict:
        """
        Test a single query and verify language detection/response
        
        Args:
            query: User query to test
            expected_language: Expected response language (en, tl, akl)
            test_name: Name of the test
            category: Test category (basic, short, mixed, etc.)
        
        Returns:
            Dictionary with test results
        """
        try:
            print(f"\n📝 Testing: {test_name}")
            print(f"   Query: '{query}'")
            print(f"   Expected Language: {expected_language}")
            
            # Chat with the bot
            response = await self.chatbot.chat(query, session_id="test_session")
            
            # Extract detection info
            detected_lang = response.detected_language
            confidence = response.language_confidence
            response_text = response.response[0] if response.response else ""
            
            # Determine actual language of response
            actual_language = self._detect_response_language(response_text, detected_lang)
            
            # Check if it matches expected
            is_correct = actual_language == expected_language or detected_lang == expected_language
            
            result = {
                "test_name": test_name,
                "category": category,
                "query": query,
                "expected_lang": expected_language,
                "detected_lang": detected_lang,
                "actual_response_lang": actual_language,
                "confidence": confidence,
                "response_preview": response_text[:100] + "..." if len(response_text) > 100 else response_text,
                "passed": is_correct,
                "response_full": response_text
            }
            
            # Print result
            status = "✅ PASS" if is_correct else "❌ FAIL"
            print(f"   {status}")
            print(f"   Detected: {detected_lang} (confidence: {confidence:.2f})")
            print(f"   Response Language: {actual_language}")
            
            # Update stats
            if is_correct:
                self.passed += 1
            else:
                self.failed += 1
            
            self.test_results.append(result)
            return result
            
        except Exception as e:
            print(f"   ❌ ERROR: {str(e)}")
            result = {
                "test_name": test_name,
                "category": category,
                "query": query,
                "expected_lang": expected_language,
                "error": str(e),
                "passed": False
            }
            self.failed += 1
            self.test_results.append(result)
            return result
    
    def _detect_response_language(self, response_text: str, detected_lang: str) -> str:
        """Detect the language of the response text"""
        if not response_text:
            return "unknown"
        
        response_lower = response_text.lower()
        
        # Tagalog indicators
        tagalog_indicators = [
            'ang ', 'ng ', 'sa ', 'ay ', 'po ', 'ito', 'dito', 'iyan',
            'sino', 'ano', 'saan', 'kailan', 'bakit', 'paano',
            'salamat', 'paumanhin', 'kumusta', 'maganda', 'hello',
            'guro', 'titser', 'baitang', 'estudyante', 'paaralan',
            'araw', 'oras', 'umaga', 'hapon', 'gabi', 'mainit', 'malamig',
            'mabuti', 'masaya', 'malungkot', 'natutuwa', 'nag-aaral'
        ]
        
        # English indicators  
        english_indicators = [
            'the ', 'is ', 'are ', 'a ', 'an ', 'and ', 'or ', 'but ',
            'hello', 'grade', 'teacher', 'school', 'time', 'what', 'when',
            'where', 'who', 'how', 'why', 'can', 'will', 'would', 'could',
            'should', 'may', 'might', 'must', 'thank', 'please', 'sorry',
            'hours', 'morning', 'afternoon', 'evening', 'day', 'week',
            'information', 'offer', 'provide', 'welcome', 'help', 'available'
        ]
        
        # Count indicators
        tagalog_count = sum(1 for indicator in tagalog_indicators if indicator in response_lower)
        english_count = sum(1 for indicator in english_indicators if indicator in response_lower)
        
        # Determine language
        if tagalog_count > english_count and tagalog_count > 0:
            return "tl"
        elif english_count > tagalog_count and english_count > 0:
            return "en"
        else:
            # Default to detected language
            return detected_lang if detected_lang in ["en", "tl", "akl"] else "unknown"
    
    async def run_all_tests(self):
        """Run complete test suite"""
        print("\n" + "="*70)
        print("🤖 CHATBOT LANGUAGE BUG FIX - TEST SUITE")
        print("="*70)
        
        # Test 1: English Short Queries (Priority 1 Fix)
        print("\n\n" + "="*70)
        print("TEST GROUP 1: English Short Queries")
        print("(Tests Priority 1 & 2 fixes - short query detection)")
        print("="*70)
        
        english_short_queries = [
            ("what grade", "en", "Short question about grades"),
            ("13 years old", "en", "Short age query - THE ORIGINAL BUG"),
            ("who is teacher", "en", "Short person inquiry"),
            ("grade 1", "en", "Just grade number"),
            ("school hours", "en", "Short phrase query"),
            ("when start", "en", "Minimal question"),
        ]
        
        for query, expected_lang, test_name in english_short_queries:
            await self.test_query(query, expected_lang, test_name, "short_english")
        
        # Test 2: English Full Queries
        print("\n\n" + "="*70)
        print("TEST GROUP 2: English Full Queries")
        print("(Tests full English detection)")
        print("="*70)
        
        english_full_queries = [
            ("What grade level should I enroll her?", "en", "Full English enrollment query"),
            ("Who is the teacher for grade 1?", "en", "Full teacher inquiry"),
            ("What are the school hours?", "en", "Full schedule inquiry"),
            ("Can you tell me about the school?", "en", "Full school info request"),
            ("Hello, I have a question about grades", "en", "Full greeting + inquiry"),
            ("Good morning, when does school start?", "en", "Full greeting with question"),
        ]
        
        for query, expected_lang, test_name in english_full_queries:
            await self.test_query(query, expected_lang, test_name, "full_english")
        
        # Test 3: Tagalog Queries
        print("\n\n" + "="*70)
        print("TEST GROUP 3: Tagalog Queries")
        print("(Tests Tagalog detection and response)")
        print("="*70)
        
        tagalog_queries = [
            ("Sino ang guro?", "tl", "Short Tagalog: Who is teacher?"),
            ("Sino ang guro ng Grade 1?", "tl", "Tagalog: Grade 1 teacher"),
            ("Kailan mag-start ang school?", "tl", "Tagalog: When does school start?"),
            ("Ano ang school hours?", "tl", "Tagalog: What are school hours?"),
            ("Ano ang mga baitang namin?", "tl", "Tagalog: What are our grades?"),
            ("May teacher ba ang Grade 5?", "tl", "Tagalog: Does Grade 5 have teacher?"),
        ]
        
        for query, expected_lang, test_name in tagalog_queries:
            await self.test_query(query, expected_lang, test_name, "tagalog")
        
        # Test 4: Mixed Language Queries
        print("\n\n" + "="*70)
        print("TEST GROUP 4: Mixed Language Queries")
        print("(Tests mixed language handling)")
        print("="*70)
        
        mixed_queries = [
            ("Hello, sino ang guro?", "tl", "Mixed: English greeting + Tagalog question"),
            ("Good morning, ano ang grade levels?", "tl", "Mixed: English greeting + Tagalog question"),
            ("My daughter is in Grade 3 na siya ay masaya", "en", "Mixed: English primary + Tagalog phrase"),
        ]
        
        for query, expected_lang, test_name in mixed_queries:
            await self.test_query(query, expected_lang, test_name, "mixed")
        
        # Test 5: Edge Cases
        print("\n\n" + "="*70)
        print("TEST GROUP 5: Edge Cases")
        print("(Tests edge cases and special scenarios)")
        print("="*70)
        
        edge_cases = [
            ("grade", "en", "Single English word"),
            ("guro", "tl", "Single Tagalog word"),
            ("1", "en", "Single number"),
            ("???", "en", "Just punctuation"),
            ("hello world", "en", "Two English words"),
            ("sino ano", "tl", "Two Tagalog words"),
        ]
        
        for query, expected_lang, test_name in edge_cases:
            await self.test_query(query, expected_lang, test_name, "edge_case")
    
    def print_summary(self):
        """Print test results summary"""
        print("\n\n" + "="*70)
        print("📊 TEST SUMMARY")
        print("="*70)
        
        total = self.passed + self.failed
        pass_rate = (self.passed / total * 100) if total > 0 else 0
        
        print(f"\n✅ Passed: {self.passed}/{total}")
        print(f"❌ Failed: {self.failed}/{total}")
        print(f"📈 Pass Rate: {pass_rate:.1f}%")
        
        # Group results by category
        categories = {}
        for result in self.test_results:
            category = result.get("category", "unknown")
            if category not in categories:
                categories[category] = {"passed": 0, "failed": 0}
            
            if result.get("passed"):
                categories[category]["passed"] += 1
            else:
                categories[category]["failed"] += 1
        
        print("\n📋 Results by Category:")
        for category, stats in sorted(categories.items()):
            total_cat = stats["passed"] + stats["failed"]
            rate = (stats["passed"] / total_cat * 100) if total_cat > 0 else 0
            print(f"   {category:20} {stats['passed']:2}/{total_cat:2} ({rate:5.1f}%)")
        
        # Show failures
        failures = [r for r in self.test_results if not r.get("passed")]
        if failures:
            print("\n⚠️  Failed Tests:")
            for failure in failures:
                print(f"\n   Test: {failure.get('test_name')}")
                print(f"   Query: {failure.get('query')}")
                print(f"   Expected: {failure.get('expected_lang')}")
                print(f"   Got: {failure.get('actual_response_lang', 'N/A')}")
                if failure.get("error"):
                    print(f"   Error: {failure.get('error')}")
    
    def save_results(self, filename="test_results.json"):
        """Save test results to file"""
        output_file = os.path.join(os.path.dirname(__file__), filename)
        
        summary = {
            "total": self.passed + self.failed,
            "passed": self.passed,
            "failed": self.failed,
            "pass_rate": (self.passed / (self.passed + self.failed) * 100) if (self.passed + self.failed) > 0 else 0,
            "results": self.test_results
        }
        
        with open(output_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"\n💾 Results saved to: {output_file}")


async def main():
    """Main test execution"""
    try:
        suite = LanguageTestSuite()
        await suite.run_all_tests()
        suite.print_summary()
        suite.save_results()
        
        # Exit with appropriate code
        sys.exit(0 if suite.failed == 0 else 1)
        
    except Exception as e:
        print(f"\n❌ Test suite error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
