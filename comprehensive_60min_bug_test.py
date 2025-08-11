#!/usr/bin/env python3
"""
COMPREHENSIVE 60-MINUTE BUG REPRODUCTION TEST
Simulating the exact user scenario: "When I refresh page, compteur in salle d'attente shows 60 min, while I left it at 1 min"

This test will:
1. Create a patient in attente with a specific timestamp that would cause 60-minute calculation
2. Test different timestamp formats and timezone scenarios
3. Verify frontend calculation logic by examining the exact timestamps
4. Reproduce the bug by manipulating timestamps to match the user's scenario
"""

import requests
import json
import time
from datetime import datetime, timedelta
import sys
import os
from dateutil import parser
import pytz

# Configuration
BACKEND_URL = "https://86e1ae33-6e29-4ce5-a743-1e543eb0a6b8.preview.emergentagent.com/api"
TEST_CREDENTIALS = {
    "username": "medecin",
    "password": "medecin123"
}

class ComprehensiveBugReproduction:
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
        """Authenticate with the backend"""
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
    
    def get_current_appointments(self):
        """Get current appointments to work with"""
        print("\n📋 GETTING CURRENT APPOINTMENTS")
        
        today = datetime.now().strftime("%Y-%m-%d")
        start_time = time.time()
        
        try:
            response = self.session.get(f"{BACKEND_URL}/rdv/jour/{today}", timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                appointments = response.json()
                if isinstance(appointments, list):
                    details = f"Found {len(appointments)} appointments for today"
                    self.log_test("Get Current Appointments", True, details, response_time)
                    return appointments
                else:
                    self.log_test("Get Current Appointments", False, "Response is not a list", response_time)
                    return []
            else:
                self.log_test("Get Current Appointments", False, f"HTTP {response.status_code}: {response.text}", response_time)
                return []
                
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("Get Current Appointments", False, f"Exception: {str(e)}", response_time)
            return []
    
    def test_scenario_1_timezone_mismatch(self, appointments):
        """Test Scenario 1: Timestamp stored in UTC but frontend calculates in local time"""
        print("\n🌍 SCENARIO 1: UTC TIMESTAMP + LOCAL CALCULATION = 60 MIN BUG")
        
        if not appointments:
            self.log_test("Scenario 1 - No Appointments", False, "No appointments available for testing", 0)
            return
        
        test_patient = appointments[0]
        rdv_id = test_patient.get("id")
        patient_info = test_patient.get("patient", {})
        patient_name = f"{patient_info.get('prenom', '')} {patient_info.get('nom', '')}"
        
        print(f"Testing with patient: {patient_name}")
        
        # Create a timestamp that would cause 60-minute difference
        # If current time is 16:11 UTC, and we set timestamp to 15:11 UTC,
        # but frontend treats it as 15:11 local time (which is 14:11 UTC),
        # the difference would be 16:11 - 14:11 = 2 hours = 120 minutes
        # Let's try a different approach: set timestamp 1 hour ago
        
        current_utc = datetime.now(pytz.UTC)
        one_hour_ago_utc = current_utc - timedelta(hours=1)
        
        # Format as ISO string without timezone (this is key!)
        timestamp_utc_as_naive = one_hour_ago_utc.strftime("%Y-%m-%dT%H:%M:%S.%f")
        
        print(f"Current UTC time: {current_utc}")
        print(f"Setting timestamp to: {timestamp_utc_as_naive} (1 hour ago in UTC, but stored as naive)")
        
        # Manually update the appointment with this timestamp
        start_time = time.time()
        try:
            # First move to attente
            update_data = {"statut": "attente"}
            response = self.session.put(f"{BACKEND_URL}/rdv/{rdv_id}/statut", json=update_data, timeout=10)
            
            if response.status_code == 200:
                # Now we need to manually set the timestamp to test the bug
                # Since we can't directly manipulate the database, let's examine what timestamp was set
                response_data = response.json()
                actual_timestamp = response_data.get("heure_arrivee_attente", "NOT_SET")
                
                print(f"Backend set timestamp to: {actual_timestamp}")
                
                # Calculate what the difference would be if this were interpreted differently
                if actual_timestamp and actual_timestamp != "NOT_SET":
                    # Parse the timestamp
                    parsed_timestamp = parser.parse(actual_timestamp)
                    
                    # Scenario: Frontend treats this naive timestamp as local time
                    # but it's actually UTC
                    local_tz = pytz.timezone('Europe/Paris')  # UTC+1
                    
                    if parsed_timestamp.tzinfo is None:
                        # Treat as local time
                        local_timestamp = local_tz.localize(parsed_timestamp)
                        current_local = datetime.now(local_tz)
                        
                        # Calculate difference
                        diff_minutes = (current_local - local_timestamp).total_seconds() / 60
                        
                        print(f"If timestamp {actual_timestamp} is treated as local time:")
                        print(f"  Local timestamp: {local_timestamp}")
                        print(f"  Current local: {current_local}")
                        print(f"  Difference: {diff_minutes:.1f} minutes")
                        
                        if abs(diff_minutes - 60) < 10:  # Within 10 minutes of 60
                            details = f"🚨 BUG REPRODUCED: Difference is {diff_minutes:.1f} minutes (close to 60!)"
                            self.log_test("Scenario 1 - 60 Minute Bug", False, details, time.time() - start_time)
                        else:
                            details = f"Difference is {diff_minutes:.1f} minutes (not 60-minute bug)"
                            self.log_test("Scenario 1 - Timezone Test", True, details, time.time() - start_time)
                    else:
                        details = f"Timestamp has timezone info: {parsed_timestamp.tzinfo}"
                        self.log_test("Scenario 1 - Timezone Present", True, details, time.time() - start_time)
                else:
                    self.log_test("Scenario 1 - No Timestamp", False, "No timestamp returned", time.time() - start_time)
            else:
                self.log_test("Scenario 1 - Status Update Failed", False, f"HTTP {response.status_code}", time.time() - start_time)
                
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("Scenario 1 - Exception", False, f"Exception: {str(e)}", response_time)
    
    def test_scenario_2_refresh_bug(self, appointments):
        """Test Scenario 2: Simulate page refresh and check if calculation changes"""
        print("\n🔄 SCENARIO 2: PAGE REFRESH CALCULATION CHANGE")
        
        if not appointments:
            self.log_test("Scenario 2 - No Appointments", False, "No appointments available for testing", 0)
            return
        
        # Find a patient in attente or create one
        attente_patient = None
        for apt in appointments:
            if apt.get("statut") == "attente":
                attente_patient = apt
                break
        
        if not attente_patient:
            # Create one
            test_patient = appointments[0]
            rdv_id = test_patient.get("id")
            
            start_time = time.time()
            try:
                update_data = {"statut": "attente"}
                response = self.session.put(f"{BACKEND_URL}/rdv/{rdv_id}/statut", json=update_data, timeout=10)
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    attente_patient = response.json()
                    self.log_test("Create Attente Patient", True, "Patient moved to attente", response_time)
                else:
                    self.log_test("Create Attente Patient", False, f"HTTP {response.status_code}", response_time)
                    return
            except Exception as e:
                response_time = time.time() - start_time
                self.log_test("Create Attente Patient", False, f"Exception: {str(e)}", response_time)
                return
        
        # Now simulate multiple API calls (like page refreshes) and check for consistency
        patient_info = attente_patient.get("patient", {})
        patient_name = f"{patient_info.get('prenom', '')} {patient_info.get('nom', '')}"
        
        print(f"Testing refresh consistency with patient: {patient_name}")
        
        # Make multiple API calls and compare timestamps/calculations
        refresh_results = []
        
        for i in range(3):
            print(f"  Refresh {i+1}...")
            start_time = time.time()
            
            try:
                today = datetime.now().strftime("%Y-%m-%d")
                response = self.session.get(f"{BACKEND_URL}/rdv/jour/{today}", timeout=10)
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    appointments_refresh = response.json()
                    
                    # Find our test patient
                    test_patient_refresh = None
                    for apt in appointments_refresh:
                        if apt.get("id") == attente_patient.get("id"):
                            test_patient_refresh = apt
                            break
                    
                    if test_patient_refresh:
                        timestamp = test_patient_refresh.get("heure_arrivee_attente", "NOT_SET")
                        duree_attente = test_patient_refresh.get("duree_attente", "NOT_SET")
                        
                        # Calculate time difference manually
                        if timestamp and timestamp != "NOT_SET":
                            parsed_timestamp = parser.parse(timestamp)
                            current_time = datetime.now()
                            
                            if parsed_timestamp.tzinfo is None and current_time.tzinfo is None:
                                diff_minutes = (current_time - parsed_timestamp).total_seconds() / 60
                            else:
                                # Handle timezone-aware comparison
                                if parsed_timestamp.tzinfo is None:
                                    parsed_timestamp = pytz.UTC.localize(parsed_timestamp)
                                if current_time.tzinfo is None:
                                    current_time = pytz.UTC.localize(current_time)
                                diff_minutes = (current_time - parsed_timestamp).total_seconds() / 60
                            
                            refresh_results.append({
                                "refresh": i+1,
                                "timestamp": timestamp,
                                "duree_attente": duree_attente,
                                "calculated_diff": diff_minutes,
                                "response_time": response_time
                            })
                            
                            print(f"    Timestamp: {timestamp}")
                            print(f"    Duree_attente: {duree_attente}")
                            print(f"    Calculated diff: {diff_minutes:.1f} minutes")
                        else:
                            refresh_results.append({
                                "refresh": i+1,
                                "timestamp": "NOT_SET",
                                "error": "No timestamp"
                            })
                    else:
                        refresh_results.append({
                            "refresh": i+1,
                            "error": "Patient not found"
                        })
                else:
                    refresh_results.append({
                        "refresh": i+1,
                        "error": f"HTTP {response.status_code}"
                    })
                    
            except Exception as e:
                refresh_results.append({
                    "refresh": i+1,
                    "error": f"Exception: {str(e)}"
                })
            
            # Wait a moment between refreshes
            time.sleep(1)
        
        # Analyze refresh results
        print(f"\n🔍 REFRESH ANALYSIS:")
        timestamps_consistent = True
        calculations_consistent = True
        
        if len(refresh_results) > 1:
            first_timestamp = refresh_results[0].get("timestamp")
            first_calc = refresh_results[0].get("calculated_diff")
            
            for result in refresh_results[1:]:
                if result.get("timestamp") != first_timestamp:
                    timestamps_consistent = False
                if abs(result.get("calculated_diff", 0) - (first_calc or 0)) > 1:  # More than 1 minute difference
                    calculations_consistent = False
        
        if timestamps_consistent and calculations_consistent:
            details = f"All {len(refresh_results)} refreshes consistent"
            self.log_test("Refresh Consistency", True, details, 0)
        else:
            details = f"Inconsistency detected - Timestamps: {timestamps_consistent}, Calculations: {calculations_consistent}"
            self.log_test("Refresh Inconsistency Bug", False, details, 0)
        
        # Check for 60-minute values
        for result in refresh_results:
            calc_diff = result.get("calculated_diff", 0)
            if abs(calc_diff - 60) < 5:  # Within 5 minutes of 60
                details = f"🚨 60-MINUTE BUG DETECTED in refresh {result['refresh']}: {calc_diff:.1f} minutes"
                self.log_test("60-Minute Bug in Refresh", False, details, 0)
    
    def test_scenario_3_backend_calculation_vs_frontend(self, appointments):
        """Test Scenario 3: Compare backend calculation vs expected frontend calculation"""
        print("\n🧮 SCENARIO 3: BACKEND VS FRONTEND CALCULATION COMPARISON")
        
        if not appointments:
            self.log_test("Scenario 3 - No Appointments", False, "No appointments available for testing", 0)
            return
        
        # Test with a patient in attente
        test_patient = appointments[0]
        rdv_id = test_patient.get("id")
        patient_info = test_patient.get("patient", {})
        patient_name = f"{patient_info.get('prenom', '')} {patient_info.get('nom', '')}"
        
        print(f"Testing calculation comparison with patient: {patient_name}")
        
        # Move patient to attente
        start_time = time.time()
        try:
            update_data = {"statut": "attente"}
            response = self.session.put(f"{BACKEND_URL}/rdv/{rdv_id}/statut", json=update_data, timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                backend_timestamp = data.get("heure_arrivee_attente", "NOT_SET")
                
                print(f"Backend set timestamp: {backend_timestamp}")
                
                # Wait a specific amount of time
                wait_seconds = 5
                print(f"Waiting {wait_seconds} seconds...")
                time.sleep(wait_seconds)
                
                # Move to en_cours to trigger calculation
                start_time = time.time()
                update_data = {"statut": "en_cours"}
                response = self.session.put(f"{BACKEND_URL}/rdv/{rdv_id}/statut", json=update_data, timeout=10)
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    backend_duree = data.get("duree_attente", "NOT_CALCULATED")
                    
                    # Calculate what frontend would calculate
                    if backend_timestamp and backend_timestamp != "NOT_SET":
                        parsed_timestamp = parser.parse(backend_timestamp)
                        current_time = datetime.now()
                        
                        # Frontend calculation (assuming no timezone issues)
                        if parsed_timestamp.tzinfo is None and current_time.tzinfo is None:
                            frontend_calc = (current_time - parsed_timestamp).total_seconds() / 60
                        else:
                            # Handle timezone-aware comparison
                            if parsed_timestamp.tzinfo is None:
                                parsed_timestamp = pytz.UTC.localize(parsed_timestamp)
                            if current_time.tzinfo is None:
                                current_time = pytz.UTC.localize(current_time)
                            frontend_calc = (current_time - parsed_timestamp).total_seconds() / 60
                        
                        frontend_calc_rounded = int(frontend_calc)
                        
                        print(f"Backend calculated: {backend_duree} minutes")
                        print(f"Frontend would calculate: {frontend_calc:.1f} minutes (rounded: {frontend_calc_rounded})")
                        
                        # Compare calculations
                        if backend_duree != "NOT_CALCULATED":
                            diff = abs(float(backend_duree) - frontend_calc_rounded)
                            if diff <= 1:  # Within 1 minute is acceptable
                                details = f"Backend: {backend_duree} min, Frontend: {frontend_calc_rounded} min (consistent)"
                                self.log_test("Backend-Frontend Calculation Consistency", True, details, response_time)
                            else:
                                details = f"🚨 CALCULATION MISMATCH: Backend: {backend_duree} min, Frontend: {frontend_calc_rounded} min (diff: {diff} min)"
                                self.log_test("Backend-Frontend Calculation Mismatch", False, details, response_time)
                        else:
                            details = "Backend did not calculate duree_attente"
                            self.log_test("Backend Calculation Missing", False, details, response_time)
                    else:
                        details = "No timestamp available for comparison"
                        self.log_test("No Timestamp for Comparison", False, details, response_time)
                else:
                    self.log_test("Move to En_Cours Failed", False, f"HTTP {response.status_code}", response_time)
            else:
                self.log_test("Move to Attente Failed", False, f"HTTP {response.status_code}", response_time)
                
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("Scenario 3 - Exception", False, f"Exception: {str(e)}", response_time)
    
    def run_comprehensive_test(self):
        """Run comprehensive bug reproduction test"""
        print("🚨 COMPREHENSIVE 60-MINUTE BUG REPRODUCTION TEST")
        print("=" * 80)
        print("Simulating user scenario: 'When I refresh page, compteur shows 60 min, while I left it at 1 min'")
        print("Testing multiple scenarios to reproduce the bug...")
        print("=" * 80)
        
        # Authenticate
        if not self.authenticate():
            print("❌ Authentication failed - cannot proceed")
            return
        
        # Get current appointments
        appointments = self.get_current_appointments()
        if not appointments:
            print("❌ No appointments found - cannot proceed")
            return
        
        # Test different scenarios
        self.test_scenario_1_timezone_mismatch(appointments)
        self.test_scenario_2_refresh_bug(appointments)
        self.test_scenario_3_backend_calculation_vs_frontend(appointments)
        
        # Summary
        self.print_test_summary()
    
    def print_test_summary(self):
        """Print test summary"""
        print("\n" + "=" * 80)
        print("🔍 COMPREHENSIVE TEST SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = len([t for t in self.test_results if t["success"]])
        failed_tests = total_tests - passed_tests
        
        print(f"Total tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        
        # Show critical findings
        bug_findings = [t for t in self.test_results if not t["success"] and ("BUG" in t["test"] or "60" in t["test"] or "MISMATCH" in t["test"])]
        
        if bug_findings:
            print(f"\n🚨 BUG FINDINGS:")
            for finding in bug_findings:
                print(f"  ❌ {finding['test']}: {finding['details']}")
        else:
            print(f"\n✅ NO 60-MINUTE BUG REPRODUCED")
            print("The bug may occur under different conditions or may have been fixed.")
        
        print(f"\nTotal test time: {time.time() - self.start_time:.2f} seconds")
        print("=" * 80)

if __name__ == "__main__":
    tester = ComprehensiveBugReproduction()
    tester.run_comprehensive_test()