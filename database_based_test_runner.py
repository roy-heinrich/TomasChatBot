#!/usr/bin/env python3
"""
Database-based test runner using actual content from Supabase
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime
from typing import List, Dict, Any

class DatabaseBasedTester:
    def __init__(self, api_base: str = "http://localhost:8000"):
        self.api_base = api_base
        self.test_results = []
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def send_query(self, query: str, conversation_history: List[Dict] = None) -> Dict[str, Any]:
        """Send a query to the chatbot API"""
        if conversation_history is None:
            conversation_history = []
            
        payload = {
            "query": query,
            "conversation_history": conversation_history,
            "user_timezone": "Asia/Manila",
            "session_id": f"test_{int(time.time())}_{hash(query) % 10000}"
        }
        
        try:
            async with self.session.post(
                f"{self.api_base}/chat",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return {
                        "error": f"HTTP {response.status}",
                        "response": f"Error: {response.status}"
                    }
        except asyncio.TimeoutError:
            return {"error": "Timeout", "response": "Request timed out"}
        except Exception as e:
            return {"error": str(e), "response": f"Error: {e}"}
    
    async def run_database_based_tests(self):
        """Run tests based on actual database content"""
        print("🔍 Starting Database-Based Test Suite")
        print("=" * 60)
        
        # Test questions based on actual database content
        test_categories = {
            "School Information": [
                "What is Tomas SM. Bautista Elementary School?",
                "Grade level",
                "What is the schools class schedule?",
                "Does the school use report cards or online grading?",
                "Are transferees accepted?",
                "Are there Remedial or tutorial classes offered?"
            ],
            "Staff Information": [
                "Head Teacher",
                "Principal", 
                "How many teachers are currently in the school?",
                "How do teachers communicate with parents"
            ],
            "Location & Facilities": [
                "Location of the school",
                "Where is the guidance office?",
                "comfort room, cr",
                "Where i can buy the school uniform"
            ],
            "School Operations": [
                "flag cermony",
                "Rules for wearing IDs inside the school",
                "gmail, email",
                "Does the school have a feeding Program?"
            ],
            "Greetings & Basic": [
                "Hello",
                "Hi", 
                "Kumusta",
                "Good morning"
            ],
            "Language Detection": [
                "Hello",
                "Kumusta ka",
                "Sino ang head teacher?",
                "Saan ang paaralan?"
            ]
        }
        
        # Run tests for each category
        for category, questions in test_categories.items():
            await self.run_category_test(category, questions)
            await asyncio.sleep(1)  # Brief pause between categories
        
        # Generate comprehensive report
        self.generate_database_report()
    
    async def run_category_test(self, category_name: str, questions: List[str]):
        """Run tests for a specific category"""
        print(f"\n🧪 Testing {category_name}...")
        
        category_results = []
        conversation_history = []
        
        for question in questions:
            query_start = time.time()
            response = await self.send_query(question, conversation_history)
            query_time = time.time() - query_start
            
            # Add to conversation history for memory tests
            conversation_history.append({"role": "user", "content": question})
            if "response" in response and response["response"]:
                response_text = response["response"]
                if isinstance(response_text, list):
                    response_text = response_text[0] if response_text else ""
                conversation_history.append({"role": "assistant", "content": response_text})
            
            success = "error" not in response and response.get("response") is not None
            category_results.append({
                "question": question,
                "response": response,
                "response_time": query_time,
                "success": success
            })
            
            # Small delay between queries
            await asyncio.sleep(0.5)
        
        # Calculate category statistics
        success_count = sum(1 for r in category_results if r["success"])
        success_rate = success_count / len(category_results)
        avg_response_time = sum(r["response_time"] for r in category_results) / len(category_results)
        
        # Store results
        self.test_results.append({
            "category": category_name,
            "questions": questions,
            "results": category_results,
            "success_rate": success_rate,
            "avg_response_time": avg_response_time,
            "total_questions": len(questions)
        })
        
        # Display results
        status = "✅ PASS" if success_rate >= 0.8 else "❌ FAIL"
        print(f"   {status} - Success rate: {success_rate:.1%}, Avg time: {avg_response_time:.1f}ms")
        
        # Show sample responses
        successful_results = [r for r in category_results if r["success"]]
        if successful_results:
            sample = successful_results[0]
            response_text = sample["response"].get("response", "No response")
            if isinstance(response_text, list):
                response_text = response_text[0] if response_text else "No response"
            print(f"   Sample: {response_text[:80]}...")
    
    def generate_database_report(self):
        """Generate comprehensive test report"""
        print("\n" + "=" * 60)
        print("📊 DATABASE-BASED TEST REPORT")
        print("=" * 60)
        
        total_categories = len(self.test_results)
        passed_categories = sum(1 for t in self.test_results if t["success_rate"] >= 0.8)
        failed_categories = total_categories - passed_categories
        
        total_questions = sum(t["total_questions"] for t in self.test_results)
        successful_questions = sum(
            sum(1 for r in t["results"] if r["success"]) 
            for t in self.test_results
        )
        
        avg_response_time = sum(t["avg_response_time"] for t in self.test_results) / total_categories
        
        print(f"📈 SUMMARY STATISTICS:")
        print(f"   Total Categories: {total_categories}")
        print(f"   Passed Categories: {passed_categories}")
        print(f"   Failed Categories: {failed_categories}")
        print(f"   Category Success Rate: {passed_categories/total_categories:.1%}")
        print(f"   Total Questions: {total_questions}")
        print(f"   Successful Questions: {successful_questions}")
        print(f"   Question Success Rate: {successful_questions/total_questions:.1%}")
        print(f"   Average Response Time: {avg_response_time:.1f}ms")
        
        print(f"\n📋 DETAILED RESULTS BY CATEGORY:")
        for test in self.test_results:
            status = "✅ PASS" if test["success_rate"] >= 0.8 else "❌ FAIL"
            print(f"   {status} {test['category']}")
            print(f"      Success Rate: {test['success_rate']:.1%}")
            print(f"      Avg Response Time: {test['avg_response_time']:.1f}ms")
            print(f"      Questions: {test['total_questions']}")
            
            # Show failed questions if any
            failed_questions = [r for r in test["results"] if not r["success"]]
            if failed_questions:
                print(f"      Failed Questions:")
                for fq in failed_questions:
                    error = fq["response"].get("error", "Unknown error")
                    print(f"        - {fq['question']} (Error: {error})")
            print()
        
        # Save detailed report
        report_data = {
            "timestamp": datetime.now().isoformat(),
            "test_type": "database_based",
            "summary": {
                "total_categories": total_categories,
                "passed_categories": passed_categories,
                "failed_categories": failed_categories,
                "category_success_rate": passed_categories/total_categories,
                "total_questions": total_questions,
                "successful_questions": successful_questions,
                "question_success_rate": successful_questions/total_questions,
                "avg_response_time": avg_response_time
            },
            "category_results": self.test_results
        }
        
        filename = f"database_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, "w") as f:
            json.dump(report_data, f, indent=2)
        
        print(f"💾 Detailed report saved to: {filename}")
        
        # Overall assessment
        if passed_categories / total_categories >= 0.8:
            print("🎉 OVERALL ASSESSMENT: EXCELLENT - Chatbot is working well with database content!")
        elif passed_categories / total_categories >= 0.6:
            print("⚠️  OVERALL ASSESSMENT: GOOD - Some improvements needed")
        else:
            print("❌ OVERALL ASSESSMENT: NEEDS WORK - Significant issues with database queries")

async def main():
    """Main function to run the database-based test suite"""
    async with DatabaseBasedTester() as tester:
        await tester.run_database_based_tests()

if __name__ == "__main__":
    print("🔍 Database-Based Chatbot Test Runner")
    print("Testing with actual database content from Supabase")
    print("Make sure your chatbot server is running on http://localhost:8000")
    print("Press Ctrl+C to cancel")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Test suite cancelled by user")
    except Exception as e:
        print(f"\n❌ Error running test suite: {e}")
