#!/usr/bin/env python3
"""
EXTENDED WORKFLOW TEST - Testing with 70 seconds to verify 1+ minutes calculation

This test verifies that the correction also works for longer durations:
- 70 seconds should give 1 minute (70s / 60 = 1.16... → 1 minute in integer division)
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

class ExtendedWorkflowTester:
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
        """Login with medecin/medecin123"""
        print("\n🔐 AUTHENTICATION")
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
    
    def test_extended_workflow(self):
        """Test with 70 seconds wait time to verify 1+ minutes calculation"""
        print("\n🎯 TESTING EXTENDED WORKFLOW - 70 seconds wait time")
        
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Get a patient
        print("\n👤 Get patient for testing")
        start_time = time.time()
        try:
            response = self.session.get(f"{BACKEND_URL}/rdv/jour/{today}", timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                appointments = response.json()
                if appointments:
                    # Take the first available patient
                    test_appointment = appointments[0]
                    patient_info = test_appointment.get("patient", {})
                    test_patient_name = f"{patient_info.get('prenom', '')} {patient_info.get('nom', '')}"
                    rdv_id = test_appointment.get("id")
                    current_duree = test_appointment.get("duree_attente")
                    current_status = test_appointment.get("statut")
                    
                    details = f"Patient: '{test_patient_name}' - Status: {current_status}, duree_attente: {current_duree}"
                    self.log_test("Patient Selection", True, details, response_time)
                    
                    # Move to attente
                    print("\n🏥 Move to 'attente'")
                    start_time = time.time()
                    
                    attente_start_time = datetime.now()
                    
                    update_data = {"statut": "attente"}
                    response = self.session.put(f"{BACKEND_URL}/rdv/{rdv_id}/statut", json=update_data, timeout=10)
                    response_time = time.time() - start_time
                    
                    if response.status_code == 200:
                        data = response.json()
                        heure_arrivee = data.get("heure_arrivee_attente", "NOT_SET")
                        
                        details = f"Patient '{test_patient_name}' moved to attente - heure_arrivee_attente: {heure_arrivee}"
                        self.log_test("Move to Attente", True, details, response_time)
                        
                        # Wait 70 seconds
                        print("\n⏰ Wait 70 seconds (should give 1 minute)")
                        print("Waiting 70 seconds...")
                        time.sleep(70)  # Wait 70 seconds
                        
                        elapsed_time = datetime.now() - attente_start_time
                        elapsed_seconds = elapsed_time.total_seconds()
                        print(f"🔍 DEBUG: Elapsed seconds: {elapsed_seconds:.1f}s")
                        
                        # Move to en_cours
                        print("\n🩺 Move to 'en_cours' - verify duree_attente calculation")
                        start_time = time.time()
                        
                        update_data = {"statut": "en_cours"}
                        response = self.session.put(f"{BACKEND_URL}/rdv/{rdv_id}/statut", json=update_data, timeout=10)
                        response_time = time.time() - start_time
                        
                        if response.status_code == 200:
                            data = response.json()
                            
                            # Check duree_attente calculation
                            if "duree_attente" in data:
                                calculated_duree = data["duree_attente"]
                                
                                # Expected: 70 seconds = 1 minute (70s / 60 = 1.16... → 1 minute)
                                expected_minutes = 1  # 70s / 60 = 1.16... → 1 minute in integer division
                                
                                details = f"duree_attente calculated: {calculated_duree} minutes (expected: {expected_minutes} min for ~70s)"
                                
                                print(f"🔍 DEBUG: duree_attente calculated: {calculated_duree}")
                                print(f"🔍 DEBUG: Expected for 70s: {expected_minutes} minutes")
                                
                                # VERIFICATION
                                if calculated_duree == expected_minutes:
                                    self.log_test("EXTENDED TEST VERIFIED - 70s = 1 minute", True, details, response_time)
                                else:
                                    self.log_test("EXTENDED TEST FAILED - Wrong calculation", False, f"Got {calculated_duree} min, expected {expected_minutes} min", response_time)
                                
                            else:
                                details = "API response does NOT include duree_attente field"
                                self.log_test("API Response Missing duree_attente", False, details, response_time)
                            
                            # Verify API persistence
                            print("\n💾 Verify API persistence")
                            start_time = time.time()
                            
                            response = self.session.get(f"{BACKEND_URL}/rdv/jour/{today}", timeout=10)
                            response_time = time.time() - start_time
                            
                            if response.status_code == 200:
                                updated_appointments = response.json()
                                updated_appointment = next((apt for apt in updated_appointments if apt.get("id") == rdv_id), None)
                                
                                if updated_appointment:
                                    persisted_duree = updated_appointment.get("duree_attente")
                                    details = f"API GET returns duree_attente: {persisted_duree} (should match calculated value)"
                                    
                                    if persisted_duree == calculated_duree:
                                        self.log_test("API Persistence Verified", True, details, response_time)
                                    else:
                                        self.log_test("API Persistence Failed", False, f"GET returns {persisted_duree}, PUT returned {calculated_duree}", response_time)
                                else:
                                    self.log_test("API Persistence Check", False, "Updated appointment not found", response_time)
                            else:
                                self.log_test("API Persistence Check", False, f"HTTP {response.status_code}: {response.text}", response_time)
                        
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
            self.log_test("Extended Workflow Test", False, f"Exception: {str(e)}", response_time)
    
    def run_all_tests(self):
        """Run all tests in sequence"""
        print("🚀 STARTING EXTENDED WORKFLOW TEST")
        print("=" * 80)
        print("Testing with 70 seconds wait time to verify:")
        print("- 70 seconds should give 1 minute (70s / 60 = 1.16... → 1 minute)")
        print("- Verifies that the correction works for longer durations")
        print("=" * 80)
        
        # Test 1: Authentication
        if not self.test_authentication():
            print("❌ Authentication failed - cannot continue")
            return
        
        # Test 2: Extended workflow
        self.test_extended_workflow()
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        total_time = time.time() - self.start_time
        total_tests = len(self.test_results)
        passed_tests = len([t for t in self.test_results if t["success"]])
        failed_tests = total_tests - passed_tests
        
        print("\n" + "=" * 80)
        print("🎯 EXTENDED WORKFLOW TEST SUMMARY")
        print("=" * 80)
        
        print(f"⏱️  Total execution time: {total_time:.2f} seconds")
        print(f"📊 Total tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"📈 Success rate: {(passed_tests/total_tests*100):.1f}%")
        
        print("\n📋 DETAILED RESULTS:")
        for result in self.test_results:
            print(f"{result['status']} {result['test']} ({result['response_time']:.3f}s)")
            if result['details']:
                print(f"    {result['details']}")
        
        print("\n🎯 EXTENDED TEST VERIFICATION:")
        extended_tests = [t for t in self.test_results if "EXTENDED TEST" in t['test']]
        if extended_tests:
            extended_passed = all(t['success'] for t in extended_tests)
            if extended_passed:
                print("✅ EXTENDED TEST VERIFIED - 70 seconds correctly calculated as 1 minute")
                print("✅ The correction works for both short (20s = 0 min) and long (70s = 1 min) durations")
            else:
                print("❌ EXTENDED TEST FAILED - 70 seconds not calculated correctly")
        else:
            if failed_tests == 0:
                print("✅ ALL TESTS PASSED - Extended workflow works correctly")
            else:
                print("❌ SOME TESTS FAILED - Please review issues")
        
        print("=" * 80)

if __name__ == "__main__":
    tester = ExtendedWorkflowTester()
    tester.run_all_tests()