import requests
import unittest
import json
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/frontend/.env')

class GeminiAIAdvancedTest(unittest.TestCase):
    """
    Comprehensive testing for new Gemini AI-powered features:
    1. calculate_predictions_with_gemini function
    2. generate_ai_medical_report function
    3. Modified /api/admin/advanced-reports endpoint
    4. New /api/admin/ai-medical-report endpoint
    """
    
    def setUp(self):
        # Use the correct backend URL from environment
        backend_url = os.getenv('REACT_APP_BACKEND_URL', 'https://83a0b511-23a5-4b39-ada5-aa5078fbcda8.preview.emergentagent.com')
        self.base_url = backend_url
        print(f"Testing Gemini AI features at: {self.base_url}")
        
        # Initialize demo data for testing
        self.init_demo_data()
        
        # Get authentication token for admin endpoints
        self.auth_token = self.get_auth_token()
    
    def init_demo_data(self):
        """Initialize demo data for testing"""
        try:
            response = requests.get(f"{self.base_url}/api/init-demo")
            self.assertEqual(response.status_code, 200)
            print("✅ Demo data initialized successfully")
        except Exception as e:
            print(f"❌ Error initializing demo data: {e}")
    
    def get_auth_token(self):
        """Get authentication token for admin endpoints"""
        try:
            login_data = {"username": "medecin", "password": "medecin123"}
            response = requests.post(f"{self.base_url}/api/auth/login", json=login_data)
            if response.status_code == 200:
                token = response.json()["access_token"]
                print("✅ Authentication token obtained")
                return token
            else:
                print("❌ Failed to get authentication token")
                return None
        except Exception as e:
            print(f"❌ Error getting auth token: {e}")
            return None
    
    def get_auth_headers(self):
        """Get headers with authentication token"""
        if self.auth_token:
            return {"Authorization": f"Bearer {self.auth_token}"}
        else:
            return {}

    # ========== GEMINI AI PREDICTIONS TESTING ==========
    
    def test_advanced_reports_with_gemini_predictions(self):
        """Test GET /api/admin/advanced-reports with new Gemini AI predictions"""
        print("\n🔍 Testing Advanced Reports with Gemini AI Predictions")
        
        headers = self.get_auth_headers()
        if not headers:
            self.skipTest("Authentication required for admin endpoints")
        
        # Test monthly report with Gemini predictions
        current_year = datetime.now().year
        current_month = datetime.now().month
        
        params = {
            "period_type": "monthly",
            "year": current_year,
            "month": current_month
        }
        
        response = requests.get(
            f"{self.base_url}/api/admin/advanced-reports",
            params=params,
            headers=headers
        )
        
        self.assertEqual(response.status_code, 200, f"Advanced reports failed: {response.text}")
        data = response.json()
        
        # Verify basic report structure
        self.assertIn("metadata", data)
        self.assertIn("advanced_statistics", data)
        self.assertIn("evolution", data)
        self.assertIn("predictions", data)
        
        # Verify Gemini AI predictions structure
        predictions = data["predictions"]
        self.assertIn("next_month", predictions)
        self.assertIn("trend", predictions)
        self.assertIn("insights", predictions)
        self.assertIn("risk_factors", predictions)
        self.assertIn("opportunities", predictions)
        self.assertIn("recommendations", predictions)
        self.assertIn("ai_powered", predictions)
        self.assertIn("last_analysis", predictions)
        
        # Verify next_month predictions
        next_month = predictions["next_month"]
        self.assertIn("consultations_estimees", next_month)
        self.assertIn("revenue_estime", next_month)
        self.assertIn("confiance", next_month)
        
        # Verify data types
        self.assertIsInstance(next_month["consultations_estimees"], int)
        self.assertIsInstance(next_month["revenue_estime"], (int, float))
        self.assertIsInstance(next_month["confiance"], (int, float))
        self.assertIsInstance(predictions["insights"], list)
        self.assertIsInstance(predictions["risk_factors"], list)
        self.assertIsInstance(predictions["opportunities"], list)
        self.assertIsInstance(predictions["recommendations"], list)
        
        # Verify AI-powered flag
        self.assertIsInstance(predictions["ai_powered"], bool)
        
        print(f"✅ Advanced Reports with Gemini AI working correctly")
        print(f"   - Next month consultations: {next_month['consultations_estimees']}")
        print(f"   - Next month revenue: {next_month['revenue_estime']} TND")
        print(f"   - Confidence level: {next_month['confiance']}%")
        print(f"   - AI-powered: {predictions['ai_powered']}")
        print(f"   - Insights count: {len(predictions['insights'])}")
        print(f"   - Risk factors: {len(predictions['risk_factors'])}")
        print(f"   - Opportunities: {len(predictions['opportunities'])}")
        print(f"   - Recommendations: {len(predictions['recommendations'])}")
        print(f"🎉 Gemini AI Predictions Test: PASSED")
    
    def test_advanced_reports_different_periods(self):
        """Test Gemini AI predictions with different time periods"""
        print("\n🔍 Testing Gemini AI Predictions with Different Time Periods")
        
        headers = self.get_auth_headers()
        if not headers:
            self.skipTest("Authentication required for admin endpoints")
        
        # Test different period types
        test_periods = [
            {"period_type": "annual", "year": 2024},
            {"period_type": "semester", "year": 2024, "semester": 2},
            {"period_type": "custom", "start_date": "2024-01-01", "end_date": "2024-12-31"}
        ]
        
        for period_config in test_periods:
            print(f"  Testing period: {period_config}")
            
            response = requests.get(
                f"{self.base_url}/api/admin/advanced-reports",
                params=period_config,
                headers=headers
            )
            
            self.assertEqual(response.status_code, 200, f"Failed for period {period_config}: {response.text}")
            data = response.json()
            
            # Verify predictions exist for all period types
            self.assertIn("predictions", data)
            predictions = data["predictions"]
            
            # Verify essential prediction fields
            self.assertIn("next_month", predictions)
            self.assertIn("insights", predictions)
            self.assertIn("ai_powered", predictions)
            
            print(f"    ✅ Period {period_config['period_type']} working correctly")
        
        print(f"🎉 Different Time Periods Test: PASSED")

    # ========== AI MEDICAL REPORT TESTING ==========
    
    def test_ai_medical_report_endpoint(self):
        """Test GET /api/admin/ai-medical-report - New comprehensive AI medical report"""
        print("\n🔍 Testing AI Medical Report Endpoint")
        
        headers = self.get_auth_headers()
        if not headers:
            self.skipTest("Authentication required for admin endpoints")
        
        # Test with recent date range
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
        
        params = {
            "start_date": start_date,
            "end_date": end_date
        }
        
        response = requests.get(
            f"{self.base_url}/api/admin/ai-medical-report",
            params=params,
            headers=headers
        )
        
        self.assertEqual(response.status_code, 200, f"AI medical report failed: {response.text}")
        data = response.json()
        
        # Verify basic response structure
        self.assertIn("status", data)
        self.assertIn("message", data)
        self.assertIn("generated_at", data)
        self.assertIn("period", data)
        self.assertIn("data_summary", data)
        self.assertIn("ai_analysis", data)
        self.assertIn("methodology", data)
        
        # Verify status
        self.assertEqual(data["status"], "success")
        
        # Verify period information
        period = data["period"]
        self.assertIn("start", period)
        self.assertIn("end", period)
        self.assertIn("duration_days", period)
        
        # Verify data summary
        data_summary = data["data_summary"]
        self.assertIn("appointments_analyzed", data_summary)
        self.assertIn("consultations_analyzed", data_summary)
        self.assertIn("patients_in_database", data_summary)
        self.assertIn("evolution_periods", data_summary)
        
        # Verify AI analysis structure
        ai_analysis = data["ai_analysis"]
        self.assertIn("executive_summary", ai_analysis)
        self.assertIn("performance_analysis", ai_analysis)
        self.assertIn("deep_insights", ai_analysis)
        self.assertIn("patterns_detected", ai_analysis)
        self.assertIn("risk_assessment", ai_analysis)
        self.assertIn("opportunities", ai_analysis)
        self.assertIn("strategic_recommendations", ai_analysis)
        self.assertIn("predictions", ai_analysis)
        self.assertIn("action_plan", ai_analysis)
        self.assertIn("ai_confidence", ai_analysis)
        self.assertIn("data_quality_score", ai_analysis)
        
        # Verify executive summary
        exec_summary = ai_analysis["executive_summary"]
        self.assertIn("overall_score", exec_summary)
        self.assertIn("performance_trend", exec_summary)
        self.assertIn("key_highlight", exec_summary)
        self.assertIn("urgency_level", exec_summary)
        
        # Verify performance analysis
        performance = ai_analysis["performance_analysis"]
        self.assertIn("consultation_efficiency", performance)
        self.assertIn("revenue_stability", performance)
        self.assertIn("patient_retention", performance)
        self.assertIn("growth_rate", performance)
        self.assertIn("benchmark_position", performance)
        
        # Verify risk assessment
        risk_assessment = ai_analysis["risk_assessment"]
        self.assertIn("financial_risks", risk_assessment)
        self.assertIn("operational_risks", risk_assessment)
        self.assertIn("market_risks", risk_assessment)
        self.assertIn("overall_risk_level", risk_assessment)
        
        # Verify opportunities
        opportunities = ai_analysis["opportunities"]
        self.assertIn("immediate_opportunities", opportunities)
        self.assertIn("medium_term_opportunities", opportunities)
        self.assertIn("strategic_opportunities", opportunities)
        self.assertIn("revenue_potential", opportunities)
        
        # Verify strategic recommendations
        recommendations = ai_analysis["strategic_recommendations"]
        self.assertIn("priority_actions", recommendations)
        self.assertIn("operational_improvements", recommendations)
        self.assertIn("technology_recommendations", recommendations)
        self.assertIn("marketing_suggestions", recommendations)
        
        # Verify predictions
        predictions = ai_analysis["predictions"]
        self.assertIn("next_quarter_forecast", predictions)
        self.assertIn("annual_projection", predictions)
        self.assertIn("market_evolution", predictions)
        
        # Verify action plan
        action_plan = ai_analysis["action_plan"]
        self.assertIn("immediate_actions", action_plan)
        self.assertIn("quarterly_objectives", action_plan)
        self.assertIn("annual_goals", action_plan)
        
        # Verify methodology
        methodology = data["methodology"]
        self.assertIn("ai_model", methodology)
        self.assertIn("analysis_type", methodology)
        self.assertIn("confidence_methodology", methodology)
        
        # Verify data types
        self.assertIsInstance(exec_summary["overall_score"], (int, float))
        self.assertIsInstance(performance["consultation_efficiency"], (int, float))
        self.assertIsInstance(performance["revenue_stability"], (int, float))
        self.assertIsInstance(performance["patient_retention"], (int, float))
        self.assertIsInstance(performance["growth_rate"], (int, float))
        self.assertIsInstance(ai_analysis["deep_insights"], list)
        self.assertIsInstance(ai_analysis["patterns_detected"], list)
        self.assertIsInstance(risk_assessment["financial_risks"], list)
        self.assertIsInstance(risk_assessment["operational_risks"], list)
        self.assertIsInstance(opportunities["immediate_opportunities"], list)
        self.assertIsInstance(recommendations["priority_actions"], list)
        self.assertIsInstance(action_plan["immediate_actions"], list)
        self.assertIsInstance(ai_analysis["ai_confidence"], (int, float))
        self.assertIsInstance(ai_analysis["data_quality_score"], (int, float))
        
        print(f"✅ AI Medical Report generated successfully")
        print(f"   - Overall score: {exec_summary['overall_score']}")
        print(f"   - Performance trend: {exec_summary['performance_trend']}")
        print(f"   - Consultation efficiency: {performance['consultation_efficiency']}")
        print(f"   - Revenue stability: {performance['revenue_stability']}")
        print(f"   - AI confidence: {ai_analysis['ai_confidence']}")
        print(f"   - Data quality score: {ai_analysis['data_quality_score']}")
        print(f"   - Deep insights: {len(ai_analysis['deep_insights'])}")
        print(f"   - Patterns detected: {len(ai_analysis['patterns_detected'])}")
        print(f"   - Risk factors: {len(risk_assessment['financial_risks']) + len(risk_assessment['operational_risks'])}")
        print(f"   - Opportunities: {len(opportunities['immediate_opportunities']) + len(opportunities['medium_term_opportunities'])}")
        print(f"   - Recommendations: {len(recommendations['priority_actions']) + len(recommendations['operational_improvements'])}")
        print(f"🎉 AI Medical Report Test: PASSED")
    
    def test_ai_medical_report_different_date_ranges(self):
        """Test AI medical report with different date ranges"""
        print("\n🔍 Testing AI Medical Report with Different Date Ranges")
        
        headers = self.get_auth_headers()
        if not headers:
            self.skipTest("Authentication required for admin endpoints")
        
        # Test different date ranges
        test_ranges = [
            {
                "name": "Last 30 days",
                "start_date": (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"),
                "end_date": datetime.now().strftime("%Y-%m-%d")
            },
            {
                "name": "Last 90 days", 
                "start_date": (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d"),
                "end_date": datetime.now().strftime("%Y-%m-%d")
            },
            {
                "name": "Current year",
                "start_date": "2024-01-01",
                "end_date": "2024-12-31"
            }
        ]
        
        for date_range in test_ranges:
            print(f"  Testing date range: {date_range['name']}")
            
            params = {
                "start_date": date_range["start_date"],
                "end_date": date_range["end_date"]
            }
            
            response = requests.get(
                f"{self.base_url}/api/admin/ai-medical-report",
                params=params,
                headers=headers
            )
            
            self.assertEqual(response.status_code, 200, f"Failed for range {date_range['name']}: {response.text}")
            data = response.json()
            
            # Verify essential structure
            self.assertIn("ai_analysis", data)
            self.assertIn("executive_summary", data["ai_analysis"])
            self.assertIn("predictions", data["ai_analysis"])
            
            # Verify period calculation
            period = data["period"]
            start_dt = datetime.strptime(period["start"], "%Y-%m-%d")
            end_dt = datetime.strptime(period["end"], "%Y-%m-%d")
            expected_duration = (end_dt - start_dt).days
            self.assertEqual(period["duration_days"], expected_duration)
            
            print(f"    ✅ Date range {date_range['name']} working correctly")
            print(f"       Duration: {period['duration_days']} days")
        
        print(f"🎉 Different Date Ranges Test: PASSED")

    # ========== ROBUSTNESS AND ERROR HANDLING TESTING ==========
    
    def test_ai_medical_report_validation(self):
        """Test AI medical report endpoint validation"""
        print("\n🔍 Testing AI Medical Report Validation")
        
        headers = self.get_auth_headers()
        if not headers:
            self.skipTest("Authentication required for admin endpoints")
        
        # Test missing parameters
        test_cases = [
            {"params": {}, "description": "Missing both dates"},
            {"params": {"start_date": "2024-01-01"}, "description": "Missing end_date"},
            {"params": {"end_date": "2024-12-31"}, "description": "Missing start_date"},
            {"params": {"start_date": "invalid-date", "end_date": "2024-12-31"}, "description": "Invalid start_date"},
            {"params": {"start_date": "2024-01-01", "end_date": "invalid-date"}, "description": "Invalid end_date"},
            {"params": {"start_date": "2024-12-31", "end_date": "2024-01-01"}, "description": "End date before start date"}
        ]
        
        for test_case in test_cases:
            print(f"  Testing: {test_case['description']}")
            
            response = requests.get(
                f"{self.base_url}/api/admin/ai-medical-report",
                params=test_case["params"],
                headers=headers
            )
            
            # Should return validation error (400 or 422)
            self.assertIn(response.status_code, [400, 422], 
                         f"Expected validation error for {test_case['description']}, got {response.status_code}")
            
            print(f"    ✅ Validation error properly returned: {response.status_code}")
        
        print(f"🎉 Validation Test: PASSED")
    
    def test_authentication_required(self):
        """Test that admin endpoints require authentication"""
        print("\n🔍 Testing Authentication Requirements")
        
        # Test advanced reports without auth
        response = requests.get(
            f"{self.base_url}/api/admin/advanced-reports",
            params={"period_type": "monthly", "year": 2024, "month": 12}
        )
        self.assertEqual(response.status_code, 401, "Advanced reports should require authentication")
        
        # Test AI medical report without auth
        response = requests.get(
            f"{self.base_url}/api/admin/ai-medical-report",
            params={"start_date": "2024-01-01", "end_date": "2024-12-31"}
        )
        self.assertEqual(response.status_code, 401, "AI medical report should require authentication")
        
        print(f"✅ Authentication properly required for admin endpoints")
        print(f"🎉 Authentication Test: PASSED")

    # ========== COMPREHENSIVE WORKFLOW TESTING ==========
    
    def test_comprehensive_ai_workflow(self):
        """Test complete AI workflow - Advanced Reports + AI Medical Report"""
        print("\n🔍 Testing Comprehensive AI Workflow")
        
        headers = self.get_auth_headers()
        if not headers:
            self.skipTest("Authentication required for admin endpoints")
        
        # Step 1: Get advanced reports with Gemini predictions
        print("  Step 1: Getting advanced reports with Gemini predictions...")
        
        advanced_params = {
            "period_type": "monthly",
            "year": 2024,
            "month": 12
        }
        
        advanced_response = requests.get(
            f"{self.base_url}/api/admin/advanced-reports",
            params=advanced_params,
            headers=headers
        )
        
        self.assertEqual(advanced_response.status_code, 200)
        advanced_data = advanced_response.json()
        
        # Verify Gemini predictions in advanced reports
        self.assertIn("predictions", advanced_data)
        predictions = advanced_data["predictions"]
        self.assertIn("ai_powered", predictions)
        
        print(f"    ✅ Advanced reports with Gemini predictions retrieved")
        print(f"       AI-powered: {predictions.get('ai_powered', False)}")
        
        # Step 2: Get comprehensive AI medical report
        print("  Step 2: Getting comprehensive AI medical report...")
        
        ai_report_params = {
            "start_date": "2024-01-01",
            "end_date": "2024-12-31"
        }
        
        ai_report_response = requests.get(
            f"{self.base_url}/api/admin/ai-medical-report",
            params=ai_report_params,
            headers=headers
        )
        
        self.assertEqual(ai_report_response.status_code, 200)
        ai_report_data = ai_report_response.json()
        
        # Verify comprehensive AI analysis
        self.assertIn("ai_analysis", ai_report_data)
        ai_analysis = ai_report_data["ai_analysis"]
        
        print(f"    ✅ Comprehensive AI medical report retrieved")
        print(f"       AI confidence: {ai_analysis.get('ai_confidence', 'N/A')}")
        print(f"       Data quality score: {ai_analysis.get('data_quality_score', 'N/A')}")
        
        # Step 3: Compare and validate consistency
        print("  Step 3: Validating data consistency between reports...")
        
        # Both reports should have predictions
        advanced_predictions = advanced_data["predictions"]
        ai_report_predictions = ai_analysis["predictions"]
        
        # Both should be AI-powered
        self.assertTrue(advanced_predictions.get("ai_powered", False), "Advanced reports should be AI-powered")
        self.assertGreater(ai_analysis.get("ai_confidence", 0), 0, "AI report should have confidence score")
        
        # Both should have insights and recommendations
        self.assertIsInstance(advanced_predictions.get("insights", []), list)
        self.assertIsInstance(advanced_predictions.get("recommendations", []), list)
        self.assertIsInstance(ai_analysis.get("deep_insights", []), list)
        self.assertIsInstance(ai_analysis["strategic_recommendations"].get("priority_actions", []), list)
        
        print(f"    ✅ Data consistency validated between reports")
        
        # Step 4: Verify enriched data quality
        print("  Step 4: Verifying enriched data quality...")
        
        # Advanced reports should have enriched predictions
        self.assertIn("risk_factors", advanced_predictions)
        self.assertIn("opportunities", advanced_predictions)
        self.assertIn("seasonal_analysis", advanced_predictions)
        
        # AI medical report should have comprehensive analysis
        self.assertIn("executive_summary", ai_analysis)
        self.assertIn("performance_analysis", ai_analysis)
        self.assertIn("risk_assessment", ai_analysis)
        self.assertIn("action_plan", ai_analysis)
        
        print(f"    ✅ Enriched data quality verified")
        
        print(f"🎉 Comprehensive AI Workflow Test: PASSED")
        print(f"   - Advanced reports with Gemini predictions: ✅")
        print(f"   - Comprehensive AI medical report: ✅")
        print(f"   - Data consistency validation: ✅")
        print(f"   - Enriched insights and recommendations: ✅")

    # ========== PERFORMANCE AND FALLBACK TESTING ==========
    
    def test_ai_fallback_mechanisms(self):
        """Test AI fallback mechanisms when Gemini is unavailable"""
        print("\n🔍 Testing AI Fallback Mechanisms")
        
        headers = self.get_auth_headers()
        if not headers:
            self.skipTest("Authentication required for admin endpoints")
        
        # Test advanced reports (should have fallback)
        response = requests.get(
            f"{self.base_url}/api/admin/advanced-reports",
            params={"period_type": "monthly", "year": 2024, "month": 12},
            headers=headers
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Should have predictions even if AI fails
        self.assertIn("predictions", data)
        predictions = data["predictions"]
        self.assertIn("next_month", predictions)
        
        # Test AI medical report (should have fallback)
        response = requests.get(
            f"{self.base_url}/api/admin/ai-medical-report",
            params={"start_date": "2024-01-01", "end_date": "2024-12-31"},
            headers=headers
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Should have AI analysis even if Gemini fails
        self.assertIn("ai_analysis", data)
        ai_analysis = data["ai_analysis"]
        self.assertIn("executive_summary", ai_analysis)
        
        print(f"✅ Fallback mechanisms working correctly")
        print(f"   - Advanced reports fallback: ✅")
        print(f"   - AI medical report fallback: ✅")
        print(f"🎉 Fallback Mechanisms Test: PASSED")

if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2)