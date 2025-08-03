#!/usr/bin/env python3
"""
Enhanced Facturation Endpoints Testing
Testing all 8 new facturation endpoints with comprehensive validation
"""

import requests
import json
from datetime import datetime, timedelta
import sys

# Configuration
BACKEND_URL = "https://0698237d-0754-4aa4-881e-3c8e5387d3e6.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

# Authentication token (auto-login for testing)
HEADERS = {
    "Authorization": "Bearer auto-login-token",
    "Content-Type": "application/json"
}

def print_test_header(test_name):
    """Print formatted test header"""
    print(f"\n{'='*60}")
    print(f"🧪 TESTING: {test_name}")
    print(f"{'='*60}")

def print_success(message):
    """Print success message"""
    print(f"✅ {message}")

def print_error(message):
    """Print error message"""
    print(f"❌ {message}")

def print_info(message):
    """Print info message"""
    print(f"ℹ️  {message}")

def make_request(method, endpoint, params=None, data=None):
    """Make HTTP request with error handling"""
    url = f"{API_BASE}{endpoint}"
    try:
        if method.upper() == "GET":
            response = requests.get(url, headers=HEADERS, params=params, timeout=30)
        elif method.upper() == "POST":
            response = requests.post(url, headers=HEADERS, json=data, timeout=30)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        print(f"📡 {method.upper()} {url}")
        if params:
            print(f"   Params: {params}")
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"   Error: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print_error(f"Request failed: {str(e)}")
        return None
    except json.JSONDecodeError as e:
        print_error(f"JSON decode error: {str(e)}")
        return None

def get_patient_ids():
    """Get existing patient IDs for testing"""
    print_info("Fetching patient IDs for testing...")
    response = make_request("GET", "/patients", params={"limit": 5})
    
    if response and "patients" in response:
        patient_ids = [patient["id"] for patient in response["patients"]]
        print_success(f"Found {len(patient_ids)} patients: {patient_ids}")
        return patient_ids
    else:
        print_error("Failed to fetch patient IDs")
        return []

def test_enhanced_stats():
    """Test /api/facturation/enhanced-stats endpoint"""
    print_test_header("Enhanced Facturation Stats")
    
    response = make_request("GET", "/facturation/enhanced-stats")
    
    if response:
        print_success("Enhanced stats endpoint working!")
        
        # Validate response structure
        required_fields = ["recette_jour", "recette_mois", "recette_annee", "nouveaux_patients_annee"]
        for field in required_fields:
            if field in response:
                print_success(f"✓ {field}: {response[field]}")
            else:
                print_error(f"✗ Missing field: {field}")
        
        # Validate data types
        for field in ["recette_jour", "recette_mois", "recette_annee"]:
            if field in response and isinstance(response[field], (int, float)):
                print_success(f"✓ {field} is numeric: {type(response[field]).__name__}")
            else:
                print_error(f"✗ {field} should be numeric")
        
        if "nouveaux_patients_annee" in response and isinstance(response["nouveaux_patients_annee"], int):
            print_success(f"✓ nouveaux_patients_annee is integer: {response['nouveaux_patients_annee']}")
        else:
            print_error("✗ nouveaux_patients_annee should be integer")
            
        return True
    else:
        print_error("Enhanced stats endpoint failed!")
        return False

def test_daily_payments():
    """Test /api/facturation/daily-payments endpoint"""
    print_test_header("Daily Payments")
    
    # Test with today's date
    today = datetime.now().strftime("%Y-%m-%d")
    test_date = "2025-01-28"  # Use specific date as requested
    
    print_info(f"Testing with date: {test_date}")
    response = make_request("GET", "/facturation/daily-payments", params={"date": test_date})
    
    if response:
        print_success("Daily payments endpoint working!")
        
        # Validate response structure
        required_fields = ["date", "payments", "totals"]
        for field in required_fields:
            if field in response:
                print_success(f"✓ {field} present")
            else:
                print_error(f"✗ Missing field: {field}")
        
        # Validate date
        if response.get("date") == test_date:
            print_success(f"✓ Date matches: {response['date']}")
        else:
            print_error(f"✗ Date mismatch: expected {test_date}, got {response.get('date')}")
        
        # Validate totals structure
        if "totals" in response:
            totals = response["totals"]
            total_fields = ["recette_totale", "nb_visites", "nb_controles", "nb_assures", "nb_total"]
            for field in total_fields:
                if field in totals:
                    print_success(f"✓ totals.{field}: {totals[field]}")
                else:
                    print_error(f"✗ Missing totals.{field}")
        
        # Validate payments array
        if "payments" in response:
            payments = response["payments"]
            print_info(f"Found {len(payments)} payments for {test_date}")
            
            if payments:
                # Check first payment structure
                payment = payments[0]
                payment_fields = ["id", "patient_id", "montant", "type_paiement", "statut", "date"]
                for field in payment_fields:
                    if field in payment:
                        print_success(f"✓ payment.{field}: {payment[field]}")
                    else:
                        print_error(f"✗ Missing payment.{field}")
                
                # Check if patient info is enriched
                if "patient" in payment:
                    print_success(f"✓ Patient info enriched: {payment['patient']}")
                else:
                    print_error("✗ Patient info not enriched")
            else:
                print_info("No payments found for this date")
        
        return True
    else:
        print_error("Daily payments endpoint failed!")
        return False

def test_monthly_stats():
    """Test /api/facturation/monthly-stats endpoint"""
    print_test_header("Monthly Statistics")
    
    # Test with current month
    year = 2025
    month = 1
    
    print_info(f"Testing with year: {year}, month: {month}")
    response = make_request("GET", "/facturation/monthly-stats", params={"year": year, "month": month})
    
    if response:
        print_success("Monthly stats endpoint working!")
        
        # Validate response structure
        required_fields = ["year", "month", "recette_mois", "nb_visites", "nb_controles", "nb_assures", "nb_total_rdv"]
        for field in required_fields:
            if field in response:
                print_success(f"✓ {field}: {response[field]}")
            else:
                print_error(f"✗ Missing field: {field}")
        
        # Validate year and month
        if response.get("year") == year and response.get("month") == month:
            print_success(f"✓ Year/Month match: {response['year']}/{response['month']}")
        else:
            print_error(f"✗ Year/Month mismatch")
        
        # Validate numeric fields
        numeric_fields = ["recette_mois", "nb_visites", "nb_controles", "nb_assures", "nb_total_rdv"]
        for field in numeric_fields:
            if field in response and isinstance(response[field], (int, float)):
                print_success(f"✓ {field} is numeric: {response[field]}")
            else:
                print_error(f"✗ {field} should be numeric")
        
        return True
    else:
        print_error("Monthly stats endpoint failed!")
        return False

def test_yearly_stats():
    """Test /api/facturation/yearly-stats endpoint"""
    print_test_header("Yearly Statistics")
    
    year = 2025
    
    print_info(f"Testing with year: {year}")
    response = make_request("GET", "/facturation/yearly-stats", params={"year": year})
    
    if response:
        print_success("Yearly stats endpoint working!")
        
        # Validate response structure
        required_fields = ["year", "recette_annee", "nb_visites", "nb_controles", "nb_assures", "nb_total_rdv"]
        for field in required_fields:
            if field in response:
                print_success(f"✓ {field}: {response[field]}")
            else:
                print_error(f"✗ Missing field: {field}")
        
        # Validate year
        if response.get("year") == year:
            print_success(f"✓ Year matches: {response['year']}")
        else:
            print_error(f"✗ Year mismatch")
        
        # Validate numeric fields
        numeric_fields = ["recette_annee", "nb_visites", "nb_controles", "nb_assures", "nb_total_rdv"]
        for field in numeric_fields:
            if field in response and isinstance(response[field], (int, float)):
                print_success(f"✓ {field} is numeric: {response[field]}")
            else:
                print_error(f"✗ {field} should be numeric")
        
        return True
    else:
        print_error("Yearly stats endpoint failed!")
        return False

def test_patient_payments(patient_ids):
    """Test /api/facturation/patient-payments endpoint"""
    print_test_header("Patient Payments")
    
    if not patient_ids:
        print_error("No patient IDs available for testing")
        return False
    
    # Test with first available patient
    patient_id = patient_ids[0]
    print_info(f"Testing with patient_id: {patient_id}")
    
    response = make_request("GET", "/facturation/patient-payments", params={"patient_id": patient_id})
    
    if response:
        print_success("Patient payments endpoint working!")
        
        # Validate response structure
        required_fields = ["patient", "payments", "total_paye", "nb_payments"]
        for field in required_fields:
            if field in response:
                print_success(f"✓ {field} present")
            else:
                print_error(f"✗ Missing field: {field}")
        
        # Validate patient info
        if "patient" in response:
            patient = response["patient"]
            patient_fields = ["id", "nom", "prenom", "telephone"]
            for field in patient_fields:
                if field in patient:
                    print_success(f"✓ patient.{field}: {patient[field]}")
                else:
                    print_error(f"✗ Missing patient.{field}")
        
        # Validate payments array
        if "payments" in response:
            payments = response["payments"]
            print_info(f"Found {len(payments)} payments for patient")
            
            if payments:
                # Check first payment structure
                payment = payments[0]
                payment_fields = ["id", "patient_id", "montant", "type_paiement", "statut", "date"]
                for field in payment_fields:
                    if field in payment:
                        print_success(f"✓ payment.{field}: {payment[field]}")
                    else:
                        print_error(f"✗ Missing payment.{field}")
        
        # Validate totals
        if "total_paye" in response and isinstance(response["total_paye"], (int, float)):
            print_success(f"✓ total_paye is numeric: {response['total_paye']}")
        else:
            print_error("✗ total_paye should be numeric")
        
        if "nb_payments" in response and isinstance(response["nb_payments"], int):
            print_success(f"✓ nb_payments is integer: {response['nb_payments']}")
        else:
            print_error("✗ nb_payments should be integer")
        
        return True
    else:
        print_error("Patient payments endpoint failed!")
        return False

def test_top_patients():
    """Test /api/facturation/top-patients endpoint"""
    print_test_header("Top Profitable Patients")
    
    limit = 10
    print_info(f"Testing with limit: {limit}")
    
    response = make_request("GET", "/facturation/top-patients", params={"limit": limit})
    
    if response:
        print_success("Top patients endpoint working!")
        
        # Validate response structure
        required_fields = ["top_patients", "total_analyzed"]
        for field in required_fields:
            if field in response:
                print_success(f"✓ {field} present")
            else:
                print_error(f"✗ Missing field: {field}")
        
        # Validate top_patients array
        if "top_patients" in response:
            top_patients = response["top_patients"]
            print_info(f"Found {len(top_patients)} top patients")
            
            if top_patients:
                # Check first patient structure
                patient_entry = top_patients[0]
                required_fields = ["patient", "total_montant", "nb_payments", "moyenne_paiement"]
                for field in required_fields:
                    if field in patient_entry:
                        print_success(f"✓ top_patient.{field}: {patient_entry[field]}")
                    else:
                        print_error(f"✗ Missing top_patient.{field}")
                
                # Validate patient info
                if "patient" in patient_entry:
                    patient = patient_entry["patient"]
                    patient_fields = ["id", "nom", "prenom", "telephone"]
                    for field in patient_fields:
                        if field in patient:
                            print_success(f"✓ patient.{field}: {patient[field]}")
                        else:
                            print_error(f"✗ Missing patient.{field}")
                
                # Validate that results are sorted by total_montant (descending)
                if len(top_patients) > 1:
                    first_total = top_patients[0]["total_montant"]
                    second_total = top_patients[1]["total_montant"]
                    if first_total >= second_total:
                        print_success("✓ Results properly sorted by total_montant (descending)")
                    else:
                        print_error("✗ Results not properly sorted")
            else:
                print_info("No top patients found")
        
        # Validate total_analyzed
        if "total_analyzed" in response and isinstance(response["total_analyzed"], int):
            print_success(f"✓ total_analyzed is integer: {response['total_analyzed']}")
        else:
            print_error("✗ total_analyzed should be integer")
        
        return True
    else:
        print_error("Top patients endpoint failed!")
        return False

def test_evolution_graphs():
    """Test /api/facturation/evolution-graphs endpoint"""
    print_test_header("Evolution Graphs")
    
    period = "month"
    year = 2025
    
    print_info(f"Testing with period: {period}, year: {year}")
    response = make_request("GET", "/facturation/evolution-graphs", params={"period": period, "year": year})
    
    if response:
        print_success("Evolution graphs endpoint working!")
        
        # Validate response structure
        required_fields = ["period", "year", "evolution"]
        for field in required_fields:
            if field in response:
                print_success(f"✓ {field} present")
            else:
                print_error(f"✗ Missing field: {field}")
        
        # Validate period and year
        if response.get("period") == period and response.get("year") == year:
            print_success(f"✓ Period/Year match: {response['period']}/{response['year']}")
        else:
            print_error(f"✗ Period/Year mismatch")
        
        # Validate evolution array
        if "evolution" in response:
            evolution = response["evolution"]
            print_info(f"Found {len(evolution)} evolution data points")
            
            if evolution:
                # Check first evolution entry
                entry = evolution[0]
                evolution_fields = ["periode", "mois", "recette", "nb_consultations", "nouveaux_patients"]
                for field in evolution_fields:
                    if field in entry:
                        print_success(f"✓ evolution.{field}: {entry[field]}")
                    else:
                        print_error(f"✗ Missing evolution.{field}")
                
                # Validate that we have 12 months of data
                if len(evolution) == 12:
                    print_success("✓ Complete year data (12 months)")
                else:
                    print_info(f"Evolution data has {len(evolution)} entries (may be partial year)")
                
                # Validate numeric fields
                numeric_fields = ["mois", "recette", "nb_consultations", "nouveaux_patients"]
                for field in numeric_fields:
                    if field in entry and isinstance(entry[field], (int, float)):
                        print_success(f"✓ {field} is numeric")
                    else:
                        print_error(f"✗ {field} should be numeric")
            else:
                print_info("No evolution data found")
        
        return True
    else:
        print_error("Evolution graphs endpoint failed!")
        return False

def test_predictive_analysis():
    """Test /api/facturation/predictive-analysis endpoint"""
    print_test_header("Predictive Analysis")
    
    response = make_request("GET", "/facturation/predictive-analysis")
    
    if response:
        print_success("Predictive analysis endpoint working!")
        
        # Validate response structure
        required_fields = ["ai_analysis", "historical_data", "peak_months", "trough_months", "monthly_averages", "generation_method"]
        for field in required_fields:
            if field in response:
                print_success(f"✓ {field} present")
            else:
                print_error(f"✗ Missing field: {field}")
        
        # Validate generation method
        if "generation_method" in response:
            method = response["generation_method"]
            if method in ["ai", "statistical"]:
                print_success(f"✓ Valid generation method: {method}")
            else:
                print_error(f"✗ Invalid generation method: {method}")
        
        # Validate AI analysis
        if "ai_analysis" in response and isinstance(response["ai_analysis"], str):
            print_success(f"✓ AI analysis is string (length: {len(response['ai_analysis'])})")
        else:
            print_error("✗ AI analysis should be string")
        
        # Validate historical data
        if "historical_data" in response:
            historical_data = response["historical_data"]
            print_info(f"Found {len(historical_data)} historical data points")
            
            if historical_data:
                # Check first historical entry
                entry = historical_data[0]
                historical_fields = ["year", "month", "recette", "nb_consultations", "nb_visites", "nb_controles"]
                for field in historical_fields:
                    if field in entry:
                        print_success(f"✓ historical.{field}: {entry[field]}")
                    else:
                        print_error(f"✗ Missing historical.{field}")
        
        # Validate peak months
        if "peak_months" in response:
            peak_months = response["peak_months"]
            print_info(f"Found {len(peak_months)} peak months")
            
            if peak_months:
                peak = peak_months[0]
                peak_fields = ["month", "avg_recette", "avg_consultations"]
                for field in peak_fields:
                    if field in peak:
                        print_success(f"✓ peak.{field}: {peak[field]}")
                    else:
                        print_error(f"✗ Missing peak.{field}")
        
        # Validate trough months
        if "trough_months" in response:
            trough_months = response["trough_months"]
            print_info(f"Found {len(trough_months)} trough months")
            
            if trough_months:
                trough = trough_months[0]
                trough_fields = ["month", "avg_recette", "avg_consultations"]
                for field in trough_fields:
                    if field in trough:
                        print_success(f"✓ trough.{field}: {trough[field]}")
                    else:
                        print_error(f"✗ Missing trough.{field}")
        
        # Validate monthly averages
        if "monthly_averages" in response:
            monthly_averages = response["monthly_averages"]
            print_info(f"Found {len(monthly_averages)} monthly averages")
            
            if monthly_averages:
                avg = monthly_averages[0]
                avg_fields = ["month", "avg_recette", "avg_consultations"]
                for field in avg_fields:
                    if field in avg:
                        print_success(f"✓ avg.{field}: {avg[field]}")
                    else:
                        print_error(f"✗ Missing avg.{field}")
        
        return True
    else:
        print_error("Predictive analysis endpoint failed!")
        return False

def main():
    """Main test function"""
    print("🚀 ENHANCED FACTURATION ENDPOINTS TESTING")
    print("=" * 60)
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Testing Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Initialize demo data first
    print_info("Initializing demo data...")
    demo_response = make_request("GET", "/init-demo")
    if demo_response:
        print_success("Demo data initialized successfully")
    else:
        print_error("Failed to initialize demo data")
    
    # Get patient IDs for testing
    patient_ids = get_patient_ids()
    
    # Run all tests
    test_results = []
    
    # Test 1: Enhanced Stats
    test_results.append(("Enhanced Stats", test_enhanced_stats()))
    
    # Test 2: Daily Payments
    test_results.append(("Daily Payments", test_daily_payments()))
    
    # Test 3: Monthly Stats
    test_results.append(("Monthly Stats", test_monthly_stats()))
    
    # Test 4: Yearly Stats
    test_results.append(("Yearly Stats", test_yearly_stats()))
    
    # Test 5: Patient Payments
    test_results.append(("Patient Payments", test_patient_payments(patient_ids)))
    
    # Test 6: Top Patients
    test_results.append(("Top Patients", test_top_patients()))
    
    # Test 7: Evolution Graphs
    test_results.append(("Evolution Graphs", test_evolution_graphs()))
    
    # Test 8: Predictive Analysis
    test_results.append(("Predictive Analysis", test_predictive_analysis()))
    
    # Print final results
    print_test_header("FINAL TEST RESULTS")
    
    passed = 0
    failed = 0
    
    for test_name, result in test_results:
        if result:
            print_success(f"{test_name}: PASSED")
            passed += 1
        else:
            print_error(f"{test_name}: FAILED")
            failed += 1
    
    print(f"\n📊 SUMMARY:")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📈 Success Rate: {(passed / len(test_results)) * 100:.1f}%")
    
    if failed == 0:
        print("\n🎉 ALL TESTS PASSED! Enhanced facturation endpoints are working correctly.")
        return 0
    else:
        print(f"\n⚠️  {failed} test(s) failed. Please check the implementation.")
        return 1

if __name__ == "__main__":
    sys.exit(main())