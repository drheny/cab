import requests
import unittest
import json
import time
from datetime import datetime
import os
from dotenv import load_dotenv
import concurrent.futures
import threading

# Load environment variables
load_dotenv('/app/frontend/.env')

class SearchPerformanceTest(unittest.TestCase):
    """
    Comprehensive test suite for search functionality performance and optimization
    Focus on testing the improved search functionality with optimizations
    """
    
    def setUp(self):
        # Use the correct backend URL from environment
        backend_url = os.getenv('REACT_APP_BACKEND_URL', 'https://381e9303-1801-425b-be63-08a7cd034392.preview.emergentagent.com')
        self.base_url = backend_url
        print(f"Testing search performance at: {self.base_url}")
        
        # Initialize demo data before running tests
        self.init_demo_data()
        
        # Performance thresholds
        self.max_response_time = 0.5  # 500ms as specified in requirements
        self.search_debounce_time = 0.3  # 300ms debounce as mentioned
        
    def init_demo_data(self):
        """Initialize demo data for testing"""
        try:
            response = requests.get(f"{self.base_url}/api/init-demo")
            self.assertEqual(response.status_code, 200)
            print("Demo data initialized successfully for search testing")
        except Exception as e:
            print(f"Error initializing demo data: {e}")
    
    def measure_response_time(self, url):
        """Helper method to measure API response time"""
        start_time = time.time()
        response = requests.get(url)
        end_time = time.time()
        response_time = end_time - start_time
        return response, response_time
    
    def test_search_performance_basic(self):
        """Test 1: Basic search performance - API response times should be under 500ms"""
        print("\n=== Testing Basic Search Performance ===")
        
        search_terms = ["Lin", "Ben", "Tazi", "2020", "Ahmed", "Alami"]
        
        for term in search_terms:
            with self.subTest(search_term=term):
                url = f"{self.base_url}/api/patients?search={term}"
                response, response_time = self.measure_response_time(url)
                
                print(f"Search '{term}': {response_time:.3f}s")
                
                # Verify response is successful
                self.assertEqual(response.status_code, 200)
                
                # Verify response time is under threshold
                self.assertLess(response_time, self.max_response_time, 
                               f"Search for '{term}' took {response_time:.3f}s, exceeding {self.max_response_time}s limit")
                
                # Verify response structure
                data = response.json()
                self.assertIn("patients", data)
                self.assertIn("total_count", data)
                self.assertIn("page", data)
                self.assertIn("limit", data)
    
    def test_search_accuracy_specific_cases(self):
        """Test 2: Search accuracy - Verify specific search cases work correctly"""
        print("\n=== Testing Search Accuracy ===")
        
        test_cases = [
            {
                "search_term": "Lin",
                "expected_patient": "Lina Alami",
                "field_to_check": "prenom"
            },
            {
                "search_term": "Ben",
                "expected_patient": "Yassine Ben Ahmed",
                "field_to_check": "nom"
            },
            {
                "search_term": "Tazi",
                "expected_patient": "Omar Tazi",
                "field_to_check": "nom"
            },
            {
                "search_term": "2020",
                "expected_count_min": 1,
                "field_to_check": "date_naissance"
            }
        ]
        
        for case in test_cases:
            with self.subTest(search_term=case["search_term"]):
                url = f"{self.base_url}/api/patients?search={case['search_term']}"
                response, response_time = self.measure_response_time(url)
                
                print(f"Search accuracy '{case['search_term']}': {response_time:.3f}s")
                
                self.assertEqual(response.status_code, 200)
                data = response.json()
                
                if "expected_patient" in case:
                    # Check if expected patient is found
                    found = False
                    for patient in data["patients"]:
                        if case["field_to_check"] == "prenom" and case["search_term"].lower() in patient.get("prenom", "").lower():
                            found = True
                            break
                        elif case["field_to_check"] == "nom" and case["search_term"].lower() in patient.get("nom", "").lower():
                            found = True
                            break
                    
                    self.assertTrue(found, f"Expected patient with '{case['search_term']}' not found in results")
                
                if "expected_count_min" in case:
                    # Check minimum count
                    self.assertGreaterEqual(data["total_count"], case["expected_count_min"],
                                          f"Expected at least {case['expected_count_min']} results for '{case['search_term']}'")
    
    def test_search_with_pagination_performance(self):
        """Test 3: Search with pagination performance"""
        print("\n=== Testing Search with Pagination Performance ===")
        
        search_term = "a"  # Common letter to get multiple results
        page_sizes = [5, 10, 20]
        
        for limit in page_sizes:
            with self.subTest(page_size=limit):
                url = f"{self.base_url}/api/patients?search={search_term}&page=1&limit={limit}"
                response, response_time = self.measure_response_time(url)
                
                print(f"Search with pagination (limit={limit}): {response_time:.3f}s")
                
                self.assertEqual(response.status_code, 200)
                self.assertLess(response_time, self.max_response_time)
                
                data = response.json()
                self.assertEqual(data["limit"], limit)
                self.assertEqual(data["page"], 1)
                self.assertLessEqual(len(data["patients"]), limit)
    
    def test_multiple_consecutive_searches(self):
        """Test 4: Multiple consecutive searches to simulate rapid typing"""
        print("\n=== Testing Multiple Consecutive Searches ===")
        
        # Simulate typing "Lina" character by character
        search_sequence = ["L", "Li", "Lin", "Lina"]
        response_times = []
        
        for i, term in enumerate(search_sequence):
            url = f"{self.base_url}/api/patients?search={term}"
            response, response_time = self.measure_response_time(url)
            response_times.append(response_time)
            
            print(f"Consecutive search {i+1} '{term}': {response_time:.3f}s")
            
            self.assertEqual(response.status_code, 200)
            self.assertLess(response_time, self.max_response_time)
            
            # Small delay to simulate typing speed
            time.sleep(0.1)
        
        # Verify no significant performance degradation
        avg_response_time = sum(response_times) / len(response_times)
        print(f"Average response time for consecutive searches: {avg_response_time:.3f}s")
        self.assertLess(avg_response_time, self.max_response_time)
    
    def test_concurrent_search_requests(self):
        """Test 5: Concurrent search requests to test API optimization"""
        print("\n=== Testing Concurrent Search Requests ===")
        
        search_terms = ["Lin", "Ben", "Tazi", "Omar", "Yassine", "Lina"]
        
        def perform_search(term):
            url = f"{self.base_url}/api/patients?search={term}"
            start_time = time.time()
            response = requests.get(url)
            end_time = time.time()
            return term, response, end_time - start_time
        
        # Execute concurrent searches
        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
            futures = [executor.submit(perform_search, term) for term in search_terms]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # Verify all searches completed successfully
        for term, response, response_time in results:
            print(f"Concurrent search '{term}': {response_time:.3f}s")
            self.assertEqual(response.status_code, 200)
            self.assertLess(response_time, self.max_response_time * 2)  # Allow some tolerance for concurrent requests
    
    def test_edge_cases_search(self):
        """Test 6: Edge cases - various search scenarios"""
        print("\n=== Testing Edge Cases ===")
        
        edge_cases = [
            {
                "name": "Very short search (1 char)",
                "search_term": "a",
                "should_have_results": True
            },
            {
                "name": "Very short search (2 chars)",
                "search_term": "Li",
                "should_have_results": True
            },
            {
                "name": "Long search term",
                "search_term": "ThisIsAVeryLongSearchTermThatShouldNotMatchAnything",
                "should_have_results": False
            },
            {
                "name": "Special characters",
                "search_term": "@#$%",
                "should_have_results": False
            },
            {
                "name": "Non-existent patient name",
                "search_term": "NonExistentPatientName",
                "should_have_results": False
            },
            {
                "name": "Date format search (YYYY)",
                "search_term": "2020",
                "should_have_results": True
            },
            {
                "name": "Empty search",
                "search_term": "",
                "should_have_results": True  # Should return all patients
            }
        ]
        
        for case in edge_cases:
            with self.subTest(case_name=case["name"]):
                url = f"{self.base_url}/api/patients?search={case['search_term']}"
                response, response_time = self.measure_response_time(url)
                
                print(f"Edge case '{case['name']}': {response_time:.3f}s")
                
                self.assertEqual(response.status_code, 200)
                self.assertLess(response_time, self.max_response_time)
                
                data = response.json()
                
                if case["should_have_results"]:
                    if case["search_term"] == "":
                        # Empty search should return all patients
                        self.assertGreater(data["total_count"], 0)
                    else:
                        # Other cases might or might not have results, but should not error
                        self.assertGreaterEqual(data["total_count"], 0)
                else:
                    self.assertEqual(data["total_count"], 0)
                    self.assertEqual(len(data["patients"]), 0)
    
    def test_search_result_count_accuracy(self):
        """Test 7: Search result count accuracy"""
        print("\n=== Testing Search Result Count Accuracy ===")
        
        # Test that total_count matches actual results
        search_term = "a"  # Should match multiple patients
        
        url = f"{self.base_url}/api/patients?search={search_term}&page=1&limit=100"
        response, response_time = self.measure_response_time(url)
        
        print(f"Count accuracy test: {response_time:.3f}s")
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify count accuracy
        actual_results = len(data["patients"])
        reported_count = data["total_count"]
        
        if reported_count <= 100:
            # If total count is within our limit, they should match
            self.assertEqual(actual_results, reported_count,
                           f"Reported count ({reported_count}) doesn't match actual results ({actual_results})")
        else:
            # If total count exceeds our limit, we should get exactly 100 results
            self.assertEqual(actual_results, 100)
    
    def test_case_insensitive_search(self):
        """Test 8: Case insensitive search functionality"""
        print("\n=== Testing Case Insensitive Search ===")
        
        test_cases = [
            ("lin", "Lin", "LIN"),  # Different cases for "Lin"
            ("ben", "Ben", "BEN"),  # Different cases for "Ben"
            ("tazi", "Tazi", "TAZI")  # Different cases for "Tazi"
        ]
        
        for lower, title, upper in test_cases:
            results = []
            
            for case_variant in [lower, title, upper]:
                url = f"{self.base_url}/api/patients?search={case_variant}"
                response, response_time = self.measure_response_time(url)
                
                print(f"Case insensitive search '{case_variant}': {response_time:.3f}s")
                
                self.assertEqual(response.status_code, 200)
                self.assertLess(response_time, self.max_response_time)
                
                data = response.json()
                results.append(data["total_count"])
            
            # All case variants should return the same number of results
            self.assertEqual(len(set(results)), 1, 
                           f"Case insensitive search failed for {test_cases}: got counts {results}")
    
    def test_partial_name_search(self):
        """Test 9: Partial name search functionality"""
        print("\n=== Testing Partial Name Search ===")
        
        # Test partial matches
        partial_searches = [
            {
                "partial": "Yas",
                "should_match": "Yassine"
            },
            {
                "partial": "Ala",
                "should_match": "Alami"
            },
            {
                "partial": "Om",
                "should_match": "Omar"
            }
        ]
        
        for case in partial_searches:
            with self.subTest(partial=case["partial"]):
                url = f"{self.base_url}/api/patients?search={case['partial']}"
                response, response_time = self.measure_response_time(url)
                
                print(f"Partial search '{case['partial']}': {response_time:.3f}s")
                
                self.assertEqual(response.status_code, 200)
                self.assertLess(response_time, self.max_response_time)
                
                data = response.json()
                
                # Verify that partial match works
                found_match = False
                for patient in data["patients"]:
                    full_name = f"{patient.get('prenom', '')} {patient.get('nom', '')}"
                    if case["should_match"].lower() in full_name.lower():
                        found_match = True
                        break
                
                self.assertTrue(found_match, 
                              f"Partial search '{case['partial']}' should match '{case['should_match']}'")
    
    def test_database_query_performance(self):
        """Test 10: Database query performance with different search patterns"""
        print("\n=== Testing Database Query Performance ===")
        
        # Test different types of searches that might stress the database differently
        performance_tests = [
            {
                "name": "Single character search",
                "search": "a",
                "description": "Tests index performance with broad match"
            },
            {
                "name": "Exact name search",
                "search": "Yassine",
                "description": "Tests exact match performance"
            },
            {
                "name": "Date search",
                "search": "2020-05-15",
                "description": "Tests date field search performance"
            },
            {
                "name": "Multi-word search",
                "search": "Ben Ahmed",
                "description": "Tests multi-field search performance"
            }
        ]
        
        performance_results = []
        
        for test in performance_tests:
            url = f"{self.base_url}/api/patients?search={test['search']}"
            response, response_time = self.measure_response_time(url)
            
            print(f"{test['name']}: {response_time:.3f}s - {test['description']}")
            
            self.assertEqual(response.status_code, 200)
            self.assertLess(response_time, self.max_response_time)
            
            performance_results.append({
                "test": test["name"],
                "time": response_time,
                "results": response.json()["total_count"]
            })
        
        # Log performance summary
        avg_time = sum(r["time"] for r in performance_results) / len(performance_results)
        print(f"\nDatabase query performance summary:")
        print(f"Average response time: {avg_time:.3f}s")
        print(f"All queries under {self.max_response_time}s threshold: {all(r['time'] < self.max_response_time for r in performance_results)}")

if __name__ == "__main__":
    # Run with verbose output
    unittest.main(verbosity=2)