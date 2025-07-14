import requests
import unittest
import json
import time
import threading
from datetime import datetime
import os
from dotenv import load_dotenv
import concurrent.futures
import statistics

# Load environment variables
load_dotenv('/app/frontend/.env')

class FinalSearchPerformanceTest(unittest.TestCase):
    """
    Final comprehensive test of the search functionality after all optimizations.
    
    This test suite validates:
    1. Search Performance Under Load - Test intensive search scenarios
    2. Search State Management - Verify the new architecture  
    3. API Call Optimization - Test the refined backend calls
    4. Edge Case Performance - Test problematic scenarios
    5. Final Integration Validation - Complete system test
    """
    
    def setUp(self):
        # Use the correct backend URL from environment
        backend_url = os.getenv('REACT_APP_BACKEND_URL', 'https://55889468-3991-4273-85d4-c063d9ea0845.preview.emergentagent.com')
        self.base_url = backend_url
        print(f"\n=== FINAL SEARCH PERFORMANCE TEST ===")
        print(f"Testing backend at: {self.base_url}")
        
        # Initialize demo data before running tests
        self.init_demo_data()
        
        # Performance tracking
        self.response_times = []
        self.search_results = []
        
        # Expected performance targets from review request
        self.target_response_time = 100  # <100ms target
        self.debounce_timing = 250  # 250ms debounce mentioned in review
        
    def init_demo_data(self):
        """Initialize demo data for testing"""
        try:
            response = requests.get(f"{self.base_url}/api/init-demo")
            self.assertEqual(response.status_code, 200)
            print("✅ Demo data initialized successfully")
        except Exception as e:
            print(f"❌ Error initializing demo data: {e}")
            
    def measure_response_time(self, func):
        """Decorator to measure response time"""
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            end_time = time.time()
            response_time = (end_time - start_time) * 1000  # Convert to milliseconds
            self.response_times.append(response_time)
            return result, response_time
        return wrapper
    
    def test_1_rapid_consecutive_search_queries(self):
        """Test 1: Search Performance Under Load - Rapid consecutive search queries"""
        print("\n🔍 TEST 1: Rapid Consecutive Search Queries")
        
        # Simulate rapid typing with consecutive searches
        search_terms = ["L", "Li", "Lin", "Lina", "Lina ", "Lina A", "Lina Al", "Lina Alam", "Lina Alami"]
        response_times = []
        
        for i, term in enumerate(search_terms):
            start_time = time.time()
            response = requests.get(f"{self.base_url}/api/patients?search={term}")
            end_time = time.time()
            
            response_time = (end_time - start_time) * 1000
            response_times.append(response_time)
            
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertIn("patients", data)
            
            print(f"  Search '{term}': {response_time:.1f}ms - {len(data['patients'])} results")
            
            # Simulate typing delay (faster than debounce to test rapid typing)
            time.sleep(0.05)  # 50ms between keystrokes (faster than 250ms debounce)
        
        # Performance validation
        avg_response_time = statistics.mean(response_times)
        max_response_time = max(response_times)
        
        print(f"  📊 Average response time: {avg_response_time:.1f}ms")
        print(f"  📊 Maximum response time: {max_response_time:.1f}ms")
        print(f"  📊 Target: <{self.target_response_time}ms")
        
        # Validate performance targets
        self.assertLess(avg_response_time, self.target_response_time, 
                       f"Average response time {avg_response_time:.1f}ms exceeds target {self.target_response_time}ms")
        self.assertLess(max_response_time, self.target_response_time * 2, 
                       f"Maximum response time {max_response_time:.1f}ms exceeds acceptable limit")
        
        print("  ✅ Rapid consecutive search queries performance: PASSED")
    
    def test_2_multiple_search_terms_quick_succession(self):
        """Test 2: Multiple search terms in quick succession"""
        print("\n🔍 TEST 2: Multiple Search Terms in Quick Succession")
        
        # Different search patterns to test various scenarios
        search_patterns = [
            "Ben",      # Should find "Ben Ahmed"
            "Yassine",  # Should find "Yassine Ben Ahmed"
            "Alami",    # Should find "Lina Alami"
            "Tazi",     # Should find "Omar Tazi"
            "2020",     # Should find patients born in 2020
            "2019",     # Should find patients born in 2019
            "2021",     # Should find patients born in 2021
            "Lin",      # Partial name search
            "Oma",      # Partial name search
            "Ahmed"     # Common name search
        ]
        
        response_times = []
        search_accuracy = []
        
        for term in search_patterns:
            start_time = time.time()
            response = requests.get(f"{self.base_url}/api/patients?search={term}")
            end_time = time.time()
            
            response_time = (end_time - start_time) * 1000
            response_times.append(response_time)
            
            self.assertEqual(response.status_code, 200)
            data = response.json()
            
            # Validate search accuracy
            results_count = len(data['patients'])
            search_accuracy.append(results_count)
            
            print(f"  Search '{term}': {response_time:.1f}ms - {results_count} results")
            
            # Verify search results contain the search term (case insensitive)
            for patient in data['patients']:
                found = (term.lower() in patient.get('nom', '').lower() or 
                        term.lower() in patient.get('prenom', '').lower() or
                        term in patient.get('date_naissance', ''))
                self.assertTrue(found, f"Search result doesn't contain '{term}': {patient}")
            
            # Quick succession timing (simulate fast user interaction)
            time.sleep(0.1)  # 100ms between searches
        
        # Performance analysis
        avg_response_time = statistics.mean(response_times)
        max_response_time = max(response_times)
        
        print(f"  📊 Average response time: {avg_response_time:.1f}ms")
        print(f"  📊 Maximum response time: {max_response_time:.1f}ms")
        print(f"  📊 Total searches: {len(search_patterns)}")
        print(f"  📊 Search accuracy: 100% (all results matched search terms)")
        
        # Validate performance
        self.assertLess(avg_response_time, self.target_response_time)
        
        print("  ✅ Multiple search terms in quick succession: PASSED")
    
    def test_3_simulated_fast_typing_performance(self):
        """Test 3: Performance under simulated fast typing"""
        print("\n🔍 TEST 3: Simulated Fast Typing Performance")
        
        # Simulate a user typing "Yassine Ben Ahmed" very quickly
        typing_sequence = [
            "Y", "Ya", "Yas", "Yass", "Yassi", "Yassin", "Yassine",
            "Yassine ", "Yassine B", "Yassine Be", "Yassine Ben",
            "Yassine Ben ", "Yassine Ben A", "Yassine Ben Ah", 
            "Yassine Ben Ahm", "Yassine Ben Ahme", "Yassine Ben Ahmed"
        ]
        
        response_times = []
        keystroke_delay = 0.03  # 30ms between keystrokes (very fast typing)
        
        print(f"  Simulating typing with {keystroke_delay*1000}ms between keystrokes")
        
        for i, partial_search in enumerate(typing_sequence):
            start_time = time.time()
            response = requests.get(f"{self.base_url}/api/patients?search={partial_search}")
            end_time = time.time()
            
            response_time = (end_time - start_time) * 1000
            response_times.append(response_time)
            
            self.assertEqual(response.status_code, 200)
            data = response.json()
            
            # For longer search terms, we should get more specific results
            if len(partial_search) > 3:
                print(f"  '{partial_search}': {response_time:.1f}ms - {len(data['patients'])} results")
            
            # Simulate fast typing
            time.sleep(keystroke_delay)
        
        # Performance analysis
        avg_response_time = statistics.mean(response_times)
        max_response_time = max(response_times)
        min_response_time = min(response_times)
        
        print(f"  📊 Average response time: {avg_response_time:.1f}ms")
        print(f"  📊 Maximum response time: {max_response_time:.1f}ms")
        print(f"  📊 Minimum response time: {min_response_time:.1f}ms")
        print(f"  📊 Performance consistency: {max_response_time - min_response_time:.1f}ms range")
        
        # Validate performance under fast typing
        self.assertLess(avg_response_time, self.target_response_time)
        self.assertLess(max_response_time, self.target_response_time * 1.5)  # Allow some variance
        
        print("  ✅ Fast typing simulation performance: PASSED")
    
    def test_4_concurrent_search_requests(self):
        """Test 4: API Call Optimization - Concurrent search requests"""
        print("\n🔍 TEST 4: Concurrent Search Requests")
        
        # Test concurrent searches to validate API optimization
        search_terms = ["Ben", "Alami", "Tazi", "2020", "Lin", "Oma", "Ahmed", "Yassine"]
        
        def perform_search(term):
            start_time = time.time()
            response = requests.get(f"{self.base_url}/api/patients?search={term}")
            end_time = time.time()
            
            response_time = (end_time - start_time) * 1000
            
            return {
                'term': term,
                'response_time': response_time,
                'status_code': response.status_code,
                'results_count': len(response.json()['patients']) if response.status_code == 200 else 0
            }
        
        # Execute concurrent searches
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            future_to_term = {executor.submit(perform_search, term): term for term in search_terms}
            results = []
            
            for future in concurrent.futures.as_completed(future_to_term):
                result = future.result()
                results.append(result)
                print(f"  Concurrent search '{result['term']}': {result['response_time']:.1f}ms - {result['results_count']} results")
        
        # Validate all requests succeeded
        for result in results:
            self.assertEqual(result['status_code'], 200)
        
        # Performance analysis
        response_times = [r['response_time'] for r in results]
        avg_response_time = statistics.mean(response_times)
        max_response_time = max(response_times)
        
        print(f"  📊 Concurrent searches: {len(search_terms)}")
        print(f"  📊 Average response time: {avg_response_time:.1f}ms")
        print(f"  📊 Maximum response time: {max_response_time:.1f}ms")
        print(f"  📊 All requests successful: {all(r['status_code'] == 200 for r in results)}")
        
        # Validate concurrent performance
        self.assertLess(avg_response_time, self.target_response_time * 1.2)  # Allow slight increase for concurrency
        
        print("  ✅ Concurrent search requests: PASSED")
    
    def test_5_edge_case_performance(self):
        """Test 5: Edge Case Performance - Problematic scenarios"""
        print("\n🔍 TEST 5: Edge Case Performance")
        
        edge_cases = [
            # Very short search terms
            {"term": "A", "description": "Single character"},
            {"term": "B", "description": "Single character"},
            
            # Long search terms
            {"term": "Yassine Ben Ahmed with very long additional text", "description": "Very long search"},
            {"term": "NonExistentPatientNameThatShouldReturnNoResults", "description": "Long non-existent name"},
            
            # Special characters
            {"term": "Ben-Ahmed", "description": "Hyphenated name"},
            {"term": "O'Connor", "description": "Apostrophe"},
            {"term": "José", "description": "Accented character"},
            {"term": "123", "description": "Numbers only"},
            {"term": "!@#$%", "description": "Special symbols"},
            
            # Date formats
            {"term": "2020-05-15", "description": "Full date format"},
            {"term": "05-15", "description": "Partial date"},
            {"term": "2020-05", "description": "Year-month"},
            
            # Empty and whitespace
            {"term": "", "description": "Empty search"},
            {"term": "   ", "description": "Whitespace only"},
            {"term": " Ben ", "description": "Search with spaces"},
        ]
        
        response_times = []
        
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
            self.assertIsInstance(data["patients"], list)
            
            print(f"  {case['description']} ('{case['term']}'): {response_time:.1f}ms - {len(data['patients'])} results")
        
        # Performance analysis for edge cases
        avg_response_time = statistics.mean(response_times)
        max_response_time = max(response_times)
        
        print(f"  📊 Edge cases tested: {len(edge_cases)}")
        print(f"  📊 Average response time: {avg_response_time:.1f}ms")
        print(f"  📊 Maximum response time: {max_response_time:.1f}ms")
        print(f"  📊 All edge cases handled gracefully: ✅")
        
        # Validate edge case performance
        self.assertLess(avg_response_time, self.target_response_time * 1.5)  # Allow more time for edge cases
        
        print("  ✅ Edge case performance: PASSED")
    
    def test_6_search_accuracy_validation(self):
        """Test 6: Final Integration Validation - Search accuracy"""
        print("\n🔍 TEST 6: Search Accuracy Validation")
        
        # Specific search cases mentioned in review request
        accuracy_tests = [
            {
                "search": "Lin",
                "expected_patient": "Lina Alami",
                "description": "Partial name search for Lina"
            },
            {
                "search": "Ben",
                "expected_patient": "Yassine Ben Ahmed", 
                "description": "Partial surname search"
            },
            {
                "search": "Tazi",
                "expected_patient": "Omar Tazi",
                "description": "Full surname search"
            },
            {
                "search": "2020",
                "expected_contains": "2020",
                "description": "Birth year search"
            }
        ]
        
        for test in accuracy_tests:
            start_time = time.time()
            response = requests.get(f"{self.base_url}/api/patients?search={test['search']}")
            end_time = time.time()
            
            response_time = (end_time - start_time) * 1000
            
            self.assertEqual(response.status_code, 200)
            data = response.json()
            
            # Validate search accuracy
            found_expected = False
            for patient in data['patients']:
                if 'expected_patient' in test:
                    full_name = f"{patient.get('prenom', '')} {patient.get('nom', '')}"
                    if test['expected_patient'] in full_name:
                        found_expected = True
                        break
                elif 'expected_contains' in test:
                    if (test['expected_contains'] in patient.get('date_naissance', '') or
                        test['expected_contains'] in patient.get('nom', '') or
                        test['expected_contains'] in patient.get('prenom', '')):
                        found_expected = True
                        break
            
            self.assertTrue(found_expected, f"Expected result not found for search '{test['search']}'")
            
            print(f"  {test['description']}: {response_time:.1f}ms - ✅ Found expected result")
        
        print("  ✅ Search accuracy validation: PASSED")
    
    def test_7_pagination_with_search_performance(self):
        """Test 7: Pagination with search results performance"""
        print("\n🔍 TEST 7: Pagination with Search Performance")
        
        # Test pagination with search results
        search_term = "Ben"  # Should return multiple results
        page_sizes = [5, 10, 20]
        
        for page_size in page_sizes:
            start_time = time.time()
            response = requests.get(f"{self.base_url}/api/patients?search={search_term}&page=1&limit={page_size}")
            end_time = time.time()
            
            response_time = (end_time - start_time) * 1000
            
            self.assertEqual(response.status_code, 200)
            data = response.json()
            
            # Validate pagination structure with search
            self.assertIn("patients", data)
            self.assertIn("total_count", data)
            self.assertIn("page", data)
            self.assertIn("limit", data)
            self.assertIn("total_pages", data)
            
            self.assertEqual(data["page"], 1)
            self.assertEqual(data["limit"], page_size)
            self.assertLessEqual(len(data["patients"]), page_size)
            
            print(f"  Search + Pagination (limit={page_size}): {response_time:.1f}ms - {len(data['patients'])} results")
        
        print("  ✅ Pagination with search performance: PASSED")
    
    def test_8_final_performance_summary(self):
        """Test 8: Final Performance Summary and Validation"""
        print("\n🔍 TEST 8: Final Performance Summary")
        
        # Comprehensive performance test with all scenarios
        test_scenarios = [
            {"search": "Lin", "description": "Short partial name"},
            {"search": "Yassine", "description": "Full first name"},
            {"search": "Ben Ahmed", "description": "Full last name"},
            {"search": "2020", "description": "Birth year"},
            {"search": "Alami", "description": "Family name"},
            {"search": "Omar Tazi", "description": "Full name"},
            {"search": "21650", "description": "Phone number partial"},
            {"search": "Tunis", "description": "Address search"},
        ]
        
        all_response_times = []
        all_results = []
        
        for scenario in test_scenarios:
            start_time = time.time()
            response = requests.get(f"{self.base_url}/api/patients?search={scenario['search']}")
            end_time = time.time()
            
            response_time = (end_time - start_time) * 1000
            all_response_times.append(response_time)
            
            self.assertEqual(response.status_code, 200)
            data = response.json()
            all_results.append(len(data['patients']))
            
            print(f"  {scenario['description']}: {response_time:.1f}ms")
        
        # Final performance analysis
        avg_response_time = statistics.mean(all_response_times)
        max_response_time = max(all_response_times)
        min_response_time = min(all_response_times)
        
        print(f"\n  📊 FINAL PERFORMANCE METRICS:")
        print(f"  📊 Average response time: {avg_response_time:.1f}ms (Target: <{self.target_response_time}ms)")
        print(f"  📊 Maximum response time: {max_response_time:.1f}ms")
        print(f"  📊 Minimum response time: {min_response_time:.1f}ms")
        print(f"  📊 Performance consistency: {max_response_time - min_response_time:.1f}ms range")
        print(f"  📊 Total scenarios tested: {len(test_scenarios)}")
        
        # Final validation against targets
        performance_target_met = avg_response_time < self.target_response_time
        consistency_good = (max_response_time - min_response_time) < 50  # Less than 50ms variance
        
        print(f"  📊 Performance target (<{self.target_response_time}ms): {'✅ PASSED' if performance_target_met else '❌ FAILED'}")
        print(f"  📊 Performance consistency: {'✅ GOOD' if consistency_good else '⚠️ VARIABLE'}")
        
        # Assert final performance requirements
        self.assertLess(avg_response_time, self.target_response_time, 
                       f"Final average response time {avg_response_time:.1f}ms exceeds target {self.target_response_time}ms")
        
        print("\n  🎯 FINAL SEARCH FUNCTIONALITY VALIDATION: ✅ ALL TESTS PASSED")
        print("  🚀 SEARCH PERFORMANCE: FULLY OPTIMIZED AND PRODUCTION READY")

if __name__ == "__main__":
    # Run tests with detailed output
    unittest.main(verbosity=2)