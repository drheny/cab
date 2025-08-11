#!/usr/bin/env python3
"""
SPECIFIC 60-MINUTE BUG INVESTIGATION - TIMESTAMP FORMAT ANALYSIS
Based on the frontend code analysis, the bug is likely in the timestamp format/timezone handling.

Frontend calculation (lines 2313-2330 in Calendar.js):
```javascript
const heureArrivee = new Date(appointment.heure_arrivee_attente);
const maintenant = new Date();
const diffMs = maintenant - heureArrivee;
const diffMinutes = Math.floor(diffMs / 60000);
```

Backend timestamp creation (line 1779 in server.py):
```python
update_data["heure_arrivee_attente"] = datetime.now().isoformat()
```

HYPOTHESIS: The issue is that:
1. Backend stores timestamp as `datetime.now().isoformat()` which creates a naive timestamp
2. Frontend creates `new Date()` which is timezone-aware
3. The difference calculation is affected by timezone interpretation

This test will:
1. Examine the exact timestamp format stored by backend
2. Test how JavaScript Date() interprets this timestamp
3. Reproduce the 60-minute bug by testing timezone scenarios
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
BACKEND_URL = "https://e095a16b-4f79-4d50-8576-cad954291484.preview.emergentagent.com/api"
TEST_CREDENTIALS = {
    "username": "medecin",
    "password": "medecin123"
}

class TimestampBugInvestigator:
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
    
    def analyze_backend_timestamp_format(self):
        """Analyze the exact format of timestamps created by backend"""
        print("\n🔍 BACKEND TIMESTAMP FORMAT ANALYSIS")
        
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Get current appointments
        start_time = time.time()
        try:
            response = self.session.get(f"{BACKEND_URL}/rdv/jour/{today}", timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                appointments = response.json()
                if appointments:
                    # Find or create a patient in attente
                    test_patient = appointments[0]
                    rdv_id = test_patient.get("id")
                    patient_info = test_patient.get("patient", {})
                    patient_name = f"{patient_info.get('prenom', '')} {patient_info.get('nom', '')}"
                    
                    print(f"Testing timestamp format with patient: {patient_name}")
                    
                    # Move patient to attente to trigger timestamp creation
                    start_time = time.time()
                    update_data = {"statut": "attente"}
                    response = self.session.put(f"{BACKEND_URL}/rdv/{rdv_id}/statut", json=update_data, timeout=10)
                    response_time = time.time() - start_time
                    
                    if response.status_code == 200:
                        data = response.json()
                        backend_timestamp = data.get("heure_arrivee_attente", "NOT_SET")
                        
                        print(f"\n📋 BACKEND TIMESTAMP ANALYSIS:")
                        print(f"  Raw timestamp: '{backend_timestamp}'")
                        print(f"  Type: {type(backend_timestamp)}")
                        print(f"  Length: {len(str(backend_timestamp))}")
                        
                        # Analyze timestamp components
                        timestamp_analysis = self.analyze_timestamp_components(backend_timestamp)
                        
                        # Test JavaScript Date interpretation
                        js_interpretation = self.simulate_javascript_date_parsing(backend_timestamp)
                        
                        # Compare with current time
                        time_comparison = self.compare_with_current_time(backend_timestamp)
                        
                        details = f"Backend timestamp: {backend_timestamp}, Format: {timestamp_analysis.get('format', 'UNKNOWN')}"
                        self.log_test("Backend Timestamp Format Analysis", True, details, response_time)
                        
                        return {
                            "timestamp": backend_timestamp,
                            "analysis": timestamp_analysis,
                            "js_interpretation": js_interpretation,
                            "time_comparison": time_comparison
                        }
                    else:
                        self.log_test("Backend Timestamp Creation", False, f"HTTP {response.status_code}", response_time)
                        return None
                else:
                    self.log_test("Backend Timestamp Analysis", False, "No appointments found", response_time)
                    return None
            else:
                self.log_test("Backend Timestamp Analysis", False, f"HTTP {response.status_code}: {response.text}", response_time)
                return None
                
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("Backend Timestamp Analysis", False, f"Exception: {str(e)}", response_time)
            return None
    
    def analyze_timestamp_components(self, timestamp_str):
        """Analyze the components of the timestamp string"""
        if not timestamp_str or timestamp_str == "NOT_SET":
            return {"format": "INVALID", "components": {}}
        
        analysis = {
            "format": "UNKNOWN",
            "has_date": False,
            "has_time": False,
            "has_timezone": False,
            "has_microseconds": False,
            "components": {}
        }
        
        try:
            # Check format patterns
            if "T" in timestamp_str:
                analysis["format"] = "ISO_8601"
                analysis["has_date"] = True
                analysis["has_time"] = True
                
                if "Z" in timestamp_str:
                    analysis["has_timezone"] = True
                    analysis["timezone_type"] = "UTC_Z"
                elif "+" in timestamp_str or timestamp_str.count("-") > 2:
                    analysis["has_timezone"] = True
                    analysis["timezone_type"] = "OFFSET"
                else:
                    analysis["has_timezone"] = False
                    analysis["timezone_type"] = "NAIVE"
                
                if "." in timestamp_str:
                    analysis["has_microseconds"] = True
                    # Count decimal places
                    decimal_part = timestamp_str.split(".")[-1]
                    if analysis["has_timezone"]:
                        # Remove timezone part
                        decimal_part = decimal_part.split("Z")[0].split("+")[0].split("-")[0]
                    analysis["microsecond_precision"] = len(decimal_part)
            
            # Try to parse with dateutil
            parsed_dt = parser.parse(timestamp_str)
            analysis["parseable"] = True
            analysis["parsed_datetime"] = parsed_dt
            analysis["components"] = {
                "year": parsed_dt.year,
                "month": parsed_dt.month,
                "day": parsed_dt.day,
                "hour": parsed_dt.hour,
                "minute": parsed_dt.minute,
                "second": parsed_dt.second,
                "microsecond": parsed_dt.microsecond,
                "timezone": str(parsed_dt.tzinfo) if parsed_dt.tzinfo else "None"
            }
            
        except Exception as e:
            analysis["parseable"] = False
            analysis["parse_error"] = str(e)
        
        return analysis
    
    def simulate_javascript_date_parsing(self, timestamp_str):
        """Simulate how JavaScript Date() would parse this timestamp"""
        if not timestamp_str or timestamp_str == "NOT_SET":
            return {"error": "Invalid timestamp"}
        
        simulation = {
            "input": timestamp_str,
            "interpretation": "UNKNOWN"
        }
        
        try:
            # Parse the timestamp
            parsed_dt = parser.parse(timestamp_str)
            
            # JavaScript Date behavior simulation
            if parsed_dt.tzinfo is None:
                # JavaScript treats naive ISO strings as local time
                simulation["interpretation"] = "LOCAL_TIME"
                simulation["js_behavior"] = "JavaScript will interpret this as local time"
                
                # Simulate what JavaScript would do
                # If the timestamp is "2025-08-11T16:16:28.395641"
                # JavaScript creates a Date object in local timezone
                local_tz = pytz.timezone('Europe/Paris')  # Assuming Tunisia timezone
                js_interpreted_time = local_tz.localize(parsed_dt)
                simulation["js_interpreted_datetime"] = js_interpreted_time
                
            else:
                # JavaScript handles timezone-aware timestamps correctly
                simulation["interpretation"] = "TIMEZONE_AWARE"
                simulation["js_behavior"] = "JavaScript will interpret this with timezone info"
                simulation["js_interpreted_datetime"] = parsed_dt
            
            # Calculate what the difference would be
            current_utc = datetime.now(pytz.UTC)
            current_local = datetime.now(pytz.timezone('Europe/Paris'))
            
            if simulation["interpretation"] == "LOCAL_TIME":
                # Compare local to local
                js_diff_minutes = (current_local - simulation["js_interpreted_datetime"]).total_seconds() / 60
            else:
                # Compare UTC to UTC
                js_diff_minutes = (current_utc - simulation["js_interpreted_datetime"]).total_seconds() / 60
            
            simulation["js_calculated_diff_minutes"] = js_diff_minutes
            simulation["is_60_minute_bug"] = abs(js_diff_minutes - 60) < 5
            
        except Exception as e:
            simulation["error"] = str(e)
        
        return simulation
    
    def compare_with_current_time(self, timestamp_str):
        """Compare timestamp with current time in different timezone scenarios"""
        if not timestamp_str or timestamp_str == "NOT_SET":
            return {"error": "Invalid timestamp"}
        
        comparison = {
            "timestamp": timestamp_str,
            "scenarios": []
        }
        
        try:
            parsed_dt = parser.parse(timestamp_str)
            current_time = datetime.now()
            current_utc = datetime.now(pytz.UTC)
            current_local = datetime.now(pytz.timezone('Europe/Paris'))
            
            # Scenario 1: Both naive (what Python would do)
            if parsed_dt.tzinfo is None:
                diff_naive = (current_time - parsed_dt).total_seconds() / 60
                comparison["scenarios"].append({
                    "name": "Both Naive (Python default)",
                    "diff_minutes": diff_naive,
                    "is_60_min_bug": abs(diff_naive - 60) < 5
                })
            
            # Scenario 2: Timestamp as UTC, current as local (potential bug source)
            if parsed_dt.tzinfo is None:
                timestamp_as_utc = pytz.UTC.localize(parsed_dt)
                diff_utc_local = (current_local - timestamp_as_utc).total_seconds() / 60
                comparison["scenarios"].append({
                    "name": "Timestamp as UTC, Current as Local",
                    "diff_minutes": diff_utc_local,
                    "is_60_min_bug": abs(diff_utc_local - 60) < 5
                })
            
            # Scenario 3: Timestamp as local, current as UTC (another potential bug)
            if parsed_dt.tzinfo is None:
                timestamp_as_local = pytz.timezone('Europe/Paris').localize(parsed_dt)
                diff_local_utc = (current_utc - timestamp_as_local).total_seconds() / 60
                comparison["scenarios"].append({
                    "name": "Timestamp as Local, Current as UTC",
                    "diff_minutes": diff_local_utc,
                    "is_60_min_bug": abs(diff_local_utc - 60) < 5
                })
            
            # Scenario 4: JavaScript interpretation (timestamp as local, current as local)
            if parsed_dt.tzinfo is None:
                timestamp_as_local_js = pytz.timezone('Europe/Paris').localize(parsed_dt)
                diff_js = (current_local - timestamp_as_local_js).total_seconds() / 60
                comparison["scenarios"].append({
                    "name": "JavaScript Interpretation (both local)",
                    "diff_minutes": diff_js,
                    "is_60_min_bug": abs(diff_js - 60) < 5
                })
            
        except Exception as e:
            comparison["error"] = str(e)
        
        return comparison
    
    def test_60_minute_bug_reproduction(self, timestamp_data):
        """Test specific scenarios that could cause the 60-minute bug"""
        print("\n🚨 60-MINUTE BUG REPRODUCTION TEST")
        
        if not timestamp_data:
            self.log_test("60-Minute Bug Reproduction", False, "No timestamp data available", 0)
            return
        
        timestamp_str = timestamp_data["timestamp"]
        js_interpretation = timestamp_data["js_interpretation"]
        time_comparison = timestamp_data["time_comparison"]
        
        print(f"Testing with timestamp: {timestamp_str}")
        
        # Check JavaScript interpretation for 60-minute bug
        if js_interpretation.get("is_60_minute_bug", False):
            details = f"🚨 60-MINUTE BUG FOUND: JavaScript interpretation gives {js_interpretation['js_calculated_diff_minutes']:.1f} minutes"
            self.log_test("JavaScript 60-Minute Bug", False, details, 0)
        else:
            details = f"JavaScript interpretation: {js_interpretation.get('js_calculated_diff_minutes', 0):.1f} minutes"
            self.log_test("JavaScript Interpretation", True, details, 0)
        
        # Check timezone scenarios
        bug_scenarios = []
        for scenario in time_comparison.get("scenarios", []):
            if scenario.get("is_60_min_bug", False):
                bug_scenarios.append(scenario)
                details = f"🚨 60-MINUTE BUG in {scenario['name']}: {scenario['diff_minutes']:.1f} minutes"
                self.log_test(f"60-Min Bug - {scenario['name']}", False, details, 0)
        
        if bug_scenarios:
            print(f"\n🚨 FOUND {len(bug_scenarios)} SCENARIOS THAT CAUSE 60-MINUTE BUG:")
            for scenario in bug_scenarios:
                print(f"  - {scenario['name']}: {scenario['diff_minutes']:.1f} minutes")
        else:
            print(f"\n✅ NO 60-MINUTE BUG SCENARIOS FOUND")
            print("The bug may occur under different conditions or may have been fixed.")
    
    def run_investigation(self):
        """Run the complete timestamp bug investigation"""
        print("🚨 SPECIFIC 60-MINUTE BUG INVESTIGATION - TIMESTAMP FORMAT ANALYSIS")
        print("=" * 80)
        print("Investigating timestamp format and timezone handling that causes 60-minute bug")
        print("=" * 80)
        
        # Authenticate
        if not self.authenticate():
            print("❌ Authentication failed - cannot proceed")
            return
        
        # Analyze backend timestamp format
        timestamp_data = self.analyze_backend_timestamp_format()
        
        if timestamp_data:
            # Print detailed analysis
            print(f"\n📊 DETAILED TIMESTAMP ANALYSIS:")
            print(f"  Backend timestamp: {timestamp_data['timestamp']}")
            print(f"  Format: {timestamp_data['analysis'].get('format', 'UNKNOWN')}")
            print(f"  Has timezone: {timestamp_data['analysis'].get('has_timezone', False)}")
            print(f"  JavaScript interpretation: {timestamp_data['js_interpretation'].get('interpretation', 'UNKNOWN')}")
            
            # Test for 60-minute bug
            self.test_60_minute_bug_reproduction(timestamp_data)
        
        # Summary
        self.print_investigation_summary()
    
    def print_investigation_summary(self):
        """Print investigation summary"""
        print("\n" + "=" * 80)
        print("🔍 TIMESTAMP BUG INVESTIGATION SUMMARY")
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
            print(f"\n🚨 60-MINUTE BUG FINDINGS:")
            for finding in bug_findings:
                print(f"  ❌ {finding['test']}: {finding['details']}")
            
            print(f"\n💡 RECOMMENDED FIXES:")
            print("  1. Backend: Store timestamps with explicit timezone (UTC)")
            print("  2. Frontend: Ensure consistent timezone handling in Date() parsing")
            print("  3. Add timezone conversion logic to handle naive timestamps")
        else:
            print(f"\n✅ NO 60-MINUTE BUG DETECTED")
            print("Current timestamp handling appears to be working correctly.")
        
        print(f"\nTotal investigation time: {time.time() - self.start_time:.2f} seconds")
        print("=" * 80)

if __name__ == "__main__":
    investigator = TimestampBugInvestigator()
    investigator.run_investigation()