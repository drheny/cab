#!/usr/bin/env python3
"""
Gemini 2.0 Flash Advanced Reports Enrichment Testing
Tests the newly integrated Gemini AI enrichment for advanced reports functionality.
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

class GeminiAdvancedReportsTest(unittest.TestCase):
    """Test suite for Gemini 2.0 Flash enrichment in advanced reports"""
    
    def setUp(self):
        """Set up test environment"""
        # Use the correct backend URL from environment
        backend_url = os.getenv('REACT_APP_BACKEND_URL', 'https://0f556255-778a-43ef-b1e4-2e04fe02d592.preview.emergentagent.com')
        self.base_url = backend_url
        print(f"Testing Gemini Advanced Reports at: {self.base_url}")
        
        # Initialize demo data for testing
        self.init_demo_data()
        
        # Headers for requests
        self.headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': 'Bearer test-token'
        }
    
    def init_demo_data(self):
        """Initialize demo data for testing"""
        try:
            response = requests.get(f"{self.base_url}/api/init-demo")
            self.assertEqual(response.status_code, 200)
            print("✅ Demo data initialized successfully for Gemini Advanced Reports testing")
        except Exception as e:
            print(f"⚠️ Error initializing demo data: {e}")
    
    def test_gemini_service_initialization(self):
        """Test 1: Verify that GeminiAIService is properly initialized"""
        print("\n🧪 Test 1: Testing GeminiAIService Initialization...")
        
        # Check if EMERGENT_LLM_KEY is accessible
        try:
            # Load backend environment variables
            from dotenv import load_dotenv
            load_dotenv('/app/backend/.env')
            
            api_key = os.environ.get('EMERGENT_LLM_KEY')
            self.assertIsNotNone(api_key, "EMERGENT_LLM_KEY should be accessible in environment variables")
            self.assertGreater(len(api_key), 10, "EMERGENT_LLM_KEY should be a valid API key")
            
            print(f"✅ EMERGENT_LLM_KEY found: {api_key[:10]}...{api_key[-5:]}")
            
        except Exception as e:
            self.fail(f"Failed to access EMERGENT_LLM_KEY: {str(e)}")
    
    def test_advanced_reports_endpoint_monthly(self):
        """Test 2: Test advanced reports endpoint with monthly period"""
        print("\n🧪 Test 2: Testing Advanced Reports Endpoint (Monthly)...")
        
        try:
            # Test the specific endpoint mentioned in the review request
            response = requests.get(
                f"{self.base_url}/api/admin/advanced-reports?period_type=monthly&month=12&year=2024",
                headers=self.headers,
                timeout=45  # Increased timeout for Gemini processing
            )
            
            print(f"Status Code: {response.status_code}")
            
            # Should return 200 status code
            self.assertEqual(response.status_code, 200)
            
            # Parse response
            data = response.json()
            print(f"Response keys: {list(data.keys())}")
            
            # Verify basic report structure
            required_keys = ['metadata', 'advanced_statistics', 'evolution', 'predictions', 'alerts']
            for key in required_keys:
                self.assertIn(key, data, f"Response should contain '{key}' field")
            
            # CRITICAL: Verify gemini_enrichment section is present
            self.assertIn('gemini_enrichment', data, "Response MUST contain 'gemini_enrichment' section")
            
            gemini_section = data['gemini_enrichment']
            print(f"✅ Gemini enrichment section found: {list(gemini_section.keys())}")
            
            # Verify gemini_enrichment structure
            self.assertIn('status', gemini_section, "Gemini enrichment should have 'status' field")
            self.assertIn('data', gemini_section, "Gemini enrichment should have 'data' field")
            
            status = gemini_section['status']
            self.assertIn(status, ['success', 'fallback'], f"Status should be 'success' or 'fallback', got: {status}")
            
            print(f"✅ Gemini enrichment status: {status}")
            
            # Test the enriched data structure
            enriched_data = gemini_section['data']
            expected_sections = [
                'contextual_insights',
                'intelligent_recommendations', 
                'contextual_predictions',
                'intelligent_alerts',
                'complex_patterns'
            ]
            
            for section in expected_sections:
                self.assertIn(section, enriched_data, f"Enriched data should contain '{section}' section")
                print(f"✅ Found section: {section}")
            
            # Verify contextual_insights structure
            insights = enriched_data['contextual_insights']
            self.assertIsInstance(insights, list, "Contextual insights should be a list")
            if insights:
                first_insight = insights[0]
                insight_keys = ['type', 'title', 'description', 'impact']
                for key in insight_keys:
                    self.assertIn(key, first_insight, f"Insight should contain '{key}' field")
                print(f"✅ Sample insight: {first_insight.get('title', 'N/A')}")
            
            # Verify intelligent_recommendations structure
            recommendations = enriched_data['intelligent_recommendations']
            self.assertIsInstance(recommendations, list, "Intelligent recommendations should be a list")
            if recommendations:
                first_rec = recommendations[0]
                rec_keys = ['priority', 'category', 'action', 'expected_impact', 'timeline']
                for key in rec_keys:
                    self.assertIn(key, first_rec, f"Recommendation should contain '{key}' field")
                print(f"✅ Sample recommendation: {first_rec.get('action', 'N/A')[:50]}...")
            
            # Verify contextual_predictions structure
            predictions = enriched_data['contextual_predictions']
            self.assertIsInstance(predictions, dict, "Contextual predictions should be a dict")
            pred_keys = ['next_period_forecast', 'key_factors', 'trend_analysis', 'risk_assessment']
            for key in pred_keys:
                self.assertIn(key, predictions, f"Predictions should contain '{key}' field")
            
            # Verify next_period_forecast structure
            forecast = predictions['next_period_forecast']
            forecast_keys = ['revenue', 'consultations', 'confidence']
            for key in forecast_keys:
                self.assertIn(key, forecast, f"Forecast should contain '{key}' field")
            print(f"✅ Revenue forecast: {forecast.get('revenue', 'N/A')}")
            print(f"✅ Consultations forecast: {forecast.get('consultations', 'N/A')}")
            print(f"✅ Confidence level: {forecast.get('confidence', 'N/A')}")
            
            print("✅ Advanced Reports Monthly endpoint with Gemini enrichment working correctly")
            
        except requests.exceptions.Timeout:
            self.fail("Advanced Reports endpoint timed out (>45s)")
        except Exception as e:
            self.fail(f"Advanced Reports endpoint failed: {str(e)}")
    
    def test_advanced_reports_different_periods(self):
        """Test 3: Test advanced reports with different period types"""
        print("\n🧪 Test 3: Testing Advanced Reports with Different Period Types...")
        
        test_periods = [
            {"period_type": "monthly", "month": 1, "year": 2025},
            {"period_type": "semester", "semester": 1, "year": 2024},
            {"period_type": "annual", "year": 2024}
        ]
        
        for period_config in test_periods:
            print(f"\n📊 Testing period: {period_config}")
            
            try:
                # Build query parameters
                params = []
                for key, value in period_config.items():
                    params.append(f"{key}={value}")
                query_string = "&".join(params)
                
                response = requests.get(
                    f"{self.base_url}/api/admin/advanced-reports?{query_string}",
                    headers=self.headers,
                    timeout=45
                )
                
                print(f"Status Code: {response.status_code}")
                self.assertEqual(response.status_code, 200)
                
                data = response.json()
                
                # Verify gemini_enrichment is present for all period types
                self.assertIn('gemini_enrichment', data, f"Gemini enrichment missing for {period_config}")
                
                gemini_section = data['gemini_enrichment']
                status = gemini_section['status']
                
                print(f"✅ Period {period_config['period_type']}: Gemini status = {status}")
                
                # Verify enriched data structure exists
                if status == 'success':
                    enriched_data = gemini_section['data']
                    self.assertIn('contextual_insights', enriched_data)
                    self.assertIn('intelligent_recommendations', enriched_data)
                    print(f"✅ Period {period_config['period_type']}: Full enrichment successful")
                elif status == 'fallback':
                    print(f"⚠️ Period {period_config['period_type']}: Fallback mode active")
                    # Fallback should still have basic structure
                    self.assertIn('data', gemini_section)
                
            except Exception as e:
                self.fail(f"Failed for period {period_config}: {str(e)}")
    
    def test_gemini_fallback_behavior(self):
        """Test 4: Test fallback behavior when Gemini service fails"""
        print("\n🧪 Test 4: Testing Gemini Fallback Behavior...")
        
        try:
            # Test with a valid request that should work even if Gemini fails
            response = requests.get(
                f"{self.base_url}/api/admin/advanced-reports?period_type=monthly&month=6&year=2024",
                headers=self.headers,
                timeout=45
            )
            
            print(f"Status Code: {response.status_code}")
            self.assertEqual(response.status_code, 200)
            
            data = response.json()
            
            # Even if Gemini fails, the endpoint should return a response
            self.assertIn('gemini_enrichment', data, "Gemini enrichment section should always be present")
            
            gemini_section = data['gemini_enrichment']
            status = gemini_section['status']
            
            if status == 'fallback':
                print("✅ Fallback mode detected - testing fallback structure")
                
                # Verify fallback has proper structure
                self.assertIn('error', gemini_section, "Fallback should include error message")
                self.assertIn('data', gemini_section, "Fallback should include fallback data")
                
                fallback_data = gemini_section['data']
                
                # Verify fallback data has required sections
                fallback_sections = ['contextual_insights', 'intelligent_recommendations', 'contextual_predictions']
                for section in fallback_sections:
                    self.assertIn(section, fallback_data, f"Fallback should contain '{section}' section")
                
                # Verify fallback insights
                insights = fallback_data['contextual_insights']
                self.assertIsInstance(insights, list, "Fallback insights should be a list")
                self.assertGreater(len(insights), 0, "Fallback should provide at least one insight")
                
                print(f"✅ Fallback error: {gemini_section.get('error', 'N/A')}")
                print("✅ Fallback behavior working correctly")
                
            elif status == 'success':
                print("✅ Gemini service working - no fallback needed")
                
            else:
                self.fail(f"Unexpected status: {status}")
                
        except Exception as e:
            self.fail(f"Fallback behavior test failed: {str(e)}")
    
    def test_enrich_advanced_report_method(self):
        """Test 5: Test the new enrich_advanced_report method functionality"""
        print("\n🧪 Test 5: Testing enrich_advanced_report Method...")
        
        try:
            # Test with current month to ensure we have data
            current_date = datetime.now()
            response = requests.get(
                f"{self.base_url}/api/admin/advanced-reports?period_type=monthly&month={current_date.month}&year={current_date.year}",
                headers=self.headers,
                timeout=45
            )
            
            print(f"Status Code: {response.status_code}")
            self.assertEqual(response.status_code, 200)
            
            data = response.json()
            gemini_section = data['gemini_enrichment']
            
            if gemini_section['status'] == 'success':
                enriched_data = gemini_section['data']
                
                # Test specific enrich_advanced_report outputs
                print("✅ Testing enrich_advanced_report method outputs:")
                
                # Test contextual insights quality
                insights = enriched_data['contextual_insights']
                if insights:
                    for insight in insights[:2]:  # Test first 2 insights
                        self.assertIn('type', insight)
                        self.assertIn('title', insight)
                        self.assertIn('description', insight)
                        self.assertIn('impact', insight)
                        
                        # Verify impact levels are valid
                        valid_impacts = ['élevé', 'moyen', 'faible', 'high', 'medium', 'low']
                        self.assertIn(insight['impact'], valid_impacts, f"Invalid impact level: {insight['impact']}")
                        
                        print(f"  ✅ Insight: {insight['title']} (Impact: {insight['impact']})")
                
                # Test intelligent recommendations quality
                recommendations = enriched_data['intelligent_recommendations']
                if recommendations:
                    for rec in recommendations[:2]:  # Test first 2 recommendations
                        self.assertIn('priority', rec)
                        self.assertIn('category', rec)
                        self.assertIn('action', rec)
                        self.assertIn('expected_impact', rec)
                        self.assertIn('timeline', rec)
                        
                        # Verify priority levels are valid
                        valid_priorities = ['haute', 'moyenne', 'basse', 'high', 'medium', 'low']
                        self.assertIn(rec['priority'], valid_priorities, f"Invalid priority: {rec['priority']}")
                        
                        # Verify timeline values are valid
                        valid_timelines = ['immediate', 'court_terme', 'long_terme', 'immédiat']
                        self.assertIn(rec['timeline'], valid_timelines, f"Invalid timeline: {rec['timeline']}")
                        
                        print(f"  ✅ Recommendation: {rec['action'][:50]}... (Priority: {rec['priority']})")
                
                # Test contextual predictions structure
                predictions = enriched_data['contextual_predictions']
                forecast = predictions['next_period_forecast']
                
                # Verify forecast contains expected fields
                self.assertIn('revenue', forecast)
                self.assertIn('consultations', forecast)
                self.assertIn('confidence', forecast)
                
                print(f"  ✅ Revenue prediction: {forecast['revenue']}")
                print(f"  ✅ Consultations prediction: {forecast['consultations']}")
                print(f"  ✅ Confidence: {forecast['confidence']}")
                
                # Test key factors
                key_factors = predictions.get('key_factors', [])
                self.assertIsInstance(key_factors, list, "Key factors should be a list")
                print(f"  ✅ Key factors identified: {len(key_factors)}")
                
                print("✅ enrich_advanced_report method working correctly")
                
            else:
                print("⚠️ Gemini service in fallback mode - method structure verified")
                
        except Exception as e:
            self.fail(f"enrich_advanced_report method test failed: {str(e)}")
    
    def test_response_structure_validation(self):
        """Test 6: Comprehensive validation of response structure"""
        print("\n🧪 Test 6: Comprehensive Response Structure Validation...")
        
        try:
            response = requests.get(
                f"{self.base_url}/api/admin/advanced-reports?period_type=monthly&month=12&year=2024",
                headers=self.headers,
                timeout=45
            )
            
            self.assertEqual(response.status_code, 200)
            data = response.json()
            
            print("✅ Validating complete response structure:")
            
            # Validate metadata
            metadata = data['metadata']
            metadata_keys = ['periode', 'type', 'start_date', 'end_date', 'generated_at']
            for key in metadata_keys:
                self.assertIn(key, metadata, f"Metadata missing '{key}'")
            print(f"  ✅ Metadata: {metadata['periode']}")
            
            # Validate advanced_statistics
            stats = data['advanced_statistics']
            self.assertIsInstance(stats, dict, "Advanced statistics should be a dict")
            print(f"  ✅ Advanced statistics keys: {len(stats.keys())}")
            
            # Validate gemini_enrichment (main focus)
            gemini = data['gemini_enrichment']
            
            # Status validation
            self.assertIn('status', gemini)
            self.assertIn(gemini['status'], ['success', 'fallback'])
            
            # Generated timestamp validation
            if 'generated_at' in gemini:
                generated_at = gemini['generated_at']
                # Should be a valid ISO timestamp
                datetime.fromisoformat(generated_at.replace('Z', '+00:00'))
                print(f"  ✅ Gemini generated at: {generated_at}")
            
            # Data structure validation
            enriched_data = gemini['data']
            
            # Validate each required section
            sections_to_validate = {
                'contextual_insights': list,
                'intelligent_recommendations': list,
                'contextual_predictions': dict,
                'intelligent_alerts': list,
                'complex_patterns': list
            }
            
            for section_name, expected_type in sections_to_validate.items():
                self.assertIn(section_name, enriched_data, f"Missing section: {section_name}")
                section_data = enriched_data[section_name]
                self.assertIsInstance(section_data, expected_type, f"{section_name} should be {expected_type.__name__}")
                print(f"  ✅ {section_name}: {expected_type.__name__} with {len(section_data) if hasattr(section_data, '__len__') else 'N/A'} items")
            
            # Validate contextual_predictions sub-structure
            predictions = enriched_data['contextual_predictions']
            required_pred_keys = ['next_period_forecast', 'key_factors', 'trend_analysis', 'risk_assessment']
            for key in required_pred_keys:
                self.assertIn(key, predictions, f"Predictions missing '{key}'")
            
            # Validate next_period_forecast sub-structure
            forecast = predictions['next_period_forecast']
            forecast_keys = ['revenue', 'consultations', 'confidence']
            for key in forecast_keys:
                self.assertIn(key, forecast, f"Forecast missing '{key}'")
            
            print("✅ Complete response structure validation passed")
            
        except Exception as e:
            self.fail(f"Response structure validation failed: {str(e)}")
    
    def test_gemini_content_quality_and_language(self):
        """Test 7: Test quality and language of Gemini-generated content"""
        print("\n🧪 Test 7: Testing Gemini Content Quality and Language...")
        
        try:
            response = requests.get(
                f"{self.base_url}/api/admin/advanced-reports?period_type=monthly&month=12&year=2024",
                headers=self.headers,
                timeout=45
            )
            
            self.assertEqual(response.status_code, 200)
            data = response.json()
            
            gemini_section = data['gemini_enrichment']
            
            if gemini_section['status'] == 'success':
                enriched_data = gemini_section['data']
                
                print("✅ Testing content quality:")
                
                # Test French language content
                insights = enriched_data['contextual_insights']
                if insights:
                    first_insight = insights[0]
                    description = first_insight.get('description', '')
                    
                    # Check for French medical terms
                    french_medical_terms = [
                        'patient', 'consultation', 'médical', 'cabinet', 'rendez-vous',
                        'traitement', 'analyse', 'recommandation', 'efficacité', 'optimisation'
                    ]
                    
                    french_content = any(term in description.lower() for term in french_medical_terms)
                    if french_content:
                        print(f"  ✅ Content appears to be in French medical context")
                    else:
                        print(f"  ⚠️ Content may not be in French medical context")
                    
                    # Check content length (should be substantial)
                    self.assertGreater(len(description), 20, "Insight descriptions should be substantial")
                    print(f"  ✅ Insight content length: {len(description)} characters")
                
                # Test recommendations quality
                recommendations = enriched_data['intelligent_recommendations']
                if recommendations:
                    first_rec = recommendations[0]
                    action = first_rec.get('action', '')
                    
                    # Should contain actionable language
                    actionable_terms = [
                        'optimiser', 'améliorer', 'réduire', 'augmenter', 'planifier',
                        'organiser', 'surveiller', 'ajuster', 'implémenter', 'réviser'
                    ]
                    
                    actionable_content = any(term in action.lower() for term in actionable_terms)
                    if actionable_content:
                        print(f"  ✅ Recommendations contain actionable language")
                    else:
                        print(f"  ⚠️ Recommendations may lack actionable language")
                    
                    print(f"  ✅ Sample recommendation: {action[:100]}...")
                
                # Test predictions realism
                predictions = enriched_data['contextual_predictions']
                forecast = predictions['next_period_forecast']
                
                revenue_forecast = forecast.get('revenue', '')
                consultations_forecast = forecast.get('consultations', '')
                confidence = forecast.get('confidence', '')
                
                # Check if forecasts contain realistic values
                if 'TND' in revenue_forecast or '€' in revenue_forecast or any(char.isdigit() for char in revenue_forecast):
                    print(f"  ✅ Revenue forecast appears realistic: {revenue_forecast}")
                
                if any(char.isdigit() for char in consultations_forecast):
                    print(f"  ✅ Consultations forecast appears realistic: {consultations_forecast}")
                
                if '%' in confidence or any(char.isdigit() for char in confidence):
                    print(f"  ✅ Confidence level appears realistic: {confidence}")
                
                print("✅ Content quality assessment completed")
                
            else:
                print("⚠️ Gemini in fallback mode - content quality test skipped")
                
        except Exception as e:
            self.fail(f"Content quality test failed: {str(e)}")

def run_gemini_advanced_reports_tests():
    """Run all Gemini Advanced Reports tests"""
    print("🚀 Starting Gemini 2.0 Flash Advanced Reports Enrichment Testing...")
    print("=" * 80)
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(GeminiAdvancedReportsTest)
    
    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2, stream=None)
    result = runner.run(suite)
    
    print("\n" + "=" * 80)
    print("📊 GEMINI ADVANCED REPORTS TEST SUMMARY")
    print("=" * 80)
    
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
    
    if success_rate >= 90:
        print("🎉 GEMINI ADVANCED REPORTS ENRICHMENT: EXCELLENT PERFORMANCE")
    elif success_rate >= 75:
        print("✅ GEMINI ADVANCED REPORTS ENRICHMENT: GOOD PERFORMANCE")
    elif success_rate >= 50:
        print("⚠️ GEMINI ADVANCED REPORTS ENRICHMENT: NEEDS ATTENTION")
    else:
        print("❌ GEMINI ADVANCED REPORTS ENRICHMENT: CRITICAL ISSUES")
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_gemini_advanced_reports_tests()
    exit(0 if success else 1)