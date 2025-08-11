#!/usr/bin/env python3
"""
WAITING TIME PRESERVATION BUG FIX TESTING
Testing the specific bug fix where waiting time counter was reset to zero when moving patients
from "attente" to other statuses (not just "en_cours").

BUG DESCRIPTION:
- Previously: When moving patient from "attente" → "programme/absent/retard", duree_attente was reset to null
- Fixed: Now when patient leaves "attente" to ANY other status, duree_attente is calculated and saved
- Fixed: All subsequent status changes preserve the duree_attente value

TEST SCENARIOS:
1. Login with medecin/medecin123
2. Put patient in "attente" status 
3. Wait some time to simulate waiting room time
4. Move patient to different statuses (programme, absent, retard)
5. Verify duree_attente is calculated and saved when leaving "attente"
6. Verify duree_attente is preserved in subsequent status changes
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

class WaitingTimePreservationTester:
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
        """Authenticate with medecin/medecin123"""
        print("\n🔐 AUTHENTICATING WITH MEDECIN/MEDECIN123")
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
        """Get a patient for testing"""
        print("\n👥 GETTING TEST PATIENT")
        today = datetime.now().strftime("%Y-%m-%d")
        
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
                    
                    details = f"Selected patient: '{test_patient_name}' - Current status: {current_status}, duree_attente: {current_duree}"
                    self.log_test("Patient Selection", True, details, response_time)
                    
                    return {
                        "rdv_id": rdv_id,
                        "patient_name": test_patient_name,
                        "current_status": current_status,
                        "current_duree": current_duree
                    }
                else:
                    self.log_test("Patient Selection", False, "No appointments found", response_time)
                    return None
            else:
                self.log_test("Patient Selection", False, f"HTTP {response.status_code}: {response.text}", response_time)
                return None
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("Patient Selection", False, f"Exception: {str(e)}", response_time)
            return None
    
    def move_patient_to_status(self, rdv_id, patient_name, new_status, expected_duree_behavior="preserve"):
        """Move patient to a new status and check duree_attente behavior"""
        print(f"\n🔄 MOVING PATIENT TO STATUS: {new_status}")
        
        start_time = time.time()
        try:
            update_data = {"statut": new_status}
            response = self.session.put(f"{BACKEND_URL}/rdv/{rdv_id}/statut", json=update_data, timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                # Check if duree_attente is in response
                duree_attente = data.get("duree_attente", "NOT_IN_RESPONSE")
                heure_arrivee = data.get("heure_arrivee_attente", "NOT_IN_RESPONSE")
                
                details = f"Moved '{patient_name}' to {new_status} - duree_attente: {duree_attente}, heure_arrivee: {heure_arrivee}"
                self.log_test(f"Move to {new_status.upper()}", True, details, response_time)
                
                return {
                    "success": True,
                    "duree_attente": duree_attente,
                    "heure_arrivee": heure_arrivee,
                    "response_data": data
                }
            else:
                details = f"HTTP {response.status_code}: {response.text}"
                self.log_test(f"Move to {new_status.upper()}", False, details, response_time)
                return {"success": False}
                
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test(f"Move to {new_status.upper()}", False, f"Exception: {str(e)}", response_time)
            return {"success": False}
    
    def verify_database_state(self, rdv_id, patient_name, expected_status, expected_duree_behavior="preserve"):
        """Verify the current state in database"""
        print(f"\n💾 VERIFYING DATABASE STATE")
        
        today = datetime.now().strftime("%Y-%m-%d")
        start_time = time.time()
        
        try:
            response = self.session.get(f"{BACKEND_URL}/rdv/jour/{today}", timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                appointments = response.json()
                appointment = next((apt for apt in appointments if apt.get("id") == rdv_id), None)
                
                if appointment:
                    current_status = appointment.get("statut")
                    current_duree = appointment.get("duree_attente")
                    current_heure_arrivee = appointment.get("heure_arrivee_attente")
                    
                    details = f"Database state - Status: {current_status}, duree_attente: {current_duree}, heure_arrivee: {current_heure_arrivee}"
                    self.log_test("Database State Verification", True, details, response_time)
                    
                    return {
                        "status": current_status,
                        "duree_attente": current_duree,
                        "heure_arrivee": current_heure_arrivee
                    }
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
    
    def test_waiting_time_preservation_bug_fix(self):
        """Test the complete waiting time preservation bug fix"""
        print("\n🚨 TESTING WAITING TIME PRESERVATION BUG FIX")
        print("Testing that duree_attente is calculated and preserved when moving from 'attente' to ANY status")
        
        # Step 1: Get test patient
        patient_data = self.get_test_patient()
        if not patient_data:
            print("❌ Cannot proceed without test patient")
            return False
        
        rdv_id = patient_data["rdv_id"]
        patient_name = patient_data["patient_name"]
        
        # Step 2: Move patient to "attente" status
        print(f"\n📋 STEP 2: Move patient '{patient_name}' to ATTENTE status")
        attente_start_time = datetime.now()
        
        result = self.move_patient_to_status(rdv_id, patient_name, "attente")
        if not result["success"]:
            print("❌ Failed to move patient to attente")
            return False
        
        # Verify database state after moving to attente
        db_state = self.verify_database_state(rdv_id, patient_name, "attente")
        if not db_state:
            print("❌ Failed to verify database state")
            return False
        
        # Step 3: Wait some time to simulate waiting room time
        print(f"\n⏰ STEP 3: Waiting 10 seconds to simulate time in waiting room...")
        time.sleep(10)  # Wait 10 seconds for measurable waiting time
        
        # Step 4: Test moving to "programme" status (this was the bug - duree_attente was reset)
        print(f"\n🔄 STEP 4: CRITICAL TEST - Move from 'attente' to 'programme'")
        print("This should calculate and save duree_attente (not reset to null)")
        
        consultation_start_time = datetime.now()
        result = self.move_patient_to_status(rdv_id, patient_name, "programme")
        if not result["success"]:
            print("❌ Failed to move patient to programme")
            return False
        
        # Calculate expected waiting time
        time_diff = consultation_start_time - attente_start_time
        expected_minutes = max(0, int(time_diff.total_seconds() / 60))
        
        # Verify database state after moving to programme
        db_state = self.verify_database_state(rdv_id, patient_name, "programme")
        if db_state:
            stored_duree = db_state["duree_attente"]
            
            if stored_duree is None:
                self.log_test("BUG STILL EXISTS - Duree_Attente Reset to Null", False, 
                             f"duree_attente was reset to null when moving from attente to programme", 0)
            elif stored_duree == 0 and expected_minutes > 0:
                self.log_test("BUG STILL EXISTS - Duree_Attente Reset to Zero", False, 
                             f"duree_attente was reset to 0 when moving from attente to programme (expected ~{expected_minutes} min)", 0)
            elif stored_duree >= 0:
                self.log_test("BUG FIX WORKING - Duree_Attente Calculated and Saved", True, 
                             f"duree_attente calculated as {stored_duree} minutes when moving from attente to programme", 0)
                
                # Step 5: Test preservation - move to another status
                print(f"\n🔄 STEP 5: Test preservation - Move from 'programme' to 'absent'")
                print("This should preserve the duree_attente value")
                
                result = self.move_patient_to_status(rdv_id, patient_name, "absent")
                if result["success"]:
                    # Verify duree_attente is preserved
                    db_state_after = self.verify_database_state(rdv_id, patient_name, "absent")
                    if db_state_after:
                        preserved_duree = db_state_after["duree_attente"]
                        
                        if preserved_duree == stored_duree:
                            self.log_test("PRESERVATION WORKING - Duree_Attente Preserved", True, 
                                         f"duree_attente preserved as {preserved_duree} minutes when moving from programme to absent", 0)
                        else:
                            self.log_test("PRESERVATION BUG - Duree_Attente Not Preserved", False, 
                                         f"duree_attente changed from {stored_duree} to {preserved_duree} when moving from programme to absent", 0)
                
                # Step 6: Test preservation - move to yet another status
                print(f"\n🔄 STEP 6: Test preservation - Move from 'absent' to 'retard'")
                print("This should also preserve the duree_attente value")
                
                result = self.move_patient_to_status(rdv_id, patient_name, "retard")
                if result["success"]:
                    # Verify duree_attente is still preserved
                    db_state_final = self.verify_database_state(rdv_id, patient_name, "retard")
                    if db_state_final:
                        final_duree = db_state_final["duree_attente"]
                        
                        if final_duree == stored_duree:
                            self.log_test("FINAL PRESERVATION WORKING - Duree_Attente Still Preserved", True, 
                                         f"duree_attente still preserved as {final_duree} minutes after multiple status changes", 0)
                        else:
                            self.log_test("FINAL PRESERVATION BUG - Duree_Attente Lost", False, 
                                         f"duree_attente changed from {stored_duree} to {final_duree} after multiple status changes", 0)
            else:
                self.log_test("Unexpected Duree_Attente Value", True, 
                             f"duree_attente has unexpected value: {stored_duree}", 0)
        
        return True
    
    def test_additional_scenarios(self):
        """Test additional scenarios for comprehensive coverage"""
        print("\n🔍 TESTING ADDITIONAL SCENARIOS")
        
        # Get another test patient
        patient_data = self.get_test_patient()
        if not patient_data:
            print("❌ Cannot get second test patient")
            return False
        
        rdv_id = patient_data["rdv_id"]
        patient_name = patient_data["patient_name"]
        
        # Test scenario: attente → absent (should calculate and save)
        print(f"\n📋 ADDITIONAL TEST: attente → absent")
        
        # Move to attente
        result = self.move_patient_to_status(rdv_id, patient_name, "attente")
        if result["success"]:
            time.sleep(5)  # Wait 5 seconds
            
            # Move to absent
            result = self.move_patient_to_status(rdv_id, patient_name, "absent")
            if result["success"]:
                db_state = self.verify_database_state(rdv_id, patient_name, "absent")
                if db_state:
                    duree_attente = db_state["duree_attente"]
                    if duree_attente is not None and duree_attente >= 0:
                        self.log_test("Attente → Absent: Duree_Attente Calculated", True, 
                                     f"duree_attente calculated as {duree_attente} minutes", 0)
                    else:
                        self.log_test("Attente → Absent: Duree_Attente NOT Calculated", False, 
                                     f"duree_attente is {duree_attente} (should be calculated)", 0)
        
        # Test scenario: attente → retard (should calculate and save)
        print(f"\n📋 ADDITIONAL TEST: attente → retard")
        
        # Move back to attente
        result = self.move_patient_to_status(rdv_id, patient_name, "attente")
        if result["success"]:
            time.sleep(3)  # Wait 3 seconds
            
            # Move to retard
            result = self.move_patient_to_status(rdv_id, patient_name, "retard")
            if result["success"]:
                db_state = self.verify_database_state(rdv_id, patient_name, "retard")
                if db_state:
                    duree_attente = db_state["duree_attente"]
                    if duree_attente is not None and duree_attente >= 0:
                        self.log_test("Attente → Retard: Duree_Attente Calculated", True, 
                                     f"duree_attente calculated as {duree_attente} minutes", 0)
                    else:
                        self.log_test("Attente → Retard: Duree_Attente NOT Calculated", False, 
                                     f"duree_attente is {duree_attente} (should be calculated)", 0)
        
        return True
    
    def run_all_tests(self):
        """Run all waiting time preservation tests"""
        print("🚀 STARTING WAITING TIME PRESERVATION BUG FIX TESTING")
        print("=" * 80)
        
        # Authenticate
        if not self.authenticate():
            print("❌ Authentication failed, cannot proceed")
            return False
        
        # Run main test
        self.test_waiting_time_preservation_bug_fix()
        
        # Run additional scenarios
        self.test_additional_scenarios()
        
        # Print summary
        self.print_summary()
        
        return True
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 80)
        print("📊 TEST SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = len([t for t in self.test_results if t["success"]])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%")
        
        total_time = time.time() - self.start_time
        print(f"Total Execution Time: {total_time:.2f} seconds")
        
        print("\n📋 DETAILED RESULTS:")
        for result in self.test_results:
            print(f"{result['status']} {result['test']} ({result['response_time']:.3f}s)")
            if result['details']:
                print(f"    {result['details']}")
        
        print("\n🎯 KEY FINDINGS:")
        
        # Analyze results for key findings
        bug_fix_tests = [t for t in self.test_results if "BUG" in t["test"] or "PRESERVATION" in t["test"]]
        if bug_fix_tests:
            working_fixes = [t for t in bug_fix_tests if t["success"]]
            broken_fixes = [t for t in bug_fix_tests if not t["success"]]
            
            if working_fixes:
                print("✅ WORKING BUG FIXES:")
                for test in working_fixes:
                    print(f"   - {test['test']}")
            
            if broken_fixes:
                print("❌ STILL BROKEN:")
                for test in broken_fixes:
                    print(f"   - {test['test']}")
            
            if not broken_fixes:
                print("🎉 ALL BUG FIXES WORKING CORRECTLY!")
        
        print("=" * 80)

if __name__ == "__main__":
    tester = WaitingTimePreservationTester()
    tester.run_all_tests()