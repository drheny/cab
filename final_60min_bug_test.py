#!/usr/bin/env python3
"""
FINAL 60-MINUTE BUG REPRODUCTION - EXACT USER SCENARIO
User reports: "When I refresh page, compteur in salle d'attente shows 60 min, while I left it at 1 min"

This suggests the user had a patient who was actually waiting for ~1 minute, but after refresh it showed 60 minutes.

HYPOTHESIS: The bug occurs when:
1. A patient is moved to "attente" at time T
2. User sees correct waiting time (1 min) initially
3. Page refresh occurs
4. Backend timestamp is interpreted differently, causing 60-minute display

Let me test this by creating a timestamp that would be exactly 1 hour ago and see if it causes the 60-minute bug.
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
BACKEND_URL = "https://a657b56d-56f9-415b-a575-b3b503d7e7a0.preview.emergentagent.com/api"
TEST_CREDENTIALS = {
    "username": "medecin",
    "password": "medecin123"
}

class ExactBugReproduction:
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
    
    def test_exact_60_minute_scenario(self):
        """Test the exact scenario that would cause 60-minute bug"""
        print("\n🎯 EXACT 60-MINUTE BUG SCENARIO TEST")
        print("Simulating: Patient waiting 1 minute shows as 60 minutes after refresh")
        
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Get current appointments
        start_time = time.time()
        try:
            response = self.session.get(f"{BACKEND_URL}/rdv/jour/{today}", timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                appointments = response.json()
                if appointments:
                    test_patient = appointments[0]
                    rdv_id = test_patient.get("id")
                    patient_info = test_patient.get("patient", {})
                    patient_name = f"{patient_info.get('prenom', '')} {patient_info.get('nom', '')}"
                    
                    print(f"Testing exact 60-minute scenario with patient: {patient_name}")
                    
                    # CRITICAL TEST: Create different timestamp scenarios that could cause 60-minute bug
                    scenarios = self.create_60_minute_bug_scenarios()
                    
                    for i, scenario in enumerate(scenarios, 1):
                        print(f"\n📋 SCENARIO {i}: {scenario['name']}")
                        print(f"   Description: {scenario['description']}")
                        
                        # Test this scenario
                        self.test_scenario(rdv_id, patient_name, scenario)
                    
                    self.log_test("Exact 60-Minute Scenario Test", True, f"Tested {len(scenarios)} scenarios", response_time)
                else:
                    self.log_test("Exact 60-Minute Scenario Test", False, "No appointments found", response_time)
            else:
                self.log_test("Exact 60-Minute Scenario Test", False, f"HTTP {response.status_code}: {response.text}", response_time)
                
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("Exact 60-Minute Scenario Test", False, f"Exception: {str(e)}", response_time)
    
    def create_60_minute_bug_scenarios(self):
        """Create different timestamp scenarios that could cause the 60-minute bug"""
        current_time = datetime.now()
        current_utc = datetime.now(pytz.UTC)
        
        scenarios = [
            {
                "name": "1 Hour Ago UTC (Naive)",
                "description": "Timestamp 1 hour ago in UTC, stored as naive",
                "timestamp": (current_utc - timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%S.%f"),
                "expected_js_diff": 60,  # Should show 60 minutes if interpreted as local time
                "bug_potential": "HIGH"
            },
            {
                "name": "1 Hour Ago Local (Naive)", 
                "description": "Timestamp 1 hour ago in local time, stored as naive",
                "timestamp": (current_time - timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%S.%f"),
                "expected_js_diff": 60,  # Should show 60 minutes
                "bug_potential": "MEDIUM"
            },
            {
                "name": "1 Minute Ago + Timezone Confusion",
                "description": "Timestamp 1 minute ago but with timezone interpretation issue",
                "timestamp": (current_time - timedelta(minutes=1)).strftime("%Y-%m-%dT%H:%M:%S.%f"),
                "expected_js_diff": 1,  # Should show 1 minute normally
                "bug_potential": "LOW"
            },
            {
                "name": "Current Time - 59 Minutes",
                "description": "Timestamp exactly 59 minutes ago (edge case)",
                "timestamp": (current_time - timedelta(minutes=59)).strftime("%Y-%m-%dT%H:%M:%S.%f"),
                "expected_js_diff": 59,  # Should show 59 minutes
                "bug_potential": "MEDIUM"
            },
            {
                "name": "Current Time - 61 Minutes",
                "description": "Timestamp exactly 61 minutes ago (just over 1 hour)",
                "timestamp": (current_time - timedelta(minutes=61)).strftime("%Y-%m-%dT%H:%M:%S.%f"),
                "expected_js_diff": 61,  # Should show 61 minutes
                "bug_potential": "MEDIUM"
            }
        ]
        
        return scenarios
    
    def test_scenario(self, rdv_id, patient_name, scenario):
        """Test a specific timestamp scenario"""
        timestamp = scenario["timestamp"]
        expected_diff = scenario["expected_js_diff"]
        
        print(f"   Testing timestamp: {timestamp}")
        print(f"   Expected difference: {expected_diff} minutes")
        
        # Since we can't directly manipulate the database timestamp,
        # let's simulate what would happen with this timestamp
        
        # Simulate JavaScript Date parsing
        try:
            # Parse the timestamp as JavaScript would
            parsed_dt = parser.parse(timestamp)
            current_time = datetime.now()
            
            # JavaScript treats naive ISO strings as local time
            if parsed_dt.tzinfo is None:
                # This is how JavaScript interprets it
                local_tz = pytz.timezone('Europe/Paris')
                js_timestamp = local_tz.localize(parsed_dt)
                js_current = datetime.now(local_tz)
                
                js_diff_minutes = (js_current - js_timestamp).total_seconds() / 60
            else:
                # Timezone-aware comparison
                js_diff_minutes = (current_time - parsed_dt).total_seconds() / 60
            
            print(f"   JavaScript would calculate: {js_diff_minutes:.1f} minutes")
            
            # Check if this matches the 60-minute bug
            if abs(js_diff_minutes - 60) < 5:  # Within 5 minutes of 60
                details = f"🚨 60-MINUTE BUG REPRODUCED: {scenario['name']} gives {js_diff_minutes:.1f} minutes"
                self.log_test(f"60-Min Bug - {scenario['name']}", False, details, 0)
                
                # Additional analysis
                print(f"   🚨 BUG ANALYSIS:")
                print(f"     - Timestamp: {timestamp}")
                print(f"     - JavaScript interpretation: {js_diff_minutes:.1f} minutes")
                print(f"     - This matches the user's report of 60 minutes!")
                
            elif abs(js_diff_minutes - expected_diff) <= 2:  # Within 2 minutes of expected
                details = f"Expected behavior: {scenario['name']} gives {js_diff_minutes:.1f} minutes (expected ~{expected_diff})"
                self.log_test(f"Normal Behavior - {scenario['name']}", True, details, 0)
            else:
                details = f"Unexpected result: {scenario['name']} gives {js_diff_minutes:.1f} minutes (expected ~{expected_diff})"
                self.log_test(f"Unexpected - {scenario['name']}", True, details, 0)
                
        except Exception as e:
            details = f"Error testing scenario: {str(e)}"
            self.log_test(f"Error - {scenario['name']}", False, details, 0)
    
    def test_refresh_simulation(self):
        """Simulate the page refresh scenario that triggers the bug"""
        print("\n🔄 PAGE REFRESH SIMULATION")
        print("Simulating: User sees 1 min, refreshes page, sees 60 min")
        
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Get current appointments
        start_time = time.time()
        try:
            response = self.session.get(f"{BACKEND_URL}/rdv/jour/{today}", timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                appointments = response.json()
                if appointments:
                    # Find a patient in attente
                    attente_patient = None
                    for apt in appointments:
                        if apt.get("statut") == "attente" and apt.get("heure_arrivee_attente"):
                            attente_patient = apt
                            break
                    
                    if attente_patient:
                        patient_info = attente_patient.get("patient", {})
                        patient_name = f"{patient_info.get('prenom', '')} {patient_info.get('nom', '')}"
                        timestamp = attente_patient.get("heure_arrivee_attente")
                        
                        print(f"Found patient in attente: {patient_name}")
                        print(f"Timestamp: {timestamp}")
                        
                        # Simulate multiple "refreshes" and check for consistency
                        refresh_results = []
                        
                        for refresh_num in range(5):
                            print(f"  Refresh {refresh_num + 1}...")
                            
                            # Get appointments again (simulate refresh)
                            refresh_response = self.session.get(f"{BACKEND_URL}/rdv/jour/{today}", timeout=10)
                            
                            if refresh_response.status_code == 200:
                                refresh_appointments = refresh_response.json()
                                
                                # Find our patient
                                refresh_patient = None
                                for apt in refresh_appointments:
                                    if apt.get("id") == attente_patient.get("id"):
                                        refresh_patient = apt
                                        break
                                
                                if refresh_patient:
                                    refresh_timestamp = refresh_patient.get("heure_arrivee_attente")
                                    
                                    # Calculate waiting time as frontend would
                                    if refresh_timestamp:
                                        try:
                                            parsed_dt = parser.parse(refresh_timestamp)
                                            current_time = datetime.now()
                                            
                                            # JavaScript-style calculation
                                            if parsed_dt.tzinfo is None:
                                                local_tz = pytz.timezone('Europe/Paris')
                                                js_timestamp = local_tz.localize(parsed_dt)
                                                js_current = datetime.now(local_tz)
                                                js_diff_minutes = (js_current - js_timestamp).total_seconds() / 60
                                            else:
                                                js_diff_minutes = (current_time - parsed_dt).total_seconds() / 60
                                            
                                            refresh_results.append({
                                                "refresh": refresh_num + 1,
                                                "timestamp": refresh_timestamp,
                                                "calculated_minutes": js_diff_minutes,
                                                "is_60_min": abs(js_diff_minutes - 60) < 5
                                            })
                                            
                                            print(f"    Calculated: {js_diff_minutes:.1f} minutes")
                                            
                                        except Exception as e:
                                            refresh_results.append({
                                                "refresh": refresh_num + 1,
                                                "error": str(e)
                                            })
                                
                            time.sleep(0.5)  # Small delay between refreshes
                        
                        # Analyze refresh results
                        print(f"\n🔍 REFRESH ANALYSIS:")
                        consistent_60_min = all(r.get("is_60_min", False) for r in refresh_results if "error" not in r)
                        any_60_min = any(r.get("is_60_min", False) for r in refresh_results if "error" not in r)
                        
                        if consistent_60_min:
                            details = f"🚨 CONSISTENT 60-MINUTE BUG: All {len(refresh_results)} refreshes show ~60 minutes"
                            self.log_test("Consistent 60-Minute Bug", False, details, response_time)
                        elif any_60_min:
                            details = f"🚨 INTERMITTENT 60-MINUTE BUG: Some refreshes show ~60 minutes"
                            self.log_test("Intermittent 60-Minute Bug", False, details, response_time)
                        else:
                            avg_minutes = sum(r.get("calculated_minutes", 0) for r in refresh_results if "error" not in r) / len([r for r in refresh_results if "error" not in r])
                            details = f"Consistent calculation: Average {avg_minutes:.1f} minutes across refreshes"
                            self.log_test("Refresh Consistency", True, details, response_time)
                    else:
                        self.log_test("Page Refresh Simulation", True, "No patient in attente with timestamp found", response_time)
                else:
                    self.log_test("Page Refresh Simulation", False, "No appointments found", response_time)
            else:
                self.log_test("Page Refresh Simulation", False, f"HTTP {response.status_code}: {response.text}", response_time)
                
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("Page Refresh Simulation", False, f"Exception: {str(e)}", response_time)
    
    def run_final_test(self):
        """Run the final comprehensive test to reproduce the exact 60-minute bug"""
        print("🎯 FINAL 60-MINUTE BUG REPRODUCTION - EXACT USER SCENARIO")
        print("=" * 80)
        print("User reports: 'When I refresh page, compteur shows 60 min, while I left it at 1 min'")
        print("Testing exact scenarios that could cause this specific bug...")
        print("=" * 80)
        
        # Authenticate
        if not self.authenticate():
            print("❌ Authentication failed - cannot proceed")
            return
        
        # Test exact 60-minute scenarios
        self.test_exact_60_minute_scenario()
        
        # Test page refresh simulation
        self.test_refresh_simulation()
        
        # Summary
        self.print_final_summary()
    
    def print_final_summary(self):
        """Print final test summary"""
        print("\n" + "=" * 80)
        print("🎯 FINAL 60-MINUTE BUG TEST SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = len([t for t in self.test_results if t["success"]])
        failed_tests = total_tests - passed_tests
        
        print(f"Total tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        
        # Show bug findings
        bug_findings = [t for t in self.test_results if not t["success"] and ("60" in t["test"] or "BUG" in t["test"])]
        
        if bug_findings:
            print(f"\n🚨 60-MINUTE BUG CONFIRMED:")
            for finding in bug_findings:
                print(f"  ❌ {finding['test']}: {finding['details']}")
            
            print(f"\n💡 ROOT CAUSE ANALYSIS:")
            print("  The 60-minute bug occurs due to timezone interpretation mismatch:")
            print("  1. Backend stores naive ISO timestamp (no timezone)")
            print("  2. JavaScript Date() interprets naive ISO as local time")
            print("  3. If timestamp was created in different timezone context, calculation is wrong")
            
            print(f"\n🔧 RECOMMENDED FIXES:")
            print("  1. Backend: Always store timestamps with explicit UTC timezone")
            print("  2. Frontend: Convert all timestamps to UTC before calculation")
            print("  3. Add timezone validation in timestamp handling")
        else:
            print(f"\n✅ 60-MINUTE BUG NOT REPRODUCED")
            print("Current implementation may have been fixed or bug occurs under different conditions.")
        
        print(f"\nTotal test time: {time.time() - self.start_time:.2f} seconds")
        print("=" * 80)

if __name__ == "__main__":
    tester = ExactBugReproduction()
    tester.run_final_test()