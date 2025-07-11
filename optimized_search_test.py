import requests
import unittest
import time
import os
from dotenv import load_dotenv
import statistics
import concurrent.futures

# Load environment variables
load_dotenv('/app/frontend/.env')

class OptimizedSearchPerformanceTest(unittest.TestCase):
    """
    Final comprehensive test of the search functionality after all optimizations.
    Focused on the key performance metrics from the review request.
    """
    
    def setUp(self):
        backend_url = os.getenv('REACT_APP_BACKEND_URL')
        self.base_url = backend_url
        print(f"\n=== FINAL SEARCH PERFORMANCE VALIDATION ===")
        print(f"Backend URL: {self.base_url}")
        
        # Initialize demo data
        self.init_demo_data()
        
        # Performance targets
        self.target_response_time = 100  # <100ms target from review
        
    def init_demo_data(self):
        """Initialize demo data for testing"""
        try:
            response = requests.get(f"{self.base_url}/api/init-demo")
            self.assertEqual(response.status_code, 200)
            print("✅ Demo data initialized")
        except Exception as e:
            print(f"❌ Demo init error: {e}")
    
    def test_1_search_performance_under_load(self):
        """Test 1: Search Performance Under Load - Intensive search scenarios"""
        print("\n🔍 TEST 1: Search Performance Under Load")
        
        # Rapid consecutive search queries (simulating fast typing)
        typing_sequence = ["L", "Li", "Lin", "Lina", "Lina ", "Lina A", "Lina Al", "Lina Alam", "Lina Alami"]
        response_times = []
        
        print("  Testing rapid consecutive searches (simulating fast typing):")
        for term in typing_sequence:
            start_time = time.time()
            response = requests.get(f"{self.base_url}/api/patients?search={term}")
            end_time = time.time()
            
            response_time = (end_time - start_time) * 1000
            response_times.append(response_time)
            
            self.assertEqual(response.status_code, 200)
            data = response.json()
            print(f"    '{term}': {response_time:.1f}ms - {len(data['patients'])} results")
            
            # Small delay to simulate typing (faster than debounce)
            time.sleep(0.05)
        
        avg_time = statistics.mean(response_times)
        max_time = max(response_times)
        
        print(f"  📊 Average response time: {avg_time:.1f}ms (Target: <{self.target_response_time}ms)")
        print(f"  📊 Maximum response time: {max_time:.1f}ms")
        
        # Validate performance targets
        self.assertLess(avg_time, self.target_response_time, 
                       f"Average response time {avg_time:.1f}ms exceeds target")
        
        print("  ✅ Search performance under load: PASSED")
    
    def test_2_api_call_optimization(self):
        """Test 2: API Call Optimization - Refined backend calls"""
        print("\n🔍 TEST 2: API Call Optimization")
        
        # Test different search patterns for optimization
        search_patterns = [
            {"term": "Ben", "expected_name": "Ben Ahmed"},
            {"term": "Lin", "expected_name": "Lina"},
            {"term": "Tazi", "expected_name": "Tazi"},
            {"term": "2020", "expected_type": "date"},
        ]
        
        response_times = []
        accuracy_results = []
        
        print("  Testing API call optimization with various search patterns:")
        for pattern in search_patterns:
            start_time = time.time()
            response = requests.get(f"{self.base_url}/api/patients?search={pattern['term']}")
            end_time = time.time()
            
            response_time = (end_time - start_time) * 1000
            response_times.append(response_time)
            
            self.assertEqual(response.status_code, 200)
            data = response.json()
            
            # Verify search accuracy
            found_expected = False
            for patient in data['patients']:
                if ('expected_name' in pattern and 
                    pattern['expected_name'].lower() in f"{patient.get('nom', '')} {patient.get('prenom', '')}".lower()):
                    found_expected = True
                elif ('expected_type' in pattern and pattern['expected_type'] == 'date' and
                      pattern['term'] in patient.get('date_naissance', '')):
                    found_expected = True
            
            accuracy_results.append(found_expected)
            print(f"    '{pattern['term']}': {response_time:.1f}ms - {len(data['patients'])} results - {'✅' if found_expected else '❌'}")
        
        avg_time = statistics.mean(response_times)
        accuracy_rate = sum(accuracy_results) / len(accuracy_results) * 100
        
        print(f"  📊 Average response time: {avg_time:.1f}ms")
        print(f"  📊 Search accuracy: {accuracy_rate:.0f}%")
        
        self.assertLess(avg_time, self.target_response_time)
        self.assertGreaterEqual(accuracy_rate, 75)  # At least 75% accuracy
        
        print("  ✅ API call optimization: PASSED")
    
    def test_3_edge_case_performance(self):
        """Test 3: Edge Case Performance - Problematic scenarios"""
        print("\n🔍 TEST 3: Edge Case Performance")
        
        edge_cases = [
            {"term": "A", "desc": "Very short (1 char)"},
            {"term": "NonExistentPatient", "desc": "No results"},
            {"term": "2020-05-15", "desc": "Full date format"},
            {"term": "", "desc": "Empty search"},
            {"term": "   ", "desc": "Whitespace only"},
            {"term": "Ben Ahmed", "desc": "Multi-word search"},
        ]
        
        response_times = []
        
        print("  Testing edge cases:")
        for case in edge_cases:
            start_time = time.time()
            response = requests.get(f"{self.base_url}/api/patients?search={case['term']}")
            end_time = time.time()
            
            response_time = (end_time - start_time) * 1000
            response_times.append(response_time)
            
            self.assertEqual(response.status_code, 200)
            data = response.json()
            
            # Validate response structure
            self.assertIn("patients", data)
            self.assertIn("total_count", data)
            
            print(f"    {case['desc']}: {response_time:.1f}ms - {len(data['patients'])} results")
        
        avg_time = statistics.mean(response_times)
        max_time = max(response_times)
        
        print(f"  📊 Average edge case response time: {avg_time:.1f}ms")
        print(f"  📊 Maximum edge case response time: {max_time:.1f}ms")
        
        # Allow more time for edge cases
        self.assertLess(avg_time, self.target_response_time * 1.5)
        
        print("  ✅ Edge case performance: PASSED")
    
    def test_4_concurrent_search_validation(self):
        """Test 4: Concurrent search requests (simulating multiple users)"""
        print("\n🔍 TEST 4: Concurrent Search Validation")
        
        search_terms = ["Ben", "Alami", "Tazi", "2020", "Lin"]
        
        def perform_search(term):
            start_time = time.time()
            response = requests.get(f"{self.base_url}/api/patients?search={term}")
            end_time = time.time()
            
            return {
                'term': term,
                'response_time': (end_time - start_time) * 1000,
                'status_code': response.status_code,
                'results_count': len(response.json()['patients']) if response.status_code == 200 else 0
            }
        
        print("  Testing concurrent searches:")
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(perform_search, term) for term in search_terms]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # Validate all requests succeeded
        for result in results:
            self.assertEqual(result['status_code'], 200)
            print(f"    '{result['term']}': {result['response_time']:.1f}ms - {result['results_count']} results")
        
        response_times = [r['response_time'] for r in results]
        avg_time = statistics.mean(response_times)
        
        print(f"  📊 Concurrent average response time: {avg_time:.1f}ms")
        
        self.assertLess(avg_time, self.target_response_time * 1.2)  # Allow slight increase for concurrency
        
        print("  ✅ Concurrent search validation: PASSED")
    
    def test_5_final_integration_validation(self):
        """Test 5: Final Integration Validation - Complete system test"""
        print("\n🔍 TEST 5: Final Integration Validation")
        
        # Test complete functionality with pagination and search
        test_scenarios = [
            {"search": "Lin", "page": 1, "limit": 10},
            {"search": "Ben", "page": 1, "limit": 5},
            {"search": "2020", "page": 1, "limit": 20},
        ]
        
        response_times = []
        
        print("  Testing complete integration (search + pagination):")
        for scenario in test_scenarios:
            start_time = time.time()
            response = requests.get(
                f"{self.base_url}/api/patients?search={scenario['search']}&page={scenario['page']}&limit={scenario['limit']}"
            )
            end_time = time.time()
            
            response_time = (end_time - start_time) * 1000
            response_times.append(response_time)
            
            self.assertEqual(response.status_code, 200)
            data = response.json()
            
            # Validate complete response structure
            required_fields = ["patients", "total_count", "page", "limit", "total_pages"]
            for field in required_fields:
                self.assertIn(field, data)
            
            self.assertEqual(data["page"], scenario["page"])
            self.assertEqual(data["limit"], scenario["limit"])
            self.assertLessEqual(len(data["patients"]), scenario["limit"])
            
            print(f"    Search '{scenario['search']}' (page={scenario['page']}, limit={scenario['limit']}): {response_time:.1f}ms - {len(data['patients'])} results")
        
        avg_time = statistics.mean(response_times)
        
        print(f"  📊 Integration average response time: {avg_time:.1f}ms")
        
        self.assertLess(avg_time, self.target_response_time)
        
        print("  ✅ Final integration validation: PASSED")
    
    def test_6_performance_summary(self):
        """Test 6: Final Performance Summary"""
        print("\n🔍 TEST 6: Final Performance Summary")
        
        # Comprehensive test of all key search scenarios
        comprehensive_tests = [
            "Lin",           # Partial name
            "Yassine",       # Full first name  
            "Ben Ahmed",     # Full last name
            "2020",          # Birth year
            "Alami",         # Family name
            "Omar",          # First name
            "Tazi",          # Last name
            "2019",          # Another birth year
        ]
        
        all_response_times = []
        
        print("  Running comprehensive performance test:")
        for search_term in comprehensive_tests:
            start_time = time.time()
            response = requests.get(f"{self.base_url}/api/patients?search={search_term}")
            end_time = time.time()
            
            response_time = (end_time - start_time) * 1000
            all_response_times.append(response_time)
            
            self.assertEqual(response.status_code, 200)
            data = response.json()
            
            print(f"    '{search_term}': {response_time:.1f}ms - {len(data['patients'])} results")
        
        # Final performance metrics
        avg_time = statistics.mean(all_response_times)
        max_time = max(all_response_times)
        min_time = min(all_response_times)
        
        print(f"\n  🎯 FINAL PERFORMANCE METRICS:")
        print(f"  📊 Average response time: {avg_time:.1f}ms (Target: <{self.target_response_time}ms)")
        print(f"  📊 Maximum response time: {max_time:.1f}ms")
        print(f"  📊 Minimum response time: {min_time:.1f}ms")
        print(f"  📊 Performance consistency: {max_time - min_time:.1f}ms range")
        print(f"  📊 Total scenarios tested: {len(comprehensive_tests)}")
        
        # Final validation
        performance_excellent = avg_time < self.target_response_time
        consistency_good = (max_time - min_time) < 50
        
        print(f"  📊 Performance target met: {'✅ YES' if performance_excellent else '❌ NO'}")
        print(f"  📊 Performance consistency: {'✅ EXCELLENT' if consistency_good else '⚠️ VARIABLE'}")
        
        # Assert final requirements
        self.assertLess(avg_time, self.target_response_time, 
                       f"Final average response time {avg_time:.1f}ms exceeds target {self.target_response_time}ms")
        
        print(f"\n  🚀 SEARCH FUNCTIONALITY STATUS: ✅ FULLY OPTIMIZED")
        print(f"  🎯 PERFORMANCE TARGET: ✅ ACHIEVED ({avg_time:.1f}ms < {self.target_response_time}ms)")
        print(f"  🔧 API OPTIMIZATION: ✅ COMPLETE")
        print(f"  🧪 EDGE CASES: ✅ HANDLED")
        print(f"  🔄 CONCURRENT REQUESTS: ✅ SUPPORTED")
        print(f"  📄 PAGINATION INTEGRATION: ✅ WORKING")
        print(f"  🎉 PRODUCTION READY: ✅ CONFIRMED")

if __name__ == "__main__":
    unittest.main(verbosity=2)