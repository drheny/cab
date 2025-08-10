#!/usr/bin/env python3
"""
WAITING TIME BUG TESTING - SPECIFIC WORKFLOW
Testing the specific bug: "Badge of waiting time is reset to 1 min when patient passes from waiting room to other section"

WORKFLOW TO TEST:
1. Login with medecin/medecin123
2. Find or create a patient appointment 
3. Move patient to "attente" status (this should set heure_arrivee_attente)
4. Wait a few seconds
5. Move patient to "en_cours" status (this should calculate duree_attente based on time in waiting room)
6. Check what duree_attente value was calculated and stored
7. Move patient to "termine" status 
8. Check if duree_attente is preserved or changed

SUSPECTED ISSUES:
- The duree_attente calculation is always producing 1 minute regardless of actual time
- The duree_attente is not being preserved when moving to different statuses
- There's some minimum value logic still enforcing 1 minute
"""

import requests
import json
import time
from datetime import datetime, timedelta
import sys
import os

# Configuration
BACKEND_URL = "https://86e1ae33-6e29-4ce5-a743-1e543eb0a6b8.preview.emergentagent.com/api"
TEST_CREDENTIALS = {
    "username": "medecin",
    "password": "medecin123"
}

class WaitingTimeBugTester:
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
    
    def find_test_patient(self):
        """Step 2: Find or create a patient appointment"""
        print("\n👥 STEP 2: FIND TEST PATIENT - Find or create a patient appointment")
        
        today = datetime.now().strftime("%Y-%m-%d")
        start_time = time.time()
        
        try:
            response = self.session.get(f"{BACKEND_URL}/rdv/jour/{today}", timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                appointments = response.json()
                if appointments and len(appointments) > 0:
                    # Find a suitable test patient (prefer one not in termine status)
                    test_appointment = None
                    for apt in appointments:
                        if apt.get("statut") in ["programme", "attente", "en_cours"]:
                            test_appointment = apt
                            break
                    
                    if not test_appointment:
                        test_appointment = appointments[0]
                    
                    patient_info = test_appointment.get("patient", {})
                    patient_name = f"{patient_info.get('prenom', '')} {patient_info.get('nom', '')}"
                    rdv_id = test_appointment.get("id")
                    current_status = test_appointment.get("statut")
                    current_duree = test_appointment.get("duree_attente")
                    current_heure_arrivee = test_appointment.get("heure_arrivee_attente")
                    
                    details = f"Selected patient: '{patient_name}' - Status: {current_status}, duree_attente: {current_duree}, heure_arrivee: {current_heure_arrivee}"
                    self.log_test("Patient Selection", True, details, response_time)
                    
                    return {
                        "appointment": test_appointment,
                        "patient_name": patient_name,
                        "rdv_id": rdv_id,
                        "current_status": current_status,
                        "current_duree": current_duree,
                        "current_heure_arrivee": current_heure_arrivee
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
    
    def move_to_attente(self, test_data):
        """Step 3: Move patient to "attente" status (this should set heure_arrivee_attente)"""
        print("\n🏥 STEP 3: MOVE TO ATTENTE - Set heure_arrivee_attente timestamp")
        
        rdv_id = test_data["rdv_id"]
        patient_name = test_data["patient_name"]
        
        start_time = time.time()
        attente_start_time = datetime.now()
        
        try:
            update_data = {"statut": "attente"}
            response = self.session.put(f"{BACKEND_URL}/rdv/{rdv_id}/statut", json=update_data, timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                heure_arrivee = data.get("heure_arrivee_attente", "NOT_PROVIDED")
                duree_attente = data.get("duree_attente", "NOT_PROVIDED")
                
                details = f"Moved '{patient_name}' to attente - heure_arrivee_attente: {heure_arrivee}, duree_attente: {duree_attente}"
                self.log_test("Move to Attente Status", True, details, response_time)
                
                return {
                    "success": True,
                    "attente_start_time": attente_start_time,
                    "heure_arrivee_attente": heure_arrivee,
                    "duree_attente_at_attente": duree_attente
                }
            else:
                self.log_test("Move to Attente Status", False, f"HTTP {response.status_code}: {response.text}", response_time)
                return {"success": False}
                
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("Move to Attente Status", False, f"Exception: {str(e)}", response_time)
            return {"success": False}
    
    def wait_period(self, seconds=10):
        """Step 4: Wait a few seconds"""
        print(f"\n⏰ STEP 4: WAIT PERIOD - Waiting {seconds} seconds to simulate realistic waiting time")
        
        start_time = time.time()
        time.sleep(seconds)
        response_time = time.time() - start_time
        
        details = f"Waited {seconds} seconds for realistic waiting time simulation"
        self.log_test("Wait Period", True, details, response_time)
        
        return {"wait_duration_seconds": seconds}
    
    def move_to_en_cours(self, test_data, attente_data, wait_data):
        """Step 5: Move patient to "en_cours" status (this should calculate duree_attente based on time in waiting room)"""
        print("\n🩺 STEP 5: MOVE TO EN_COURS - Calculate duree_attente based on waiting time")
        
        rdv_id = test_data["rdv_id"]
        patient_name = test_data["patient_name"]
        attente_start_time = attente_data["attente_start_time"]
        
        start_time = time.time()
        en_cours_start_time = datetime.now()
        
        try:
            update_data = {"statut": "en_cours"}
            response = self.session.put(f"{BACKEND_URL}/rdv/{rdv_id}/statut", json=update_data, timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                calculated_duree = data.get("duree_attente", "NOT_PROVIDED")
                heure_arrivee = data.get("heure_arrivee_attente", "NOT_PROVIDED")
                
                # Calculate expected waiting time
                time_diff = en_cours_start_time - attente_start_time
                expected_minutes = max(1, int(time_diff.total_seconds() / 60))
                
                details = f"Moved '{patient_name}' to en_cours - API response duree_attente: {calculated_duree}, expected: ~{expected_minutes} min"
                
                # Check if duree_attente was calculated correctly
                if calculated_duree == "NOT_PROVIDED":
                    self.log_test("Move to En_Cours - API Response", False, "duree_attente not provided in API response", response_time)
                elif calculated_duree == 1 and expected_minutes > 1:
                    self.log_test("Move to En_Cours - POTENTIAL BUG", False, f"duree_attente forced to 1 min instead of real {expected_minutes} min", response_time)
                else:
                    self.log_test("Move to En_Cours - API Response", True, details, response_time)
                
                return {
                    "success": True,
                    "en_cours_start_time": en_cours_start_time,
                    "calculated_duree": calculated_duree,
                    "expected_minutes": expected_minutes,
                    "heure_arrivee_attente": heure_arrivee
                }
            else:
                self.log_test("Move to En_Cours Status", False, f"HTTP {response.status_code}: {response.text}", response_time)
                return {"success": False}
                
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("Move to En_Cours Status", False, f"Exception: {str(e)}", response_time)
            return {"success": False}
    
    def check_database_storage(self, test_data):
        """Step 6: Check what duree_attente value was calculated and stored"""
        print("\n💾 STEP 6: CHECK DATABASE STORAGE - Verify duree_attente stored correctly")
        
        rdv_id = test_data["rdv_id"]
        patient_name = test_data["patient_name"]
        today = datetime.now().strftime("%Y-%m-%d")
        
        start_time = time.time()
        
        try:
            response = self.session.get(f"{BACKEND_URL}/rdv/jour/{today}", timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                appointments = response.json()
                updated_appointment = next((apt for apt in appointments if apt.get("id") == rdv_id), None)
                
                if updated_appointment:
                    stored_duree = updated_appointment.get("duree_attente")
                    stored_heure_arrivee = updated_appointment.get("heure_arrivee_attente")
                    current_status = updated_appointment.get("statut")
                    
                    details = f"Database - Patient: '{patient_name}', Status: {current_status}, duree_attente: {stored_duree}, heure_arrivee: {stored_heure_arrivee}"
                    self.log_test("Database Storage Verification", True, details, response_time)
                    
                    return {
                        "success": True,
                        "stored_duree": stored_duree,
                        "stored_heure_arrivee": stored_heure_arrivee,
                        "current_status": current_status
                    }
                else:
                    self.log_test("Database Storage Verification", False, f"Appointment {rdv_id} not found in database", response_time)
                    return {"success": False}
            else:
                self.log_test("Database Storage Verification", False, f"HTTP {response.status_code}: {response.text}", response_time)
                return {"success": False}
                
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("Database Storage Verification", False, f"Exception: {str(e)}", response_time)
            return {"success": False}
    
    def move_to_termine(self, test_data, en_cours_data):
        """Step 7: Move patient to "termine" status"""
        print("\n✅ STEP 7: MOVE TO TERMINE - Check if duree_attente is preserved")
        
        rdv_id = test_data["rdv_id"]
        patient_name = test_data["patient_name"]
        expected_duree = en_cours_data.get("calculated_duree", "UNKNOWN")
        
        start_time = time.time()
        
        try:
            update_data = {"statut": "termine"}
            response = self.session.put(f"{BACKEND_URL}/rdv/{rdv_id}/statut", json=update_data, timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                duree_attente_in_response = data.get("duree_attente", "NOT_PROVIDED")
                
                details = f"Moved '{patient_name}' to termine - API response duree_attente: {duree_attente_in_response}, expected to preserve: {expected_duree}"
                self.log_test("Move to Termine Status", True, details, response_time)
                
                return {
                    "success": True,
                    "duree_attente_in_response": duree_attente_in_response
                }
            else:
                self.log_test("Move to Termine Status", False, f"HTTP {response.status_code}: {response.text}", response_time)
                return {"success": False}
                
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("Move to Termine Status", False, f"Exception: {str(e)}", response_time)
            return {"success": False}
    
    def final_verification(self, test_data, en_cours_data, termine_data):
        """Step 8: Check if duree_attente is preserved or changed"""
        print("\n🔍 STEP 8: FINAL VERIFICATION - Check if duree_attente preserved across status changes")
        
        rdv_id = test_data["rdv_id"]
        patient_name = test_data["patient_name"]
        today = datetime.now().strftime("%Y-%m-%d")
        
        start_time = time.time()
        
        try:
            response = self.session.get(f"{BACKEND_URL}/rdv/jour/{today}", timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                appointments = response.json()
                final_appointment = next((apt for apt in appointments if apt.get("id") == rdv_id), None)
                
                if final_appointment:
                    final_duree = final_appointment.get("duree_attente")
                    final_heure_arrivee = final_appointment.get("heure_arrivee_attente")
                    final_status = final_appointment.get("statut")
                    
                    expected_duree = en_cours_data.get("calculated_duree", "UNKNOWN")
                    
                    details = f"Final state - Patient: '{patient_name}', Status: {final_status}, duree_attente: {final_duree}, heure_arrivee: {final_heure_arrivee}"
                    
                    # Check if duree_attente was preserved
                    if final_duree == expected_duree:
                        self.log_test("Final Verification - duree_attente Preserved", True, f"duree_attente correctly preserved: {final_duree}", response_time)
                    elif final_duree != expected_duree:
                        self.log_test("Final Verification - duree_attente Changed", False, f"duree_attente changed from {expected_duree} to {final_duree}", response_time)
                    else:
                        self.log_test("Final Verification - duree_attente Status", True, details, response_time)
                    
                    return {
                        "success": True,
                        "final_duree": final_duree,
                        "final_heure_arrivee": final_heure_arrivee,
                        "final_status": final_status,
                        "preserved": final_duree == expected_duree
                    }
                else:
                    self.log_test("Final Verification", False, f"Appointment {rdv_id} not found in final check", response_time)
                    return {"success": False}
            else:
                self.log_test("Final Verification", False, f"HTTP {response.status_code}: {response.text}", response_time)
                return {"success": False}
                
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("Final Verification", False, f"Exception: {str(e)}", response_time)
            return {"success": False}
    
    def run_complete_workflow(self):
        """Run the complete waiting time bug test workflow"""
        print("🚨 WAITING TIME BUG TESTING - SPECIFIC WORKFLOW")
        print("=" * 80)
        print("Testing: Badge of waiting time is reset to 1 min when patient passes from waiting room to other section")
        print("=" * 80)
        
        # Step 1: Authentication
        if not self.authenticate():
            print("❌ Authentication failed. Cannot proceed with testing.")
            return False
        
        # Step 2: Find test patient
        test_data = self.find_test_patient()
        if not test_data:
            print("❌ Could not find test patient. Cannot proceed with testing.")
            return False
        
        # Step 3: Move to attente
        attente_data = self.move_to_attente(test_data)
        if not attente_data["success"]:
            print("❌ Failed to move patient to attente. Cannot proceed with testing.")
            return False
        
        # Step 4: Wait period
        wait_data = self.wait_period(10)  # Wait 10 seconds for measurable time
        
        # Step 5: Move to en_cours
        en_cours_data = self.move_to_en_cours(test_data, attente_data, wait_data)
        if not en_cours_data["success"]:
            print("❌ Failed to move patient to en_cours. Cannot proceed with testing.")
            return False
        
        # Step 6: Check database storage
        storage_data = self.check_database_storage(test_data)
        
        # Step 7: Move to termine
        termine_data = self.move_to_termine(test_data, en_cours_data)
        if not termine_data["success"]:
            print("❌ Failed to move patient to termine. Cannot proceed with testing.")
            return False
        
        # Step 8: Final verification
        final_data = self.final_verification(test_data, en_cours_data, termine_data)
        
        # Summary
        self.print_summary(test_data, attente_data, en_cours_data, storage_data, termine_data, final_data)
        
        return True
    
    def print_summary(self, test_data, attente_data, en_cours_data, storage_data, termine_data, final_data):
        """Print comprehensive test summary"""
        print("\n" + "=" * 80)
        print("🔍 WAITING TIME BUG TEST SUMMARY")
        print("=" * 80)
        
        patient_name = test_data["patient_name"]
        print(f"Test Patient: {patient_name}")
        print(f"Appointment ID: {test_data['rdv_id']}")
        
        print("\n📊 WORKFLOW RESULTS:")
        print(f"1. Initial Status: {test_data['current_status']}")
        print(f"2. Moved to Attente: {'✅' if attente_data['success'] else '❌'}")
        print(f"3. Wait Period: 10 seconds")
        print(f"4. Moved to En_Cours: {'✅' if en_cours_data['success'] else '❌'}")
        print(f"5. Database Storage: {'✅' if storage_data['success'] else '❌'}")
        print(f"6. Moved to Termine: {'✅' if termine_data['success'] else '❌'}")
        print(f"7. Final Verification: {'✅' if final_data['success'] else '❌'}")
        
        print("\n⏱️ WAITING TIME ANALYSIS:")
        if en_cours_data["success"]:
            calculated_duree = en_cours_data["calculated_duree"]
            expected_minutes = en_cours_data["expected_minutes"]
            print(f"Expected Duration: ~{expected_minutes} minutes")
            print(f"Calculated Duration: {calculated_duree} minutes")
            
            if calculated_duree == 1 and expected_minutes > 1:
                print("🚨 POTENTIAL BUG: Duration forced to 1 minute instead of real time")
            elif calculated_duree == "NOT_PROVIDED":
                print("🚨 POTENTIAL BUG: duree_attente not provided in API response")
            else:
                print("✅ Duration calculation appears to be working correctly")
        
        if final_data["success"]:
            preserved = final_data.get("preserved", False)
            final_duree = final_data["final_duree"]
            print(f"Final Duration: {final_duree} minutes")
            print(f"Duration Preserved: {'✅' if preserved else '❌'}")
            
            if not preserved:
                print("🚨 POTENTIAL BUG: duree_attente not preserved across status changes")
        
        print("\n📈 TEST STATISTICS:")
        total_tests = len(self.test_results)
        passed_tests = len([t for t in self.test_results if t["success"]])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        total_time = time.time() - self.start_time
        print(f"Total Execution Time: {total_time:.2f} seconds")
        
        print("\n🎯 KEY FINDINGS:")
        if failed_tests > 0:
            print("❌ Issues found during testing:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"   - {result['test']}: {result['details']}")
        else:
            print("✅ All tests passed - no obvious issues detected")
        
        print("=" * 80)

def main():
    """Main function to run the waiting time bug test"""
    tester = WaitingTimeBugTester()
    
    try:
        success = tester.run_complete_workflow()
        if success:
            print("\n✅ Waiting time bug test completed successfully")
        else:
            print("\n❌ Waiting time bug test failed")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error during testing: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()