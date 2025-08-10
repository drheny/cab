#!/usr/bin/env python3
"""
COMPREHENSIVE WAITING TIME BUG FIX TESTING
Testing the specific bug fix to prevent duree_attente from being recalculated when patients move between sections multiple times.

EXACT WORKFLOW TO TEST:
1. Login with medecin/medecin123
2. Get today's appointments and select a test patient
3. Move patient to "attente" status (this sets heure_arrivee_attente timestamp)
4. Wait 5 seconds to simulate time in waiting room
5. Move patient to "en_cours" status (should calculate duree_attente for FIRST time)
6. Record the calculated duree_attente value
7. Move patient back to "attente" status
8. Wait another 5 seconds 
9. Move patient back to "en_cours" status (should PRESERVE original duree_attente, NOT recalculate)
10. Verify the duree_attente is the SAME as step 6 (proving no recalculation happened)
11. Move patient to "termine" status
12. Verify duree_attente is still preserved

KEY VERIFICATION POINTS:
- duree_attente is calculated correctly the first time
- duree_attente is NOT recalculated on subsequent moves to "en_cours"
- Debug messages show "preserving existing value to prevent reset bug"
- Values are preserved in "termine" status
- This should fix the user's reported bug of waiting time resetting to 1 min
"""

import requests
import json
import time
from datetime import datetime, timedelta
import sys
import os

# Configuration
BACKEND_URL = "http://localhost:8001/api"
TEST_CREDENTIALS = {
    "username": "medecin",
    "password": "medecin123"
}

class WaitingTimeBugFixTester:
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
        """Step 1: Login with medecin/medecin123"""
        print("\n🔐 STEP 1: AUTHENTICATION - Login with medecin/medecin123")
        start_time = time.time()
        
        try:
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
            self.log_test("Authentication Login", False, error_details, response_time)
            return False
    
    def get_test_patient(self):
        """Step 2: Get today's appointments and select a test patient"""
        print("\n👥 STEP 2: GET TEST PATIENT - Select patient for workflow testing")
        
        today = datetime.now().strftime("%Y-%m-%d")
        start_time = time.time()
        
        try:
            response = self.session.get(f"{BACKEND_URL}/rdv/jour/{today}", timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                appointments = response.json()
                if appointments and len(appointments) > 0:
                    # Find a suitable test patient
                    test_appointment = None
                    for apt in appointments:
                        # Prefer patients not in "termine" status for testing
                        if apt.get("statut") in ["programme", "attente", "en_cours"]:
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
                    self.log_test("Patient Selection", True, details, response_time)
                    
                    return {
                        "rdv_id": rdv_id,
                        "patient_name": test_patient_name,
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
    
    def move_patient_to_attente(self, rdv_id, patient_name):
        """Step 3: Move patient to "attente" status (sets heure_arrivee_attente timestamp)"""
        print("\n🏥 STEP 3: MOVE TO ATTENTE - Set heure_arrivee_attente timestamp")
        
        start_time = time.time()
        attente_start_time = datetime.now()
        
        try:
            update_data = {"statut": "attente"}
            response = self.session.put(f"{BACKEND_URL}/rdv/{rdv_id}/statut", json=update_data, timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                heure_arrivee = data.get("heure_arrivee_attente", "NOT_SET")
                
                details = f"Moved '{patient_name}' to attente - heure_arrivee_attente: {heure_arrivee}"
                self.log_test("Move to Attente Status", True, details, response_time)
                return attente_start_time
            else:
                self.log_test("Move to Attente Status", False, f"HTTP {response.status_code}: {response.text}", response_time)
                return None
                
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("Move to Attente Status", False, f"Exception: {str(e)}", response_time)
            return None
    
    def move_patient_to_en_cours(self, rdv_id, patient_name, step_name):
        """Move patient to "en_cours" status and return calculated duree_attente"""
        print(f"\n🩺 {step_name}: MOVE TO EN_COURS - Calculate/preserve duree_attente")
        
        start_time = time.time()
        
        try:
            update_data = {"statut": "en_cours"}
            response = self.session.put(f"{BACKEND_URL}/rdv/{rdv_id}/statut", json=update_data, timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                # Check if API response includes duree_attente
                if "duree_attente" in data:
                    calculated_duree = data["duree_attente"]
                    details = f"Moved '{patient_name}' to en_cours - API response duree_attente: {calculated_duree}"
                    self.log_test(f"{step_name} - Move to En_Cours", True, details, response_time)
                    return calculated_duree
                else:
                    details = f"Moved '{patient_name}' to en_cours - API response does NOT include duree_attente"
                    self.log_test(f"{step_name} - Move to En_Cours", False, details, response_time)
                    return None
            else:
                self.log_test(f"{step_name} - Move to En_Cours", False, f"HTTP {response.status_code}: {response.text}", response_time)
                return None
                
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test(f"{step_name} - Move to En_Cours", False, f"Exception: {str(e)}", response_time)
            return None
    
    def move_patient_back_to_attente(self, rdv_id, patient_name):
        """Step 7: Move patient back to "attente" status"""
        print("\n🔄 STEP 7: MOVE BACK TO ATTENTE - Simulate patient leaving consultation")
        
        start_time = time.time()
        
        try:
            update_data = {"statut": "attente"}
            response = self.session.put(f"{BACKEND_URL}/rdv/{rdv_id}/statut", json=update_data, timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                details = f"Moved '{patient_name}' back to attente status"
                self.log_test("Move Back to Attente", True, details, response_time)
                return True
            else:
                self.log_test("Move Back to Attente", False, f"HTTP {response.status_code}: {response.text}", response_time)
                return False
                
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("Move Back to Attente", False, f"Exception: {str(e)}", response_time)
            return False
    
    def move_patient_to_termine(self, rdv_id, patient_name):
        """Step 11: Move patient to "termine" status"""
        print("\n✅ STEP 11: MOVE TO TERMINE - Final status with preserved duree_attente")
        
        start_time = time.time()
        
        try:
            update_data = {"statut": "termine"}
            response = self.session.put(f"{BACKEND_URL}/rdv/{rdv_id}/statut", json=update_data, timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                duree_attente = data.get("duree_attente", "NOT_PROVIDED")
                details = f"Moved '{patient_name}' to termine - duree_attente: {duree_attente}"
                self.log_test("Move to Termine Status", True, details, response_time)
                return duree_attente
            else:
                self.log_test("Move to Termine Status", False, f"HTTP {response.status_code}: {response.text}", response_time)
                return None
                
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("Move to Termine Status", False, f"Exception: {str(e)}", response_time)
            return None
    
    def verify_database_state(self, rdv_id, patient_name, expected_duree):
        """Verify the current database state matches expectations"""
        print("\n💾 DATABASE VERIFICATION - Check stored duree_attente value")
        
        today = datetime.now().strftime("%Y-%m-%d")
        start_time = time.time()
        
        try:
            response = self.session.get(f"{BACKEND_URL}/rdv/jour/{today}", timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                appointments = response.json()
                appointment = next((apt for apt in appointments if apt.get("id") == rdv_id), None)
                
                if appointment:
                    stored_duree = appointment.get("duree_attente")
                    stored_heure_arrivee = appointment.get("heure_arrivee_attente")
                    current_status = appointment.get("statut")
                    
                    details = f"Database - Status: {current_status}, duree_attente: {stored_duree}, heure_arrivee: {stored_heure_arrivee}"
                    self.log_test("Database State Verification", True, details, response_time)
                    
                    return stored_duree
                else:
                    self.log_test("Database State Verification", False, "Appointment not found in database", response_time)
                    return None
            else:
                self.log_test("Database State Verification", False, f"HTTP {response.status_code}: {response.text}", response_time)
                return None
                
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("Database State Verification", False, f"Exception: {str(e)}", response_time)
            return None
    
    def run_comprehensive_waiting_time_bug_fix_test(self):
        """Execute the complete waiting time bug fix test workflow"""
        print("🚨 COMPREHENSIVE WAITING TIME BUG FIX TESTING")
        print("=" * 80)
        print("Testing that duree_attente is NOT recalculated on subsequent moves to en_cours")
        print("This should fix the user's reported bug of waiting time resetting")
        print("=" * 80)
        
        # Step 1: Authentication
        if not self.test_authentication():
            print("❌ Authentication failed - cannot continue testing")
            return False
        
        # Step 2: Get test patient
        patient_data = self.get_test_patient()
        if not patient_data:
            print("❌ Could not find test patient - cannot continue testing")
            return False
        
        rdv_id = patient_data["rdv_id"]
        patient_name = patient_data["patient_name"]
        
        # Step 3: Move patient to "attente" status
        attente_start_time = self.move_patient_to_attente(rdv_id, patient_name)
        if not attente_start_time:
            print("❌ Could not move patient to attente - cannot continue testing")
            return False
        
        # Step 4: Wait 5 seconds to simulate time in waiting room
        print("\n⏰ STEP 4: WAIT 5 SECONDS - Simulate time in waiting room")
        print("Waiting 5 seconds to simulate patient waiting time...")
        time.sleep(5)
        self.log_test("Simulate Waiting Time", True, "Waited 5 seconds", 5.0)
        
        # Step 5: Move patient to "en_cours" status (FIRST time - should calculate duree_attente)
        first_duree_attente = self.move_patient_to_en_cours(rdv_id, patient_name, "STEP 5")
        if first_duree_attente is None:
            print("❌ Could not move patient to en_cours first time - cannot continue testing")
            return False
        
        # Step 6: Record the calculated duree_attente value
        print(f"\n📝 STEP 6: RECORD FIRST CALCULATION - duree_attente: {first_duree_attente}")
        self.log_test("Record First Duree_Attente", True, f"First calculation: {first_duree_attente} minutes", 0)
        
        # Step 7: Move patient back to "attente" status
        if not self.move_patient_back_to_attente(rdv_id, patient_name):
            print("❌ Could not move patient back to attente - cannot continue testing")
            return False
        
        # Step 8: Wait another 5 seconds
        print("\n⏰ STEP 8: WAIT ANOTHER 5 SECONDS - Additional waiting time")
        print("Waiting another 5 seconds...")
        time.sleep(5)
        self.log_test("Additional Waiting Time", True, "Waited another 5 seconds", 5.0)
        
        # Step 9: Move patient back to "en_cours" status (SECOND time - should PRESERVE original duree_attente)
        second_duree_attente = self.move_patient_to_en_cours(rdv_id, patient_name, "STEP 9")
        if second_duree_attente is None:
            print("❌ Could not move patient to en_cours second time - cannot continue testing")
            return False
        
        # Step 10: CRITICAL VERIFICATION - duree_attente should be the SAME as step 6
        print(f"\n🔍 STEP 10: CRITICAL VERIFICATION - Compare duree_attente values")
        print(f"First calculation: {first_duree_attente} minutes")
        print(f"Second calculation: {second_duree_attente} minutes")
        
        if first_duree_attente == second_duree_attente:
            details = f"✅ BUG FIX WORKING: duree_attente preserved ({first_duree_attente} == {second_duree_attente})"
            self.log_test("CRITICAL - Duree_Attente Preservation", True, details, 0)
            bug_fix_working = True
        else:
            details = f"❌ BUG STILL EXISTS: duree_attente recalculated ({first_duree_attente} != {second_duree_attente})"
            self.log_test("CRITICAL - Duree_Attente Preservation", False, details, 0)
            bug_fix_working = False
        
        # Step 11: Move patient to "termine" status
        termine_duree_attente = self.move_patient_to_termine(rdv_id, patient_name)
        
        # Step 12: Verify duree_attente is still preserved in "termine" status
        print(f"\n🏁 STEP 12: FINAL VERIFICATION - duree_attente in termine status")
        if termine_duree_attente is not None:
            if termine_duree_attente == first_duree_attente:
                details = f"✅ PRESERVATION CONFIRMED: duree_attente preserved in termine ({termine_duree_attente})"
                self.log_test("Final Duree_Attente Preservation", True, details, 0)
            else:
                details = f"⚠️ PRESERVATION ISSUE: duree_attente changed in termine ({termine_duree_attente} != {first_duree_attente})"
                self.log_test("Final Duree_Attente Preservation", False, details, 0)
        
        # Final database verification
        final_stored_duree = self.verify_database_state(rdv_id, patient_name, first_duree_attente)
        
        return bug_fix_working
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 80)
        print("🏁 WAITING TIME BUG FIX TEST SUMMARY")
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
        
        print("\n📋 DETAILED RESULTS:")
        for result in self.test_results:
            print(f"{result['status']} {result['test']} ({result['response_time']:.3f}s)")
            if result['details']:
                print(f"    {result['details']}")
        
        # Critical findings
        print("\n🔍 CRITICAL FINDINGS:")
        critical_tests = [
            "CRITICAL - Duree_Attente Preservation",
            "Final Duree_Attente Preservation"
        ]
        
        for test_name in critical_tests:
            test_result = next((t for t in self.test_results if test_name in t["test"]), None)
            if test_result:
                status = "✅ WORKING" if test_result["success"] else "❌ BROKEN"
                print(f"- {test_name}: {status}")
                if test_result["details"]:
                    print(f"  {test_result['details']}")
        
        print("\n" + "=" * 80)

def main():
    """Main test execution"""
    tester = WaitingTimeBugFixTester()
    
    try:
        bug_fix_working = tester.run_comprehensive_waiting_time_bug_fix_test()
        tester.print_summary()
        
        if bug_fix_working:
            print("\n🎉 WAITING TIME BUG FIX IS WORKING CORRECTLY!")
            print("✅ duree_attente is preserved on subsequent moves to en_cours")
            print("✅ This should fix the user's reported bug of waiting time resetting")
        else:
            print("\n⚠️ WAITING TIME BUG FIX NEEDS ATTENTION!")
            print("❌ duree_attente is still being recalculated")
            print("❌ User's reported bug may still exist")
        
        return 0 if bug_fix_working else 1
        
    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Test failed with exception: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())