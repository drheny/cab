#!/usr/bin/env python3
"""
DETAILED WAITING TIME CALCULATION TEST
Testing different waiting durations to understand the calculation logic
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

class DetailedWaitingTimeTester:
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
        """Authentication"""
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
    
    def test_different_waiting_durations(self):
        """Test different waiting durations to understand calculation logic"""
        print("\n🧪 TESTING DIFFERENT WAITING DURATIONS")
        
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Get appointments
        try:
            response = self.session.get(f"{BACKEND_URL}/rdv/jour/{today}", timeout=10)
            if response.status_code != 200:
                self.log_test("Get Appointments", False, f"HTTP {response.status_code}", 0)
                return
            
            appointments = response.json()
            if not appointments:
                self.log_test("Get Appointments", False, "No appointments found", 0)
                return
            
            # Find a test patient
            test_appointment = appointments[0]
            patient_info = test_appointment.get("patient", {})
            test_patient_name = f"{patient_info.get('prenom', '')} {patient_info.get('nom', '')}"
            rdv_id = test_appointment.get("id")
            
            print(f"Using test patient: {test_patient_name}")
            
            # Test different durations
            test_durations = [
                {"seconds": 5, "description": "5 seconds (very short)"},
                {"seconds": 30, "description": "30 seconds (half minute)"},
                {"seconds": 45, "description": "45 seconds (3/4 minute)"},
                {"seconds": 65, "description": "65 seconds (just over 1 minute)"},
                {"seconds": 90, "description": "90 seconds (1.5 minutes)"},
                {"seconds": 125, "description": "125 seconds (just over 2 minutes)"}
            ]
            
            for i, test_duration in enumerate(test_durations):
                print(f"\n--- TEST {i+1}: {test_duration['description']} ---")
                
                # Reset to programme
                self.reset_patient_status(rdv_id, "programme")
                time.sleep(0.5)
                
                # Move to attente
                start_time = time.time()
                attente_start_time = datetime.now()
                
                update_data = {"statut": "attente"}
                response = self.session.put(f"{BACKEND_URL}/rdv/{rdv_id}/statut", json=update_data, timeout=10)
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    heure_arrivee = data.get("heure_arrivee_attente", "NOT_SET")
                    print(f"   Moved to attente - heure_arrivee_attente: {heure_arrivee}")
                    
                    # Wait for the specified duration
                    print(f"   Waiting {test_duration['seconds']} seconds...")
                    time.sleep(test_duration["seconds"])
                    
                    # Move to en_cours
                    start_time = time.time()
                    consultation_start_time = datetime.now()
                    
                    update_data = {"statut": "en_cours"}
                    response = self.session.put(f"{BACKEND_URL}/rdv/{rdv_id}/statut", json=update_data, timeout=10)
                    response_time = time.time() - start_time
                    
                    if response.status_code == 200:
                        data = response.json()
                        calculated_duree = data.get("duree_attente", "NOT_CALCULATED")
                        
                        # Calculate expected duration
                        elapsed_time = consultation_start_time - attente_start_time
                        elapsed_seconds = elapsed_time.total_seconds()
                        expected_minutes_exact = elapsed_seconds / 60
                        expected_minutes_int = int(elapsed_seconds / 60)
                        
                        print(f"   Elapsed: {elapsed_seconds:.1f}s = {expected_minutes_exact:.2f} min")
                        print(f"   Expected (int): {expected_minutes_int} min")
                        print(f"   Calculated: {calculated_duree} min")
                        
                        # Analyze the result
                        if calculated_duree == expected_minutes_int:
                            result = "CORRECT (truncated to int)"
                        elif calculated_duree == round(expected_minutes_exact):
                            result = "CORRECT (rounded)"
                        elif calculated_duree == max(1, expected_minutes_int):
                            result = "FORCED MINIMUM 1 MINUTE"
                        elif calculated_duree == 0 and expected_minutes_exact < 1:
                            result = "CORRECT (0 for < 1 minute)"
                        else:
                            result = f"UNEXPECTED ({calculated_duree} vs expected {expected_minutes_int})"
                        
                        details = f"{test_duration['description']}: {elapsed_seconds:.1f}s → {calculated_duree} min ({result})"
                        self.log_test(f"Duration Test {i+1}", True, details, response_time)
                    else:
                        self.log_test(f"Duration Test {i+1} - En_Cours", False, f"HTTP {response.status_code}", response_time)
                else:
                    self.log_test(f"Duration Test {i+1} - Attente", False, f"HTTP {response.status_code}", response_time)
                    
        except Exception as e:
            self.log_test("Different Waiting Durations Test", False, f"Exception: {str(e)}", 0)
    
    def reset_patient_status(self, rdv_id, status):
        """Reset patient to a specific status"""
        try:
            update_data = {"statut": status}
            response = self.session.put(f"{BACKEND_URL}/rdv/{rdv_id}/statut", json=update_data, timeout=10)
            return response.status_code == 200
        except:
            return False
    
    def test_zero_minute_scenario(self):
        """Test the specific scenario that might result in 0 minutes"""
        print("\n🔍 TESTING ZERO MINUTE SCENARIO")
        
        today = datetime.now().strftime("%Y-%m-%d")
        
        try:
            response = self.session.get(f"{BACKEND_URL}/rdv/jour/{today}", timeout=10)
            if response.status_code != 200:
                return
            
            appointments = response.json()
            if not appointments:
                return
            
            test_appointment = appointments[0]
            rdv_id = test_appointment.get("id")
            patient_info = test_appointment.get("patient", {})
            test_patient_name = f"{patient_info.get('prenom', '')} {patient_info.get('nom', '')}"
            
            # Reset to programme
            self.reset_patient_status(rdv_id, "programme")
            time.sleep(0.5)
            
            # Move to attente
            attente_start_time = datetime.now()
            update_data = {"statut": "attente"}
            response = self.session.put(f"{BACKEND_URL}/rdv/{rdv_id}/statut", json=update_data, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                heure_arrivee = data.get("heure_arrivee_attente", "NOT_SET")
                print(f"   heure_arrivee_attente: {heure_arrivee}")
                
                # Wait a very short time (should result in 0 minutes)
                print("   Waiting 10 seconds (should be 0 minutes)...")
                time.sleep(10)
                
                # Move to en_cours
                consultation_start_time = datetime.now()
                update_data = {"statut": "en_cours"}
                response = self.session.put(f"{BACKEND_URL}/rdv/{rdv_id}/statut", json=update_data, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    calculated_duree = data.get("duree_attente", "NOT_CALCULATED")
                    
                    elapsed_time = consultation_start_time - attente_start_time
                    elapsed_seconds = elapsed_time.total_seconds()
                    expected_minutes = int(elapsed_seconds / 60)
                    
                    print(f"   Elapsed: {elapsed_seconds:.1f}s")
                    print(f"   Expected: {expected_minutes} min")
                    print(f"   Calculated: {calculated_duree} min")
                    
                    if calculated_duree == 0:
                        self.log_test("Zero Minute Scenario", True, f"Correctly calculated 0 minutes for {elapsed_seconds:.1f}s", 0)
                    else:
                        self.log_test("Zero Minute Scenario", False, f"Expected 0 min but got {calculated_duree} min for {elapsed_seconds:.1f}s", 0)
                        
                        # This might be the bug - check if there's a minimum duration
                        if calculated_duree == 1 and expected_minutes == 0:
                            print("   🚨 POTENTIAL BUG: System forcing minimum 1 minute even for short waits")
                
        except Exception as e:
            self.log_test("Zero Minute Scenario", False, f"Exception: {str(e)}", 0)

    def run_test(self):
        """Run the detailed waiting time calculation tests"""
        print("🚀 STARTING DETAILED WAITING TIME CALCULATION TEST")
        print("=" * 80)
        
        # Authentication
        if not self.authenticate():
            print("❌ Authentication failed - stopping test")
            return False
        
        # Test different waiting durations
        self.test_different_waiting_durations()
        
        # Test zero minute scenario specifically
        self.test_zero_minute_scenario()
        
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
    tester = DetailedWaitingTimeTester()
    success = tester.run_test()
    sys.exit(0 if success else 1)