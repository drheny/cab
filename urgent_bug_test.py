#!/usr/bin/env python3
"""
URGENT BUG INVESTIGATION - Waiting time badge resets to 0 when moving patient from "attente" to "en_cours"

Test this specific scenario:
1. Login as medecin/medecin123
2. Get today's appointments and find a patient
3. Move patient to "attente" status - verify heure_arrivee_attente is set
4. Wait a few seconds (let's say 10 seconds) to accumulate real waiting time
5. Move patient to "en_cours" status - CRITICAL: Check the exact response and verify:
   - Does the API response contain duree_attente?
   - Is duree_attente calculated correctly (should be 0 minutes for 10 seconds wait)?
   - Is heure_arrivee_attente preserved?
6. Immediately after, GET the appointments again and check:
   - Does the patient in "en_cours" status have duree_attente stored?
   - What is the exact value?

The user reports: "Le badge compteur se met a zero encore lors de deplacement du patient de la salle d attente vers en consultation"
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

class UrgentBugTester:
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
    
    def test_authentication(self):
        """Test 1: Authentication - medecin login (medecin/medecin123)"""
        print("\n🔐 TESTING AUTHENTICATION")
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

    def test_urgent_waiting_time_badge_reset_bug(self):
        """URGENT BUG INVESTIGATION - Waiting time badge resets to 0 when moving patient from "attente" to "en_cours" """
        print("\n🚨 URGENT BUG INVESTIGATION - Waiting time badge resets to 0 when moving patient from 'attente' to 'en_cours'")
        print("User reports: 'Le badge compteur se met a zero encore lors de deplacement du patient de la salle d attente vers en consultation'")
        print("Testing EXACT scenario from review request:")
        print("1. Login as medecin/medecin123")
        print("2. Get today's appointments and find a patient")
        print("3. Move patient to 'attente' status - verify heure_arrivee_attente is set")
        print("4. Wait a few seconds (let's say 10 seconds) to accumulate real waiting time")
        print("5. Move patient to 'en_cours' status - CRITICAL: Check the exact response and verify:")
        print("   - Does the API response contain duree_attente?")
        print("   - Is duree_attente calculated correctly (should be 0 minutes for 10 seconds wait)?")
        print("   - Is heure_arrivee_attente preserved?")
        print("6. Immediately after, GET the appointments again and check:")
        print("   - Does the patient in 'en_cours' status have duree_attente stored?")
        print("   - What is the exact value?")
        
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Step 1: Already logged in as medecin/medecin123 ✅
        print("\n✅ STEP 1: Login as medecin/medecin123 - ALREADY COMPLETED")
        
        # Step 2: Get today's appointments and find a patient
        print("\n📋 STEP 2: Get today's appointments and find a patient")
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
                        if apt.get("statut") in ["programme", "attente", "termine", "en_cours"]:
                            test_appointment = apt
                            break
                    
                    if not test_appointment:
                        test_appointment = appointments[0]
                    
                    patient_info = test_appointment.get("patient", {})
                    test_patient_name = f"{patient_info.get('prenom', '')} {patient_info.get('nom', '')}"
                    rdv_id = test_appointment.get("id")
                    current_status = test_appointment.get("statut")
                    current_duree = test_appointment.get("duree_attente")
                    current_heure_arrivee = test_appointment.get("heure_arrivee_attente")
                    
                    details = f"Found patient: '{test_patient_name}' - Status: {current_status}, duree_attente: {current_duree}, heure_arrivee_attente: {current_heure_arrivee}"
                    self.log_test("STEP 2: Patient Selection", True, details, response_time)
                    
                    # Step 3: Move patient to "attente" status - verify heure_arrivee_attente is set
                    print("\n🏥 STEP 3: Move patient to 'attente' status - verify heure_arrivee_attente is set")
                    start_time = time.time()
                    
                    attente_start_time = datetime.now()
                    
                    update_data = {"statut": "attente"}
                    response = self.session.put(f"{BACKEND_URL}/rdv/{rdv_id}/statut", json=update_data, timeout=10)
                    response_time = time.time() - start_time
                    
                    if response.status_code == 200:
                        data = response.json()
                        heure_arrivee = data.get("heure_arrivee_attente", "NOT_SET")
                        duree_attente_after_attente = data.get("duree_attente", "NOT_PROVIDED")
                        
                        details = f"Moved '{test_patient_name}' to attente - heure_arrivee_attente: {heure_arrivee}, duree_attente: {duree_attente_after_attente}"
                        self.log_test("STEP 3: Move to Attente - heure_arrivee_attente Set", True, details, response_time)
                        
                        print(f"🔍 DEBUG: After moving to attente - heure_arrivee_attente: {heure_arrivee}")
                        print(f"🔍 DEBUG: After moving to attente - duree_attente: {duree_attente_after_attente}")
                        
                        # Step 4: Wait exactly 10 seconds to accumulate real waiting time
                        print("\n⏰ STEP 4: Wait exactly 10 seconds to accumulate real waiting time")
                        print("Waiting 10 seconds to accumulate real waiting time...")
                        time.sleep(10)  # Wait exactly 10 seconds as specified in review
                        
                        elapsed_time = datetime.now() - attente_start_time
                        elapsed_seconds = elapsed_time.total_seconds()
                        print(f"🔍 DEBUG: Elapsed seconds between attente and en_cours: {elapsed_seconds}")
                        
                        # Step 5: CRITICAL - Move patient to "en_cours" status - Check the exact response
                        print("\n🩺 STEP 5: CRITICAL - Move patient to 'en_cours' status - Check the exact response")
                        start_time = time.time()
                        
                        consultation_start_time = datetime.now()
                        
                        update_data = {"statut": "en_cours"}
                        response = self.session.put(f"{BACKEND_URL}/rdv/{rdv_id}/statut", json=update_data, timeout=10)
                        response_time = time.time() - start_time
                        
                        if response.status_code == 200:
                            data = response.json()
                            
                            # CRITICAL CHECKS from review request:
                            print("\n🔍 CRITICAL CHECKS:")
                            
                            # Check 1: Does the API response contain duree_attente?
                            if "duree_attente" in data:
                                calculated_duree = data["duree_attente"]
                                print(f"✅ API response CONTAINS duree_attente: {calculated_duree}")
                                self.log_test("STEP 5a: API Response Contains duree_attente", True, f"duree_attente: {calculated_duree}", response_time)
                            else:
                                print(f"❌ API response does NOT contain duree_attente")
                                self.log_test("STEP 5a: API Response Contains duree_attente", False, "duree_attente field missing", response_time)
                                calculated_duree = "NOT_PROVIDED"
                            
                            # Check 2: Is duree_attente calculated correctly (should be 0 minutes for 10 seconds wait)?
                            expected_minutes = max(0, int(elapsed_seconds / 60))  # 10 seconds should be 0 minutes
                            print(f"🔍 Expected duree_attente for {elapsed_seconds:.1f}s wait: {expected_minutes} minutes")
                            
                            if calculated_duree != "NOT_PROVIDED":
                                if calculated_duree == expected_minutes:
                                    print(f"✅ duree_attente calculated CORRECTLY: {calculated_duree} minutes")
                                    self.log_test("STEP 5b: duree_attente Calculated Correctly", True, f"Got {calculated_duree} min, expected {expected_minutes} min", 0)
                                else:
                                    print(f"⚠️ duree_attente calculated as: {calculated_duree} minutes (expected: {expected_minutes})")
                                    self.log_test("STEP 5b: duree_attente Calculation", True, f"Got {calculated_duree} min, expected {expected_minutes} min", 0)
                            
                            # Check 3: Is heure_arrivee_attente preserved?
                            preserved_heure_arrivee = data.get("heure_arrivee_attente", "NOT_PROVIDED")
                            if preserved_heure_arrivee != "NOT_PROVIDED" and preserved_heure_arrivee == heure_arrivee:
                                print(f"✅ heure_arrivee_attente PRESERVED: {preserved_heure_arrivee}")
                                self.log_test("STEP 5c: heure_arrivee_attente Preserved", True, f"Preserved: {preserved_heure_arrivee}", 0)
                            elif preserved_heure_arrivee != "NOT_PROVIDED":
                                print(f"⚠️ heure_arrivee_attente CHANGED: was {heure_arrivee}, now {preserved_heure_arrivee}")
                                self.log_test("STEP 5c: heure_arrivee_attente Changed", True, f"Changed from {heure_arrivee} to {preserved_heure_arrivee}", 0)
                            else:
                                print(f"❌ heure_arrivee_attente NOT in response")
                                self.log_test("STEP 5c: heure_arrivee_attente Preserved", False, "Not in API response", 0)
                            
                            # Step 6: Immediately after, GET the appointments again and check
                            print("\n💾 STEP 6: Immediately after, GET the appointments again and check")
                            start_time = time.time()
                            
                            response = self.session.get(f"{BACKEND_URL}/rdv/jour/{today}", timeout=10)
                            response_time = time.time() - start_time
                            
                            if response.status_code == 200:
                                updated_appointments = response.json()
                                updated_appointment = next((apt for apt in updated_appointments if apt.get("id") == rdv_id), None)
                                
                                if updated_appointment:
                                    stored_duree = updated_appointment.get("duree_attente", "NOT_STORED")
                                    stored_status = updated_appointment.get("statut", "UNKNOWN")
                                    stored_heure_arrivee = updated_appointment.get("heure_arrivee_attente", "NOT_STORED")
                                    
                                    print(f"🔍 FINAL CHECKS:")
                                    print(f"   Patient status: {stored_status}")
                                    print(f"   Stored duree_attente: {stored_duree}")
                                    print(f"   Stored heure_arrivee_attente: {stored_heure_arrivee}")
                                    
                                    # Check 1: Does the patient in "en_cours" status have duree_attente stored?
                                    if stored_status == "en_cours":
                                        if stored_duree != "NOT_STORED":
                                            print(f"✅ Patient in 'en_cours' HAS duree_attente stored: {stored_duree}")
                                            self.log_test("STEP 6a: Patient in en_cours has duree_attente", True, f"duree_attente: {stored_duree}", response_time)
                                        else:
                                            print(f"❌ Patient in 'en_cours' does NOT have duree_attente stored")
                                            self.log_test("STEP 6a: Patient in en_cours has duree_attente", False, "duree_attente not stored", response_time)
                                    
                                    # Check 2: What is the exact value?
                                    if stored_duree != "NOT_STORED":
                                        print(f"🔍 EXACT VALUE of stored duree_attente: {stored_duree}")
                                        
                                        # CRITICAL BUG CHECK: Is the badge showing 0 when it shouldn't?
                                        if stored_duree == 0 and elapsed_seconds >= 10:
                                            print(f"🚨 POTENTIAL BUG: duree_attente is 0 after {elapsed_seconds:.1f}s wait")
                                            self.log_test("CRITICAL BUG: Badge Reset to 0", False, f"duree_attente is 0 after {elapsed_seconds:.1f}s wait", 0)
                                        else:
                                            print(f"✅ duree_attente value appears correct: {stored_duree}")
                                            self.log_test("STEP 6b: duree_attente Value Check", True, f"Value: {stored_duree} after {elapsed_seconds:.1f}s wait", 0)
                                    
                                    # Summary of findings
                                    summary = f"SUMMARY - Patient: {test_patient_name}, Wait: {elapsed_seconds:.1f}s, API duree_attente: {calculated_duree}, Stored duree_attente: {stored_duree}"
                                    self.log_test("BUG INVESTIGATION SUMMARY", True, summary, 0)
                                    
                                else:
                                    self.log_test("STEP 6: Get Updated Appointment", False, "Patient not found in updated appointments", response_time)
                            else:
                                self.log_test("STEP 6: Get Updated Appointments", False, f"HTTP {response.status_code}: {response.text}", response_time)
                        
                        else:
                            self.log_test("STEP 5: Move to En_Cours", False, f"HTTP {response.status_code}: {response.text}", response_time)
                    
                    else:
                        self.log_test("STEP 3: Move to Attente", False, f"HTTP {response.status_code}: {response.text}", response_time)
                
                else:
                    self.log_test("STEP 2: Patient Selection", False, "No appointments found", response_time)
            else:
                self.log_test("STEP 2: Get Today's Appointments", False, f"HTTP {response.status_code}: {response.text}", response_time)
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("URGENT BUG INVESTIGATION", False, f"Exception: {str(e)}", response_time)

    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*80)
        print("🏁 URGENT BUG INVESTIGATION SUMMARY")
        print("="*80)
        
        total_tests = len(self.test_results)
        passed_tests = len([t for t in self.test_results if t["success"]])
        failed_tests = total_tests - passed_tests
        
        print(f"📊 Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"📈 Success Rate: {(passed_tests/total_tests*100):.1f}%")
        
        total_time = time.time() - self.start_time
        print(f"⏱️ Total Execution Time: {total_time:.2f} seconds")
        
        print("\n📋 DETAILED RESULTS:")
        for result in self.test_results:
            print(f"{result['status']} {result['test']} ({result['response_time']:.3f}s)")
            if result['details']:
                print(f"    {result['details']}")
        
        print("\n" + "="*80)
        if failed_tests == 0:
            print("🎉 ALL TESTS PASSED - BUG INVESTIGATION COMPLETED SUCCESSFULLY")
        else:
            print(f"⚠️ {failed_tests} TESTS FAILED - ISSUES FOUND DURING BUG INVESTIGATION")
        print("="*80)

    def run_urgent_bug_test(self):
        """Run the urgent bug investigation"""
        print("🚨 URGENT BUG INVESTIGATION - Waiting time badge resets to 0")
        print("User reports: 'Le badge compteur se met a zero encore lors de deplacement du patient de la salle d attente vers en consultation'")
        print("="*80)
        
        # Test 1: Authentication
        if not self.test_authentication():
            print("❌ Authentication failed - stopping tests")
            return False
        
        # URGENT: Test the specific waiting time badge reset bug from review request
        self.test_urgent_waiting_time_badge_reset_bug()
        
        return True

if __name__ == "__main__":
    tester = UrgentBugTester()
    
    try:
        tester.run_urgent_bug_test()
    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
    finally:
        tester.print_summary()