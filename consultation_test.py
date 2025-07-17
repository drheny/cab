#!/usr/bin/env python3
"""
Focused Backend API Testing for Cabinet Médical - Consultation Features
Tests consultation-related endpoints specifically
"""

import requests
import sys
import json
from datetime import datetime, timedelta

def test_consultation_apis():
    """Test consultation-related APIs"""
    base_url = "https://1fb31e4b-51b3-4865-9aeb-aafab30b5994.preview.emergentagent.com"
    
    print("🏥 Testing Cabinet Médical Consultation APIs")
    print("=" * 60)
    
    tests_passed = 0
    tests_total = 0
    
    def run_test(name, test_func):
        nonlocal tests_passed, tests_total
        tests_total += 1
        try:
            result = test_func()
            if result:
                print(f"✅ {name} - PASSED")
                tests_passed += 1
            else:
                print(f"❌ {name} - FAILED")
        except Exception as e:
            print(f"❌ {name} - ERROR: {str(e)}")
    
    # Test 1: Initialize demo data
    def test_init_demo():
        try:
            response = requests.get(f"{base_url}/api/init-demo", timeout=10)
            return response.status_code == 200
        except:
            return False
    
    # Test 2: Get all consultations
    def test_get_consultations():
        try:
            response = requests.get(f"{base_url}/api/consultations", timeout=10)
            if response.status_code == 200:
                data = response.json()
                print(f"   Found {len(data)} consultations")
                return True
            return False
        except:
            return False
    
    # Test 3: Get patient consultations
    def test_get_patient_consultations():
        try:
            response = requests.get(f"{base_url}/api/consultations/patient/patient1", timeout=10)
            if response.status_code == 200:
                data = response.json()
                print(f"   Patient1 has {len(data)} consultations")
                return True
            return False
        except:
            return False
    
    # Test 4: Get patient full consultations
    def test_get_patient_full_consultations():
        try:
            response = requests.get(f"{base_url}/api/patients/patient1/consultations", timeout=10)
            if response.status_code == 200:
                data = response.json()
                print(f"   Patient1 full consultations: {len(data)}")
                if data:
                    sample = data[0]
                    print(f"   Sample fields: {list(sample.keys())}")
                return True
            return False
        except:
            return False
    
    # Test 5: Create consultation
    def test_create_consultation():
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            consultation_data = {
                "patient_id": "patient1",
                "appointment_id": "test_appt_" + str(int(datetime.now().timestamp())),
                "date": today,
                "duree": 25,
                "poids": 13.2,
                "taille": 87.5,
                "pc": 48.0,
                "observations": "Test consultation - enfant en bonne santé",
                "traitement": "Aucun traitement spécifique",
                "bilan": "Développement normal pour l'âge",
                "relance_date": ""
            }
            
            response = requests.post(f"{base_url}/api/consultations", json=consultation_data, timeout=10)
            if response.status_code == 200:
                data = response.json()
                print(f"   Created consultation: {data.get('consultation_id', 'N/A')}")
                return True
            return False
        except:
            return False
    
    # Test 6: Get patients (context)
    def test_get_patients():
        try:
            response = requests.get(f"{base_url}/api/patients", timeout=10)
            if response.status_code == 200:
                data = response.json()
                patients = data.get('patients', [])
                print(f"   Found {len(patients)} patients")
                return True
            return False
        except:
            return False
    
    # Test 7: Get specific patient
    def test_get_patient():
        try:
            response = requests.get(f"{base_url}/api/patients/patient1", timeout=10)
            if response.status_code == 200:
                data = response.json()
                name = f"{data.get('nom', '')} {data.get('prenom', '')}"
                consultations = len(data.get('consultations', []))
                print(f"   Patient: {name}, Consultations: {consultations}")
                return True
            return False
        except:
            return False
    
    # Run all tests
    run_test("Initialize Demo Data", test_init_demo)
    run_test("Get All Consultations", test_get_consultations)
    run_test("Get Patient Consultations", test_get_patient_consultations)
    run_test("Get Patient Full Consultations", test_get_patient_full_consultations)
    run_test("Create Consultation", test_create_consultation)
    run_test("Get Patients", test_get_patients)
    run_test("Get Specific Patient", test_get_patient)
    
    # Summary
    print("\n" + "=" * 60)
    print(f"📊 CONSULTATION API TEST SUMMARY")
    print(f"Tests Passed: {tests_passed}/{tests_total}")
    print(f"Success Rate: {(tests_passed/tests_total*100):.1f}%" if tests_total > 0 else "0%")
    
    return tests_passed == tests_total

if __name__ == "__main__":
    success = test_consultation_apis()
    sys.exit(0 if success else 1)