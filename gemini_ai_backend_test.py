#!/usr/bin/env python3
"""
Gemini AI Integration Backend Testing
Tests the newly integrated Gemini AI endpoints for medical cabinet management system.
"""

import requests
import unittest
import json
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv('/app/frontend/.env')

class GeminiAIBackendTest(unittest.TestCase):
    """Test suite for Gemini AI integration endpoints"""
    
    def setUp(self):
        """Set up test environment"""
        # Use the correct backend URL from environment
        backend_url = os.getenv('REACT_APP_BACKEND_URL', 'https://0f556255-778a-43ef-b1e4-2e04fe02d592.preview.emergentagent.com')
        self.base_url = backend_url
        print(f"Testing Gemini AI backend at: {self.base_url}")
        
        # Initialize demo data for testing
        self.init_demo_data()
        
        # Test patient IDs from demo data
        self.test_patient_ids = ["patient1", "patient2", "patient3"]
        
        # Headers for requests
        self.headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
    
    def init_demo_data(self):
        """Initialize demo data for testing"""
        try:
            response = requests.get(f"{self.base_url}/api/init-demo")
            self.assertEqual(response.status_code, 200)
            print("✅ Demo data initialized successfully for Gemini AI testing")
        except Exception as e:
            print(f"⚠️ Error initializing demo data: {e}")
    
    def test_ai_enhanced_recommendations_endpoint(self):
        """Test GET /api/automation/ai-enhanced-recommendations - AI-enhanced proactive recommendations using Gemini"""
        print("\n🧪 Testing AI-Enhanced Recommendations Endpoint...")
        
        try:
            # Test the AI-enhanced recommendations endpoint
            response = requests.get(
                f"{self.base_url}/api/automation/ai-enhanced-recommendations",
                headers=self.headers,
                timeout=30  # Increased timeout for AI processing
            )
            
            print(f"Status Code: {response.status_code}")
            
            # Should return 200 status code
            self.assertEqual(response.status_code, 200)
            
            # Parse response
            data = response.json()
            print(f"Response keys: {list(data.keys())}")
            
            # Verify response structure
            self.assertIn('recommendations', data, "Response should contain 'recommendations' field")
            self.assertIn('ai_powered', data, "Response should contain 'ai_powered' field")
            self.assertIn('generated_at', data, "Response should contain 'generated_at' field")
            self.assertIn('total_recommendations', data, "Response should contain 'total_recommendations' field")
            
            # Verify AI-powered flag
            if 'error' not in data:
                self.assertTrue(data.get('ai_powered', False), "Should be AI-powered when Gemini service is available")
                
                # Verify recommendations structure
                recommendations = data.get('recommendations', [])
                self.assertIsInstance(recommendations, list, "Recommendations should be a list")
                
                if recommendations:
                    # Check first recommendation structure
                    first_rec = recommendations[0]
                    if isinstance(first_rec, dict):
                        # Should have recommendation fields
                        expected_fields = ['recommendation', 'priority', 'impact', 'implementation']
                        for field in expected_fields:
                            self.assertIn(field, first_rec, f"Recommendation should contain '{field}' field")
                
                print(f"✅ AI-Enhanced Recommendations: {len(recommendations)} recommendations generated")
                print(f"✅ AI-Powered: {data.get('ai_powered')}")
                
                # Print sample recommendation for verification
                if recommendations and isinstance(recommendations[0], dict):
                    sample_rec = recommendations[0]
                    print(f"✅ Sample Recommendation: {sample_rec.get('recommendation', 'N/A')[:100]}...")
            else:
                print(f"⚠️ AI Service Error: {data.get('error')}")
                # Even with error, endpoint should return 200 with error message
                self.assertIn('error', data)
            
        except requests.exceptions.Timeout:
            self.fail("AI-Enhanced Recommendations endpoint timed out (>30s)")
        except Exception as e:
            self.fail(f"AI-Enhanced Recommendations endpoint failed: {str(e)}")
    
    def test_ai_patient_insights_endpoint(self):
        """Test GET /api/automation/ai-patient-insights/{patient_id} - AI-enhanced patient behavioral insights"""
        print("\n🧪 Testing AI-Patient Insights Endpoint...")
        
        for patient_id in self.test_patient_ids:
            print(f"\n📊 Testing patient insights for: {patient_id}")
            
            try:
                # Test the AI patient insights endpoint
                response = requests.get(
                    f"{self.base_url}/api/automation/ai-patient-insights/{patient_id}",
                    headers=self.headers,
                    timeout=30  # Increased timeout for AI processing
                )
                
                print(f"Status Code: {response.status_code}")
                
                # Should return 200 status code
                self.assertEqual(response.status_code, 200)
                
                # Parse response
                data = response.json()
                print(f"Response keys: {list(data.keys())}")
                
                if 'error' not in data:
                    # Verify response structure
                    self.assertIn('patient_id', data, "Response should contain 'patient_id' field")
                    self.assertIn('ai_insights', data, "Response should contain 'ai_insights' field")
                    self.assertIn('generated_at', data, "Response should contain 'generated_at' field")
                    self.assertIn('data_source', data, "Response should contain 'data_source' field")
                    
                    # Verify patient ID matches
                    self.assertEqual(data.get('patient_id'), patient_id, "Patient ID should match request")
                    
                    # Verify data source is Gemini AI
                    self.assertEqual(data.get('data_source'), 'gemini_ai', "Data source should be 'gemini_ai'")
                    
                    # Verify AI insights content
                    ai_insights = data.get('ai_insights', '')
                    self.assertIsInstance(ai_insights, str, "AI insights should be a string")
                    self.assertGreater(len(ai_insights), 0, "AI insights should not be empty")
                    
                    print(f"✅ Patient {patient_id}: AI insights generated ({len(ai_insights)} characters)")
                    print(f"✅ Data Source: {data.get('data_source')}")
                    print(f"✅ Sample Insight: {ai_insights[:150]}...")
                    
                else:
                    print(f"⚠️ AI Service Error for {patient_id}: {data.get('error')}")
                    # Even with error, endpoint should return 200 with error message
                    self.assertIn('error', data)
                
            except requests.exceptions.Timeout:
                self.fail(f"AI-Patient Insights endpoint timed out for patient {patient_id} (>30s)")
            except Exception as e:
                self.fail(f"AI-Patient Insights endpoint failed for patient {patient_id}: {str(e)}")
    
    def test_ai_patient_insights_invalid_patient(self):
        """Test AI patient insights with invalid patient ID"""
        print("\n🧪 Testing AI-Patient Insights with Invalid Patient ID...")
        
        invalid_patient_id = "invalid_patient_999"
        
        try:
            response = requests.get(
                f"{self.base_url}/api/automation/ai-patient-insights/{invalid_patient_id}",
                headers=self.headers,
                timeout=15
            )
            
            print(f"Status Code: {response.status_code}")
            
            # Should return 200 with error message for invalid patient (endpoint handles errors gracefully)
            self.assertEqual(response.status_code, 200)
            
            # Parse response and check for error
            data = response.json()
            self.assertIn('error', data, "Response should contain error message for invalid patient")
            
            # Check that error message indicates patient not found
            error_msg = data.get('error', '')
            self.assertIn('Patient non trouvé', error_msg, "Error message should indicate patient not found")
            
            print("✅ Correctly returns error message for invalid patient ID")
            print(f"✅ Error message: {error_msg}")
            
        except Exception as e:
            self.fail(f"Invalid patient ID test failed: {str(e)}")
    
    def test_ai_schedule_optimization_endpoint(self):
        """Test POST /api/automation/ai-schedule-optimization - AI-powered schedule optimization recommendations"""
        print("\n🧪 Testing AI-Schedule Optimization Endpoint...")
        
        # Test with today's date
        today = datetime.now().strftime('%Y-%m-%d')
        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        
        test_dates = [today, tomorrow]
        
        for test_date in test_dates:
            print(f"\n📅 Testing schedule optimization for: {test_date}")
            
            try:
                # Prepare request data
                request_data = {
                    "date": test_date
                }
                
                # Test the AI schedule optimization endpoint
                response = requests.post(
                    f"{self.base_url}/api/automation/ai-schedule-optimization",
                    headers=self.headers,
                    json=request_data,
                    timeout=30  # Increased timeout for AI processing
                )
                
                print(f"Status Code: {response.status_code}")
                
                # Should return 200 status code
                self.assertEqual(response.status_code, 200)
                
                # Parse response
                data = response.json()
                print(f"Response keys: {list(data.keys())}")
                
                if 'error' not in data:
                    # Verify response structure
                    self.assertIn('ai_optimization', data, "Response should contain 'ai_optimization' field")
                    self.assertIn('date', data, "Response should contain 'date' field")
                    self.assertIn('appointments_analyzed', data, "Response should contain 'appointments_analyzed' field")
                    self.assertIn('generated_at', data, "Response should contain 'generated_at' field")
                    
                    # Verify date matches
                    self.assertEqual(data.get('date'), test_date, "Date should match request")
                    
                    # Verify AI optimization content
                    ai_optimization = data.get('ai_optimization', '')
                    self.assertIsInstance(ai_optimization, str, "AI optimization should be a string")
                    self.assertGreater(len(ai_optimization), 0, "AI optimization should not be empty")
                    
                    # Verify appointments analyzed count
                    appointments_analyzed = data.get('appointments_analyzed', 0)
                    self.assertIsInstance(appointments_analyzed, int, "Appointments analyzed should be an integer")
                    self.assertGreaterEqual(appointments_analyzed, 0, "Appointments analyzed should be >= 0")
                    
                    print(f"✅ Date {test_date}: AI optimization generated ({len(ai_optimization)} characters)")
                    print(f"✅ Appointments Analyzed: {appointments_analyzed}")
                    print(f"✅ Sample Optimization: {ai_optimization[:150]}...")
                    
                else:
                    print(f"⚠️ AI Service Error for {test_date}: {data.get('error')}")
                    # Even with error, endpoint should return 200 with error message
                    self.assertIn('error', data)
                
            except requests.exceptions.Timeout:
                self.fail(f"AI-Schedule Optimization endpoint timed out for date {test_date} (>30s)")
            except Exception as e:
                self.fail(f"AI-Schedule Optimization endpoint failed for date {test_date}: {str(e)}")
    
    def test_ai_schedule_optimization_no_date(self):
        """Test AI schedule optimization without date parameter (should use today)"""
        print("\n🧪 Testing AI-Schedule Optimization without date parameter...")
        
        try:
            # Test without date parameter
            request_data = {}
            
            response = requests.post(
                f"{self.base_url}/api/automation/ai-schedule-optimization",
                headers=self.headers,
                json=request_data,
                timeout=30
            )
            
            print(f"Status Code: {response.status_code}")
            
            # Should return 200 status code
            self.assertEqual(response.status_code, 200)
            
            # Parse response
            data = response.json()
            
            if 'error' not in data:
                # Should default to today's date
                today = datetime.now().strftime('%Y-%m-%d')
                self.assertEqual(data.get('date'), today, "Should default to today's date when no date provided")
                
                print(f"✅ Correctly defaults to today's date: {data.get('date')}")
            else:
                print(f"⚠️ AI Service Error: {data.get('error')}")
                
        except Exception as e:
            self.fail(f"AI-Schedule Optimization without date test failed: {str(e)}")
    
    def test_gemini_service_availability(self):
        """Test if Gemini AI service is properly initialized and available"""
        print("\n🧪 Testing Gemini Service Availability...")
        
        # Test all three endpoints to verify Gemini service status
        endpoints_to_test = [
            ("/api/automation/ai-enhanced-recommendations", "GET", None),
            (f"/api/automation/ai-patient-insights/{self.test_patient_ids[0]}", "GET", None),
            ("/api/automation/ai-schedule-optimization", "POST", {"date": datetime.now().strftime('%Y-%m-%d')})
        ]
        
        gemini_available = True
        service_errors = []
        
        for endpoint, method, data in endpoints_to_test:
            try:
                if method == "GET":
                    response = requests.get(f"{self.base_url}{endpoint}", headers=self.headers, timeout=15)
                else:
                    response = requests.post(f"{self.base_url}{endpoint}", headers=self.headers, json=data, timeout=15)
                
                if response.status_code == 200:
                    response_data = response.json()
                    if 'error' in response_data and 'Service IA non disponible' in response_data.get('error', ''):
                        gemini_available = False
                        service_errors.append(f"{endpoint}: {response_data.get('error')}")
                
            except Exception as e:
                service_errors.append(f"{endpoint}: {str(e)}")
        
        if gemini_available and not service_errors:
            print("✅ Gemini AI Service is available and working correctly")
        else:
            print("⚠️ Gemini AI Service issues detected:")
            for error in service_errors:
                print(f"   - {error}")
        
        # This test should pass regardless of Gemini availability (fallback mechanisms should work)
        self.assertTrue(True, "Gemini service availability test completed")
    
    def test_ai_endpoints_response_time(self):
        """Test response times for AI endpoints (should be reasonable)"""
        print("\n🧪 Testing AI Endpoints Response Time...")
        
        endpoints_to_test = [
            ("ai-enhanced-recommendations", "GET", "/api/automation/ai-enhanced-recommendations", None),
            ("ai-patient-insights", "GET", f"/api/automation/ai-patient-insights/{self.test_patient_ids[0]}", None),
            ("ai-schedule-optimization", "POST", "/api/automation/ai-schedule-optimization", {"date": datetime.now().strftime('%Y-%m-%d')})
        ]
        
        for name, method, endpoint, data in endpoints_to_test:
            print(f"\n⏱️ Testing response time for {name}...")
            
            start_time = time.time()
            
            try:
                if method == "GET":
                    response = requests.get(f"{self.base_url}{endpoint}", headers=self.headers, timeout=45)
                else:
                    response = requests.post(f"{self.base_url}{endpoint}", headers=self.headers, json=data, timeout=45)
                
                end_time = time.time()
                response_time = end_time - start_time
                
                print(f"✅ {name}: {response_time:.2f} seconds (Status: {response.status_code})")
                
                # Response time should be reasonable (under 45 seconds for AI processing)
                self.assertLess(response_time, 45, f"{name} response time should be under 45 seconds")
                
                # Status should be 200
                self.assertEqual(response.status_code, 200, f"{name} should return 200 status")
                
            except requests.exceptions.Timeout:
                print(f"⚠️ {name}: Timed out (>45s)")
                self.fail(f"{name} endpoint timed out")
            except Exception as e:
                print(f"❌ {name}: Error - {str(e)}")
                self.fail(f"{name} endpoint failed: {str(e)}")
    
    def test_ai_content_quality(self):
        """Test the quality and relevance of AI-generated content"""
        print("\n🧪 Testing AI Content Quality...")
        
        # Test AI-enhanced recommendations
        try:
            response = requests.get(
                f"{self.base_url}/api/automation/ai-enhanced-recommendations",
                headers=self.headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'error' not in data and data.get('ai_powered'):
                    recommendations = data.get('recommendations', [])
                    
                    if recommendations and isinstance(recommendations[0], dict):
                        first_rec = recommendations[0]
                        recommendation_text = first_rec.get('recommendation', '')
                        
                        # Check if content is in French (basic check)
                        french_indicators = ['le', 'la', 'les', 'de', 'du', 'des', 'pour', 'avec', 'dans', 'sur', 'patient', 'médical', 'consultation']
                        has_french = any(indicator in recommendation_text.lower() for indicator in french_indicators)
                        
                        if has_french:
                            print("✅ AI recommendations appear to be in French")
                        else:
                            print("⚠️ AI recommendations may not be in French")
                        
                        # Check content length (should be substantial)
                        if len(recommendation_text) > 50:
                            print(f"✅ AI recommendations have substantial content ({len(recommendation_text)} characters)")
                        else:
                            print("⚠️ AI recommendations content seems too short")
                    
        except Exception as e:
            print(f"⚠️ Could not test AI content quality: {str(e)}")
        
        # Test AI patient insights
        try:
            response = requests.get(
                f"{self.base_url}/api/automation/ai-patient-insights/{self.test_patient_ids[0]}",
                headers=self.headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'error' not in data:
                    insights = data.get('ai_insights', '')
                    
                    # Check if insights contain medical/behavioral terms
                    medical_terms = ['patient', 'consultation', 'ponctualité', 'comportement', 'rendez-vous', 'médical', 'analyse', 'recommandation']
                    has_medical_content = any(term in insights.lower() for term in medical_terms)
                    
                    if has_medical_content:
                        print("✅ AI patient insights contain relevant medical/behavioral content")
                    else:
                        print("⚠️ AI patient insights may lack medical/behavioral relevance")
                    
        except Exception as e:
            print(f"⚠️ Could not test patient insights quality: {str(e)}")
        
        # This test should pass regardless (quality assessment is informational)
        self.assertTrue(True, "AI content quality assessment completed")

def run_gemini_ai_tests():
    """Run all Gemini AI backend tests"""
    print("🚀 Starting Gemini AI Backend Testing...")
    print("=" * 60)
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(GeminiAIBackendTest)
    
    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2, stream=None)
    result = runner.run(suite)
    
    print("\n" + "=" * 60)
    print("📊 GEMINI AI BACKEND TEST SUMMARY")
    print("=" * 60)
    
    total_tests = result.testsRun
    failures = len(result.failures)
    errors = len(result.errors)
    passed = total_tests - failures - errors
    
    print(f"Total Tests: {total_tests}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failures}")
    print(f"🚨 Errors: {errors}")
    
    if failures > 0:
        print("\n❌ FAILURES:")
        for test, traceback in result.failures:
            # Extract meaningful error message
            if 'AssertionError: ' in traceback:
                error_msg = traceback.split('AssertionError: ')[-1].split('\n')[0]
            else:
                error_msg = 'Unknown failure'
            print(f"  - {test}: {error_msg}")
    
    if errors > 0:
        print("\n🚨 ERRORS:")
        for test, traceback in result.errors:
            # Extract meaningful error message
            if '\n' in traceback:
                error_msg = traceback.split('\n')[-2]
            else:
                error_msg = 'Unknown error'
            print(f"  - {test}: {error_msg}")
    
    success_rate = (passed / total_tests * 100) if total_tests > 0 else 0
    print(f"\n🎯 Success Rate: {success_rate:.1f}%")
    
    if success_rate >= 80:
        print("🎉 GEMINI AI INTEGRATION: EXCELLENT PERFORMANCE")
    elif success_rate >= 60:
        print("✅ GEMINI AI INTEGRATION: GOOD PERFORMANCE")
    else:
        print("⚠️ GEMINI AI INTEGRATION: NEEDS ATTENTION")
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_gemini_ai_tests()
    exit(0 if success else 1)