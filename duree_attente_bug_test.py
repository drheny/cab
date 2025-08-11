#!/usr/bin/env python3
"""
SPECIFIC DUREE_ATTENTE BUG FIX TESTING
Testing the specific bug fix applied to line 1789 in backend/server.py

BUG FIX APPLIED:
Changed: `if existing_duree_attente is None:`
TO: `if existing_duree_attente is None or existing_duree_attente == 0:`

This should fix the issue where duree_attente=0 was treated as "already calculated" 
instead of "needs calculation".

TEST SEQUENCE:
1. Login with medecin/medecin123  
2. Take any patient
3. Move to "attente" status 
4. Wait 15 seconds to accumulate time
5. Move to "en_cours" status
6. Verify that duree_attente is calculated correctly (should be ≈1 minute for 15 seconds)
"""

import requests
import json
import time
from datetime import datetime, timedelta
import sys
import os

# Configuration
BACKEND_URL = "https://a657b56d-56f9-415b-a575-b3b503d7e7a0.preview.emergentagent.com/api"
TEST_CREDENTIALS = {
    "username": "medecin",
    "password": "medecin123"
}

class DureeAttenteBugTester:
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
        """Step 1: Login with medecin/medecin123"""
        print("\n🔐 STEP 1: Login with medecin/medecin123")
        start_time = time.time()
        
        try:
            response = self.session.post(
                f"{BACKEND_URL}/auth/login",
                json=TEST_CREDENTIALS,
                timeout=30
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
            self.log_test("Authentication Login", False, error_details, response_time)
            return False
    
    def get_test_patient(self):
        """Step 2: Get any patient for testing"""
        print("\n👥 STEP 2: Get any patient for testing")
        start_time = time.time()
        
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            response = self.session.get(f"{BACKEND_URL}/rdv/jour/{today}", timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                appointments = response.json()
                if appointments and len(appointments) > 0:
                    # Find a suitable test appointment
                    test_appointment = appointments[0]  # Take the first one
                    
                    patient_info = test_appointment.get("patient", {})
                    patient_name = f"{patient_info.get('prenom', '')} {patient_info.get('nom', '')}"
                    rdv_id = test_appointment.get("id")
                    current_status = test_appointment.get("statut")
                    current_duree = test_appointment.get("duree_attente")
                    
                    details = f"Selected patient: '{patient_name}' - ID: {rdv_id}, Status: {current_status}, duree_attente: {current_duree}"
                    self.log_test("Patient Selection", True, details, response_time)
                    
                    return {
                        "rdv_id": rdv_id,
                        "patient_name": patient_name,
                        "current_status": current_status,
                        "current_duree": current_duree
                    }
                else:
                    self.log_test("Patient Selection", False, "No appointments found for today", response_time)
                    return None
            else:
                self.log_test("Patient Selection", False, f"HTTP {response.status_code}: {response.text}", response_time)
                return None
                
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("Patient Selection", False, f"Exception: {str(e)}", response_time)
            return None
    
    def move_to_attente(self, patient_data):
        """Step 3: Move patient to 'attente' status"""
        print("\n🏥 STEP 3: Move patient to 'attente' status")
        start_time = time.time()
        
        try:
            rdv_id = patient_data["rdv_id"]
            patient_name = patient_data["patient_name"]
            
            # Record the time when we move to attente
            self.attente_start_time = datetime.now()
            
            update_data = {"statut": "attente"}
            response = self.session.put(f"{BACKEND_URL}/rdv/{rdv_id}/statut", json=update_data, timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                heure_arrivee = data.get("heure_arrivee_attente", "NOT_SET")
                duree_attente = data.get("duree_attente", "NOT_PROVIDED")
                
                details = f"Moved '{patient_name}' to attente - heure_arrivee_attente: {heure_arrivee}, duree_attente: {duree_attente}"
                self.log_test("Move to Attente Status", True, details, response_time)
                return True
            else:
                self.log_test("Move to Attente Status", False, f"HTTP {response.status_code}: {response.text}", response_time)
                return False
                
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("Move to Attente Status", False, f"Exception: {str(e)}", response_time)
            return False
    
    def wait_accumulate_time(self):
        """Step 4: Wait 15 seconds to accumulate time"""
        print("\n⏰ STEP 4: Wait 15 seconds to accumulate time")
        print("Waiting 15 seconds to accumulate waiting time...")
        
        start_time = time.time()
        time.sleep(15)  # Wait 15 seconds
        response_time = time.time() - start_time
        
        details = f"Waited {response_time:.1f} seconds to accumulate waiting time"
        self.log_test("Wait to Accumulate Time", True, details, response_time)
        return True
    
    def move_to_en_cours_and_verify(self, patient_data):
        """Step 5: Move to 'en_cours' status and verify duree_attente calculation"""
        print("\n🩺 STEP 5: Move to 'en_cours' and verify duree_attente calculation")
        start_time = time.time()
        
        try:
            rdv_id = patient_data["rdv_id"]
            patient_name = patient_data["patient_name"]
            
            # Record the time when we move to en_cours
            en_cours_start_time = datetime.now()
            
            update_data = {"statut": "en_cours"}
            response = self.session.put(f"{BACKEND_URL}/rdv/{rdv_id}/statut", json=update_data, timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                # CRITICAL CHECK: duree_attente should be calculated correctly
                if "duree_attente" in data:
                    calculated_duree = data["duree_attente"]
                    
                    # Calculate expected waiting time (should be ≈1 minute for 15 seconds)
                    time_diff = en_cours_start_time - self.attente_start_time
                    expected_minutes = max(0, int(time_diff.total_seconds() / 60))
                    
                    details = f"API response duree_attente: {calculated_duree} minutes (expected: ≈{expected_minutes} min for {time_diff.total_seconds():.1f}s wait)"
                    
                    # BUG FIX VERIFICATION: Duration should be calculated correctly
                    if calculated_duree == 0 and time_diff.total_seconds() >= 15:
                        # This would indicate the bug is NOT fixed - duree_attente=0 was treated as "already calculated"
                        self.log_test("🚨 BUG NOT FIXED - duree_attente=0 treated as calculated", False, 
                                    f"duree_attente remained 0 despite {time_diff.total_seconds():.1f}s wait time", response_time)
                    elif calculated_duree >= expected_minutes:
                        # This indicates the bug fix is working - duree_attente=0 was recalculated
                        self.log_test("✅ BUG FIX WORKING - duree_attente recalculated correctly", True, details, response_time)
                    else:
                        # Unexpected result
                        self.log_test("⚠️ Unexpected duree_attente calculation", True, details, response_time)
                    
                    return calculated_duree
                else:
                    details = "API response does NOT include duree_attente field"
                    self.log_test("API Response Missing duree_attente", False, details, response_time)
                    return None
            else:
                self.log_test("Move to En_Cours Status", False, f"HTTP {response.status_code}: {response.text}", response_time)
                return None
                
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("Move to En_Cours Status", False, f"Exception: {str(e)}", response_time)
            return None
    
    def verify_database_persistence(self, patient_data, expected_duree):
        """Step 6: Verify that duree_attente is stored correctly in database"""
        print("\n💾 STEP 6: Verify database persistence")
        start_time = time.time()
        
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            response = self.session.get(f"{BACKEND_URL}/rdv/jour/{today}", timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                appointments = response.json()
                rdv_id = patient_data["rdv_id"]
                patient_name = patient_data["patient_name"]
                
                # Find our test appointment
                updated_appointment = next((apt for apt in appointments if apt.get("id") == rdv_id), None)
                
                if updated_appointment:
                    stored_duree = updated_appointment.get("duree_attente")
                    stored_heure_arrivee = updated_appointment.get("heure_arrivee_attente")
                    current_status = updated_appointment.get("statut")
                    
                    details = f"Database - Patient: '{patient_name}', Status: {current_status}, duree_attente: {stored_duree}, heure_arrivee: {stored_heure_arrivee}"
                    
                    # Verify the value is stored correctly
                    if stored_duree == expected_duree:
                        self.log_test("Database Persistence Verification", True, details, response_time)
                    else:
                        self.log_test("Database Persistence Mismatch", False, 
                                    f"Expected: {expected_duree}, Stored: {stored_duree}. {details}", response_time)
                    
                    return stored_duree
                else:
                    self.log_test("Database Persistence Verification", False, f"Appointment {rdv_id} not found", response_time)
                    return None
            else:
                self.log_test("Database Persistence Verification", False, f"HTTP {response.status_code}: {response.text}", response_time)
                return None
                
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("Database Persistence Verification", False, f"Exception: {str(e)}", response_time)
            return None
    
    def run_bug_fix_test(self):
        """Run the complete bug fix test sequence"""
        print("🚨 SPECIFIC DUREE_ATTENTE BUG FIX TESTING")
        print("=" * 60)
        print("Testing the fix: `if existing_duree_attente is None or existing_duree_attente == 0:`")
        print("This should fix duree_attente=0 being treated as 'already calculated'")
        print("=" * 60)
        
        # Step 1: Authenticate
        if not self.authenticate():
            print("❌ Authentication failed - cannot continue test")
            return False
        
        # Step 2: Get test patient
        patient_data = self.get_test_patient()
        if not patient_data:
            print("❌ No patient available for testing - cannot continue")
            return False
        
        # Step 3: Move to attente
        if not self.move_to_attente(patient_data):
            print("❌ Failed to move patient to attente - cannot continue")
            return False
        
        # Step 4: Wait to accumulate time
        self.wait_accumulate_time()
        
        # Step 5: Move to en_cours and verify calculation
        calculated_duree = self.move_to_en_cours_and_verify(patient_data)
        if calculated_duree is None:
            print("❌ Failed to move to en_cours or get duree_attente - test incomplete")
            return False
        
        # Step 6: Verify database persistence
        stored_duree = self.verify_database_persistence(patient_data, calculated_duree)
        
        # Final summary
        self.print_summary()
        
        return True
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("🏁 DUREE_ATTENTE BUG FIX TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = len([t for t in self.test_results if t["success"]])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        total_time = time.time() - self.start_time
        print(f"Total Execution Time: {total_time:.2f} seconds")
        
        print("\nDetailed Results:")
        for result in self.test_results:
            print(f"{result['status']} {result['test']} ({result['response_time']:.3f}s)")
            if result['details']:
                print(f"    {result['details']}")
        
        # Key findings
        print("\n🔍 KEY FINDINGS:")
        bug_fix_tests = [t for t in self.test_results if "BUG" in t["test"]]
        if bug_fix_tests:
            for test in bug_fix_tests:
                if test["success"]:
                    print(f"✅ {test['test']}: {test['details']}")
                else:
                    print(f"❌ {test['test']}: {test['details']}")
        
        print("\n" + "=" * 60)

def main():
    """Main function to run the bug fix test"""
    tester = DureeAttenteBugTester()
    success = tester.run_bug_fix_test()
    
    if success:
        print("\n🎉 Bug fix test completed successfully!")
        return 0
    else:
        print("\n💥 Bug fix test failed or incomplete!")
        return 1

if __name__ == "__main__":
    sys.exit(main())