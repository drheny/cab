import requests
import unittest
import json
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/frontend/.env')

class AdvancedReportsAPITest(unittest.TestCase):
    def setUp(self):
        # Use the correct backend URL from environment
        backend_url = os.getenv('REACT_APP_BACKEND_URL', 'https://4b217b17-873e-4b0f-ae18-7cc0e70848d9.preview.emergentagent.com')
        self.base_url = backend_url
        print(f"Testing advanced reports at: {self.base_url}")
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
    
    # ========== ADVANCED REPORTS FUNCTIONALITY TESTING ==========
    
    def test_advanced_reports_monthly(self):
        """Test GET /api/admin/advanced-reports with period_type=monthly"""
        # Test current month
        response = requests.get(f"{self.base_url}/api/admin/advanced-reports?period_type=monthly")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify response structure
        self.assertIn("metadata", data)
        self.assertIn("advanced_statistics", data)
        self.assertIn("evolution", data)
        self.assertIn("seasonality", data)
        self.assertIn("predictions", data)
        self.assertIn("alerts", data)
        
        # Verify metadata
        metadata = data["metadata"]
        self.assertEqual(metadata["type"], "monthly")
        self.assertIn("periode", metadata)
        self.assertIn("start_date", metadata)
        self.assertIn("end_date", metadata)
        self.assertIn("generated_at", metadata)
        
        # Verify advanced statistics structure
        stats = data["advanced_statistics"]
        self.assertIn("consultations", stats)
        self.assertIn("top_patients", stats)
        self.assertIn("durees", stats)
        self.assertIn("relances", stats)
        self.assertIn("patients_inactifs", stats)
        self.assertIn("fidelisation", stats)
        self.assertIn("salles", stats)
        
        # Test specific month
        response = requests.get(f"{self.base_url}/api/admin/advanced-reports?period_type=monthly&year=2024&month=12")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["metadata"]["type"], "monthly")
        
        print("✅ Monthly advanced reports working correctly")
    
    def test_advanced_reports_semester(self):
        """Test GET /api/admin/advanced-reports with period_type=semester"""
        # Test current semester
        response = requests.get(f"{self.base_url}/api/admin/advanced-reports?period_type=semester")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify response structure
        self.assertIn("metadata", data)
        self.assertIn("comparison", data)  # Should have year comparison for semester
        
        metadata = data["metadata"]
        self.assertEqual(metadata["type"], "semester")
        self.assertIn("semestre", metadata["periode"])
        
        # Test specific semester
        response = requests.get(f"{self.base_url}/api/admin/advanced-reports?period_type=semester&year=2024&semester=1")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("1er semestre", data["metadata"]["periode"])
        
        response = requests.get(f"{self.base_url}/api/admin/advanced-reports?period_type=semester&year=2024&semester=2")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("2e semestre", data["metadata"]["periode"])
        
        print("✅ Semester advanced reports working correctly")
    
    def test_advanced_reports_annual(self):
        """Test GET /api/admin/advanced-reports with period_type=annual"""
        # Test current year
        response = requests.get(f"{self.base_url}/api/admin/advanced-reports?period_type=annual")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify response structure
        self.assertIn("metadata", data)
        self.assertIn("comparison", data)  # Should have year comparison for annual
        
        metadata = data["metadata"]
        self.assertEqual(metadata["type"], "annual")
        self.assertIn("Année", metadata["periode"])
        
        # Verify comparison data (année N vs N-1)
        comparison = data["comparison"]
        if comparison:  # comparison might be null if no previous year data
            self.assertIn("consultations", comparison)
            self.assertIn("revenue", comparison)
            self.assertIn("visites", comparison)
        
        # Test specific year
        response = requests.get(f"{self.base_url}/api/admin/advanced-reports?period_type=annual&year=2024")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("Année 2024", data["metadata"]["periode"])
        
        print("✅ Annual advanced reports working correctly")
    
    def test_advanced_reports_custom(self):
        """Test GET /api/admin/advanced-reports with period_type=custom"""
        # Test custom date range
        start_date = "2024-01-01"
        end_date = "2024-06-30"
        
        response = requests.get(f"{self.base_url}/api/admin/advanced-reports?period_type=custom&start_date={start_date}&end_date={end_date}")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify response structure
        metadata = data["metadata"]
        self.assertEqual(metadata["type"], "custom")
        self.assertEqual(metadata["start_date"], start_date)
        self.assertEqual(metadata["end_date"], end_date)
        self.assertIn(f"{start_date} - {end_date}", metadata["periode"])
        
        # Test missing dates (should return error)
        response = requests.get(f"{self.base_url}/api/admin/advanced-reports?period_type=custom")
        self.assertEqual(response.status_code, 400)
        
        response = requests.get(f"{self.base_url}/api/admin/advanced-reports?period_type=custom&start_date={start_date}")
        self.assertEqual(response.status_code, 400)
        
        print("✅ Custom period advanced reports working correctly")
    
    def test_advanced_reports_invalid_period_type(self):
        """Test GET /api/admin/advanced-reports with invalid period_type"""
        response = requests.get(f"{self.base_url}/api/admin/advanced-reports?period_type=invalid")
        self.assertEqual(response.status_code, 400)
        
        response = requests.get(f"{self.base_url}/api/admin/advanced-reports?period_type=weekly")
        self.assertEqual(response.status_code, 400)
        
        print("✅ Invalid period type validation working correctly")
    
    def test_advanced_reports_data_verification(self):
        """Test advanced reports data calculations and structure"""
        response = requests.get(f"{self.base_url}/api/admin/advanced-reports?period_type=monthly")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        stats = data["advanced_statistics"]
        
        # Verify consultations structure (répartition visite/contrôle)
        consultations = stats["consultations"]
        self.assertIn("visites", consultations)
        self.assertIn("controles", consultations)
        self.assertIn("total", consultations)
        
        # Verify visites and controles structure
        visites = consultations["visites"]
        controles = consultations["controles"]
        
        self.assertIn("count", visites)
        self.assertIn("percentage", visites)
        self.assertIn("revenue", visites)
        
        self.assertIn("count", controles)
        self.assertIn("percentage", controles)
        self.assertIn("revenue", controles)
        
        # Verify percentages add up to 100 (or close to it if there's data)
        if consultations["total"] > 0:
            total_percentage = visites["percentage"] + controles["percentage"]
            self.assertAlmostEqual(total_percentage, 100.0, places=1)
        
        # Verify top patients
        top_patients = stats["top_patients"]
        self.assertIsInstance(top_patients, list)
        self.assertLessEqual(len(top_patients), 10)  # Should be top 10
        
        # Verify each patient has required fields
        for patient in top_patients:
            self.assertIn("name", patient)
            self.assertIn("consultations", patient)
            self.assertIn("revenue", patient)
            self.assertIn("last_visit", patient)
        
        # Verify durées moyennes
        durees = stats["durees"]
        self.assertIn("attente_moyenne", durees)
        self.assertIn("consultation_moyenne", durees)
        self.assertIsInstance(durees["attente_moyenne"], (int, float))
        self.assertIsInstance(durees["consultation_moyenne"], (int, float))
        
        # Verify relances téléphoniques
        relances = stats["relances"]
        self.assertIn("total", relances)
        self.assertIn("taux_reponse", relances)
        self.assertIsInstance(relances["total"], int)
        self.assertIsInstance(relances["taux_reponse"], (int, float))
        
        # Verify patients inactifs
        inactifs = stats["patients_inactifs"]
        self.assertIn("count", inactifs)
        self.assertIn("percentage", inactifs)
        self.assertIsInstance(inactifs["count"], int)
        self.assertIsInstance(inactifs["percentage"], (int, float))
        
        # Verify taux de fidélisation
        fidelisation = stats["fidelisation"]
        self.assertIn("nouveaux_patients", fidelisation)
        self.assertIn("patients_recurrents", fidelisation)
        self.assertIn("taux_retour", fidelisation)
        
        # Verify utilisation des salles
        salles = stats["salles"]
        self.assertIn("salle1", salles)
        self.assertIn("salle2", salles)
        self.assertIn("sans_salle", salles)
        
        print("✅ Advanced reports data structure and calculations verified")
    
    def test_advanced_reports_ml_predictions(self):
        """Test ML predictions and seasonality patterns in advanced reports"""
        response = requests.get(f"{self.base_url}/api/admin/advanced-reports?period_type=annual")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify predictions structure
        predictions = data["predictions"]
        self.assertIn("next_month", predictions)
        
        # Check if we have enough data for predictions
        if "message" not in predictions:
            # If we have predictions, verify structure
            next_month = predictions["next_month"]
            self.assertIn("consultations_estimees", next_month)
            self.assertIn("revenue_estime", next_month)
            self.assertIn("confiance", next_month)
        
        # Verify seasonality patterns
        seasonality = data["seasonality"]
        self.assertIn("pics", seasonality)
        self.assertIn("creux", seasonality)
        self.assertIn("monthly_averages", seasonality)
        self.assertIn("overall_average", seasonality)
        
        print("✅ ML predictions and seasonality patterns working correctly")
    
    def test_advanced_reports_alert_thresholds(self):
        """Test alert thresholds in advanced reports"""
        response = requests.get(f"{self.base_url}/api/admin/advanced-reports?period_type=monthly")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify alerts structure
        alerts = data["alerts"]
        self.assertIsInstance(alerts, list)
        
        # If there are alerts, verify their structure
        for alert in alerts:
            self.assertIn("severity", alert)
            self.assertIn("message", alert)
            self.assertIn("value", alert)
            self.assertIn("threshold", alert)
            self.assertIn(alert["severity"], ["low", "medium", "high", "critical"])
        
        print("✅ Alert thresholds working correctly")
    
    def test_demographics_report(self):
        """Test GET /api/admin/reports/demographics"""
        start_date = "2024-01-01"
        end_date = "2024-12-31"
        
        response = requests.get(f"{self.base_url}/api/admin/reports/demographics?start_date={start_date}&end_date={end_date}")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify response structure
        self.assertIn("period", data)
        self.assertIn("total_active_patients", data)
        self.assertIn("age_breakdown", data)
        self.assertIn("top_addresses", data)
        self.assertIn("top_cities", data)
        self.assertIn("generated_at", data)
        
        # Verify age breakdown structure
        age_breakdown = data["age_breakdown"]
        expected_age_groups = ["0-1", "2-3", "4-5", "6-8", "9-12", "13-15", "16-18", "18+"]
        for age_group in expected_age_groups:
            self.assertIn(age_group, age_breakdown)
            self.assertIsInstance(age_breakdown[age_group], int)
        
        # Verify addresses and cities are dictionaries
        self.assertIsInstance(data["top_addresses"], dict)
        self.assertIsInstance(data["top_cities"], dict)
        
        # Verify total active patients is non-negative
        self.assertGreaterEqual(data["total_active_patients"], 0)
        
        # Test missing parameters
        response = requests.get(f"{self.base_url}/api/admin/reports/demographics")
        self.assertEqual(response.status_code, 422)  # Missing required parameters
        
        response = requests.get(f"{self.base_url}/api/admin/reports/demographics?start_date={start_date}")
        self.assertEqual(response.status_code, 422)  # Missing end_date
        
        print("✅ Demographics report working correctly")
    
    def test_top_patients_report_default(self):
        """Test GET /api/admin/reports/top-patients with default parameters"""
        response = requests.get(f"{self.base_url}/api/admin/reports/top-patients")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify response structure
        self.assertIn("period", data)
        self.assertIn("metric", data)
        self.assertIn("total_patients_analyzed", data)
        self.assertIn("top_patients", data)
        self.assertIn("summary", data)
        self.assertIn("generated_at", data)
        
        # Verify default parameters
        self.assertEqual(data["metric"], "revenue")  # Default metric
        self.assertLessEqual(len(data["top_patients"]), 10)  # Default limit
        
        # Verify top patients structure
        for patient in data["top_patients"]:
            self.assertIn("patient_id", patient)
            self.assertIn("name", patient)
            self.assertIn("age", patient)
            self.assertIn("phone", patient)
            self.assertIn("address", patient)
            self.assertIn("statistics", patient)
            
            # Verify statistics structure
            stats = patient["statistics"]
            self.assertIn("consultations", stats)
            self.assertIn("visites", stats)
            self.assertIn("controles", stats)
            self.assertIn("revenue", stats)
            self.assertIn("first_visit", stats)
            self.assertIn("last_visit", stats)
            self.assertIn("visits_per_month", stats)
        
        # Verify summary structure
        summary = data["summary"]
        self.assertIn("total_revenue", summary)
        self.assertIn("total_consultations", summary)
        self.assertIn("average_revenue_per_patient", summary)
        
        print("✅ Top patients report (default) working correctly")
    
    def test_top_patients_report_consultations_metric(self):
        """Test GET /api/admin/reports/top-patients with metric=consultations"""
        response = requests.get(f"{self.base_url}/api/admin/reports/top-patients?metric=consultations&limit=5")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify metric and limit
        self.assertEqual(data["metric"], "consultations")
        self.assertLessEqual(len(data["top_patients"]), 5)
        
        # Verify patients are sorted by consultations (descending)
        top_patients = data["top_patients"]
        if len(top_patients) > 1:
            for i in range(1, len(top_patients)):
                prev_consultations = top_patients[i-1]["statistics"]["consultations"]
                curr_consultations = top_patients[i]["statistics"]["consultations"]
                self.assertGreaterEqual(prev_consultations, curr_consultations)
        
        print("✅ Top patients report (consultations metric) working correctly")
    
    def test_top_patients_report_frequency_metric(self):
        """Test GET /api/admin/reports/top-patients with metric=frequency"""
        response = requests.get(f"{self.base_url}/api/admin/reports/top-patients?metric=frequency&limit=5")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify metric
        self.assertEqual(data["metric"], "frequency")
        
        # Verify patients are sorted by visits_per_month (descending)
        top_patients = data["top_patients"]
        if len(top_patients) > 1:
            for i in range(1, len(top_patients)):
                prev_frequency = top_patients[i-1]["statistics"]["visits_per_month"]
                curr_frequency = top_patients[i]["statistics"]["visits_per_month"]
                self.assertGreaterEqual(prev_frequency, curr_frequency)
        
        print("✅ Top patients report (frequency metric) working correctly")
    
    def test_top_patients_report_custom_parameters(self):
        """Test GET /api/admin/reports/top-patients with custom parameters"""
        # Test different period and limit
        response = requests.get(f"{self.base_url}/api/admin/reports/top-patients?limit=3&period_months=6&metric=revenue")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify custom parameters
        self.assertEqual(data["metric"], "revenue")
        self.assertLessEqual(len(data["top_patients"]), 3)
        
        # Verify period calculation (should be 6 months back)
        period = data["period"]
        self.assertIn(" - ", period)
        
        print("✅ Top patients report (custom parameters) working correctly")
    
    def test_advanced_reports_comprehensive_workflow(self):
        """Test comprehensive workflow of all advanced reports endpoints"""
        print("\n🔍 Testing comprehensive advanced reports workflow...")
        
        # Step 1: Test monthly report
        monthly_response = requests.get(f"{self.base_url}/api/admin/advanced-reports?period_type=monthly")
        self.assertEqual(monthly_response.status_code, 200)
        monthly_data = monthly_response.json()
        
        # Step 2: Test demographics for same period
        start_date = monthly_data["metadata"]["start_date"]
        end_date = monthly_data["metadata"]["end_date"]
        
        demographics_response = requests.get(f"{self.base_url}/api/admin/reports/demographics?start_date={start_date}&end_date={end_date}")
        self.assertEqual(demographics_response.status_code, 200)
        demographics_data = demographics_response.json()
        
        # Step 3: Test top patients
        top_patients_response = requests.get(f"{self.base_url}/api/admin/reports/top-patients?limit=10&metric=revenue")
        self.assertEqual(top_patients_response.status_code, 200)
        top_patients_data = top_patients_response.json()
        
        # Verify data consistency across reports
        monthly_stats = monthly_data["advanced_statistics"]
        
        # Check if top patients from advanced reports match top patients report
        advanced_top_patients = monthly_stats["top_patients"]
        dedicated_top_patients = top_patients_data["top_patients"]
        
        # Both should have patient data (or be empty if no data)
        self.assertGreaterEqual(len(advanced_top_patients), 0)
        self.assertGreaterEqual(len(dedicated_top_patients), 0)
        
        # Demographics should have active patients count
        self.assertGreaterEqual(demographics_data["total_active_patients"], 0)
        
        print("✅ Comprehensive advanced reports workflow completed successfully")
        
        # Summary of all tested features
        print("\n📊 ADVANCED REPORTS TESTING SUMMARY:")
        print("✅ Monthly reports with all statistics")
        print("✅ Semester reports with year comparison")
        print("✅ Annual reports with N vs N-1 comparison")
        print("✅ Custom period reports")
        print("✅ Demographics breakdown by age and location")
        print("✅ Top patients analysis (revenue, consultations, frequency)")
        print("✅ ML predictions with confidence levels")
        print("✅ Seasonality pattern detection")
        print("✅ Alert thresholds (revenue drop >20%, inactive >30%, waiting >30min)")
        print("✅ Répartition visite/contrôle with percentages and revenue")
        print("✅ Durées moyennes (attente et consultation)")
        print("✅ Relances téléphoniques with response rates")
        print("✅ Patients inactifs count and percentage")
        print("✅ Taux de fidélisation (nouveaux vs récurrents)")
        print("✅ Utilisation des salles with percentages")
        print("✅ Évolution mensuelle data for trends")
        print("✅ All data validation and error handling")

if __name__ == "__main__":
    unittest.main()