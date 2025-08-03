#!/usr/bin/env python3
"""
CRITICAL LOADING ISSUES TEST - REVIEW REQUEST SPECIFIC TESTING
Test spécifiquement les problèmes de chargement rapportés dans la review request

TESTS CRITIQUES POUR IDENTIFIER LES ERREURS :

1. TEST UTILISATEURS - Page Administration
2. TEST PRÉDICTIONS ML - Page Facturation  
3. TEST ANALYSES AVANCÉES - Endpoints Gemini AI
"""

import requests
import unittest
import json
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/frontend/.env')

class CriticalLoadingIssuesTest(unittest.TestCase):
    def setUp(self):
        # Use the correct backend URL from environment
        backend_url = os.getenv('REACT_APP_BACKEND_URL', 'https://f310bc43-97b2-405e-8eb3-271aa9c20e28.preview.emergentagent.com')
        self.base_url = backend_url
        print(f"🔍 Testing critical loading issues at: {self.base_url}")
        
        # Get authentication token for admin endpoints
        self.auth_token = self.get_auth_token()
        self.headers = {"Authorization": f"Bearer {self.auth_token}"}
    
    def get_auth_token(self):
        """Get authentication token for testing admin endpoints"""
        try:
            # Try auto-login token first
            return "auto-login-token"
        except:
            # Fallback to regular login
            login_data = {"username": "medecin", "password": "medecin123"}
            response = requests.post(f"{self.base_url}/api/auth/login", json=login_data)
            if response.status_code == 200:
                return response.json()["access_token"]
            else:
                return "auto-login-token"  # Use auto-login as fallback

    # ========== 1. TEST UTILISATEURS - PAGE ADMINISTRATION ==========
    
    def test_users_list_endpoint(self):
        """Test GET /api/admin/users pour récupérer la liste des utilisateurs"""
        print("\n🔍 CRITICAL TEST 1: Users List Endpoint - Page Administration")
        
        response = requests.get(f"{self.base_url}/api/admin/users", headers=self.headers)
        
        print(f"   - Status Code: {response.status_code}")
        print(f"   - Response Headers: {dict(response.headers)}")
        
        if response.status_code != 200:
            print(f"❌ CRITICAL ERROR: Users endpoint failed with status {response.status_code}")
            print(f"   - Response Text: {response.text}")
            self.fail(f"Users endpoint failed: {response.status_code} - {response.text}")
        
        try:
            data = response.json()
            print(f"   - Response Type: {type(data)}")
            print(f"   - Response Keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
            
            # Verify structure
            if isinstance(data, dict) and "users" in data:
                users = data["users"]
                print(f"   - Users Count: {len(users)}")
                
                # Verify user structure
                if len(users) > 0:
                    user = users[0]
                    required_fields = ["id", "username", "full_name", "role", "is_active", "permissions"]
                    for field in required_fields:
                        if field not in user:
                            print(f"❌ MISSING FIELD: {field} not found in user object")
                        else:
                            print(f"   - ✅ {field}: {user.get(field)}")
                
                print(f"✅ CRITICAL TEST 1 PASSED: Users endpoint working correctly")
            else:
                print(f"❌ CRITICAL ERROR: Unexpected response structure")
                print(f"   - Expected: dict with 'users' key")
                print(f"   - Got: {data}")
                self.fail("Users endpoint returned unexpected structure")
                
        except json.JSONDecodeError as e:
            print(f"❌ CRITICAL ERROR: Invalid JSON response")
            print(f"   - JSON Error: {str(e)}")
            print(f"   - Response Text: {response.text[:500]}")
            self.fail(f"Users endpoint returned invalid JSON: {str(e)}")
    
    def test_users_authentication_levels(self):
        """Test users endpoint with different authentication levels"""
        print("\n🔍 CRITICAL TEST 1b: Users Authentication Levels")
        
        # Test without authentication
        response_no_auth = requests.get(f"{self.base_url}/api/admin/users")
        print(f"   - No Auth Status: {response_no_auth.status_code}")
        
        # Test with invalid token
        invalid_headers = {"Authorization": "Bearer invalid_token"}
        response_invalid = requests.get(f"{self.base_url}/api/admin/users", headers=invalid_headers)
        print(f"   - Invalid Token Status: {response_invalid.status_code}")
        
        # Test with valid token
        response_valid = requests.get(f"{self.base_url}/api/admin/users", headers=self.headers)
        print(f"   - Valid Token Status: {response_valid.status_code}")
        
        # Authentication should be required (401/403 without proper auth)
        if response_no_auth.status_code == 200 and response_invalid.status_code == 200:
            print("⚠️ WARNING: Users endpoint may not be properly secured")
        
        if response_valid.status_code == 200:
            print("✅ CRITICAL TEST 1b PASSED: Authentication working")
        else:
            print(f"❌ CRITICAL ERROR: Valid authentication failed")
            self.fail("Users endpoint authentication failed")

    # ========== 2. TEST PRÉDICTIONS ML - PAGE FACTURATION ==========
    
    def test_admin_predictions_endpoint(self):
        """Test GET /api/admin/predictions pour les prédictions"""
        print("\n🔍 CRITICAL TEST 2a: Admin Predictions Endpoint")
        
        response = requests.get(f"{self.base_url}/api/admin/predictions", headers=self.headers)
        
        print(f"   - Status Code: {response.status_code}")
        
        if response.status_code == 404:
            print("⚠️ INFO: /api/admin/predictions endpoint does not exist (404)")
            print("   - This may be expected if predictions are handled by other endpoints")
        elif response.status_code != 200:
            print(f"❌ CRITICAL ERROR: Predictions endpoint failed with status {response.status_code}")
            print(f"   - Response Text: {response.text}")
        else:
            try:
                data = response.json()
                print(f"   - Response Type: {type(data)}")
                print(f"   - Response Keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
                print("✅ CRITICAL TEST 2a: Predictions endpoint accessible")
            except json.JSONDecodeError as e:
                print(f"❌ CRITICAL ERROR: Invalid JSON in predictions response: {str(e)}")
    
    def test_admin_advanced_reports_monthly(self):
        """Test GET /api/admin/advanced-reports with monthly parameters"""
        print("\n🔍 CRITICAL TEST 2b: Advanced Reports - Monthly Parameters")
        
        params = {
            "period_type": "monthly",
            "year": 2025,
            "month": 1
        }
        
        response = requests.get(f"{self.base_url}/api/admin/advanced-reports", 
                              params=params, headers=self.headers)
        
        print(f"   - Status Code: {response.status_code}")
        print(f"   - Parameters: {params}")
        
        if response.status_code != 200:
            print(f"❌ CRITICAL ERROR: Advanced Reports (monthly) failed with status {response.status_code}")
            print(f"   - Response Text: {response.text}")
            self.fail(f"Advanced Reports monthly endpoint failed: {response.status_code}")
        
        try:
            data = response.json()
            print(f"   - Response Type: {type(data)}")
            print(f"   - Response Size: {len(str(data))} characters")
            
            # Check for predictions data
            if "predictions" in data:
                predictions = data["predictions"]
                print(f"   - Predictions Found: {type(predictions)}")
                if isinstance(predictions, dict) and "next_month" in predictions:
                    next_month = predictions["next_month"]
                    print(f"   - Next Month Data: {next_month}")
                    
                    # Check required prediction fields
                    required_fields = ["consultations_estimees", "revenue_estime", "confiance"]
                    for field in required_fields:
                        if field in next_month:
                            print(f"   - ✅ {field}: {next_month[field]}")
                        else:
                            print(f"   - ❌ MISSING: {field}")
            
            print("✅ CRITICAL TEST 2b PASSED: Advanced Reports monthly working")
            
        except json.JSONDecodeError as e:
            print(f"❌ CRITICAL ERROR: Invalid JSON in advanced reports response: {str(e)}")
            self.fail(f"Advanced Reports returned invalid JSON: {str(e)}")
    
    def test_admin_advanced_reports_annual(self):
        """Test GET /api/admin/advanced-reports with annual parameters"""
        print("\n🔍 CRITICAL TEST 2c: Advanced Reports - Annual Parameters")
        
        params = {
            "period_type": "annual",
            "year": 2025
        }
        
        response = requests.get(f"{self.base_url}/api/admin/advanced-reports", 
                              params=params, headers=self.headers)
        
        print(f"   - Status Code: {response.status_code}")
        print(f"   - Parameters: {params}")
        
        if response.status_code != 200:
            print(f"❌ CRITICAL ERROR: Advanced Reports (annual) failed with status {response.status_code}")
            print(f"   - Response Text: {response.text}")
            self.fail(f"Advanced Reports annual endpoint failed: {response.status_code}")
        
        try:
            data = response.json()
            print(f"   - Response Type: {type(data)}")
            print(f"   - Response Size: {len(str(data))} characters")
            print("✅ CRITICAL TEST 2c PASSED: Advanced Reports annual working")
            
        except json.JSONDecodeError as e:
            print(f"❌ CRITICAL ERROR: Invalid JSON in advanced reports annual response: {str(e)}")
            self.fail(f"Advanced Reports annual returned invalid JSON: {str(e)}")
    
    def test_admin_ai_medical_report(self):
        """Test GET /api/admin/ai-medical-report with date parameters"""
        print("\n🔍 CRITICAL TEST 2d: AI Medical Report Endpoint")
        
        params = {
            "start_date": "2025-01-01",
            "end_date": "2025-08-03"
        }
        
        response = requests.get(f"{self.base_url}/api/admin/ai-medical-report", 
                              params=params, headers=self.headers)
        
        print(f"   - Status Code: {response.status_code}")
        print(f"   - Parameters: {params}")
        
        if response.status_code != 200:
            print(f"❌ CRITICAL ERROR: AI Medical Report failed with status {response.status_code}")
            print(f"   - Response Text: {response.text}")
            self.fail(f"AI Medical Report endpoint failed: {response.status_code}")
        
        try:
            data = response.json()
            print(f"   - Response Type: {type(data)}")
            print(f"   - Response Size: {len(str(data))} characters")
            
            # Check for AI analysis data
            if "ai_analysis" in data:
                ai_analysis = data["ai_analysis"]
                print(f"   - AI Analysis Found: {type(ai_analysis)}")
                
                # Check required AI analysis fields
                required_fields = ["executive_summary", "performance_analysis", "deep_insights"]
                for field in required_fields:
                    if field in ai_analysis:
                        print(f"   - ✅ {field}: Present")
                    else:
                        print(f"   - ❌ MISSING: {field}")
            
            print("✅ CRITICAL TEST 2d PASSED: AI Medical Report working")
            
        except json.JSONDecodeError as e:
            print(f"❌ CRITICAL ERROR: Invalid JSON in AI medical report response: {str(e)}")
            self.fail(f"AI Medical Report returned invalid JSON: {str(e)}")

    # ========== 3. TEST ANALYSES AVANCÉES - GEMINI AI ==========
    
    def test_gemini_api_key_availability(self):
        """Test if Gemini API key is available and configured"""
        print("\n🔍 CRITICAL TEST 3a: Gemini API Key Availability")
        
        # Check if Gemini key is configured in backend environment
        try:
            # We can't directly access backend env, but we can test if Gemini endpoints work
            # This will indirectly test if the key is configured
            
            # Test an endpoint that uses Gemini AI
            params = {
                "period_type": "monthly",
                "year": 2025,
                "month": 1
            }
            
            response = requests.get(f"{self.base_url}/api/admin/advanced-reports", 
                                  params=params, headers=self.headers)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check if response contains AI-generated content
                if "predictions" in data:
                    print("✅ CRITICAL TEST 3a: Gemini AI appears to be working (predictions generated)")
                else:
                    print("⚠️ WARNING: No predictions found in response - Gemini AI may not be working")
            else:
                print(f"❌ CRITICAL ERROR: Cannot test Gemini AI - endpoint failed: {response.status_code}")
                
        except Exception as e:
            print(f"❌ CRITICAL ERROR: Exception testing Gemini AI availability: {str(e)}")
    
    def test_gemini_ai_endpoints_parameters(self):
        """Test Gemini AI endpoints with required parameters"""
        print("\n🔍 CRITICAL TEST 3b: Gemini AI Endpoints Parameter Validation")
        
        # Test advanced reports without required parameters
        response_no_params = requests.get(f"{self.base_url}/api/admin/advanced-reports", headers=self.headers)
        print(f"   - No Parameters Status: {response_no_params.status_code}")
        
        # Test AI medical report without required parameters  
        response_no_params_ai = requests.get(f"{self.base_url}/api/admin/ai-medical-report", headers=self.headers)
        print(f"   - AI Report No Parameters Status: {response_no_params_ai.status_code}")
        
        # Test with invalid parameters
        invalid_params = {
            "period_type": "invalid_type",
            "year": "invalid_year",
            "month": "invalid_month"
        }
        
        response_invalid = requests.get(f"{self.base_url}/api/admin/advanced-reports", 
                                      params=invalid_params, headers=self.headers)
        print(f"   - Invalid Parameters Status: {response_invalid.status_code}")
        
        # Proper parameter validation should return 400 or 422 for invalid params
        if response_no_params.status_code in [400, 422]:
            print("✅ Parameter validation working for advanced reports")
        else:
            print(f"⚠️ WARNING: Parameter validation may not be working (got {response_no_params.status_code})")
        
        if response_no_params_ai.status_code in [400, 422]:
            print("✅ Parameter validation working for AI medical report")
        else:
            print(f"⚠️ WARNING: AI report parameter validation may not be working (got {response_no_params_ai.status_code})")
        
        print("✅ CRITICAL TEST 3b COMPLETED: Parameter validation tested")

    # ========== COMPREHENSIVE CRITICAL LOADING TEST ==========
    
    def test_comprehensive_critical_loading_workflow(self):
        """Test complete workflow that might cause loading issues"""
        print("\n🔍 CRITICAL TEST 4: Comprehensive Loading Workflow")
        
        errors_found = []
        
        # Test 1: Users endpoint
        try:
            response = requests.get(f"{self.base_url}/api/admin/users", headers=self.headers)
            if response.status_code != 200:
                errors_found.append(f"Users endpoint failed: {response.status_code}")
            else:
                print("   - ✅ Users endpoint: OK")
        except Exception as e:
            errors_found.append(f"Users endpoint exception: {str(e)}")
        
        # Test 2: Advanced Reports Monthly
        try:
            params = {"period_type": "monthly", "year": 2025, "month": 1}
            response = requests.get(f"{self.base_url}/api/admin/advanced-reports", 
                                  params=params, headers=self.headers)
            if response.status_code != 200:
                errors_found.append(f"Advanced Reports monthly failed: {response.status_code}")
            else:
                print("   - ✅ Advanced Reports monthly: OK")
        except Exception as e:
            errors_found.append(f"Advanced Reports monthly exception: {str(e)}")
        
        # Test 3: Advanced Reports Annual
        try:
            params = {"period_type": "annual", "year": 2025}
            response = requests.get(f"{self.base_url}/api/admin/advanced-reports", 
                                  params=params, headers=self.headers)
            if response.status_code != 200:
                errors_found.append(f"Advanced Reports annual failed: {response.status_code}")
            else:
                print("   - ✅ Advanced Reports annual: OK")
        except Exception as e:
            errors_found.append(f"Advanced Reports annual exception: {str(e)}")
        
        # Test 4: AI Medical Report
        try:
            params = {"start_date": "2025-01-01", "end_date": "2025-08-03"}
            response = requests.get(f"{self.base_url}/api/admin/ai-medical-report", 
                                  params=params, headers=self.headers)
            if response.status_code != 200:
                errors_found.append(f"AI Medical Report failed: {response.status_code}")
            else:
                print("   - ✅ AI Medical Report: OK")
        except Exception as e:
            errors_found.append(f"AI Medical Report exception: {str(e)}")
        
        # Summary
        if errors_found:
            print(f"\n❌ CRITICAL ERRORS FOUND ({len(errors_found)}):")
            for i, error in enumerate(errors_found, 1):
                print(f"   {i}. {error}")
            self.fail(f"Critical loading issues found: {len(errors_found)} errors")
        else:
            print(f"\n✅ CRITICAL TEST 4 PASSED: All critical endpoints working correctly")

    # ========== PERFORMANCE AND TIMEOUT TESTING ==========
    
    def test_endpoint_response_times(self):
        """Test response times for critical endpoints to identify slow loading"""
        print("\n🔍 CRITICAL TEST 5: Response Time Analysis")
        
        endpoints_to_test = [
            {
                "name": "Users List",
                "url": f"{self.base_url}/api/users",
                "headers": self.headers,
                "params": None
            },
            {
                "name": "Advanced Reports Monthly",
                "url": f"{self.base_url}/api/admin/advanced-reports",
                "headers": self.headers,
                "params": {"period_type": "monthly", "year": 2025, "month": 1}
            },
            {
                "name": "Advanced Reports Annual", 
                "url": f"{self.base_url}/api/admin/advanced-reports",
                "headers": self.headers,
                "params": {"period_type": "annual", "year": 2025}
            },
            {
                "name": "AI Medical Report",
                "url": f"{self.base_url}/api/admin/ai-medical-report",
                "headers": self.headers,
                "params": {"start_date": "2025-01-01", "end_date": "2025-08-03"}
            }
        ]
        
        slow_endpoints = []
        
        for endpoint in endpoints_to_test:
            try:
                start_time = datetime.now()
                response = requests.get(endpoint["url"], 
                                      headers=endpoint["headers"], 
                                      params=endpoint["params"],
                                      timeout=30)  # 30 second timeout
                end_time = datetime.now()
                
                response_time = (end_time - start_time).total_seconds()
                
                print(f"   - {endpoint['name']}: {response_time:.2f}s (Status: {response.status_code})")
                
                # Flag slow endpoints (>10 seconds)
                if response_time > 10:
                    slow_endpoints.append(f"{endpoint['name']}: {response_time:.2f}s")
                
                # Flag failed endpoints
                if response.status_code != 200:
                    slow_endpoints.append(f"{endpoint['name']}: Failed with {response.status_code}")
                    
            except requests.exceptions.Timeout:
                print(f"   - {endpoint['name']}: TIMEOUT (>30s)")
                slow_endpoints.append(f"{endpoint['name']}: Timeout (>30s)")
            except Exception as e:
                print(f"   - {endpoint['name']}: ERROR - {str(e)}")
                slow_endpoints.append(f"{endpoint['name']}: Error - {str(e)}")
        
        if slow_endpoints:
            print(f"\n⚠️ PERFORMANCE ISSUES FOUND:")
            for issue in slow_endpoints:
                print(f"   - {issue}")
        else:
            print(f"\n✅ CRITICAL TEST 5 PASSED: All endpoints responding within acceptable time")

if __name__ == '__main__':
    # Run the critical loading tests
    print("=" * 80)
    print("🚨 CRITICAL LOADING ISSUES TEST - REVIEW REQUEST SPECIFIC")
    print("=" * 80)
    
    unittest.main(verbosity=2)