#!/usr/bin/env python3
"""
CRITICAL 60-MINUTE WAITING TIME BUG INVESTIGATION
Testing the specific bug reported by user: "When I refresh page, compteur in salle d'attente shows 60 min, while I left it at 1 min"

This indicates a problem with real-time calculation on the frontend. The timestamp `heure_arrivee_attente` 
might have a format, timezone, or calculation issue.

SPECIFIC DEBUG SCENARIO:
1. Login with medecin/medecin123
2. Find a patient in "salle d'attente" (status "attente") 
3. Examine EXACTLY the format of their `heure_arrivee_attente`
4. Calculate manually the difference between now and that timestamp
5. Verify if the calculation gives ~60 min or the real difference

HYPOTHESES:
- heure_arrivee_attente could be in UTC
- Frontend calculates in local time
- Difference of 1 hour = 60 min bug

The objective is to identify EXACTLY why the frontend calculation gives 60 min instead of the real time difference.
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

class WaitingTimeBugInvestigator:
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
    
    def find_patient_in_attente(self):
        """Step 2: Find a patient in "salle d'attente" (status "attente")"""
        print("\n🏥 STEP 2: FIND PATIENT IN SALLE D'ATTENTE - Looking for patient with status 'attente'")
        
        today = datetime.now().strftime("%Y-%m-%d")
        start_time = time.time()
        
        try:
            response = self.session.get(f"{BACKEND_URL}/rdv/jour/{today}", timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                appointments = response.json()
                if isinstance(appointments, list):
                    # Find patients in "attente" status
                    attente_patients = [apt for apt in appointments if apt.get("statut") == "attente"]
                    
                    if attente_patients:
                        for patient in attente_patients:
                            patient_info = patient.get("patient", {})
                            patient_name = f"{patient_info.get('prenom', '')} {patient_info.get('nom', '')}"
                            heure_arrivee = patient.get("heure_arrivee_attente", "NOT_SET")
                            duree_attente = patient.get("duree_attente", "NOT_SET")
                            
                            details = f"Found patient '{patient_name}' in attente - heure_arrivee_attente: {heure_arrivee}, duree_attente: {duree_attente}"
                            self.log_test(f"Patient in Attente - {patient_name}", True, details, 0)
                        
                        # Select the first patient for detailed investigation
                        selected_patient = attente_patients[0]
                        self.log_test("Patient Selection for Investigation", True, f"Selected: {selected_patient.get('patient', {}).get('prenom', '')} {selected_patient.get('patient', {}).get('nom', '')}", response_time)
                        return selected_patient
                    else:
                        # No patients in attente, let's create one for testing
                        self.log_test("No Patients in Attente", True, "No patients found in attente status - will create test scenario", response_time)
                        
                        # Find any patient to move to attente
                        if appointments:
                            test_patient = appointments[0]
                            return self.move_patient_to_attente(test_patient)
                        else:
                            self.log_test("No Appointments Found", False, "No appointments found for today", response_time)
                            return None
                else:
                    self.log_test("Find Patient in Attente", False, "Response is not a list", response_time)
                    return None
            else:
                self.log_test("Find Patient in Attente", False, f"HTTP {response.status_code}: {response.text}", response_time)
                return None
                
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("Find Patient in Attente", False, f"Exception: {str(e)}", response_time)
            return None
    
    def move_patient_to_attente(self, patient):
        """Move a patient to attente status to create test scenario"""
        print("\n🔄 CREATING TEST SCENARIO: Moving patient to attente status")
        
        rdv_id = patient.get("id")
        patient_info = patient.get("patient", {})
        patient_name = f"{patient_info.get('prenom', '')} {patient_info.get('nom', '')}"
        
        start_time = time.time()
        try:
            update_data = {"statut": "attente"}
            response = self.session.put(f"{BACKEND_URL}/rdv/{rdv_id}/statut", json=update_data, timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                heure_arrivee = data.get("heure_arrivee_attente", "NOT_SET")
                details = f"Moved '{patient_name}' to attente - heure_arrivee_attente: {heure_arrivee}"
                self.log_test("Move Patient to Attente", True, details, response_time)
                
                # Update patient data with new status
                patient["statut"] = "attente"
                patient["heure_arrivee_attente"] = heure_arrivee
                return patient
            else:
                self.log_test("Move Patient to Attente", False, f"HTTP {response.status_code}: {response.text}", response_time)
                return None
                
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("Move Patient to Attente", False, f"Exception: {str(e)}", response_time)
            return None
    
    def examine_timestamp_format(self, patient):
        """Step 3: Examine EXACTLY the format of heure_arrivee_attente"""
        print("\n🔍 STEP 3: EXAMINE TIMESTAMP FORMAT - Analyzing heure_arrivee_attente format")
        
        patient_info = patient.get("patient", {})
        patient_name = f"{patient_info.get('prenom', '')} {patient_info.get('nom', '')}"
        heure_arrivee = patient.get("heure_arrivee_attente", "NOT_SET")
        
        print(f"\n📋 DETAILED TIMESTAMP ANALYSIS FOR: {patient_name}")
        print(f"Raw heure_arrivee_attente value: '{heure_arrivee}'")
        print(f"Type: {type(heure_arrivee)}")
        print(f"Length: {len(str(heure_arrivee))}")
        
        # Analyze timestamp format
        timestamp_analysis = {
            "raw_value": heure_arrivee,
            "type": str(type(heure_arrivee)),
            "length": len(str(heure_arrivee)),
            "format_detected": "UNKNOWN",
            "timezone_info": "NONE",
            "parseable": False,
            "parsed_datetime": None
        }
        
        if heure_arrivee and heure_arrivee != "NOT_SET":
            # Try to detect format
            if "T" in str(heure_arrivee) and ("Z" in str(heure_arrivee) or "+" in str(heure_arrivee) or "-" in str(heure_arrivee)[-6:]):
                timestamp_analysis["format_detected"] = "ISO_8601_WITH_TIMEZONE"
                timestamp_analysis["timezone_info"] = "PRESENT"
            elif "T" in str(heure_arrivee):
                timestamp_analysis["format_detected"] = "ISO_8601_NO_TIMEZONE"
                timestamp_analysis["timezone_info"] = "MISSING"
            elif ":" in str(heure_arrivee) and len(str(heure_arrivee)) <= 8:
                timestamp_analysis["format_detected"] = "TIME_ONLY_HH:MM"
                timestamp_analysis["timezone_info"] = "NOT_APPLICABLE"
            else:
                timestamp_analysis["format_detected"] = "UNKNOWN_FORMAT"
            
            # Try to parse the timestamp
            try:
                if timestamp_analysis["format_detected"] in ["ISO_8601_WITH_TIMEZONE", "ISO_8601_NO_TIMEZONE"]:
                    parsed_dt = parser.parse(str(heure_arrivee))
                    timestamp_analysis["parseable"] = True
                    timestamp_analysis["parsed_datetime"] = parsed_dt
                    
                    # Check timezone info
                    if parsed_dt.tzinfo:
                        timestamp_analysis["timezone_info"] = f"TIMEZONE: {parsed_dt.tzinfo}"
                    else:
                        timestamp_analysis["timezone_info"] = "NO_TIMEZONE_INFO"
                        
                elif timestamp_analysis["format_detected"] == "TIME_ONLY_HH:MM":
                    # For time-only format, assume today's date
                    today = datetime.now().strftime("%Y-%m-%d")
                    full_timestamp = f"{today} {heure_arrivee}"
                    parsed_dt = datetime.strptime(full_timestamp, "%Y-%m-%d %H:%M")
                    timestamp_analysis["parseable"] = True
                    timestamp_analysis["parsed_datetime"] = parsed_dt
                    
            except Exception as e:
                timestamp_analysis["parse_error"] = str(e)
        
        # Log detailed analysis
        details = f"Format: {timestamp_analysis['format_detected']}, Timezone: {timestamp_analysis['timezone_info']}, Parseable: {timestamp_analysis['parseable']}"
        self.log_test("Timestamp Format Analysis", True, details, 0)
        
        # Print detailed analysis
        print(f"\n🔍 TIMESTAMP ANALYSIS RESULTS:")
        for key, value in timestamp_analysis.items():
            print(f"  {key}: {value}")
        
        return timestamp_analysis
    
    def calculate_time_difference_manually(self, timestamp_analysis):
        """Step 4: Calculate manually the difference between now and that timestamp"""
        print("\n🧮 STEP 4: MANUAL TIME DIFFERENCE CALCULATION")
        
        if not timestamp_analysis["parseable"] or not timestamp_analysis["parsed_datetime"]:
            self.log_test("Manual Time Calculation", False, "Cannot calculate - timestamp not parseable", 0)
            return None
        
        parsed_datetime = timestamp_analysis["parsed_datetime"]
        current_time = datetime.now()
        
        # Handle timezone-aware vs naive datetime comparison
        if parsed_datetime.tzinfo:
            # If parsed datetime has timezone, convert current time to same timezone or UTC
            if parsed_datetime.tzinfo == pytz.UTC:
                current_time = datetime.now(pytz.UTC)
            else:
                # Convert to UTC for comparison
                current_time = datetime.now(pytz.UTC)
                if parsed_datetime.tzinfo != pytz.UTC:
                    parsed_datetime = parsed_datetime.astimezone(pytz.UTC)
        
        # Calculate time difference
        time_diff = current_time - parsed_datetime
        total_seconds = time_diff.total_seconds()
        total_minutes = total_seconds / 60
        total_hours = total_minutes / 60
        
        calculation_results = {
            "parsed_datetime": parsed_datetime,
            "current_time": current_time,
            "time_difference": time_diff,
            "total_seconds": total_seconds,
            "total_minutes": total_minutes,
            "total_hours": total_hours,
            "minutes_rounded": int(total_minutes),
            "is_60_minutes": abs(total_minutes - 60) < 5,  # Within 5 minutes of 60
            "is_1_hour_difference": abs(total_hours - 1) < 0.1  # Within 6 minutes of 1 hour
        }
        
        print(f"\n🧮 MANUAL CALCULATION RESULTS:")
        print(f"  Parsed timestamp: {parsed_datetime}")
        print(f"  Current time: {current_time}")
        print(f"  Time difference: {time_diff}")
        print(f"  Total seconds: {total_seconds:.1f}")
        print(f"  Total minutes: {total_minutes:.1f}")
        print(f"  Total hours: {total_hours:.2f}")
        print(f"  Minutes (rounded): {calculation_results['minutes_rounded']}")
        print(f"  Is ~60 minutes?: {calculation_results['is_60_minutes']}")
        print(f"  Is ~1 hour difference?: {calculation_results['is_1_hour_difference']}")
        
        # Check if this matches the 60-minute bug
        if calculation_results["is_60_minutes"]:
            details = f"🚨 BUG CONFIRMED: Time difference is ~60 minutes ({total_minutes:.1f} min) - This matches user's report!"
            self.log_test("60-Minute Bug Detection", False, details, 0)
        elif calculation_results["is_1_hour_difference"]:
            details = f"🚨 TIMEZONE BUG SUSPECTED: Time difference is ~1 hour ({total_hours:.2f} h) - Likely timezone issue!"
            self.log_test("1-Hour Timezone Bug Detection", False, details, 0)
        else:
            details = f"Real time difference: {total_minutes:.1f} minutes ({total_hours:.2f} hours)"
            self.log_test("Manual Time Calculation", True, details, 0)
        
        return calculation_results
    
    def verify_timezone_hypothesis(self, timestamp_analysis, calculation_results):
        """Step 5: Verify timezone hypothesis"""
        print("\n🌍 STEP 5: TIMEZONE HYPOTHESIS VERIFICATION")
        
        if not timestamp_analysis["parseable"]:
            self.log_test("Timezone Hypothesis", False, "Cannot verify - timestamp not parseable", 0)
            return
        
        parsed_datetime = timestamp_analysis["parsed_datetime"]
        
        # Test different timezone interpretations
        timezone_tests = []
        
        # Test 1: If timestamp is UTC but frontend treats as local
        if parsed_datetime.tzinfo is None:
            # Assume timestamp is UTC
            utc_datetime = parsed_datetime.replace(tzinfo=pytz.UTC)
            local_tz = pytz.timezone('Europe/Paris')  # Tunisia is UTC+1
            local_current = datetime.now(local_tz)
            
            utc_diff = (local_current.astimezone(pytz.UTC) - utc_datetime).total_seconds() / 60
            
            timezone_tests.append({
                "scenario": "Timestamp is UTC, Frontend calculates in local time",
                "utc_timestamp": utc_datetime,
                "local_current": local_current,
                "difference_minutes": utc_diff,
                "matches_60min_bug": abs(utc_diff - 60) < 5
            })
        
        # Test 2: If timestamp is local but frontend treats as UTC
        if parsed_datetime.tzinfo is None:
            # Assume timestamp is local time
            local_tz = pytz.timezone('Europe/Paris')
            local_datetime = local_tz.localize(parsed_datetime)
            utc_current = datetime.now(pytz.UTC)
            
            local_diff = (utc_current - local_datetime.astimezone(pytz.UTC)).total_seconds() / 60
            
            timezone_tests.append({
                "scenario": "Timestamp is local, Frontend calculates in UTC",
                "local_timestamp": local_datetime,
                "utc_current": utc_current,
                "difference_minutes": local_diff,
                "matches_60min_bug": abs(local_diff - 60) < 5
            })
        
        # Analyze results
        print(f"\n🌍 TIMEZONE HYPOTHESIS TESTING:")
        for i, test in enumerate(timezone_tests, 1):
            print(f"\n  Test {i}: {test['scenario']}")
            print(f"    Difference: {test['difference_minutes']:.1f} minutes")
            print(f"    Matches 60min bug: {test['matches_60min_bug']}")
            
            if test['matches_60min_bug']:
                details = f"🚨 TIMEZONE BUG CONFIRMED: {test['scenario']} - Difference: {test['difference_minutes']:.1f} min"
                self.log_test("Timezone Bug Confirmation", False, details, 0)
            else:
                details = f"Timezone test: {test['scenario']} - Difference: {test['difference_minutes']:.1f} min"
                self.log_test(f"Timezone Test {i}", True, details, 0)
    
    def investigate_server_timestamp(self):
        """Step 6: Check server timestamp to understand timezone"""
        print("\n🖥️ STEP 6: SERVER TIMESTAMP INVESTIGATION")
        
        start_time = time.time()
        try:
            # Get current server time from dashboard or any endpoint that returns timestamps
            response = self.session.get(f"{BACKEND_URL}/dashboard", timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                # Server responded - check response headers for server time
                server_date = response.headers.get('Date', 'NOT_PROVIDED')
                
                # Also check if we can get server time from any timestamp in response
                current_client_time = datetime.now()
                current_utc_time = datetime.now(pytz.UTC)
                
                details = f"Server Date header: {server_date}, Client time: {current_client_time}, UTC time: {current_utc_time}"
                self.log_test("Server Timestamp Investigation", True, details, response_time)
                
                print(f"\n🖥️ SERVER TIME ANALYSIS:")
                print(f"  Server Date header: {server_date}")
                print(f"  Client local time: {current_client_time}")
                print(f"  Client UTC time: {current_utc_time}")
                
                # Try to parse server date
                if server_date != 'NOT_PROVIDED':
                    try:
                        server_datetime = parser.parse(server_date)
                        time_diff = (current_utc_time - server_datetime).total_seconds() / 60
                        print(f"  Server-Client time difference: {time_diff:.1f} minutes")
                        
                        if abs(time_diff - 60) < 5:
                            details = f"🚨 SERVER-CLIENT TIMEZONE MISMATCH: {time_diff:.1f} minutes difference"
                            self.log_test("Server-Client Timezone Mismatch", False, details, 0)
                    except Exception as e:
                        print(f"  Could not parse server date: {e}")
            else:
                self.log_test("Server Timestamp Investigation", False, f"HTTP {response.status_code}: {response.text}", response_time)
                
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("Server Timestamp Investigation", False, f"Exception: {str(e)}", response_time)
    
    def run_investigation(self):
        """Run the complete 60-minute bug investigation"""
        print("🚨 CRITICAL 60-MINUTE WAITING TIME BUG INVESTIGATION")
        print("=" * 80)
        print("User reports: 'When I refresh page, compteur in salle d'attente shows 60 min, while I left it at 1 min'")
        print("Investigating timestamp format, timezone, and calculation issues...")
        print("=" * 80)
        
        # Step 1: Authenticate
        if not self.authenticate():
            print("❌ Authentication failed - cannot proceed with investigation")
            return
        
        # Step 2: Find patient in attente
        patient = self.find_patient_in_attente()
        if not patient:
            print("❌ No patient found in attente - cannot proceed with investigation")
            return
        
        # Step 3: Examine timestamp format
        timestamp_analysis = self.examine_timestamp_format(patient)
        
        # Step 4: Calculate time difference manually
        calculation_results = self.calculate_time_difference_manually(timestamp_analysis)
        
        # Step 5: Verify timezone hypothesis
        if calculation_results:
            self.verify_timezone_hypothesis(timestamp_analysis, calculation_results)
        
        # Step 6: Investigate server timestamp
        self.investigate_server_timestamp()
        
        # Summary
        self.print_investigation_summary()
    
    def print_investigation_summary(self):
        """Print investigation summary"""
        print("\n" + "=" * 80)
        print("🔍 INVESTIGATION SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = len([t for t in self.test_results if t["success"]])
        failed_tests = total_tests - passed_tests
        
        print(f"Total tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        
        # Show critical findings
        critical_findings = [t for t in self.test_results if not t["success"] and ("BUG" in t["test"] or "TIMEZONE" in t["test"])]
        
        if critical_findings:
            print(f"\n🚨 CRITICAL FINDINGS:")
            for finding in critical_findings:
                print(f"  ❌ {finding['test']}: {finding['details']}")
        
        print(f"\nTotal investigation time: {time.time() - self.start_time:.2f} seconds")
        print("=" * 80)

if __name__ == "__main__":
    investigator = WaitingTimeBugInvestigator()
    investigator.run_investigation()