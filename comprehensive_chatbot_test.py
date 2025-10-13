#!/usr/bin/env python3
"""
Comprehensive Chatbot Test Suite
Tests all major functionality with real-world scenarios
"""
import asyncio
import sys
import os
import time
import json
from datetime import datetime
from typing import Dict, List, Any, Tuple

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from chatbot_refactored import ChatBot

class ComprehensiveChatbotTester:
    """Comprehensive test suite for the Tomas Chatbot"""
    
    def __init__(self):
        self.chatbot = ChatBot('test_key')
        self.session_id = f"comprehensive_test_{int(time.time())}"
        self.test_results = {}
        self.conversation_history = []
        
    async def run_all_tests(self):
        """Run all comprehensive tests"""
        print("🚀 Starting Comprehensive Chatbot Test Suite")
        print("=" * 60)
        print(f"Session ID: {self.session_id}")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        # Test Categories
        test_categories = [
            ("Core Functionality", self.test_core_functionality),
            ("Multilingual Support", self.test_multilingual_support),
            ("Memory & Context", self.test_memory_context),
            ("Database Search", self.test_database_search),
            ("Security Features", self.test_security_features),
            ("Special Features", self.test_special_features),
            ("Response Quality", self.test_response_quality),
            ("Error Handling", self.test_error_handling),
            ("Performance", self.test_performance),
            ("Real-World Scenarios", self.test_real_world_scenarios)
        ]
        
        total_tests = 0
        passed_tests = 0
        
        for category_name, test_method in test_categories:
            print(f"\n📋 Testing Category: {category_name}")
            print("-" * 40)
            
            try:
                category_results = await test_method()
                self.test_results[category_name] = category_results
                
                category_passed = sum(1 for result in category_results.values() if result.get('success', False))
                category_total = len(category_results)
                
                total_tests += category_total
                passed_tests += category_passed
                
                print(f"✅ {category_name}: {category_passed}/{category_total} tests passed")
                
            except Exception as e:
                print(f"❌ {category_name}: Test suite failed - {e}")
                self.test_results[category_name] = {"error": str(e)}
        
        # Final Results
        print("\n" + "=" * 60)
        print("📊 COMPREHENSIVE TEST RESULTS")
        print("=" * 60)
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        print(f"Overall Success Rate: {success_rate:.1f}% ({passed_tests}/{total_tests})")
        
        if success_rate >= 95:
            print("🎉 EXCELLENT - Chatbot is performing exceptionally well!")
        elif success_rate >= 85:
            print("✅ GOOD - Chatbot is performing well with minor issues")
        elif success_rate >= 70:
            print("⚠️ FAIR - Chatbot needs some improvements")
        else:
            print("❌ POOR - Chatbot needs significant improvements")
        
        # Save detailed results
        self.save_results()
        
        return success_rate >= 85
    
    async def test_core_functionality(self) -> Dict[str, Any]:
        """Test core chatbot functionality"""
        results = {}
        
        # Test 1: Basic Query Processing
        print("  Testing basic query processing...")
        try:
            response = await self.chatbot.chat("Who is the principal?", session_id=self.session_id)
            success = response and response.response and len(response.response[0]) > 10
            results["basic_query"] = {
                "success": success,
                "response_length": len(response.response[0]) if response and response.response else 0,
                "time": 0
            }
        except Exception as e:
            results["basic_query"] = {"success": False, "error": str(e)}
        
        # Test 2: Intent Classification
        print("  Testing intent classification...")
        try:
            response = await self.chatbot.chat("What grade is my child in?", session_id=self.session_id)
            success = response and hasattr(response, 'intent') and response.intent is not None
            results["intent_classification"] = {
                "success": success,
                "intent": response.intent if success else None,
                "confidence": "N/A"  # Intent is stored as string, not object
            }
        except Exception as e:
            results["intent_classification"] = {"success": False, "error": str(e)}
        
        # Test 3: Entity Extraction
        print("  Testing entity extraction...")
        try:
            response = await self.chatbot.chat("My daughter Maria is in grade 4", session_id=self.session_id)
            success = response and hasattr(response, 'entities') and response.entities
            results["entity_extraction"] = {
                "success": success,
                "entities_found": len(response.entities) if response and hasattr(response, 'entities') else 0
            }
        except Exception as e:
            results["entity_extraction"] = {"success": False, "error": str(e)}
        
        return results
    
    async def test_multilingual_support(self) -> Dict[str, Any]:
        """Test multilingual support"""
        results = {}
        
        # Test 1: English Detection and Response
        print("  Testing English language support...")
        try:
            response = await self.chatbot.chat("What are the school hours?", session_id=self.session_id)
            success = response and response.detected_language == "en"
            results["english_support"] = {
                "success": success,
                "detected_language": response.detected_language if response else None,
                "response_preview": response.response[0][:50] if response and response.response else ""
            }
        except Exception as e:
            results["english_support"] = {"success": False, "error": str(e)}
        
        # Test 2: Tagalog Detection and Response
        print("  Testing Tagalog language support...")
        try:
            response = await self.chatbot.chat("Ano ang oras ng paaralan?", session_id=self.session_id)
            success = response and response.detected_language == "tl"
            results["tagalog_support"] = {
                "success": success,
                "detected_language": response.detected_language if response else None,
                "response_preview": response.response[0][:50] if response and response.response else ""
            }
        except Exception as e:
            results["tagalog_support"] = {"success": False, "error": str(e)}
        
        # Test 3: Aklanon Detection
        print("  Testing Aklanon language support...")
        try:
            response = await self.chatbot.chat("Sino du teacher sa grade 5?", session_id=self.session_id)
            success = response and response.detected_language == "tl"  # Aklanon detected as Tagalog
            results["aklanon_support"] = {
                "success": success,
                "detected_language": response.detected_language if response else None,
                "response_preview": response.response[0][:50] if response and response.response else ""
            }
        except Exception as e:
            results["aklanon_support"] = {"success": False, "error": str(e)}
        
        # Test 4: Mixed Language Handling
        print("  Testing mixed language handling...")
        try:
            response = await self.chatbot.chat("Principal po ng school?", session_id=self.session_id)
            success = response and response.detected_language == "tl"
            results["mixed_language"] = {
                "success": success,
                "detected_language": response.detected_language if response else None,
                "response_preview": response.response[0][:50] if response and response.response else ""
            }
        except Exception as e:
            results["mixed_language"] = {"success": False, "error": str(e)}
        
        return results
    
    async def test_memory_context(self) -> Dict[str, Any]:
        """Test memory and context retention"""
        results = {}
        
        # Test 1: Name Memory
        print("  Testing name memory...")
        try:
            # Store name
            await self.chatbot.chat("My name is John", session_id=self.session_id)
            # Recall name
            response = await self.chatbot.chat("What is my name?", session_id=self.session_id)
            success = response and "john" in response.response[0].lower()
            results["name_memory"] = {
                "success": success,
                "response_preview": response.response[0][:50] if response and response.response else ""
            }
        except Exception as e:
            results["name_memory"] = {"success": False, "error": str(e)}
        
        # Test 2: Child Information Memory
        print("  Testing child information memory...")
        try:
            # Store child info
            await self.chatbot.chat("I have a daughter named Maria in grade 4", session_id=self.session_id)
            # Recall child info
            response = await self.chatbot.chat("What grade is my child in?", session_id=self.session_id)
            success = response and ("maria" in response.response[0].lower() or "grade 4" in response.response[0].lower())
            results["child_memory"] = {
                "success": success,
                "response_preview": response.response[0][:50] if response and response.response else ""
            }
        except Exception as e:
            results["child_memory"] = {"success": False, "error": str(e)}
        
        # Test 3: Conversation Context
        print("  Testing conversation context...")
        try:
            conversation_history = []
            # First query
            response1 = await self.chatbot.chat("Tell me about school activities", 
                                              conversation_history=conversation_history, 
                                              session_id=self.session_id)
            conversation_history.append({"role": "user", "content": "Tell me about school activities"})
            conversation_history.append({"role": "assistant", "content": response1.response[0]})
            
            # Follow-up query
            response2 = await self.chatbot.chat("When are they held?", 
                                              conversation_history=conversation_history, 
                                              session_id=self.session_id)
            
            activity_words = ["activity", "activities", "event", "events", "program", "schedule"]
            success = any(word in response2.response[0].lower() for word in activity_words)
            results["conversation_context"] = {
                "success": success,
                "response_preview": response2.response[0][:50] if response2 and response2.response else ""
            }
        except Exception as e:
            results["conversation_context"] = {"success": False, "error": str(e)}
        
        return results
    
    async def test_database_search(self) -> Dict[str, Any]:
        """Test database search functionality"""
        results = {}
        
        # Test 1: Principal Information
        print("  Testing principal information search...")
        try:
            response = await self.chatbot.chat("Who is the principal?", session_id=self.session_id)
            success = response and response.response and len(response.response[0]) > 20
            results["principal_search"] = {
                "success": success,
                "response_length": len(response.response[0]) if response and response.response else 0,
                "response_preview": response.response[0][:50] if response and response.response else ""
            }
        except Exception as e:
            results["principal_search"] = {"success": False, "error": str(e)}
        
        # Test 2: Grade Teacher Query
        print("  Testing grade teacher search...")
        try:
            response = await self.chatbot.chat("Who is the teacher for grade 5?", session_id=self.session_id)
            success = response and response.response and ("teacher" in response.response[0].lower() or "grade 5" in response.response[0].lower())
            results["grade_teacher_search"] = {
                "success": success,
                "response_preview": response.response[0][:50] if response and response.response else ""
            }
        except Exception as e:
            results["grade_teacher_search"] = {"success": False, "error": str(e)}
        
        # Test 3: School Activities
        print("  Testing school activities search...")
        try:
            response = await self.chatbot.chat("What activities does the school have?", session_id=self.session_id)
            success = response and response.response and len(response.response[0]) > 30
            results["activities_search"] = {
                "success": success,
                "response_length": len(response.response[0]) if response and response.response else 0,
                "response_preview": response.response[0][:50] if response and response.response else ""
            }
        except Exception as e:
            results["activities_search"] = {"success": False, "error": str(e)}
        
        # Test 4: Fuzzy Matching
        print("  Testing fuzzy matching...")
        try:
            response = await self.chatbot.chat("Who is the prinsipal?", session_id=self.session_id)  # Intentional typo
            success = response and response.response and len(response.response[0]) > 10
            results["fuzzy_matching"] = {
                "success": success,
                "response_preview": response.response[0][:50] if response and response.response else ""
            }
        except Exception as e:
            results["fuzzy_matching"] = {"success": False, "error": str(e)}
        
        return results
    
    async def test_security_features(self) -> Dict[str, Any]:
        """Test security features"""
        results = {}
        
        # Test 1: SQL Injection Protection
        print("  Testing SQL injection protection...")
        try:
            malicious_query = "'; DROP TABLE users; --"
            response = await self.chatbot.chat(malicious_query, session_id=self.session_id)
            success = response and ("sorry" in response.response[0].lower() or "cannot" in response.response[0].lower())
            results["sql_injection_protection"] = {
                "success": success,
                "response_preview": response.response[0][:50] if response and response.response else ""
            }
        except Exception as e:
            results["sql_injection_protection"] = {"success": False, "error": str(e)}
        
        # Test 2: XSS Protection
        print("  Testing XSS protection...")
        try:
            malicious_query = "<script>alert('xss')</script>"
            response = await self.chatbot.chat(malicious_query, session_id=self.session_id)
            success = response and ("sorry" in response.response[0].lower() or "cannot" in response.response[0].lower())
            results["xss_protection"] = {
                "success": success,
                "response_preview": response.response[0][:50] if response and response.response else ""
            }
        except Exception as e:
            results["xss_protection"] = {"success": False, "error": str(e)}
        
        # Test 3: Input Validation
        print("  Testing input validation...")
        try:
            response = await self.chatbot.chat("", session_id=self.session_id)
            success = False  # Should fail for empty input
        except Exception as e:
            success = "empty" in str(e).lower() or "whitespace" in str(e).lower()
            results["input_validation"] = {
                "success": success,
                "error_message": str(e)
            }
        
        return results
    
    async def test_special_features(self) -> Dict[str, Any]:
        """Test special features"""
        results = {}
        
        # Test 1: Multi-Question Handling
        print("  Testing multi-question handling...")
        try:
            response = await self.chatbot.chat("What is the school schedule? Where is the office?", session_id=self.session_id)
            success = response and len(response.response) > 1  # Should return multiple responses
            results["multi_question"] = {
                "success": success,
                "response_count": len(response.response) if response and response.response else 0
            }
        except Exception as e:
            results["multi_question"] = {"success": False, "error": str(e)}
        
        # Test 2: Emergency Detection
        print("  Testing emergency detection...")
        try:
            response = await self.chatbot.chat("I'm having a heart attack", session_id=self.session_id)
            emergency_indicators = ["emergency", "911", "medical", "🚨"]
            success = any(indicator in response.response[0] for indicator in emergency_indicators)
            results["emergency_detection"] = {
                "success": success,
                "response_preview": response.response[0][:50] if response and response.response else ""
            }
        except Exception as e:
            results["emergency_detection"] = {"success": False, "error": str(e)}
        
        # Test 3: Grade Validation
        print("  Testing grade validation...")
        try:
            response = await self.chatbot.chat("Who is the teacher for grade 20?", session_id=self.session_id)
            validation_indicators = ["not valid", "invalid", "grade 20", "elementary schools", "grades 1-6"]
            success = response and any(indicator in response.response[0].lower() for indicator in validation_indicators)
            results["grade_validation"] = {
                "success": success,
                "response_preview": response.response[0][:50] if response and response.response else ""
            }
        except Exception as e:
            results["grade_validation"] = {"success": False, "error": str(e)}
        
        return results
    
    async def test_response_quality(self) -> Dict[str, Any]:
        """Test response quality"""
        results = {}
        
        # Test 1: Natural Language Generation
        print("  Testing natural language generation...")
        try:
            response = await self.chatbot.chat("Tell me about the school's programs", session_id=self.session_id)
            word_count = len(response.response[0].split())
            has_period = "." in response.response[0]
            success = word_count > 10 and has_period
            results["natural_language"] = {
                "success": success,
                "word_count": word_count,
                "has_period": has_period,
                "response_preview": response.response[0][:50] if response and response.response else ""
            }
        except Exception as e:
            results["natural_language"] = {"success": False, "error": str(e)}
        
        # Test 2: Grammar Correctness
        print("  Testing grammar correctness...")
        try:
            response = await self.chatbot.chat("What grades does the school offer?", session_id=self.session_id)
            has_proper_punctuation = "." in response.response[0]
            no_double_spaces = "  " not in response.response[0]
            success = has_proper_punctuation and no_double_spaces
            results["grammar_correctness"] = {
                "success": success,
                "has_punctuation": has_proper_punctuation,
                "no_double_spaces": no_double_spaces,
                "response_preview": response.response[0][:50] if response and response.response else ""
            }
        except Exception as e:
            results["grammar_correctness"] = {"success": False, "error": str(e)}
        
        # Test 3: Helpfulness
        print("  Testing response helpfulness...")
        try:
            response = await self.chatbot.chat("Hello", session_id=self.session_id)
            helpful_indicators = ["welcome", "help", "assist", "information", "school"]
            success = any(indicator in response.response[0].lower() for indicator in helpful_indicators)
            results["helpfulness"] = {
                "success": success,
                "response_preview": response.response[0][:50] if response and response.response else ""
            }
        except Exception as e:
            results["helpfulness"] = {"success": False, "error": str(e)}
        
        return results
    
    async def test_error_handling(self) -> Dict[str, Any]:
        """Test error handling"""
        results = {}
        
        # Test 1: Invalid Query Handling
        print("  Testing invalid query handling...")
        try:
            response = await self.chatbot.chat("asdfghjkl", session_id=self.session_id)
            success = response and response.response and len(response.response[0]) > 0
            results["invalid_query"] = {
                "success": success,
                "response_preview": response.response[0][:50] if response and response.response else ""
            }
        except Exception as e:
            results["invalid_query"] = {"success": False, "error": str(e)}
        
        # Test 2: Very Long Query
        print("  Testing very long query handling...")
        try:
            long_query = "What is the school " * 50  # Very long query
            response = await self.chatbot.chat(long_query, session_id=self.session_id)
            success = response and response.response and len(response.response[0]) > 0
            results["long_query"] = {
                "success": success,
                "response_preview": response.response[0][:50] if response and response.response else ""
            }
        except Exception as e:
            results["long_query"] = {"success": False, "error": str(e)}
        
        return results
    
    async def test_performance(self) -> Dict[str, Any]:
        """Test performance metrics"""
        results = {}
        
        # Test 1: Response Time
        print("  Testing response time...")
        try:
            start_time = time.time()
            response = await self.chatbot.chat("Who is the principal?", session_id=self.session_id)
            end_time = time.time()
            
            response_time = end_time - start_time
            success = response_time < 5.0  # Should respond within 5 seconds
            results["response_time"] = {
                "success": success,
                "response_time": response_time,
                "response_preview": response.response[0][:50] if response and response.response else ""
            }
        except Exception as e:
            results["response_time"] = {"success": False, "error": str(e)}
        
        # Test 2: Memory Usage
        print("  Testing memory efficiency...")
        try:
            # Send multiple queries to test memory efficiency
            for i in range(5):
                await self.chatbot.chat(f"Test query {i}", session_id=self.session_id)
            
            # Final query should still work
            response = await self.chatbot.chat("Who is the principal?", session_id=self.session_id)
            success = response and response.response and len(response.response[0]) > 0
            results["memory_efficiency"] = {
                "success": success,
                "response_preview": response.response[0][:50] if response and response.response else ""
            }
        except Exception as e:
            results["memory_efficiency"] = {"success": False, "error": str(e)}
        
        return results
    
    async def test_real_world_scenarios(self) -> Dict[str, Any]:
        """Test real-world usage scenarios"""
        results = {}
        
        # Test 1: Parent Inquiry Scenario
        print("  Testing parent inquiry scenario...")
        try:
            conversation_history = []
            
            # Parent introduces themselves and child
            await self.chatbot.chat("Hello, my name is Sarah", 
                                  conversation_history=conversation_history, 
                                  session_id=self.session_id)
            conversation_history.append({"role": "user", "content": "Hello, my name is Sarah"})
            
            # Parent asks about child's teacher
            response = await self.chatbot.chat("My daughter is in grade 3. Who is her teacher?", 
                                             conversation_history=conversation_history, 
                                             session_id=self.session_id)
            
            success = response and ("teacher" in response.response[0].lower() or "grade 3" in response.response[0].lower())
            results["parent_inquiry"] = {
                "success": success,
                "response_preview": response.response[0][:50] if response and response.response else ""
            }
        except Exception as e:
            results["parent_inquiry"] = {"success": False, "error": str(e)}
        
        # Test 2: Student Information Scenario
        print("  Testing student information scenario...")
        try:
            conversation_history = []
            
            # Student asks about activities
            response1 = await self.chatbot.chat("What activities can I join?", 
                                              conversation_history=conversation_history, 
                                              session_id=self.session_id)
            conversation_history.append({"role": "user", "content": "What activities can I join?"})
            conversation_history.append({"role": "assistant", "content": response1.response[0]})
            
            # Follow-up about schedule
            response2 = await self.chatbot.chat("When do they meet?", 
                                              conversation_history=conversation_history, 
                                              session_id=self.session_id)
            
            success = response2 and len(response2.response[0]) > 20
            results["student_inquiry"] = {
                "success": success,
                "response_preview": response2.response[0][:50] if response2 and response2.response else ""
            }
        except Exception as e:
            results["student_inquiry"] = {"success": False, "error": str(e)}
        
        # Test 3: Multilingual Parent Scenario
        print("  Testing multilingual parent scenario...")
        try:
            # Tagalog query
            response = await self.chatbot.chat("Sino ang principal ng paaralan?", session_id=self.session_id)
            success = response and response.detected_language == "tl" and len(response.response[0]) > 10
            results["multilingual_parent"] = {
                "success": success,
                "detected_language": response.detected_language if response else None,
                "response_preview": response.response[0][:50] if response and response.response else ""
            }
        except Exception as e:
            results["multilingual_parent"] = {"success": False, "error": str(e)}
        
        return results
    
    def save_results(self):
        """Save test results to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"comprehensive_test_results_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.test_results, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 Detailed results saved to: {filename}")

async def main():
    """Main test runner"""
    tester = ComprehensiveChatbotTester()
    success = await tester.run_all_tests()
    
    if success:
        print("\n🎉 Comprehensive test suite completed successfully!")
        return 0
    else:
        print("\n⚠️ Comprehensive test suite completed with some issues.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
