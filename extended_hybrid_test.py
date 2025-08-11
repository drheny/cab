#!/usr/bin/env python3
"""
EXTENDED HYBRID WAITING TIME SYSTEM TESTING
Testing with longer waiting times to verify minute calculations

This test will:
1. Test with 70+ seconds (should give 1+ minutes)
2. Verify the hybrid system works with actual minute values
3. Test preservation across multiple status changes
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

class ExtendedHybridTester:
    def __init__(self):
        self.session = requests.Session()
        self.session.verify = False
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
        """Test authentication"""
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
    
    def test_extended_waiting_time(self):
        """Test with extended waiting time (70+ seconds = 1+ minutes)"""
        print("\n⏱️ TESTING EXTENDED WAITING TIME (70+ seconds)")
        
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Get appointments
        start_time = time.time()
        try:
            response = self.session.get(f"{BACKEND_URL}/rdv/jour/{today}", timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                appointments = response.json()
                if appointments:
                    # Find a suitable test patient
                    test_appointment = appointments[0]  # Use first available
                    
                    patient_info = test_appointment.get("patient", {})
                    test_patient_name = f"{patient_info.get('prenom', '')} {patient_info.get('nom', '')}"
                    rdv_id = test_appointment.get("id")
                    
                    details = f"Selected patient: '{test_patient_name}' for extended waiting time test"
                    self.log_test("Patient Selection for Extended Test", True, details, response_time)
                    
                    # Step 1: Move to attente
                    print("\n🏥 STEP 1: Move to 'attente'")
                    start_time = time.time()
                    
                    attente_start_time = datetime.now()
                    
                    update_data = {"statut": "attente"}
                    response = self.session.put(f"{BACKEND_URL}/rdv/{rdv_id}/statut", json=update_data, timeout=10)
                    response_time = time.time() - start_time
                    
                    if response.status_code == 200:
                        data = response.json()
                        heure_arrivee = data.get("heure_arrivee_attente", "NOT_SET")
                        
                        details = f"Moved '{test_patient_name}' to attente - heure_arrivee_attente: {heure_arrivee}"
                        self.log_test("Extended Test - Move to Attente", True, details, response_time)
                        
                        # Step 2: Wait 70+ seconds for 1+ minute calculation
                        print("\n⏰ STEP 2: Wait 70+ seconds for 1+ minute calculation")
                        print("Waiting 72 seconds to accumulate 1+ minutes of waiting time...")
                        time.sleep(72)  # Wait 72 seconds = 1.2 minutes
                        
                        elapsed_time = datetime.now() - attente_start_time
                        elapsed_seconds = elapsed_time.total_seconds()
                        expected_minutes = int(elapsed_seconds / 60)
                        print(f"🔍 DEBUG: Elapsed seconds: {elapsed_seconds}, Expected minutes: {expected_minutes}")
                        
                        # Step 3: Move to en_cours and verify calculation
                        print("\n🩺 STEP 3: Move to 'en_cours' and verify calculation")
                        start_time = time.time()
                        
                        update_data = {"statut": "en_cours"}
                        response = self.session.put(f"{BACKEND_URL}/rdv/{rdv_id}/statut", json=update_data, timeout=10)
                        response_time = time.time() - start_time
                        
                        if response.status_code == 200:
                            data = response.json()
                            calculated_duree = data.get("duree_attente")
                            
                            details = f"EXTENDED TEST: duree_attente calculated: {calculated_duree} minutes (expected: {expected_minutes} min for {elapsed_seconds:.1f}s)"
                            
                            if calculated_duree == expected_minutes:
                                self.log_test("Extended Test - Correct Minute Calculation", True, details, response_time)
                            else:
                                self.log_test("Extended Test - Minute Calculation Issue", False, details, response_time)
                            
                            # Step 4: Test multiple status changes preserve the calculated value
                            print("\n🔄 STEP 4: Test multiple status changes preserve duree_attente")
                            
                            status_sequence = ["termine", "absent", "retard", "programme"]
                            
                            for new_status in status_sequence:
                                start_time = time.time()
                                update_data = {"statut": new_status}
                                response = self.session.put(f"{BACKEND_URL}/rdv/{rdv_id}/statut", json=update_data, timeout=10)
                                response_time = time.time() - start_time
                                
                                if response.status_code == 200:
                                    data = response.json()
                                    preserved_duree = data.get("duree_attente")
                                    
                                    if preserved_duree == calculated_duree:
                                        details = f"Status {new_status}: duree_attente preserved ({preserved_duree} min)"
                                        self.log_test(f"Extended Test - Preserve in {new_status}", True, details, response_time)
                                    else:
                                        details = f"Status {new_status}: duree_attente changed from {calculated_duree} to {preserved_duree}"
                                        self.log_test(f"Extended Test - Preserve in {new_status}", False, details, response_time)
                                else:
                                    self.log_test(f"Extended Test - Status Change to {new_status}", False, f"HTTP {response.status_code}", response_time)
                            
                            # Step 5: Final verification via GET API
                            print("\n📊 STEP 5: Final verification via GET API")
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
                                        details = f"EXTENDED TEST SUCCESS: Patient '{test_patient_name}' - Status: {final_status}, duree_attente: {final_duree} min (preserved for statistics)"
                                        self.log_test("Extended Test - Final Statistics Verification", True, details, response_time)
                                    else:
                                        details = f"EXTENDED TEST ISSUE: Final duree_attente {final_duree} != calculated {calculated_duree}"
                                        self.log_test("Extended Test - Final Statistics Verification", False, details, response_time)
                                else:
                                    self.log_test("Extended Test - Final Statistics Verification", False, "Appointment not found", response_time)
                            else:
                                self.log_test("Extended Test - Final Statistics Verification", False, f"HTTP {response.status_code}", response_time)
                        else:
                            self.log_test("Extended Test - Move to En_Cours", False, f"HTTP {response.status_code}", response_time)
                    else:
                        self.log_test("Extended Test - Move to Attente", False, f"HTTP {response.status_code}", response_time)
                else:
                    self.log_test("Patient Selection for Extended Test", False, "No appointments found", response_time)
            else:
                self.log_test("Patient Selection for Extended Test", False, f"HTTP {response.status_code}", response_time)
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("Extended Waiting Time Test", False, f"Exception: {str(e)}", response_time)
    
    def run_all_tests(self):
        """Run all extended tests"""
        print("🚀 STARTING EXTENDED HYBRID WAITING TIME TESTING")
        print("=" * 80)
        
        # Test 1: Authentication
        if not self.test_authentication():
            print("❌ Authentication failed. Cannot proceed with tests.")
            return
        
        # Test 2: Extended waiting time test
        self.test_extended_waiting_time()
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        total_time = time.time() - self.start_time
        total_tests = len(self.test_results)
        passed_tests = len([t for t in self.test_results if t["success"]])
        failed_tests = total_tests - passed_tests
        
        print("\n" + "=" * 80)
        print("🏁 EXTENDED HYBRID WAITING TIME TEST SUMMARY")
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
        
        print("=" * 80)

if __name__ == "__main__":
    tester = ExtendedHybridTester()
    tester.run_all_tests()