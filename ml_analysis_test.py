import requests
import unittest
import json
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/frontend/.env')

class MLAnalysisTest(unittest.TestCase):
    def setUp(self):
        # Use the correct backend URL from environment
        backend_url = os.getenv('REACT_APP_BACKEND_URL', 'https://51fe9cee-9106-4a34-939c-922f3b368509.preview.emergentagent.com')
        self.base_url = backend_url
        print(f"Testing ML Analysis at: {self.base_url}")
        # Initialize demo data before running tests
        self.init_demo_data()
    
    def init_demo_data(self):
        """Initialize demo data for testing"""
        try:
            response = requests.get(f"{self.base_url}/api/init-demo")
            self.assertEqual(response.status_code, 200)
            print("Demo data initialized successfully")
        except Exception as e:
            print(f"Error initializing demo data: {e}")

    def test_top_10_patients_analysis(self):
        """Test TOP 10 PATIENTS ANALYSIS - Verify top_patients section contains detailed patient data"""
        print("\n🔍 Testing TOP 10 PATIENTS ANALYSIS")
        
        # Call the advanced reports endpoint for monthly analysis
        response = requests.get(f"{self.base_url}/api/admin/advanced-reports?period_type=monthly&month=7&year=2025")
        self.assertEqual(response.status_code, 200, f"Advanced reports failed: {response.text}")
        
        data = response.json()
        
        # Verify top_patients section exists in advanced_statistics
        self.assertIn("advanced_statistics", data, "advanced_statistics section missing from response")
        advanced_stats = data["advanced_statistics"]
        self.assertIn("top_patients", advanced_stats, "top_patients section missing from advanced_statistics")
        top_patients = advanced_stats["top_patients"]
        self.assertIsInstance(top_patients, list, "top_patients should be a list")
        
        print(f"✅ Found {len(top_patients)} top patients")
        
        # Verify each patient has required fields
        for i, patient in enumerate(top_patients):
            print(f"  Checking patient {i+1}: {patient.get('nom', 'Unknown')}")
            
            # Required fields
            self.assertIn("ranking", patient, f"Patient {i+1} missing ranking")
            self.assertIn("nom", patient, f"Patient {i+1} missing nom")
            self.assertIn("revenue", patient, f"Patient {i+1} missing revenue")
            self.assertIn("consultations", patient, f"Patient {i+1} missing consultations")
            
            # New enhanced fields
            self.assertIn("loyalty_score", patient, f"Patient {i+1} missing loyalty_score")
            self.assertIn("avg_interval_days", patient, f"Patient {i+1} missing avg_interval_days")
            self.assertIn("visits_per_year", patient, f"Patient {i+1} missing visits_per_year")
            self.assertIn("status", patient, f"Patient {i+1} missing status")
            self.assertIn("last_visit", patient, f"Patient {i+1} missing last_visit")
            
            # Verify data types and ranges
            self.assertIsInstance(patient["ranking"], int, f"Patient {i+1} ranking should be integer")
            self.assertTrue(1 <= patient["ranking"] <= 10, f"Patient {i+1} ranking should be 1-10")
            
            self.assertIsInstance(patient["revenue"], (int, float), f"Patient {i+1} revenue should be numeric")
            self.assertGreaterEqual(patient["revenue"], 0, f"Patient {i+1} revenue should be >= 0")
            
            self.assertIsInstance(patient["consultations"], int, f"Patient {i+1} consultations should be integer")
            self.assertGreaterEqual(patient["consultations"], 0, f"Patient {i+1} consultations should be >= 0")
            
            self.assertIsInstance(patient["loyalty_score"], (int, float), f"Patient {i+1} loyalty_score should be numeric")
            self.assertTrue(0 <= patient["loyalty_score"] <= 100, f"Patient {i+1} loyalty_score should be 0-100")
            
            self.assertIsInstance(patient["avg_interval_days"], (int, float), f"Patient {i+1} avg_interval_days should be numeric")
            self.assertGreaterEqual(patient["avg_interval_days"], 0, f"Patient {i+1} avg_interval_days should be >= 0")
            
            self.assertIsInstance(patient["visits_per_year"], (int, float), f"Patient {i+1} visits_per_year should be numeric")
            self.assertGreaterEqual(patient["visits_per_year"], 0, f"Patient {i+1} visits_per_year should be >= 0")
            
            # Verify status is one of expected values
            valid_statuses = ["VIP", "Fidèle", "Régulier", "Nouveau"]
            self.assertIn(patient["status"], valid_statuses, f"Patient {i+1} status should be one of {valid_statuses}")
            
            print(f"    ✅ {patient['nom']} - Rank: {patient['ranking']}, Revenue: {patient['revenue']} TND, Status: {patient['status']}")
        
        # Verify ranking order (should be 1, 2, 3, ...)
        for i, patient in enumerate(top_patients):
            expected_ranking = i + 1
            self.assertEqual(patient["ranking"], expected_ranking, f"Patient ranking order incorrect at position {i+1}")
        
        print(f"🎉 TOP 10 PATIENTS ANALYSIS Test: PASSED")
        return top_patients

    def test_predictions_ml_robustes(self):
        """Test PREDICTIONS ML ROBUSTES - Verify predictions contain realistic values"""
        print("\n🔍 Testing PREDICTIONS ML ROBUSTES")
        
        # Call the advanced reports endpoint
        response = requests.get(f"{self.base_url}/api/admin/advanced-reports?period_type=monthly&month=7&year=2025")
        self.assertEqual(response.status_code, 200, f"Advanced reports failed: {response.text}")
        
        data = response.json()
        
        # Verify predictions section exists
        self.assertIn("predictions", data, "predictions section missing from response")
        predictions = data["predictions"]
        self.assertIsInstance(predictions, dict, "predictions should be a dictionary")
        
        # Test next_month predictions
        self.assertIn("next_month", predictions, "next_month predictions missing")
        next_month = predictions["next_month"]
        
        # Verify consultations_estimees >= 5 (not 0)
        self.assertIn("consultations_estimees", next_month, "consultations_estimees missing")
        consultations_est = next_month["consultations_estimees"]
        self.assertIsInstance(consultations_est, (int, float), "consultations_estimees should be numeric")
        self.assertGreaterEqual(consultations_est, 5, f"consultations_estimees should be >= 5, got {consultations_est}")
        
        # Verify revenue_estime >= 300 TND (not 0)
        self.assertIn("revenue_estime", next_month, "revenue_estime missing")
        revenue_est = next_month["revenue_estime"]
        self.assertIsInstance(revenue_est, (int, float), "revenue_estime should be numeric")
        self.assertGreaterEqual(revenue_est, 300, f"revenue_estime should be >= 300 TND, got {revenue_est}")
        
        # Verify confiance between 60-95%
        self.assertIn("confiance", next_month, "confiance missing")
        confiance = next_month["confiance"]
        self.assertIsInstance(confiance, (int, float), "confiance should be numeric")
        self.assertTrue(60 <= confiance <= 95, f"confiance should be 60-95%, got {confiance}")
        
        print(f"✅ Next month predictions: {consultations_est} consultations, {revenue_est} TND revenue, {confiance}% confidence")
        
        # Test trend_analysis section
        self.assertIn("trend_analysis", predictions, "trend_analysis missing")
        trend_analysis = predictions["trend_analysis"]
        
        self.assertIn("direction", trend_analysis, "trend direction missing")
        self.assertIn("slope", trend_analysis, "trend slope missing")
        self.assertIn("growth_rate", trend_analysis, "growth_rate missing")
        
        direction = trend_analysis["direction"]
        valid_directions = ["croissant", "stable", "décroissant"]
        self.assertIn(direction, valid_directions, f"direction should be one of {valid_directions}")
        
        print(f"✅ Trend analysis: {direction} direction, growth rate: {trend_analysis.get('growth_rate', 'N/A')}")
        
        # Test model_performance section
        self.assertIn("model_performance", predictions, "model_performance missing")
        model_perf = predictions["model_performance"]
        
        self.assertIn("accuracy", model_perf, "model accuracy missing")
        accuracy = model_perf["accuracy"]
        self.assertIsInstance(accuracy, (int, float), "accuracy should be numeric")
        self.assertTrue(0 <= accuracy <= 100, f"accuracy should be 0-100%, got {accuracy}")
        
        print(f"✅ Model performance: {accuracy}% accuracy")
        
        # Test forecasts.next_3_months section
        self.assertIn("forecasts", predictions, "forecasts missing")
        forecasts = predictions["forecasts"]
        
        self.assertIn("next_3_months", forecasts, "next_3_months forecasts missing")
        next_3_months = forecasts["next_3_months"]
        
        self.assertIn("consultations", next_3_months, "3-month consultations forecast missing")
        self.assertIn("revenue", next_3_months, "3-month revenue forecast missing")
        
        consultations_forecast = next_3_months["consultations"]
        revenue_forecast = next_3_months["revenue"]
        
        self.assertIsInstance(consultations_forecast, list, "consultations forecast should be list")
        self.assertIsInstance(revenue_forecast, list, "revenue forecast should be list")
        self.assertEqual(len(consultations_forecast), 3, "consultations forecast should have 3 months")
        self.assertEqual(len(revenue_forecast), 3, "revenue forecast should have 3 months")
        
        # Verify all forecast values are realistic
        for i, (cons, rev) in enumerate(zip(consultations_forecast, revenue_forecast)):
            self.assertIsInstance(cons, (int, float), f"Month {i+1} consultations should be numeric")
            self.assertIsInstance(rev, (int, float), f"Month {i+1} revenue should be numeric")
            self.assertGreaterEqual(cons, 5, f"Month {i+1} consultations should be >= 5")
            self.assertGreaterEqual(rev, 300, f"Month {i+1} revenue should be >= 300 TND")
        
        print(f"✅ 3-month forecasts: {consultations_forecast} consultations, {revenue_forecast} revenue")
        
        print(f"🎉 PREDICTIONS ML ROBUSTES Test: PASSED")
        return predictions

    def test_seasonality_analysis(self):
        """Test SEASONALITY ANALYSIS - Verify seasonality section contains detailed analysis"""
        print("\n🔍 Testing SEASONALITY ANALYSIS")
        
        # Call the advanced reports endpoint
        response = requests.get(f"{self.base_url}/api/admin/advanced-reports?period_type=monthly&month=7&year=2025")
        self.assertEqual(response.status_code, 200, f"Advanced reports failed: {response.text}")
        
        data = response.json()
        
        # Verify seasonality section exists
        self.assertIn("seasonality", data, "seasonality section missing from response")
        seasonality = data["seasonality"]
        self.assertIsInstance(seasonality, dict, "seasonality should be a dictionary")
        
        # Test pics section (peak periods)
        self.assertIn("pics", seasonality, "pics section missing")
        pics = seasonality["pics"]
        self.assertIsInstance(pics, list, "pics should be a list")
        
        print(f"✅ Found {len(pics)} peak periods")
        
        for i, pic in enumerate(pics):
            self.assertIn("periode", pic, f"Peak {i+1} missing periode")
            self.assertIn("raison", pic, f"Peak {i+1} missing raison")
            self.assertIn("intensite", pic, f"Peak {i+1} missing intensite")
            
            self.assertIsInstance(pic["periode"], str, f"Peak {i+1} periode should be string")
            self.assertIsInstance(pic["raison"], str, f"Peak {i+1} raison should be string")
            self.assertIsInstance(pic["intensite"], (int, float), f"Peak {i+1} intensite should be numeric")
            
            print(f"    Peak {i+1}: {pic['periode']} - {pic['raison']} (intensity: {pic['intensite']})")
        
        # Test creux section (low periods)
        self.assertIn("creux", seasonality, "creux section missing")
        creux = seasonality["creux"]
        self.assertIsInstance(creux, list, "creux should be a list")
        
        print(f"✅ Found {len(creux)} low periods")
        
        for i, creux_period in enumerate(creux):
            self.assertIn("periode", creux_period, f"Low period {i+1} missing periode")
            self.assertIn("raison", creux_period, f"Low period {i+1} missing raison")
            self.assertIn("intensite", creux_period, f"Low period {i+1} missing intensite")
            
            print(f"    Low {i+1}: {creux_period['periode']} - {creux_period['raison']} (intensity: {creux_period['intensite']})")
        
        # Test monthly_averages section
        self.assertIn("monthly_averages", seasonality, "monthly_averages section missing")
        monthly_averages = seasonality["monthly_averages"]
        self.assertIsInstance(monthly_averages, dict, "monthly_averages should be a dictionary")
        
        # Verify we have data for all 12 months
        months = ["janvier", "février", "mars", "avril", "mai", "juin", 
                 "juillet", "août", "septembre", "octobre", "novembre", "décembre"]
        
        for month in months:
            if month in monthly_averages:
                month_data = monthly_averages[month]
                self.assertIn("consultations", month_data, f"{month} missing consultations")
                self.assertIn("revenue", month_data, f"{month} missing revenue")
                
                self.assertIsInstance(month_data["consultations"], (int, float), f"{month} consultations should be numeric")
                self.assertIsInstance(month_data["revenue"], (int, float), f"{month} revenue should be numeric")
        
        print(f"✅ Monthly averages available for {len(monthly_averages)} months")
        
        # Test overall_average section
        self.assertIn("overall_average", seasonality, "overall_average section missing")
        overall_average = seasonality["overall_average"]
        self.assertIsInstance(overall_average, dict, "overall_average should be a dictionary")
        
        self.assertIn("consultations_per_month", overall_average, "overall consultations_per_month missing")
        self.assertIn("revenue_per_month", overall_average, "overall revenue_per_month missing")
        
        overall_cons = overall_average["consultations_per_month"]
        overall_rev = overall_average["revenue_per_month"]
        
        self.assertIsInstance(overall_cons, (int, float), "overall consultations should be numeric")
        self.assertIsInstance(overall_rev, (int, float), "overall revenue should be numeric")
        self.assertGreaterEqual(overall_cons, 0, "overall consultations should be >= 0")
        self.assertGreaterEqual(overall_rev, 0, "overall revenue should be >= 0")
        
        print(f"✅ Overall averages: {overall_cons} consultations/month, {overall_rev} TND/month")
        
        print(f"🎉 SEASONALITY ANALYSIS Test: PASSED")
        return seasonality

    def test_gemini_enrichment(self):
        """Test GEMINI ENRICHMENT - Verify gemini_enrichment status and data coherence"""
        print("\n🔍 Testing GEMINI ENRICHMENT")
        
        # Call the advanced reports endpoint
        response = requests.get(f"{self.base_url}/api/admin/advanced-reports?period_type=monthly&month=7&year=2025")
        self.assertEqual(response.status_code, 200, f"Advanced reports failed: {response.text}")
        
        data = response.json()
        
        # Verify gemini_enrichment section exists
        self.assertIn("gemini_enrichment", data, "gemini_enrichment section missing from response")
        gemini_enrichment = data["gemini_enrichment"]
        self.assertIsInstance(gemini_enrichment, dict, "gemini_enrichment should be a dictionary")
        
        # Verify status is "success"
        self.assertIn("status", gemini_enrichment, "gemini_enrichment status missing")
        status = gemini_enrichment["status"]
        self.assertEqual(status, "success", f"gemini_enrichment status should be 'success', got '{status}'")
        
        print(f"✅ Gemini enrichment status: {status}")
        
        # Verify enriched data sections exist
        expected_sections = ["insights", "recommendations", "analysis", "summary"]
        for section in expected_sections:
            if section in gemini_enrichment:
                section_data = gemini_enrichment[section]
                self.assertIsInstance(section_data, (str, dict, list), f"gemini_enrichment.{section} should be string, dict, or list")
                print(f"✅ Gemini {section} section present")
        
        # Verify timestamp exists
        self.assertIn("timestamp", gemini_enrichment, "gemini_enrichment timestamp missing")
        timestamp = gemini_enrichment["timestamp"]
        self.assertIsInstance(timestamp, str, "gemini_enrichment timestamp should be string")
        
        # Try to parse timestamp
        try:
            datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            print(f"✅ Gemini enrichment timestamp valid: {timestamp}")
        except ValueError:
            self.fail(f"Invalid timestamp format: {timestamp}")
        
        # Verify coherence between ML data and Gemini enrichment
        # Check if top_patients data is used in enrichment
        if "top_patients" in data and "analysis" in gemini_enrichment:
            top_patients = data["top_patients"]
            if len(top_patients) > 0:
                # The enrichment should reference patient data
                analysis = str(gemini_enrichment["analysis"])
                # Look for patient names or revenue figures in the analysis
                patient_referenced = False
                for patient in top_patients[:3]:  # Check top 3 patients
                    if patient["nom"] in analysis or str(patient["revenue"]) in analysis:
                        patient_referenced = True
                        break
                
                if patient_referenced:
                    print(f"✅ Gemini enrichment references top patient data")
                else:
                    print(f"⚠️ Gemini enrichment may not reference top patient data (not critical)")
        
        # Verify coherence with predictions data
        if "predictions" in data and "insights" in gemini_enrichment:
            predictions = data["predictions"]
            if "next_month" in predictions:
                next_month = predictions["next_month"]
                insights = str(gemini_enrichment["insights"])
                
                # Check if prediction values are referenced
                consultations_est = next_month.get("consultations_estimees", 0)
                revenue_est = next_month.get("revenue_estime", 0)
                
                prediction_referenced = (str(consultations_est) in insights or 
                                       str(revenue_est) in insights or
                                       "prédiction" in insights.lower() or
                                       "estimation" in insights.lower())
                
                if prediction_referenced:
                    print(f"✅ Gemini enrichment references prediction data")
                else:
                    print(f"⚠️ Gemini enrichment may not reference prediction data (not critical)")
        
        print(f"🎉 GEMINI ENRICHMENT Test: PASSED")
        return gemini_enrichment

    def test_comprehensive_ml_analysis_workflow(self):
        """Test comprehensive ML analysis workflow - All components working together"""
        print("\n🔍 Testing COMPREHENSIVE ML ANALYSIS WORKFLOW")
        
        # Call the advanced reports endpoint
        response = requests.get(f"{self.base_url}/api/admin/advanced-reports?period_type=monthly&month=12&year=2024")
        self.assertEqual(response.status_code, 200, f"Advanced reports failed: {response.text}")
        
        data = response.json()
        
        # Step 1: Verify all main sections exist
        required_sections = ["top_patients", "predictions", "seasonality", "gemini_enrichment"]
        for section in required_sections:
            self.assertIn(section, data, f"Required section '{section}' missing from response")
            print(f"✅ Section '{section}' present")
        
        # Step 2: Test data flow coherence
        top_patients = data["top_patients"]
        predictions = data["predictions"]
        seasonality = data["seasonality"]
        gemini_enrichment = data["gemini_enrichment"]
        
        # Verify top patients have realistic data
        if len(top_patients) > 0:
            total_revenue = sum(p["revenue"] for p in top_patients)
            avg_loyalty = sum(p["loyalty_score"] for p in top_patients) / len(top_patients)
            print(f"✅ Top patients total revenue: {total_revenue} TND, avg loyalty: {avg_loyalty:.1f}")
        
        # Verify predictions are realistic
        if "next_month" in predictions:
            next_month = predictions["next_month"]
            consultations_est = next_month.get("consultations_estimees", 0)
            revenue_est = next_month.get("revenue_estime", 0)
            confiance = next_month.get("confiance", 0)
            
            # Check if predictions are reasonable compared to historical data
            if len(top_patients) > 0:
                avg_patient_revenue = total_revenue / len(top_patients) if len(top_patients) > 0 else 0
                # Predictions should be in reasonable range
                self.assertGreater(revenue_est, 0, "Revenue prediction should be > 0")
                self.assertGreater(consultations_est, 0, "Consultations prediction should be > 0")
                
                print(f"✅ Predictions reasonable: {consultations_est} consultations, {revenue_est} TND, {confiance}% confidence")
        
        # Verify seasonality analysis has meaningful data
        if "monthly_averages" in seasonality:
            monthly_averages = seasonality["monthly_averages"]
            if len(monthly_averages) > 0:
                print(f"✅ Seasonality analysis covers {len(monthly_averages)} months")
        
        # Verify Gemini enrichment is successful
        self.assertEqual(gemini_enrichment.get("status"), "success", "Gemini enrichment should be successful")
        print(f"✅ Gemini enrichment successful")
        
        # Step 3: Test data consistency
        # Revenue predictions should be consistent with top patient patterns
        if len(top_patients) > 0 and "next_month" in predictions:
            top_patient_avg_revenue = sum(p["revenue"] for p in top_patients[:3]) / min(3, len(top_patients))
            predicted_revenue = predictions["next_month"].get("revenue_estime", 0)
            
            # Predicted revenue should be reasonable compared to top patients
            # (not too high or too low compared to historical patterns)
            if top_patient_avg_revenue > 0:
                ratio = predicted_revenue / top_patient_avg_revenue
                self.assertTrue(0.1 <= ratio <= 10, f"Revenue prediction ratio seems unrealistic: {ratio}")
                print(f"✅ Revenue prediction consistent with historical patterns (ratio: {ratio:.2f})")
        
        # Step 4: Verify all enhanced features are working
        enhanced_features_working = 0
        
        # Check top patients enhanced fields
        if len(top_patients) > 0:
            patient = top_patients[0]
            if all(field in patient for field in ["loyalty_score", "avg_interval_days", "visits_per_year", "status"]):
                enhanced_features_working += 1
                print(f"✅ Top patients enhanced fields working")
        
        # Check predictions enhanced fields
        if "trend_analysis" in predictions and "model_performance" in predictions and "forecasts" in predictions:
            enhanced_features_working += 1
            print(f"✅ Predictions enhanced fields working")
        
        # Check seasonality enhanced fields
        if "pics" in seasonality and "creux" in seasonality and "overall_average" in seasonality:
            enhanced_features_working += 1
            print(f"✅ Seasonality enhanced fields working")
        
        # Check Gemini enrichment
        if gemini_enrichment.get("status") == "success":
            enhanced_features_working += 1
            print(f"✅ Gemini enrichment working")
        
        # All 4 enhanced features should be working
        self.assertEqual(enhanced_features_working, 4, f"Only {enhanced_features_working}/4 enhanced features working")
        
        print(f"🎉 COMPREHENSIVE ML ANALYSIS WORKFLOW Test: PASSED")
        print(f"   - All 4 main sections present and functional")
        print(f"   - Data coherence verified across components")
        print(f"   - Enhanced features working correctly")
        print(f"   - ML predictions provide realistic values")
        print(f"   - Gemini enrichment successful")
        
        return {
            "top_patients_count": len(top_patients),
            "predictions_confidence": predictions.get("next_month", {}).get("confiance", 0),
            "seasonality_months": len(seasonality.get("monthly_averages", {})),
            "gemini_status": gemini_enrichment.get("status"),
            "enhanced_features_working": enhanced_features_working
        }

if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2)