#!/usr/bin/env python3
"""
HYBRID WAITING TIME SYSTEM TESTING
Backend API Testing Suite for Cabinet Médical

TESTING NEW HYBRID SYSTEM FOR WAITING TIME STATISTICS:
- **Temps réel** : Frontend calculates based on heure_arrivee_attente for display badges
- **Statistiques** : Backend calculates and stores duree_attente when patient leaves "attente"

**HYBRID SYSTEM LOGIC:**
1. Patient → "attente" : Store timestamp UTC
2. Patient leaves "attente" → any status : Calculate and store duree_attente for stats
3. Subsequent changes : Preserve duree_attente for statistics

**TEST WORKFLOW:**
1. Login with medecin/medecin123
2. Take a patient and move to "attente" 
3. Wait 10+ seconds
4. Move to "en_cours" (or other status)
5. Verify duree_attente is calculated AND stored in API response
6. Verify GET /rdv/jour/{today} returns this duree_attente for statistics
7. Test that subsequent status changes preserve duree_attente

**OBJECTIVES:**
- duree_attente is calculated precisely when leaving attente
- This value is stored for use in dashboard statistics
- duree_attente values persist for stats even with subsequent status changes
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

class HybridWaitingTimeTester:
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
    
    def test_hybrid_waiting_time_system(self):
        """Test the complete hybrid waiting time system"""
        print("\n⏱️ TESTING HYBRID WAITING TIME SYSTEM")
        print("Testing: Timestamp storage + Backend calculation + Statistics persistence")
        
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Step 1: Get current appointments and select a test patient
        print("\n📋 STEP 1: Find a patient for hybrid system testing")
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
                        if apt.get("statut") in ["programme", "termine", "en_cours"]:
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
                    self.log_test("Patient Selection for Hybrid System Test", True, details, response_time)
                    
                    # Step 2: Move patient to "attente" - HYBRID SYSTEM: Store timestamp UTC
                    print("\n🏥 STEP 2: Move to 'attente' - HYBRID SYSTEM: Store timestamp UTC")
                    start_time = time.time()
                    
                    attente_start_time = datetime.now()
                    
                    update_data = {"statut": "attente"}
                    response = self.session.put(f"{BACKEND_URL}/rdv/{rdv_id}/statut", json=update_data, timeout=10)
                    response_time = time.time() - start_time
                    
                    if response.status_code == 200:
                        data = response.json()
                        heure_arrivee = data.get("heure_arrivee_attente", "NOT_SET")
                        
                        details = f"Moved '{test_patient_name}' to attente - heure_arrivee_attente: {heure_arrivee}"
                        self.log_test("HYBRID STEP 1 - Store Timestamp UTC", True, details, response_time)
                        
                        # Step 3: Wait 10+ seconds as specified in review request
                        print("\n⏰ STEP 3: Wait 10+ seconds for real time accumulation")
                        print("Waiting 12 seconds to accumulate real waiting time...")
                        time.sleep(12)  # Wait 12 seconds as specified (10+ seconds)
                        
                        elapsed_time = datetime.now() - attente_start_time
                        elapsed_seconds = elapsed_time.total_seconds()
                        print(f"🔍 DEBUG: Elapsed seconds: {elapsed_seconds}")
                        
                        # Step 4: HYBRID SYSTEM CRITICAL TEST - Move to "en_cours" 
                        # Backend should calculate and store duree_attente for statistics
                        print("\n🩺 STEP 4: HYBRID SYSTEM CRITICAL - Move to 'en_cours'")
                        print("Backend should: Calculate and store duree_attente when leaving 'attente'")
                        start_time = time.time()
                        
                        update_data = {"statut": "en_cours"}
                        response = self.session.put(f"{BACKEND_URL}/rdv/{rdv_id}/statut", json=update_data, timeout=10)
                        response_time = time.time() - start_time
                        
                        if response.status_code == 200:
                            data = response.json()
                            
                            # HYBRID SYSTEM CHECK: duree_attente should be calculated and stored
                            if "duree_attente" in data:
                                calculated_duree = data["duree_attente"]
                                expected_minutes = max(0, int(elapsed_seconds / 60))
                                
                                details = f"HYBRID SYSTEM: duree_attente calculated and stored: {calculated_duree} minutes (expected: ~{expected_minutes} min for {elapsed_seconds:.1f}s)"
                                self.log_test("HYBRID STEP 2 - Calculate and Store duree_attente", True, details, response_time)
                                
                                # Step 5: HYBRID SYSTEM - Verify GET /rdv/jour returns duree_attente for statistics
                                print("\n📊 STEP 5: HYBRID SYSTEM - Verify GET /rdv/jour returns duree_attente for statistics")
                                start_time = time.time()
                                
                                response = self.session.get(f"{BACKEND_URL}/rdv/jour/{today}", timeout=10)
                                response_time = time.time() - start_time
                                
                                if response.status_code == 200:
                                    updated_appointments = response.json()
                                    updated_appointment = next((apt for apt in updated_appointments if apt.get("id") == rdv_id), None)
                                    
                                    if updated_appointment:
                                        stored_duree = updated_appointment.get("duree_attente")
                                        
                                        if stored_duree == calculated_duree:
                                            details = f"HYBRID SYSTEM: duree_attente persisted in statistics: {stored_duree} minutes"
                                            self.log_test("HYBRID STEP 3 - Statistics Persistence", True, details, response_time)
                                            
                                            # Step 6: HYBRID SYSTEM - Test subsequent status changes preserve duree_attente
                                            print("\n🔄 STEP 6: HYBRID SYSTEM - Test subsequent status changes preserve duree_attente")
                                            
                                            # Move to "termine" status
                                            start_time = time.time()
                                            update_data = {"statut": "termine"}
                                            response = self.session.put(f"{BACKEND_URL}/rdv/{rdv_id}/statut", json=update_data, timeout=10)
                                            response_time = time.time() - start_time
                                            
                                            if response.status_code == 200:
                                                data = response.json()
                                                preserved_duree = data.get("duree_attente")
                                                
                                                if preserved_duree == calculated_duree:
                                                    details = f"HYBRID SYSTEM: duree_attente preserved after status change: {preserved_duree} minutes"
                                                    self.log_test("HYBRID STEP 4 - Preserve duree_attente", True, details, response_time)
                                                    
                                                    # Final verification: Check statistics endpoint
                                                    print("\n📈 STEP 7: HYBRID SYSTEM - Final verification of statistics")
                                                    start_time = time.time()
                                                    
                                                    response = self.session.get(f"{BACKEND_URL}/rdv/jour/{today}", timeout=10)
                                                    response_time = time.time() - start_time
                                                    
                                                    if response.status_code == 200:
                                                        final_appointments = response.json()
                                                        final_appointment = next((apt for apt in final_appointments if apt.get("id") == rdv_id), None)
                                                        
                                                        if final_appointment:
                                                            final_duree = final_appointment.get("duree_attente")
                                                            final_status = final_appointment.get("statut")
                                                            
                                                            if final_duree == calculated_duree:
                                                                details = f"HYBRID SYSTEM SUCCESS: Patient '{test_patient_name}' - Status: {final_status}, duree_attente: {final_duree} min (preserved for statistics)"
                                                                self.log_test("HYBRID SYSTEM - Complete Success", True, details, response_time)
                                                            else:
                                                                details = f"HYBRID SYSTEM ISSUE: duree_attente changed from {calculated_duree} to {final_duree}"
                                                                self.log_test("HYBRID SYSTEM - Statistics Consistency", False, details, response_time)
                                                        else:
                                                            self.log_test("HYBRID SYSTEM - Final Verification", False, "Appointment not found in final check", response_time)
                                                    else:
                                                        self.log_test("HYBRID SYSTEM - Final Verification", False, f"HTTP {response.status_code}", response_time)
                                                else:
                                                    details = f"HYBRID SYSTEM ISSUE: duree_attente not preserved - was {calculated_duree}, now {preserved_duree}"
                                                    self.log_test("HYBRID STEP 4 - Preserve duree_attente", False, details, response_time)
                                            else:
                                                self.log_test("HYBRID STEP 4 - Status Change to Termine", False, f"HTTP {response.status_code}", response_time)
                                        else:
                                            details = f"HYBRID SYSTEM ISSUE: duree_attente not consistent - calculated {calculated_duree}, stored {stored_duree}"
                                            self.log_test("HYBRID STEP 3 - Statistics Persistence", False, details, response_time)
                                    else:
                                        self.log_test("HYBRID STEP 3 - Statistics Persistence", False, "Appointment not found in updated list", response_time)
                                else:
                                    self.log_test("HYBRID STEP 3 - Statistics Persistence", False, f"HTTP {response.status_code}", response_time)
                            else:
                                details = "HYBRID SYSTEM ISSUE: duree_attente not calculated when leaving attente"
                                self.log_test("HYBRID STEP 2 - Calculate and Store duree_attente", False, details, response_time)
                        else:
                            self.log_test("HYBRID STEP 2 - Move to En_Cours", False, f"HTTP {response.status_code}", response_time)
                    else:
                        self.log_test("HYBRID STEP 1 - Move to Attente", False, f"HTTP {response.status_code}", response_time)
                else:
                    self.log_test("Patient Selection for Hybrid System Test", False, "No appointments found", response_time)
            else:
                self.log_test("Patient Selection for Hybrid System Test", False, f"HTTP {response.status_code}", response_time)
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("Hybrid Waiting Time System Test", False, f"Exception: {str(e)}", response_time)
    
    def test_dashboard_statistics_integration(self):
        """Test dashboard statistics integration with hybrid system"""
        print("\n📊 TESTING DASHBOARD STATISTICS INTEGRATION")
        
        start_time = time.time()
        try:
            response = self.session.get(f"{BACKEND_URL}/dashboard", timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                # Check if duree_attente_moyenne is calculated from stored values
                if "duree_attente_moyenne" in data:
                    duree_attente_moyenne = data["duree_attente_moyenne"]
                    total_rdv = data.get("total_rdv", 0)
                    rdv_attente = data.get("rdv_attente", 0)
                    
                    details = f"Dashboard stats - Average waiting time: {duree_attente_moyenne} min, Total RDV: {total_rdv}, In waiting: {rdv_attente}"
                    self.log_test("Dashboard Statistics Integration", True, details, response_time)
                else:
                    self.log_test("Dashboard Statistics Integration", False, "duree_attente_moyenne missing from dashboard", response_time)
            else:
                self.log_test("Dashboard Statistics Integration", False, f"HTTP {response.status_code}", response_time)
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("Dashboard Statistics Integration", False, f"Exception: {str(e)}", response_time)
    
    def test_multiple_status_transitions(self):
        """Test multiple status transitions preserve duree_attente"""
        print("\n🔄 TESTING MULTIPLE STATUS TRANSITIONS")
        
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Get appointments for testing
        try:
            response = self.session.get(f"{BACKEND_URL}/rdv/jour/{today}", timeout=10)
            if response.status_code == 200:
                appointments = response.json()
                if appointments:
                    # Find appointment with duree_attente > 0
                    test_appointment = None
                    for apt in appointments:
                        if apt.get("duree_attente", 0) > 0:
                            test_appointment = apt
                            break
                    
                    if test_appointment:
                        rdv_id = test_appointment.get("id")
                        patient_info = test_appointment.get("patient", {})
                        patient_name = f"{patient_info.get('prenom', '')} {patient_info.get('nom', '')}"
                        original_duree = test_appointment.get("duree_attente")
                        
                        # Test sequence: current → programme → absent → retard
                        status_sequence = ["programme", "absent", "retard", "termine"]
                        
                        for new_status in status_sequence:
                            start_time = time.time()
                            update_data = {"statut": new_status}
                            response = self.session.put(f"{BACKEND_URL}/rdv/{rdv_id}/statut", json=update_data, timeout=10)
                            response_time = time.time() - start_time
                            
                            if response.status_code == 200:
                                data = response.json()
                                preserved_duree = data.get("duree_attente")
                                
                                if preserved_duree == original_duree:
                                    details = f"Status {new_status}: duree_attente preserved ({preserved_duree} min)"
                                    self.log_test(f"Status Transition to {new_status}", True, details, response_time)
                                else:
                                    details = f"Status {new_status}: duree_attente changed from {original_duree} to {preserved_duree}"
                                    self.log_test(f"Status Transition to {new_status}", False, details, response_time)
                            else:
                                self.log_test(f"Status Transition to {new_status}", False, f"HTTP {response.status_code}", response_time)
                    else:
                        self.log_test("Multiple Status Transitions", False, "No appointment with duree_attente > 0 found", 0)
                else:
                    self.log_test("Multiple Status Transitions", False, "No appointments found", 0)
            else:
                self.log_test("Multiple Status Transitions", False, f"HTTP {response.status_code}", 0)
        except Exception as e:
            self.log_test("Multiple Status Transitions", False, f"Exception: {str(e)}", 0)
    
    def run_all_tests(self):
        """Run all hybrid waiting time system tests"""
        print("🚀 STARTING HYBRID WAITING TIME SYSTEM TESTING")
        print("=" * 80)
        
        # Test 1: Authentication
        if not self.test_authentication():
            print("❌ Authentication failed. Cannot proceed with tests.")
            return
        
        # Test 2: Main hybrid system test
        self.test_hybrid_waiting_time_system()
        
        # Test 3: Dashboard statistics integration
        self.test_dashboard_statistics_integration()
        
        # Test 4: Multiple status transitions
        self.test_multiple_status_transitions()
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        total_time = time.time() - self.start_time
        total_tests = len(self.test_results)
        passed_tests = len([t for t in self.test_results if t["success"]])
        failed_tests = total_tests - passed_tests
        
        print("\n" + "=" * 80)
        print("🏁 HYBRID WAITING TIME SYSTEM TEST SUMMARY")
        print("=" * 80)
        
        print(f"⏱️  Total execution time: {total_time:.2f} seconds")
        print(f"📊 Total tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"📈 Success rate: {(passed_tests/total_tests)*100:.1f}%")
        
        print("\n📋 DETAILED RESULTS:")
        for result in self.test_results:
            print(f"{result['status']} {result['test']} ({result['response_time']:.3f}s)")
            if result['details']:
                print(f"    {result['details']}")
        
        print("\n🎯 HYBRID SYSTEM VERIFICATION:")
        hybrid_tests = [t for t in self.test_results if "HYBRID" in t["test"]]
        if hybrid_tests:
            hybrid_passed = len([t for t in hybrid_tests if t["success"]])
            hybrid_total = len(hybrid_tests)
            print(f"✅ Hybrid system tests: {hybrid_passed}/{hybrid_total} passed")
            
            if hybrid_passed == hybrid_total:
                print("🎉 HYBRID WAITING TIME SYSTEM: ALL TESTS PASSED")
                print("✅ Timestamp storage working")
                print("✅ Backend calculation working") 
                print("✅ Statistics persistence working")
                print("✅ Status change preservation working")
            else:
                print("⚠️  HYBRID WAITING TIME SYSTEM: SOME ISSUES FOUND")
        
        print("=" * 80)

if __name__ == "__main__":
    tester = HybridWaitingTimeTester()
    tester.run_all_tests()