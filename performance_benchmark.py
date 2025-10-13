#!/usr/bin/env python3
"""
Performance Benchmark Test
Tests response times, cache efficiency, and system performance
"""
import asyncio
import time
import statistics
import os
from dotenv import load_dotenv
from chatbot_refactored import ChatBot

load_dotenv()

class PerformanceBenchmark:
    """Performance testing for chatbot"""
    
    def __init__(self):
        self.chatbot = None
        self.results = []
    
    async def initialize(self):
        """Initialize chatbot"""
        try:
            groq_key = os.environ.get('GROQ_API_KEY')
            if not groq_key:
                raise ValueError("GROQ_API_KEY not found")
            
            self.chatbot = ChatBot(groq_key=groq_key)
            print("✅ Chatbot initialized for performance testing")
            return True
        except Exception as e:
            print(f"❌ Initialization failed: {e}")
            return False
    
    async def benchmark_query(self, query: str, iterations: int = 5) -> dict:
        """Benchmark a single query multiple times"""
        times = []
        cache_hits = 0
        
        print(f"🔄 Benchmarking: {query[:50]}... ({iterations} iterations)")
        
        for i in range(iterations):
            start_time = time.time()
            
            try:
                response = await self.chatbot.chat(query)
                end_time = time.time()
                
                response_time = end_time - start_time
                times.append(response_time)
                
                # Check if this was likely a cache hit (faster response)
                if response_time < 1.0:  # Arbitrary threshold
                    cache_hits += 1
                
                print(f"  Iteration {i+1}: {response_time:.3f}s")
                
            except Exception as e:
                print(f"  Iteration {i+1}: ERROR - {str(e)}")
                times.append(10.0)  # Penalty for errors
            
            # Small delay between requests
            await asyncio.sleep(0.2)
        
        return {
            "query": query,
            "iterations": iterations,
            "times": times,
            "average_time": statistics.mean(times),
            "median_time": statistics.median(times),
            "min_time": min(times),
            "max_time": max(times),
            "std_dev": statistics.stdev(times) if len(times) > 1 else 0,
            "cache_hit_rate": (cache_hits / iterations) * 100,
            "success_rate": (len([t for t in times if t < 10.0]) / iterations) * 100
        }
    
    async def run_performance_benchmark(self):
        """Run comprehensive performance benchmark"""
        
        print("🚀 PERFORMANCE BENCHMARK TEST")
        print("=" * 60)
        
        # Test queries covering different scenarios
        test_queries = [
            # Simple queries
            "What are the school hours?",
            "Who is the principal?",
            
            # Grade-specific queries (your main concern)
            "Who is the teacher of grade 4?",
            "Who is the teacher of grade 6?",
            
            # Language variations
            "Ano ang oras ng school?",
            "Sino ang principal?",
            
            # Complex queries
            "What are the enrollment requirements for grade 1?",
            "How do I pay the school fees?",
            
            # Follow-up queries
            "How about grade 5?",
            "Ano naman ang grade 3?",
            
            # Emergency queries
            "My child is sick",
            "There's an emergency"
        ]
        
        benchmark_results = []
        
        for query in test_queries:
            result = await self.benchmark_query(query, iterations=3)
            benchmark_results.append(result)
            self.results.append(result)
        
        # Calculate overall metrics
        all_times = []
        for result in benchmark_results:
            all_times.extend(result['times'])
        
        overall_metrics = {
            "total_queries": len(test_queries),
            "total_iterations": sum(r['iterations'] for r in benchmark_results),
            "overall_average": statistics.mean(all_times),
            "overall_median": statistics.median(all_times),
            "overall_min": min(all_times),
            "overall_max": max(all_times),
            "overall_std_dev": statistics.stdev(all_times) if len(all_times) > 1 else 0,
            "average_cache_hit_rate": statistics.mean([r['cache_hit_rate'] for r in benchmark_results]),
            "average_success_rate": statistics.mean([r['success_rate'] for r in benchmark_results])
        }
        
        # Print results
        self.print_performance_matrix(benchmark_results, overall_metrics)
        
        return overall_metrics
    
    def print_performance_matrix(self, results: list, overall: dict):
        """Print detailed performance matrix"""
        
        print(f"\n📊 PERFORMANCE BENCHMARK RESULTS")
        print("=" * 80)
        
        # Overall metrics
        print("🎯 OVERALL PERFORMANCE METRICS")
        print("-" * 40)
        print(f"Total Queries Tested: {overall['total_queries']}")
        print(f"Total Iterations: {overall['total_iterations']}")
        print(f"Overall Average Response Time: {overall['overall_average']:.3f}s")
        print(f"Overall Median Response Time: {overall['overall_median']:.3f}s")
        print(f"Fastest Response: {overall['overall_min']:.3f}s")
        print(f"Slowest Response: {overall['overall_max']:.3f}s")
        print(f"Standard Deviation: {overall['overall_std_dev']:.3f}s")
        print(f"Average Cache Hit Rate: {overall['average_cache_hit_rate']:.1f}%")
        print(f"Average Success Rate: {overall['average_success_rate']:.1f}%")
        print()
        
        # Performance grade
        avg_time = overall['overall_average']
        if avg_time <= 1.0:
            grade = "A+"
        elif avg_time <= 1.5:
            grade = "A"
        elif avg_time <= 2.0:
            grade = "B+"
        elif avg_time <= 2.5:
            grade = "B"
        elif avg_time <= 3.0:
            grade = "C+"
        elif avg_time <= 4.0:
            grade = "C"
        else:
            grade = "F"
        
        print(f"Performance Grade: {grade}")
        print()
        
        # Detailed results table
        print("📋 DETAILED RESULTS TABLE")
        print("-" * 80)
        print(f"{'Query':<40} {'Avg(s)':<8} {'Min(s)':<8} {'Max(s)':<8} {'Cache%':<8} {'Success%':<8}")
        print("-" * 80)
        
        for result in results:
            query_short = result['query'][:37] + "..." if len(result['query']) > 40 else result['query']
            print(f"{query_short:<40} {result['average_time']:<8.3f} {result['min_time']:<8.3f} {result['max_time']:<8.3f} {result['cache_hit_rate']:<8.1f} {result['success_rate']:<8.1f}")
        
        print()
        
        # Performance analysis
        print("🔍 PERFORMANCE ANALYSIS")
        print("-" * 40)
        
        # Find slowest queries
        slowest = sorted(results, key=lambda x: x['average_time'], reverse=True)[:3]
        print("🐌 SLOWEST QUERIES:")
        for i, result in enumerate(slowest, 1):
            print(f"{i}. {result['query'][:50]}... - {result['average_time']:.3f}s avg")
        
        print()
        
        # Find fastest queries
        fastest = sorted(results, key=lambda x: x['average_time'])[:3]
        print("⚡ FASTEST QUERIES:")
        for i, result in enumerate(fastest, 1):
            print(f"{i}. {result['query'][:50]}... - {result['average_time']:.3f}s avg")
        
        print()
        
        # Cache analysis
        high_cache = [r for r in results if r['cache_hit_rate'] > 50]
        low_cache = [r for r in results if r['cache_hit_rate'] < 20]
        
        if high_cache:
            print("💾 HIGH CACHE HIT RATE:")
            for result in high_cache:
                print(f"  - {result['query'][:50]}... - {result['cache_hit_rate']:.1f}%")
        
        if low_cache:
            print("💾 LOW CACHE HIT RATE:")
            for result in low_cache:
                print(f"  - {result['query'][:50]}... - {result['cache_hit_rate']:.1f}%")
        
        print()
        
        # Recommendations
        print("💡 PERFORMANCE RECOMMENDATIONS")
        print("-" * 40)
        
        if overall['overall_average'] > 3.0:
            print("🚨 CRITICAL: Average response time > 3s - Major optimization needed")
        elif overall['overall_average'] > 2.0:
            print("⚠️  WARNING: Average response time > 2s - Consider optimization")
        else:
            print("✅ GOOD: Response times are acceptable")
        
        if overall['average_cache_hit_rate'] < 30:
            print("⚠️  WARNING: Low cache hit rate - Redis caching may not be working optimally")
        else:
            print("✅ GOOD: Cache hit rate is acceptable")
        
        if overall['average_success_rate'] < 95:
            print("🚨 CRITICAL: Success rate < 95% - System reliability issues")
        else:
            print("✅ GOOD: Success rate is high")
        
        # Grade-specific performance
        grade_queries = [r for r in results if 'grade' in r['query'].lower()]
        if grade_queries:
            grade_avg = statistics.mean([r['average_time'] for r in grade_queries])
            print(f"📚 Grade-specific queries average: {grade_avg:.3f}s")
            if grade_avg > 2.0:
                print("⚠️  WARNING: Grade queries are slow - Your consistency fixes may impact performance")
            else:
                print("✅ GOOD: Grade queries are performing well")

async def main():
    """Run performance benchmark"""
    benchmark = PerformanceBenchmark()
    
    if not await benchmark.initialize():
        return
    
    metrics = await benchmark.run_performance_benchmark()
    return metrics

if __name__ == "__main__":
    asyncio.run(main())
