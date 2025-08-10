#!/usr/bin/env python3
"""
EXTENDED WAITING TIME BUG TESTING
Testing with longer waiting periods to understand the calculation logic
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

class ExtendedWaitingTimeTester:
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
    
    def test_multiple_waiting_periods(self):
        """Test with multiple different waiting periods"""
        print("\n⏱️ TESTING MULTIPLE WAITING PERIODS")
        
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Get appointments
        try:
            response = self.session.get(f"{BACKEND_URL}/rdv/jour/{today}", timeout=10)
            if response.status_code == 200:
                appointments = response.json()
                if appointments and len(appointments) > 0:
                    test_appointment = appointments[0]
                    rdv_id = test_appointment.get("id")
                    patient_info = test_appointment.get("patient", {})
                    patient_name = f"{patient_info.get('prenom', '')} {patient_info.get('nom', '')}"
                    
                    print(f"Using test patient: {patient_name}")
                    
                    # Test different waiting periods
                    waiting_periods = [5, 30, 60, 120]  # 5 seconds, 30 seconds, 1 minute, 2 minutes
                    
                    for wait_seconds in waiting_periods:
                        print(f"\n--- Testing {wait_seconds} second waiting period ---")
                        
                        # Move to attente
                        start_time = time.time()
                        attente_start_time = datetime.now()
                        
                        update_data = {"statut": "attente"}
                        response = self.session.put(f"{BACKEND_URL}/rdv/{rdv_id}/statut", json=update_data, timeout=10)
                        response_time = time.time() - start_time
                        
                        if response.status_code == 200:
                            data = response.json()
                            heure_arrivee = data.get("heure_arrivee_attente", "NOT_PROVIDED")
                            self.log_test(f"Move to Attente ({wait_seconds}s test)", True, f"heure_arrivee_attente: {heure_arrivee}", response_time)
                            
                            # Wait the specified period
                            print(f"Waiting {wait_seconds} seconds...")
                            time.sleep(wait_seconds)
                            
                            # Move to en_cours
                            start_time = time.time()
                            en_cours_start_time = datetime.now()
                            
                            update_data = {"statut": "en_cours"}
                            response = self.session.put(f"{BACKEND_URL}/rdv/{rdv_id}/statut", json=update_data, timeout=10)
                            response_time = time.time() - start_time
                            
                            if response.status_code == 200:
                                data = response.json()
                                calculated_duree = data.get("duree_attente", "NOT_PROVIDED")
                                
                                # Calculate expected waiting time
                                time_diff = en_cours_start_time - attente_start_time
                                expected_minutes = max(0, int(time_diff.total_seconds() / 60))
                                actual_seconds = time_diff.total_seconds()
                                
                                details = f"Waited {wait_seconds}s ({actual_seconds:.1f}s actual), calculated duree_attente: {calculated_duree}, expected: ~{expected_minutes} min"
                                
                                if calculated_duree == "NOT_PROVIDED":
                                    self.log_test(f"En_Cours Calculation ({wait_seconds}s)", False, "duree_attente not in API response", response_time)
                                else:
                                    self.log_test(f"En_Cours Calculation ({wait_seconds}s)", True, details, response_time)
                                
                                # Check database storage
                                start_time = time.time()
                                response = self.session.get(f"{BACKEND_URL}/rdv/jour/{today}", timeout=10)
                                response_time = time.time() - start_time
                                
                                if response.status_code == 200:
                                    updated_appointments = response.json()
                                    updated_appointment = next((apt for apt in updated_appointments if apt.get("id") == rdv_id), None)
                                    
                                    if updated_appointment:
                                        stored_duree = updated_appointment.get("duree_attente")
                                        stored_heure_arrivee = updated_appointment.get("heure_arrivee_attente")
                                        
                                        details = f"Database - duree_attente: {stored_duree}, heure_arrivee: {stored_heure_arrivee}"
                                        self.log_test(f"Database Storage ({wait_seconds}s)", True, details, response_time)
                            else:
                                self.log_test(f"En_Cours Move ({wait_seconds}s)", False, f"HTTP {response.status_code}", response_time)
                        else:
                            self.log_test(f"Attente Move ({wait_seconds}s)", False, f"HTTP {response.status_code}", response_time)
                        
                        # Small delay between tests
                        time.sleep(2)
                
                else:
                    print("No appointments found for testing")
            else:
                print(f"Failed to get appointments: HTTP {response.status_code}")
        except Exception as e:
            print(f"Exception during testing: {str(e)}")
    
    def analyze_current_appointments(self):
        """Analyze current appointments and their duree_attente values"""
        print("\n📊 ANALYZING CURRENT APPOINTMENTS")
        
        today = datetime.now().strftime("%Y-%m-%d")
        start_time = time.time()
        
        try:
            response = self.session.get(f"{BACKEND_URL}/rdv/jour/{today}", timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                appointments = response.json()
                if isinstance(appointments, list):
                    total_appointments = len(appointments)
                    
                    print(f"Total appointments today: {total_appointments}")
                    
                    # Analyze duree_attente values
                    duree_analysis = {
                        "null": 0,
                        "zero": 0,
                        "one": 0,
                        "greater_than_one": 0,
                        "undefined": 0
                    }
                    
                    for apt in appointments:
                        patient_info = apt.get("patient", {})
                        patient_name = f"{patient_info.get('prenom', '')} {patient_info.get('nom', '')}"
                        duree_attente = apt.get("duree_attente")
                        statut = apt.get("statut")
                        heure_arrivee = apt.get("heure_arrivee_attente", "")
                        
                        if duree_attente is None:
                            duree_analysis["null"] += 1
                            category = "null"
                        elif duree_attente == 0:
                            duree_analysis["zero"] += 1
                            category = "zero"
                        elif duree_attente == 1:
                            duree_analysis["one"] += 1
                            category = "one"
                        elif duree_attente > 1:
                            duree_analysis["greater_than_one"] += 1
                            category = "greater_than_one"
                        elif "duree_attente" not in apt:
                            duree_analysis["undefined"] += 1
                            category = "undefined"
                        else:
                            category = "other"
                        
                        details = f"Patient: '{patient_name}' - Status: {statut}, duree_attente: {duree_attente} ({category}), heure_arrivee: {heure_arrivee}"
                        self.log_test(f"Appointment Analysis - {patient_name}", True, details, 0)
                    
                    # Summary
                    summary = f"Null: {duree_analysis['null']}, Zero: {duree_analysis['zero']}, One: {duree_analysis['one']}, >1: {duree_analysis['greater_than_one']}, Undefined: {duree_analysis['undefined']}"
                    self.log_test("Duree_Attente Distribution", True, summary, response_time)
                    
                else:
                    self.log_test("Current Appointments Analysis", False, "Response is not a list", response_time)
            else:
                self.log_test("Current Appointments Analysis", False, f"HTTP {response.status_code}: {response.text}", response_time)
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("Current Appointments Analysis", False, f"Exception: {str(e)}", response_time)
    
    def run_extended_tests(self):
        """Run extended waiting time tests"""
        print("🚨 EXTENDED WAITING TIME BUG TESTING")
        print("=" * 80)
        
        # Step 1: Authentication
        if not self.authenticate():
            print("❌ Authentication failed. Cannot proceed with testing.")
            return False
        
        # Step 2: Analyze current appointments
        self.analyze_current_appointments()
        
        # Step 3: Test multiple waiting periods
        self.test_multiple_waiting_periods()
        
        # Summary
        self.print_summary()
        
        return True
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 80)
        print("🔍 EXTENDED WAITING TIME TEST SUMMARY")
        print("=" * 80)
        
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
        
        if failed_tests > 0:
            print("\n❌ Issues found:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"   - {result['test']}: {result['details']}")
        else:
            print("\n✅ All tests passed")
        
        print("=" * 80)

def main():
    """Main function"""
    tester = ExtendedWaitingTimeTester()
    
    try:
        success = tester.run_extended_tests()
        if success:
            print("\n✅ Extended waiting time test completed")
        else:
            print("\n❌ Extended waiting time test failed")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()