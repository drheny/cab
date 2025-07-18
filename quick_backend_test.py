#!/usr/bin/env python3
import requests
import json
from datetime import datetime

# Test configuration
BASE_URL = "https://189cf242-5572-47ba-b2e8-ae8bb83bb108.preview.emergentagent.com"

def test_endpoint(name, endpoint, expected_status=200):
    """Test a single endpoint"""
    url = f"{BASE_URL}{endpoint}"
    print(f"\n🔍 Testing {name}: {endpoint}")
    
    try:
        response = requests.get(url, timeout=10)
        status = response.status_code
        
        if status == expected_status:
            print(f"✅ PASS - Status: {status}")
            try:
                data = response.json()
                print(f"   Response keys: {list(data.keys()) if isinstance(data, dict) else f'List with {len(data)} items'}")
                return True, data
            except:
                print(f"   Response: {response.text[:100]}...")
                return True, response.text
        else:
            print(f"❌ FAIL - Expected {expected_status}, got {status}")
            print(f"   Response: {response.text[:200]}...")
            return False, None
            
    except Exception as e:
        print(f"❌ ERROR - {str(e)}")
        return False, None

def main():
    print("🚀 Quick Backend API Test")
    print(f"Testing: {BASE_URL}")
    
    tests = [
        ("Root", "/"),
        ("Init Demo", "/api/init-demo"),
        ("Dashboard", "/api/dashboard"),
        ("Patients", "/api/patients"),
        ("Patients Count", "/api/patients/count"),
        ("Appointments", "/api/appointments"),
        ("Today's Appointments", "/api/appointments/today"),
        ("Consultations", "/api/consultations"),
        ("Payments", "/api/payments"),
    ]
    
    passed = 0
    total = len(tests)
    
    for name, endpoint in tests:
        success, data = test_endpoint(name, endpoint)
        if success:
            passed += 1
    
    print(f"\n📊 Results: {passed}/{total} tests passed")
    
    # Test a specific patient if we have demo data
    if passed > 0:
        print("\n🔍 Testing specific patient retrieval...")
        success, patients_data = test_endpoint("Get Patients", "/api/patients")
        if success and isinstance(patients_data, dict) and "patients" in patients_data:
            patients = patients_data["patients"]
            if len(patients) > 0:
                patient_id = patients[0]["id"]
                test_endpoint(f"Get Patient {patient_id}", f"/api/patients/{patient_id}")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)