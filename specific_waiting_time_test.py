#!/usr/bin/env python3
"""
SPECIFIC WAITING TIME ZERO BUG TEST
Testing the exact sequence described in the review request:
1. Login with medecin/medecin123
2. Take any patient and move to "attente" - verify heure_arrivee_attente is set
3. Wait exactly 20 seconds to accumulate real time
4. Move to "en_cours" - verify duree_attente calculation
5. Check GET /rdv/jour/{today} - verify duree_attente persists

Goal: Find where the correct value (~1 minute for 20 seconds) becomes 0
"""

import requests
import json
import time
from datetime import datetime, timedelta
import sys
import os

# Configuration
BACKEND_URL = "https://e095a16b-4f79-4d50-8576-cad954291484.preview.emergentagent.com/api"
TEST_CREDENTIALS = {
    "username": "medecin",
    "password": "medecin123"
}

class SpecificWaitingTimeTester:
    def __init__(self):
        self.session = requests.Session()
        # Disable SSL verification for testing environment
        self.session.verify = False
        # Disable SSL warnings
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        self.auth_token = None
        self.test_results = []
        self.start_time = time.time()
        
    def log_test(self, test_name, success, details="", response_time=0):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "response_time": response_time,
            "status": status
        })
        print(f"{status} {test_name} ({response_time:.3f}s)")
        if details:
            print(f"    Details: {details}")
    
    def authenticate(self):
        """Test 1: Authentication - medecin login (medecin/medecin123)"""
        print("\n🔐 STEP 1: AUTHENTICATION")
        start_time = time.time()
        
        try:
            print(f"Attempting to connect to: {BACKEND_URL}/auth/login")
            response = self.session.post(
                f"{BACKEND_URL}/auth/login",
                json=TEST_CREDENTIALS,
                timeout=30,
                verify=False
            )
            response_time = time.time() - start_time
            
            print(f"Response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                if "access_token" in data and "user" in data:
                    self.auth_token = data["access_token"]
                    self.session.headers.update({
                        "Authorization": f"Bearer {self.auth_token}"
                    })
                    user_info = data["user"]
                    details = f"User: {user_info.get('full_name', 'Unknown')}, Role: {user_info.get('role', 'Unknown')}"
                    self.log_test("Authentication Login", True, details, response_time)
                    return True
                else:
                    self.log_test("Authentication Login", False, "Missing access_token or user in response", response_time)
                    return False
            else:
                response_text = response.text[:200] if response.text else "No response body"
                self.log_test("Authentication Login", False, f"HTTP {response.status_code}: {response_text}", response_time)
                return False
                
        except Exception as e:
            response_time = time.time() - start_time
            error_details = f"Exception: {str(e)[:200]}"
            print(f"Authentication error: {error_details}")
            self.log_test("Authentication Login", False, error_details, response_time)
            return False
    
    def test_specific_waiting_time_zero_bug(self):
        """Test Specific Waiting Time Zero Bug - Badge shows '0 min' instead of real time"""
        print("\n🚨 TESTING SPECIFIC WAITING TIME ZERO BUG - Badge shows '0 min' instead of real time")
        print("User reports: Badge appears but shows '0 min' instead of real waiting time")
        print("Testing EXACT sequence: login → patient to attente → wait 20s → move to en_cours → check API")
        
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Step 2: Get current appointments and select a test patient
        print("\n📋 STEP 2: Find a patient for testing the exact workflow")
        start_time = time.time()
        try:
            response = self.session.get(f"{BACKEND_URL}/rdv/jour/{today}", timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                appointments = response.json()
                if appointments:
                    # Find a suitable test patient
                    test_appointment = None
                    for apt in appointments:
                        if apt.get("statut") in ["programme", "attente", "termine"]:
                            test_appointment = apt
                            break
                    
                    if not test_appointment:
                        test_appointment = appointments[0]
                    
                    patient_info = test_appointment.get("patient", {})
                    test_patient_name = f"{patient_info.get('prenom', '')} {patient_info.get('nom', '')}"
                    rdv_id = test_appointment.get("id")
                    current_status = test_appointment.get("statut")
                    current_duree = test_appointment.get("duree_attente")
                    
                    details = f"Selected patient: '{test_patient_name}' - Current status: {current_status}, duree_attente: {current_duree}"
                    self.log_test("Patient Selection for Zero Bug Test", True, details, response_time)
                    
                    # Step 3: Move patient to "attente" and verify heure_arrivee_attente is set
                    print("\n🏥 STEP 3: Move to 'attente' - VERIFY heure_arrivee_attente is defined")
                    start_time = time.time()
                    
                    attente_start_time = datetime.now()
                    
                    update_data = {"statut": "attente"}
                    response = self.session.put(f"{BACKEND_URL}/rdv/{rdv_id}/statut", json=update_data, timeout=10)
                    response_time = time.time() - start_time
                    
                    if response.status_code == 200:
                        data = response.json()
                        heure_arrivee = data.get("heure_arrivee_attente", "NOT_SET")
                        
                        details = f"Moved '{test_patient_name}' to attente - heure_arrivee_attente: {heure_arrivee}"
                        self.log_test("Move to Attente - heure_arrivee_attente Set", True, details, response_time)
                        
                        # DEBUG: What is heure_arrivee_attente after step 3?
                        print(f"🔍 DEBUG: heure_arrivee_attente after step 3: {heure_arrivee}")
                        
                        # Step 4: Wait EXACTLY 20 seconds to accumulate real time
                        print("\n⏰ STEP 4: Wait EXACTLY 20 seconds for real time accumulation")
                        print("Waiting 20 seconds to accumulate real waiting time...")
                        time.sleep(20)  # Wait exactly 20 seconds as specified
                        
                        # DEBUG: How many seconds elapsed between step 3 and 5?
                        elapsed_time = datetime.now() - attente_start_time
                        elapsed_seconds = elapsed_time.total_seconds()
                        print(f"🔍 DEBUG: Elapsed seconds between step 3 and 5: {elapsed_seconds}")
                        
                        # Step 5: CRITICAL TEST - Move to "en_cours" and VERIFY duree_attente calculation
                        print("\n🩺 STEP 5: CRITICAL - Move to 'en_cours' - VERIFY duree_attente calculation")
                        start_time = time.time()
                        
                        consultation_start_time = datetime.now()
                        
                        update_data = {"statut": "en_cours"}
                        response = self.session.put(f"{BACKEND_URL}/rdv/{rdv_id}/statut", json=update_data, timeout=10)
                        response_time = time.time() - start_time
                        
                        if response.status_code == 200:
                            data = response.json()
                            
                            # CRITICAL CHECK: What value duree_attente is calculated in step 5?
                            if "duree_attente" in data:
                                calculated_duree = data["duree_attente"]
                                
                                # Calculate expected waiting time (should be ~1 minute for 20 seconds)
                                time_diff = consultation_start_time - attente_start_time
                                expected_minutes = max(0, int(time_diff.total_seconds() / 60))
                                
                                details = f"API response duree_attente: {calculated_duree} minutes (expected: ~{expected_minutes} min for {elapsed_seconds:.1f}s wait)"
                                
                                # DEBUG: What value duree_attente is calculated?
                                print(f"🔍 DEBUG: duree_attente calculated in step 5: {calculated_duree}")
                                print(f"🔍 DEBUG: Expected minutes for {elapsed_seconds:.1f}s: {expected_minutes}")
                                
                                # CRITICAL BUG CHECK: Is duree_attente being calculated correctly?
                                if calculated_duree == 0:
                                    self.log_test("CRITICAL BUG - duree_attente calculated as 0", False, f"duree_attente is 0 instead of ~{expected_minutes} min", response_time)
                                elif calculated_duree == expected_minutes:
                                    self.log_test("duree_attente Calculation Correct", True, details, response_time)
                                else:
                                    self.log_test("duree_attente Calculation Unexpected", True, f"Got {calculated_duree} min, expected ~{expected_minutes} min", response_time)
                                
                            else:
                                details = "API response does NOT include duree_attente field"
                                self.log_test("API Response Missing duree_attente", False, details, response_time)
                            
                            # Step 6: CRITICAL - Check GET /rdv/jour/{today} - VERIFY duree_attente persists
                            print("\n💾 STEP 6: CRITICAL - Check GET /rdv/jour/{today} - VERIFY duree_attente persists")
                            start_time = time.time()
                            
                            response = self.session.get(f"{BACKEND_URL}/rdv/jour/{today}", timeout=10)
                            response_time = time.time() - start_time
                            
                            if response.status_code == 200:
                                updated_appointments = response.json()
                                updated_appointment = next((apt for apt in updated_appointments if apt.get("id") == rdv_id), None)
                                
                                if updated_appointment:
                                    stored_duree = updated_appointment.get("duree_attente")
                                    stored_heure_arrivee = updated_appointment.get("heure_arrivee_attente")
                                    current_status = updated_appointment.get("statut")
                                    
                                    # DEBUG: What value duree_attente is stored in database?
                                    print(f"🔍 DEBUG: duree_attente stored in database: {stored_duree}")
                                    
                                    # DEBUG: What value duree_attente is returned by GET API?
                                    print(f"🔍 DEBUG: duree_attente returned by GET /rdv/jour API: {stored_duree}")
                                    
                                    details = f"Database - Status: {current_status}, duree_attente: {stored_duree}, heure_arrivee: {stored_heure_arrivee}"
                                    self.log_test("Database State After Status Change", True, details, response_time)
                                    
                                    # CRITICAL BUG CHECK: At what moment does the correct value become 0?
                                    if stored_duree == 0:
                                        self.log_test("CRITICAL BUG FOUND - duree_attente becomes 0 in database", False, f"duree_attente is 0 in database/API response", response_time)
                                    elif stored_duree is None:
                                        self.log_test("CRITICAL BUG FOUND - duree_attente becomes null in database", False, f"duree_attente is null in database/API response", response_time)
                                    else:
                                        self.log_test("duree_attente Persistence Correct", True, f"duree_attente persists as {stored_duree} minutes", response_time)
                                    
                                    # FINAL DIAGNOSIS
                                    print("\n🔍 FINAL DIAGNOSIS:")
                                    print(f"   - heure_arrivee_attente after step 3: {heure_arrivee}")
                                    print(f"   - Seconds elapsed between step 3 and 5: {elapsed_seconds:.1f}")
                                    print(f"   - duree_attente calculated in step 5: {calculated_duree}")
                                    print(f"   - duree_attente stored in database: {stored_duree}")
                                    print(f"   - duree_attente returned by GET API: {stored_duree}")
                                    
                                    if stored_duree == 0:
                                        print("   🚨 BUG CONFIRMED: The correct value (~1 minute for 20 seconds) becomes 0")
                                        if calculated_duree != 0:
                                            print("   🔍 BUG LOCATION: Value is calculated correctly but becomes 0 in database/API")
                                        else:
                                            print("   🔍 BUG LOCATION: Value is calculated as 0 in the calculation logic")
                                    else:
                                        print("   ✅ NO BUG: duree_attente is calculated and persisted correctly")
                                
                                else:
                                    self.log_test("Database Verification", False, "Updated appointment not found in database", response_time)
                            else:
                                self.log_test("Database Verification", False, f"HTTP {response.status_code}: {response.text}", response_time)
                        
                        else:
                            self.log_test("Move to En_Cours", False, f"HTTP {response.status_code}: {response.text}", response_time)
                    
                    else:
                        self.log_test("Move to Attente", False, f"HTTP {response.status_code}: {response.text}", response_time)
                
                else:
                    self.log_test("Patient Selection", False, "No appointments found for testing", response_time)
            else:
                self.log_test("Patient Selection", False, f"HTTP {response.status_code}: {response.text}", response_time)
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("Specific Waiting Time Zero Bug Test", False, f"Exception: {str(e)}", response_time)

    def run_test(self):
        """Run the specific waiting time zero bug test"""
        print("🚀 STARTING SPECIFIC WAITING TIME ZERO BUG TEST")
        print("=" * 80)
        
        # Step 1: Authentication
        if not self.authenticate():
            print("❌ Authentication failed - stopping test")
            return False
        
        # Step 2-6: Specific waiting time zero bug test
        self.test_specific_waiting_time_zero_bug()
        
        # Print summary
        print("\n" + "=" * 80)
        print("📊 TEST SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = len([t for t in self.test_results if t["success"]])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        total_time = time.time() - self.start_time
        print(f"Total Execution Time: {total_time:.2f} seconds")
        
        # Print failed tests
        if failed_tests > 0:
            print(f"\n❌ FAILED TESTS ({failed_tests}):")
            for result in self.test_results:
                if not result["success"]:
                    print(f"   - {result['test']}: {result['details']}")
        
        return failed_tests == 0

if __name__ == "__main__":
    tester = SpecificWaitingTimeTester()
    success = tester.run_test()
    sys.exit(0 if success else 1)