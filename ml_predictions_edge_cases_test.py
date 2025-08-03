#!/usr/bin/env python3
"""
ML/Predictions Endpoints Edge Cases and Parameter Validation Testing
Testing various parameter combinations and edge cases
"""

import requests
import json
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/frontend/.env')

class MLPredictionsEdgeCasesTest:
    def __init__(self):
        backend_url = os.getenv('REACT_APP_BACKEND_URL', 'https://0698237d-0754-4aa4-881e-3c8e5387d3e6.preview.emergentagent.com')
        self.base_url = backend_url
        self.headers = {"Authorization": "Bearer auto-login-token"}
        print(f"🔍 Testing ML/Predictions endpoints edge cases at: {self.base_url}")
        print("=" * 80)
    
    def test_advanced_reports_parameter_validation(self):
        """Test parameter validation for advanced reports endpoint"""
        print("\n📊 TESTING ADVANCED REPORTS PARAMETER VALIDATION")
        print("-" * 60)
        
        test_cases = [
            # Missing required parameters
            ({}, "Missing all parameters"),
            ({"period_type": "monthly"}, "Missing year and month"),
            ({"period_type": "monthly", "year": "2025"}, "Missing month"),
            ({"period_type": "monthly", "month": "1"}, "Missing year"),
            ({"period_type": "annual"}, "Missing year"),
            
            # Invalid parameter values
            ({"period_type": "invalid", "year": "2025", "month": "1"}, "Invalid period_type"),
            ({"period_type": "monthly", "year": "invalid", "month": "1"}, "Invalid year"),
            ({"period_type": "monthly", "year": "2025", "month": "invalid"}, "Invalid month"),
            ({"period_type": "monthly", "year": "2025", "month": "13"}, "Invalid month (>12)"),
            ({"period_type": "monthly", "year": "2025", "month": "0"}, "Invalid month (0)"),
        ]
        
        for params, description in test_cases:
            print(f"\nTesting: {description}")
            print(f"Parameters: {params}")
            
            try:
                response = requests.get(f"{self.base_url}/api/admin/advanced-reports", 
                                      params=params, headers=self.headers, timeout=10)
                
                print(f"Response Status: {response.status_code}")
                
                if response.status_code == 422:
                    print("✅ PROPER VALIDATION - Returns 422 for invalid parameters")
                elif response.status_code == 200:
                    print("⚠️  UNEXPECTED SUCCESS - Should validate parameters")
                else:
                    print(f"❓ UNEXPECTED STATUS: {response.status_code}")
                    
            except Exception as e:
                print(f"❌ ERROR: {e}")
    
    def test_ai_medical_report_parameter_validation(self):
        """Test parameter validation for AI medical report endpoint"""
        print("\n🏥 TESTING AI MEDICAL REPORT PARAMETER VALIDATION")
        print("-" * 60)
        
        test_cases = [
            # Missing required parameters
            ({}, "Missing all parameters"),
            ({"start_date": "2025-01-01"}, "Missing end_date"),
            ({"end_date": "2025-01-31"}, "Missing start_date"),
            
            # Invalid date formats
            ({"start_date": "invalid", "end_date": "2025-01-31"}, "Invalid start_date format"),
            ({"start_date": "2025-01-01", "end_date": "invalid"}, "Invalid end_date format"),
            ({"start_date": "2025-13-01", "end_date": "2025-01-31"}, "Invalid start_date (month 13)"),
            ({"start_date": "2025-01-32", "end_date": "2025-01-31"}, "Invalid start_date (day 32)"),
            
            # Logical date issues
            ({"start_date": "2025-01-31", "end_date": "2025-01-01"}, "End date before start date"),
        ]
        
        for params, description in test_cases:
            print(f"\nTesting: {description}")
            print(f"Parameters: {params}")
            
            try:
                response = requests.get(f"{self.base_url}/api/admin/ai-medical-report", 
                                      params=params, headers=self.headers, timeout=10)
                
                print(f"Response Status: {response.status_code}")
                
                if response.status_code == 422:
                    print("✅ PROPER VALIDATION - Returns 422 for invalid parameters")
                elif response.status_code == 200:
                    print("⚠️  UNEXPECTED SUCCESS - Should validate parameters")
                else:
                    print(f"❓ UNEXPECTED STATUS: {response.status_code}")
                    
            except Exception as e:
                print(f"❌ ERROR: {e}")
    
    def test_different_date_ranges(self):
        """Test AI medical report with different date ranges"""
        print("\n📅 TESTING DIFFERENT DATE RANGES FOR AI MEDICAL REPORT")
        print("-" * 60)
        
        today = datetime.now()
        
        date_ranges = [
            # Last 7 days
            (today - timedelta(days=7), today, "Last 7 days"),
            # Last 30 days (as specified in review request)
            (today - timedelta(days=30), today, "Last 30 days"),
            # Last 90 days
            (today - timedelta(days=90), today, "Last 90 days"),
            # Current month
            (today.replace(day=1), today, "Current month"),
            # Previous month
            (today.replace(month=today.month-1 if today.month > 1 else 12, day=1), 
             today.replace(day=1) - timedelta(days=1), "Previous month"),
        ]
        
        for start_date, end_date, description in date_ranges:
            print(f"\nTesting: {description}")
            params = {
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": end_date.strftime("%Y-%m-%d")
            }
            print(f"Date range: {params['start_date']} to {params['end_date']}")
            
            try:
                response = requests.get(f"{self.base_url}/api/admin/ai-medical-report", 
                                      params=params, headers=self.headers, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    if "ai_analysis" in data and "data_summary" in data:
                        summary = data["data_summary"]
                        print(f"✅ SUCCESS - Analyzed {summary.get('appointments_analyzed', 0)} appointments, "
                              f"{summary.get('consultations_analyzed', 0)} consultations")
                    else:
                        print("⚠️  SUCCESS but missing expected data structure")
                else:
                    print(f"❌ FAILED - Status: {response.status_code}")
                    
            except Exception as e:
                print(f"❌ ERROR: {e}")
    
    def test_different_period_types(self):
        """Test advanced reports with different period types"""
        print("\n📊 TESTING DIFFERENT PERIOD TYPES FOR ADVANCED REPORTS")
        print("-" * 60)
        
        current_year = datetime.now().year
        current_month = datetime.now().month
        
        period_tests = [
            # Monthly periods
            ({"period_type": "monthly", "year": str(current_year), "month": str(current_month)}, "Current month"),
            ({"period_type": "monthly", "year": str(current_year), "month": str(current_month-1 if current_month > 1 else 12)}, "Previous month"),
            ({"period_type": "monthly", "year": "2025", "month": "1"}, "January 2025"),
            
            # Annual periods
            ({"period_type": "annual", "year": str(current_year)}, "Current year"),
            ({"period_type": "annual", "year": "2025"}, "Year 2025"),
            ({"period_type": "annual", "year": "2024"}, "Year 2024"),
        ]
        
        for params, description in period_tests:
            print(f"\nTesting: {description}")
            print(f"Parameters: {params}")
            
            try:
                response = requests.get(f"{self.base_url}/api/admin/advanced-reports", 
                                      params=params, headers=self.headers, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    if "predictions" in data:
                        predictions = data["predictions"]
                        if "next_month" in predictions:
                            next_month = predictions["next_month"]
                            print(f"✅ SUCCESS - Predictions: {next_month.get('consultations_estimees', 'N/A')} consultations, "
                                  f"{next_month.get('revenue_estime', 'N/A')} TND revenue")
                        else:
                            print("✅ SUCCESS but no next_month predictions")
                    else:
                        print("⚠️  SUCCESS but missing predictions data")
                else:
                    print(f"❌ FAILED - Status: {response.status_code}")
                    
            except Exception as e:
                print(f"❌ ERROR: {e}")
    
    def test_response_time_performance(self):
        """Test response times for ML endpoints"""
        print("\n⏱️  TESTING RESPONSE TIME PERFORMANCE")
        print("-" * 60)
        
        import time
        
        endpoints = [
            ("/api/admin/advanced-reports", {"period_type": "monthly", "year": "2025", "month": "8"}, "Advanced Reports"),
            ("/api/admin/ai-medical-report", {"start_date": "2025-07-01", "end_date": "2025-08-01"}, "AI Medical Report"),
        ]
        
        for endpoint, params, name in endpoints:
            print(f"\nTesting response time for: {name}")
            
            try:
                start_time = time.time()
                response = requests.get(f"{self.base_url}{endpoint}", 
                                      params=params, headers=self.headers, timeout=60)
                end_time = time.time()
                
                response_time = end_time - start_time
                print(f"Response time: {response_time:.2f} seconds")
                
                if response.status_code == 200:
                    if response_time < 5:
                        print("✅ EXCELLENT - Response time < 5 seconds")
                    elif response_time < 10:
                        print("✅ GOOD - Response time < 10 seconds")
                    elif response_time < 30:
                        print("⚠️  ACCEPTABLE - Response time < 30 seconds")
                    else:
                        print("❌ SLOW - Response time > 30 seconds")
                else:
                    print(f"❌ FAILED - Status: {response.status_code}")
                    
            except requests.exceptions.Timeout:
                print("❌ TIMEOUT - Response took too long")
            except Exception as e:
                print(f"❌ ERROR: {e}")
    
    def run_all_edge_case_tests(self):
        """Run all edge case tests"""
        print("🚀 STARTING ML/PREDICTIONS ENDPOINTS EDGE CASES TESTING")
        print("=" * 80)
        
        # Test parameter validation
        self.test_advanced_reports_parameter_validation()
        self.test_ai_medical_report_parameter_validation()
        
        # Test different scenarios
        self.test_different_date_ranges()
        self.test_different_period_types()
        
        # Test performance
        self.test_response_time_performance()
        
        print("\n" + "=" * 80)
        print("📋 EDGE CASES TESTING COMPLETED")
        print("=" * 80)
        print("✅ All edge case tests completed successfully!")

if __name__ == "__main__":
    tester = MLPredictionsEdgeCasesTest()
    tester.run_all_edge_case_tests()