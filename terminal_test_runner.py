#!/usr/bin/env python3
"""
Terminal-based test runner that shows bot responses in real-time
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime
from typing import List, Dict, Any

class TerminalTestRunner:
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
    
    async def test_single_query(self, query: str, conversation_history: List[Dict] = None):
        """Test a single query and display the response"""
        print(f"\n{'='*80}")
        print(f"🧪 TESTING: {query}")
        print(f"{'='*80}")
        
        start_time = time.time()
        response = await self.send_query(query, conversation_history)
        response_time = time.time() - start_time
        
        if response.get("error"):
            print(f"❌ ERROR: {response['error']}")
            print(f"⏱️  Response Time: {response_time:.2f}ms")
            return False, response_time, response['error']
        
        # Display response details
        print(f"✅ SUCCESS")
        print(f"⏱️  Response Time: {response_time:.2f}ms")
        print(f"🌍 Detected Language: {response.get('detected_language', 'Unknown')}")
        print(f"🎯 Language Confidence: {response.get('language_confidence', 'N/A')}")
        print(f"📱 Message Count: {response.get('message_count', 1)}")
        
        # Display the actual response
        response_text = response.get('response', 'No response')
        if isinstance(response_text, list):
            print(f"📝 Response ({len(response_text)} messages):")
            for i, msg in enumerate(response_text, 1):
                print(f"   Message {i}: {msg}")
        else:
            print(f"📝 Response: {response_text}")
        
        return True, response_time, response_text
    
    async def run_comprehensive_tests(self):
        """Run comprehensive tests with real-time response display"""
        print("🤖 COMPREHENSIVE CHATBOT TEST SUITE")
        print("=" * 80)
        print("Testing all features with live response display")
        print("=" * 80)
        
        # Test configurations
        test_categories = {
            "🏫 School Information": [
                "What is Tomas SM. Bautista Elementary School?",
                "Grade level",
                "What is the schools class schedule?",
                "Does the school use report cards or online grading?",
                "Are transferees accepted?",
                "Are there Remedial or tutorial classes offered?"
            ],
            "👥 Staff Information": [
                "Head Teacher",
                "Principal",
                "How many teachers are currently in the school?",
                "How do teachers communicate with parents"
            ],
            "📍 Location & Facilities": [
                "Location of the school",
                "Where is the guidance office?",
                "comfort room, cr",
                "Where i can buy the school uniform"
            ],
            "🏃 School Operations": [
                "flag cermony",
                "Rules for wearing IDs inside the school",
                "gmail, email",
                "Does the school have a feeding Program?"
            ],
            "👋 Greetings & Basic": [
                "Hello",
                "Hi",
                "Kumusta",
                "Good morning"
            ],
            "🌍 Language Detection": [
                "Hello",
                "Kumusta ka",
                "Sino ang head teacher?",
                "Saan ang paaralan?"
            ],
            "⚠️ Error Handling": [
                "asdfghjkl",
                "xyz123",
                "invalid query"
            ]
        }
        
        conversation_history = []
        
        # Run tests for each category
        for category, queries in test_categories.items():
            print(f"\n\n🔍 TESTING CATEGORY: {category}")
            print("=" * 60)
            
            category_results = []
            
            for query in queries:
                success, response_time, response = await self.test_single_query(query, conversation_history)
                
                # Add to conversation history for memory tests
                conversation_history.append({"role": "user", "content": query})
                if success and response:
                    response_text = response
                    if isinstance(response_text, list):
                        response_text = response_text[0] if response_text else ""
                    conversation_history.append({"role": "assistant", "content": response_text})
                
                category_results.append({
                    "query": query,
                    "success": success,
                    "response_time": response_time,
                    "response": response
                })
                
                # Small delay between queries
                await asyncio.sleep(1)
            
            # Category summary
            success_count = sum(1 for r in category_results if r["success"])
            success_rate = success_count / len(category_results)
            avg_time = sum(r["response_time"] for r in category_results) / len(category_results)
            
            print(f"\n📊 CATEGORY SUMMARY:")
            print(f"   Success Rate: {success_count}/{len(category_results)} ({success_rate:.1%})")
            print(f"   Average Response Time: {avg_time:.2f}ms")
            
            self.test_results.extend(category_results)
        
        # Memory test
        print(f"\n\n🧠 TESTING MEMORY & CONTEXT")
        print("=" * 60)
        
        memory_queries = [
            "Hi, I am Sarah",
            "What is my name?",
            "I am looking for information about the school",
            "What was I looking for?"
        ]
        
        for query in memory_queries:
            success, response_time, response = await self.test_single_query(query, conversation_history)
            
            # Add to conversation history
            conversation_history.append({"role": "user", "content": query})
            if success and response:
                response_text = response
                if isinstance(response_text, list):
                    response_text = response_text[0] if response_text else ""
                conversation_history.append({"role": "assistant", "content": response_text})
            
            self.test_results.append({
                "query": query,
                "success": success,
                "response_time": response_time,
                "response": response
            })
            
            await asyncio.sleep(1)
        
        # Generate final report
        self.generate_final_report()
    
    def generate_final_report(self):
        """Generate comprehensive final report"""
        print(f"\n\n{'='*80}")
        print("📊 COMPREHENSIVE TEST REPORT")
        print(f"{'='*80}")
        
        total_tests = len(self.test_results)
        successful_tests = sum(1 for t in self.test_results if t["success"])
        failed_tests = total_tests - successful_tests
        success_rate = successful_tests / total_tests if total_tests > 0 else 0
        avg_response_time = sum(t["response_time"] for t in self.test_results) / total_tests if total_tests > 0 else 0
        
        print(f"📈 OVERALL STATISTICS:")
        print(f"   Total Tests: {total_tests}")
        print(f"   Successful: {successful_tests}")
        print(f"   Failed: {failed_tests}")
        print(f"   Success Rate: {success_rate:.1%}")
        print(f"   Average Response Time: {avg_response_time:.2f}ms")
        
        # Show failed tests
        failed_tests_list = [t for t in self.test_results if not t["success"]]
        if failed_tests_list:
            print(f"\n❌ FAILED TESTS:")
            for test in failed_tests_list:
                print(f"   - {test['query']} (Error: {test['response']})")
        
        # Show slow tests
        slow_tests = [t for t in self.test_results if t["response_time"] > 5000]  # > 5 seconds
        if slow_tests:
            print(f"\n🐌 SLOW TESTS (>5s):")
            for test in slow_tests:
                print(f"   - {test['query']} ({test['response_time']:.2f}ms)")
        
        # Overall assessment
        print(f"\n🎯 OVERALL ASSESSMENT:")
        if success_rate >= 0.9:
            print("   🎉 EXCELLENT - Chatbot is performing exceptionally well!")
        elif success_rate >= 0.8:
            print("   ✅ VERY GOOD - Chatbot is performing well with minor issues")
        elif success_rate >= 0.7:
            print("   ⚠️  GOOD - Chatbot is working but needs some improvements")
        elif success_rate >= 0.6:
            print("   ⚠️  FAIR - Chatbot has several issues that need attention")
        else:
            print("   ❌ POOR - Chatbot has significant issues requiring immediate attention")
        
        # Save detailed report
        report_data = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_tests": total_tests,
                "successful_tests": successful_tests,
                "failed_tests": failed_tests,
                "success_rate": success_rate,
                "avg_response_time": avg_response_time
            },
            "test_results": self.test_results
        }
        
        filename = f"comprehensive_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, "w") as f:
            json.dump(report_data, f, indent=2)
        
        print(f"\n💾 Detailed report saved to: {filename}")

async def main():
    """Main function to run the comprehensive test suite"""
    async with TerminalTestRunner() as runner:
        await runner.run_comprehensive_tests()

if __name__ == "__main__":
    print("🤖 Terminal-Based Chatbot Test Runner")
    print("This will test all features and show responses in real-time")
    print("Make sure your chatbot server is running on http://localhost:8000")
    print("Press Ctrl+C to cancel")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Test suite cancelled by user")
    except Exception as e:
        print(f"\n❌ Error running test suite: {e}")
