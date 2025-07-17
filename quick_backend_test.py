#!/usr/bin/env python3

import requests
import sys
from datetime import datetime

class QuickAPITester:
    def __init__(self, base_url="https://1fb31e4b-51b3-4865-9aeb-aafab30b5994.preview.emergentagent.com"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0

    def run_test(self, name, method, endpoint, expected_status, data=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=10)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                if response.status_code == 200:
                    try:
                        json_data = response.json()
                        if isinstance(json_data, dict):
                            print(f"   Response keys: {list(json_data.keys())}")
                        elif isinstance(json_data, list):
                            print(f"   Response: List with {len(json_data)} items")
                    except:
                        print(f"   Response: Non-JSON content")
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                if response.status_code != expected_status:
                    print(f"   Response: {response.text[:200]}")

            return success, response.json() if success and response.status_code == 200 else {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

def main():
    print("🚀 Quick Backend API Test")
    print("=" * 50)
    
    tester = QuickAPITester()
    
    # Test 1: Initialize demo data
    print("\n📊 INITIALIZING DEMO DATA")
    success, _ = tester.run_test("Initialize Demo Data", "GET", "api/init-demo", 200)
    
    # Test 2: Dashboard endpoint
    print("\n📊 DASHBOARD TESTS")
    success, dashboard_data = tester.run_test("Dashboard", "GET", "api/dashboard", 200)
    if success and dashboard_data:
        print(f"   📈 Total RDV: {dashboard_data.get('total_rdv', 'N/A')}")
        print(f"   👥 Total Patients: {dashboard_data.get('total_patients', 'N/A')}")
        print(f"   💰 Recette Jour: {dashboard_data.get('recette_jour', 'N/A')} TND")
        print(f"   ⏳ RDV Attente: {dashboard_data.get('rdv_attente', 'N/A')}")
        print(f"   ✅ RDV Terminés: {dashboard_data.get('rdv_termines', 'N/A')}")

    # Test 3: Patients endpoint
    print("\n👥 PATIENTS TESTS")
    success, patients_data = tester.run_test("Patients List", "GET", "api/patients", 200)
    if success and patients_data:
        patients = patients_data.get('patients', [])
        print(f"   📋 Found {len(patients)} patients")
        for i, patient in enumerate(patients[:3]):  # Show first 3
            print(f"   {i+1}. {patient.get('nom', '')} {patient.get('prenom', '')}")

    # Test 4: Today's appointments
    print("\n📅 APPOINTMENTS TESTS")
    today = datetime.now().strftime("%Y-%m-%d")
    success, appointments_data = tester.run_test("Today's Appointments", "GET", f"api/rdv/jour/{today}", 200)
    if success and appointments_data:
        print(f"   📋 Found {len(appointments_data)} appointments today")
        for i, appt in enumerate(appointments_data[:3]):  # Show first 3
            patient_info = appt.get('patient', {})
            patient_name = f"{patient_info.get('nom', '')} {patient_info.get('prenom', '')}"
            print(f"   {i+1}. {appt.get('heure', '')} - {patient_name} ({appt.get('statut', '')})")

    # Test 5: Patients count
    print("\n🔢 COUNTS TESTS")
    success, count_data = tester.run_test("Patients Count", "GET", "api/patients/count", 200)
    if success and count_data:
        print(f"   👥 Total Patients Count: {count_data.get('count', 'N/A')}")

    # Print final results
    print("\n" + "=" * 50)
    print(f"📊 FINAL RESULTS: {tester.tests_passed}/{tester.tests_run} tests passed")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 All tests PASSED! Backend APIs are working correctly.")
        return 0
    else:
        print("⚠️  Some tests FAILED. Check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())