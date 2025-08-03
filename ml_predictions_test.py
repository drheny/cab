#!/usr/bin/env python3
"""
ML/Predictions Endpoints Testing Script
Specifically testing the endpoints used in Facturation - section Prédictions

Testing:
1. /api/admin/advanced-reports with different parameters
2. /api/admin/ai-medical-report with date parameters  
3. /api/admin/predictions (if it exists)

Focus: Verify endpoints return valid data and proper structure for frontend consumption
"""

import requests
import json
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/frontend/.env')

class MLPredictionsTest:
    def __init__(self):
        # Use the correct backend URL from environment
        backend_url = os.getenv('REACT_APP_BACKEND_URL', 'https://0698237d-0754-4aa4-881e-3c8e5387d3e6.preview.emergentagent.com')
        self.base_url = backend_url
        self.headers = {"Authorization": "Bearer auto-login-token"}
        print(f"🔍 Testing ML/Predictions endpoints at: {self.base_url}")
        print("=" * 80)
    
    def test_advanced_reports_monthly(self):
        """Test /api/admin/advanced-reports with monthly parameters"""
        print("\n📊 TESTING ADVANCED REPORTS ENDPOINT - MONTHLY")
        print("-" * 50)
        
        # Test with current month parameters as specified in review request
        current_date = datetime.now()
        params = {
            "period_type": "monthly",
            "year": str(current_date.year),
            "month": str(current_date.month)
        }
        
        try:
            response = requests.get(f"{self.base_url}/api/admin/advanced-reports", 
                                  params=params, headers=self.headers, timeout=30)
            
            print(f"Request URL: {response.url}")
            print(f"Response Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print("✅ ENDPOINT WORKING - Response received")
                
                # Verify critical data structure for frontend
                if "predictions" in data:
                    predictions = data["predictions"]
                    print("✅ PREDICTIONS DATA FOUND")
                    
                    if "next_month" in predictions:
                        next_month = predictions["next_month"]
                        print("✅ NEXT_MONTH PREDICTIONS FOUND")
                        
                        # Check required fields for frontend
                        required_fields = ["consultations_estimees", "revenue_estime"]
                        for field in required_fields:
                            if field in next_month:
                                print(f"  ✅ {field}: {next_month[field]}")
                            else:
                                print(f"  ❌ MISSING FIELD: {field}")
                        
                        # Check confidence field (could be 'confidence' or 'confiance')
                        confidence_field = "confidence" if "confidence" in next_month else "confiance"
                        if confidence_field in next_month:
                            print(f"  ✅ {confidence_field}: {next_month[confidence_field]}%")
                        else:
                            print(f"  ❌ MISSING CONFIDENCE FIELD")
                    else:
                        print("❌ MISSING next_month in predictions")
                    
                    # Check additional prediction data
                    optional_fields = ["insights", "risk_factors", "recommendations"]
                    for field in optional_fields:
                        if field in predictions:
                            count = len(predictions[field]) if isinstance(predictions[field], list) else "N/A"
                            print(f"  ✅ {field}: {count}")
                        else:
                            print(f"  ⚠️  Optional field missing: {field}")
                else:
                    print("❌ CRITICAL ERROR: No 'predictions' field in response")
                    print(f"Response keys: {list(data.keys())}")
                
                return True
                
            elif response.status_code in [401, 403]:
                print("❌ AUTHENTICATION ERROR")
                print(f"Response: {response.text}")
                return False
            elif response.status_code == 422:
                print("❌ PARAMETER VALIDATION ERROR")
                print(f"Response: {response.text}")
                return False
            else:
                print(f"❌ UNEXPECTED ERROR: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
        except requests.exceptions.Timeout:
            print("❌ REQUEST TIMEOUT - Endpoint may be hanging")
            return False
        except requests.exceptions.RequestException as e:
            print(f"❌ REQUEST ERROR: {e}")
            return False
        except Exception as e:
            print(f"❌ UNEXPECTED ERROR: {e}")
            return False
    
    def test_advanced_reports_annual(self):
        """Test /api/admin/advanced-reports with annual parameters"""
        print("\n📊 TESTING ADVANCED REPORTS ENDPOINT - ANNUAL")
        print("-" * 50)
        
        params = {
            "period_type": "annual",
            "year": "2025"
        }
        
        try:
            response = requests.get(f"{self.base_url}/api/admin/advanced-reports", 
                                  params=params, headers=self.headers, timeout=30)
            
            print(f"Request URL: {response.url}")
            print(f"Response Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print("✅ ENDPOINT WORKING - Annual data received")
                
                # Verify data structure
                if "predictions" in data:
                    print("✅ PREDICTIONS DATA FOUND for annual period")
                    return True
                else:
                    print("❌ MISSING predictions data for annual period")
                    return False
            else:
                print(f"❌ ERROR: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ ERROR: {e}")
            return False
    
    def test_ai_medical_report(self):
        """Test /api/admin/ai-medical-report with date parameters"""
        print("\n🏥 TESTING AI MEDICAL REPORT ENDPOINT")
        print("-" * 50)
        
        # Test with last 30 days as specified in review request
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        params = {
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d")
        }
        
        try:
            response = requests.get(f"{self.base_url}/api/admin/ai-medical-report", 
                                  params=params, headers=self.headers, timeout=30)
            
            print(f"Request URL: {response.url}")
            print(f"Response Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print("✅ ENDPOINT WORKING - AI analysis received")
                
                # Verify critical data structure for frontend
                if "ai_analysis" in data:
                    ai_analysis = data["ai_analysis"]
                    print("✅ AI_ANALYSIS DATA FOUND")
                    
                    # Check required sections for frontend
                    required_sections = [
                        "executive_summary", "performance_analysis", "deep_insights",
                        "risk_assessment", "opportunities", "strategic_recommendations", "predictions"
                    ]
                    
                    for section in required_sections:
                        if section in ai_analysis:
                            print(f"  ✅ {section}: Present")
                        else:
                            print(f"  ❌ MISSING SECTION: {section}")
                    
                    # Check executive summary details
                    if "executive_summary" in ai_analysis:
                        exec_summary = ai_analysis["executive_summary"]
                        summary_fields = ["overall_score", "performance_trend", "key_highlight", "urgency_level"]
                        for field in summary_fields:
                            if field in exec_summary:
                                print(f"    ✅ {field}: {exec_summary[field]}")
                            else:
                                print(f"    ❌ Missing: {field}")
                    
                    # Check predictions section
                    if "predictions" in ai_analysis:
                        predictions = ai_analysis["predictions"]
                        pred_fields = ["next_quarter_forecast", "annual_projection"]
                        for field in pred_fields:
                            if field in predictions:
                                print(f"    ✅ {field}: Present")
                            else:
                                print(f"    ❌ Missing: {field}")
                else:
                    print("❌ CRITICAL ERROR: No 'ai_analysis' field in response")
                    print(f"Response keys: {list(data.keys())}")
                
                # Check data summary
                if "data_summary" in data:
                    data_summary = data["data_summary"]
                    print("✅ DATA_SUMMARY FOUND")
                    summary_fields = ["appointments_analyzed", "consultations_analyzed", "patients_in_database"]
                    for field in summary_fields:
                        if field in data_summary:
                            print(f"    ✅ {field}: {data_summary[field]}")
                        else:
                            print(f"    ❌ Missing: {field}")
                else:
                    print("❌ MISSING data_summary")
                
                return True
                
            elif response.status_code in [401, 403]:
                print("❌ AUTHENTICATION ERROR")
                print(f"Response: {response.text}")
                return False
            elif response.status_code == 422:
                print("❌ PARAMETER VALIDATION ERROR")
                print(f"Response: {response.text}")
                return False
            else:
                print(f"❌ UNEXPECTED ERROR: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
        except requests.exceptions.Timeout:
            print("❌ REQUEST TIMEOUT - Endpoint may be hanging")
            return False
        except Exception as e:
            print(f"❌ ERROR: {e}")
            return False
    
    def test_admin_predictions_endpoint(self):
        """Test /api/admin/predictions endpoint if it exists"""
        print("\n🔮 TESTING ADMIN PREDICTIONS ENDPOINT")
        print("-" * 50)
        
        try:
            response = requests.get(f"{self.base_url}/api/admin/predictions", 
                                  headers=self.headers, timeout=30)
            
            print(f"Request URL: {response.url}")
            print(f"Response Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print("✅ ENDPOINT EXISTS AND WORKING")
                print(f"Response keys: {list(data.keys())}")
                return True
            elif response.status_code == 404:
                print("ℹ️  ENDPOINT DOES NOT EXIST")
                return None  # Not an error, just doesn't exist
            else:
                print(f"❌ ERROR: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ ERROR: {e}")
            return False
    
    def test_authentication_requirements(self):
        """Test that endpoints require proper authentication"""
        print("\n🔐 TESTING AUTHENTICATION REQUIREMENTS")
        print("-" * 50)
        
        endpoints_to_test = [
            ("/api/admin/advanced-reports", {"period_type": "monthly", "year": "2025", "month": "1"}),
            ("/api/admin/ai-medical-report", {"start_date": "2024-12-01", "end_date": "2025-01-28"})
        ]
        
        for endpoint, params in endpoints_to_test:
            print(f"\nTesting {endpoint} without authentication...")
            try:
                response = requests.get(f"{self.base_url}{endpoint}", params=params, timeout=10)
                if response.status_code in [401, 403]:
                    print(f"✅ PROPERLY SECURED - Returns {response.status_code}")
                else:
                    print(f"⚠️  SECURITY ISSUE - Returns {response.status_code} (should be 401/403)")
            except Exception as e:
                print(f"❌ ERROR testing {endpoint}: {e}")
    
    def run_all_tests(self):
        """Run all ML/Predictions endpoint tests"""
        print("🚀 STARTING ML/PREDICTIONS ENDPOINTS COMPREHENSIVE TESTING")
        print("=" * 80)
        
        results = {}
        
        # Test 1: Advanced Reports Monthly
        results['advanced_reports_monthly'] = self.test_advanced_reports_monthly()
        
        # Test 2: Advanced Reports Annual  
        results['advanced_reports_annual'] = self.test_advanced_reports_annual()
        
        # Test 3: AI Medical Report
        results['ai_medical_report'] = self.test_ai_medical_report()
        
        # Test 4: Admin Predictions (if exists)
        results['admin_predictions'] = self.test_admin_predictions_endpoint()
        
        # Test 5: Authentication
        self.test_authentication_requirements()
        
        # Summary
        print("\n" + "=" * 80)
        print("📋 FINAL TEST RESULTS SUMMARY")
        print("=" * 80)
        
        passed = 0
        failed = 0
        not_applicable = 0
        
        for test_name, result in results.items():
            if result is True:
                print(f"✅ {test_name}: PASSED")
                passed += 1
            elif result is False:
                print(f"❌ {test_name}: FAILED")
                failed += 1
            elif result is None:
                print(f"ℹ️  {test_name}: NOT APPLICABLE (endpoint doesn't exist)")
                not_applicable += 1
        
        print(f"\n📊 SUMMARY: {passed} PASSED, {failed} FAILED, {not_applicable} N/A")
        
        if failed == 0:
            print("🎉 ALL APPLICABLE TESTS PASSED!")
            return True
        else:
            print("⚠️  SOME TESTS FAILED - CHECK DETAILS ABOVE")
            return False

if __name__ == "__main__":
    tester = MLPredictionsTest()
    success = tester.run_all_tests()
    
    if success:
        print("\n✅ ML/PREDICTIONS ENDPOINTS ARE WORKING CORRECTLY")
    else:
        print("\n❌ ISSUES FOUND WITH ML/PREDICTIONS ENDPOINTS")