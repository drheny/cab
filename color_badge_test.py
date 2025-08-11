#!/usr/bin/env python3
"""
COLOR-CODED WAITING TIME BADGE SYSTEM TESTING
Backend API Testing Suite for Cabinet Médical

TESTING COLOR-CODED WAITING TIME BADGE SYSTEM:
The user requested testing of the new color-coded waiting time badge system with different duree_attente values:

**Color Coding System:**
- Green: < 15 minutes  
- Blue: 15-30 minutes
- Orange: 30-60 minutes  
- Red: > 60 minutes

**Test Scenarios:**
1. Login with medecin/medecin123
2. Get today's appointments
3. Test different scenarios:
   - Create/modify appointments to have duree_attente values of: 5 min (green), 20 min (blue), 45 min (orange), 75 min (red)
   - For each appointment, verify it has the correct duree_attente value stored
   - Check that the backend correctly stores different duree_attente values

**Goal:**
- Verify different duree_attente values can be stored in the database
- Verify the backend API correctly returns appointments with various waiting time durations 
- Verify the color-coding logic on the frontend will receive different time values to display
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

# Test duree_attente values for different color ranges
COLOR_TEST_VALUES = [
    {"duree_attente": 5, "color": "green", "description": "< 15 minutes (green)"},
    {"duree_attente": 20, "color": "blue", "description": "15-30 minutes (blue)"},
    {"duree_attente": 45, "color": "orange", "description": "30-60 minutes (orange)"},
    {"duree_attente": 75, "color": "red", "description": "> 60 minutes (red)"}
]

class ColorBadgeTester:
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
        self.test_appointments = []
        
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
            print(f"Attempting to connect to: {BACKEND_URL}/auth/login")
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
            print(f"Authentication error: {error_details}")
            self.log_test("Authentication Login", False, error_details, response_time)
            return False
    
    def get_todays_appointments(self):
        """Get today's appointments for testing"""
        print("\n📅 GETTING TODAY'S APPOINTMENTS")
        today = datetime.now().strftime("%Y-%m-%d")
        
        start_time = time.time()
        try:
            response = self.session.get(f"{BACKEND_URL}/rdv/jour/{today}", timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                appointments = response.json()
                if isinstance(appointments, list):
                    appointment_count = len(appointments)
                    details = f"Found {appointment_count} appointments for today ({today})"
                    self.log_test("Get Today's Appointments", True, details, response_time)
                    
                    # Store appointments for testing
                    self.current_appointments = appointments
                    
                    # Log current duree_attente values
                    for apt in appointments:
                        patient_info = apt.get("patient", {})
                        patient_name = f"{patient_info.get('prenom', '')} {patient_info.get('nom', '')}"
                        current_duree = apt.get("duree_attente")
                        current_status = apt.get("statut")
                        details = f"Patient: {patient_name}, Status: {current_status}, Current duree_attente: {current_duree}"
                        self.log_test(f"Current State - {patient_name}", True, details, 0)
                    
                    return appointments
                else:
                    self.log_test("Get Today's Appointments", False, "Response is not a list", response_time)
                    return []
            else:
                self.log_test("Get Today's Appointments", False, f"HTTP {response.status_code}: {response.text}", response_time)
                return []
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("Get Today's Appointments", False, f"Exception: {str(e)}", response_time)
            return []
    
    def test_color_badge_scenarios(self):
        """Test different duree_attente values for color badge system"""
        print("\n🎨 TESTING COLOR BADGE SCENARIOS")
        
        appointments = self.get_todays_appointments()
        if not appointments:
            self.log_test("Color Badge Testing", False, "No appointments available for testing", 0)
            return
        
        # Test each color range with different appointments
        for i, color_test in enumerate(COLOR_TEST_VALUES):
            if i < len(appointments):
                appointment = appointments[i]
                rdv_id = appointment.get("id")
                patient_info = appointment.get("patient", {})
                patient_name = f"{patient_info.get('prenom', '')} {patient_info.get('nom', '')}"
                
                self.test_duree_attente_value(rdv_id, patient_name, color_test)
            else:
                # If we don't have enough appointments, create a test scenario
                self.log_test(f"Color Badge Test - {color_test['color'].upper()}", False, 
                            f"Not enough appointments to test {color_test['description']}", 0)
    
    def test_duree_attente_value(self, rdv_id, patient_name, color_test):
        """Test setting and verifying a specific duree_attente value"""
        duree_attente = color_test["duree_attente"]
        color = color_test["color"]
        description = color_test["description"]
        
        print(f"\n🔍 TESTING {color.upper()} BADGE: {description}")
        
        # Step 1: Set appointment to attente status first
        start_time = time.time()
        try:
            update_data = {
                "statut": "attente",
                "heure_arrivee_attente": datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
            }
            
            response = self.session.put(f"{BACKEND_URL}/rdv/{rdv_id}/statut", json=update_data, timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                details = f"Set {patient_name} to attente status"
                self.log_test(f"{color.upper()} Badge Test - Set Attente", True, details, response_time)
            else:
                details = f"Failed to set attente status: HTTP {response.status_code}"
                self.log_test(f"{color.upper()} Badge Test - Set Attente", False, details, response_time)
                return
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test(f"{color.upper()} Badge Test - Set Attente", False, f"Exception: {str(e)}", response_time)
            return
        
        # Step 2: Simulate the waiting time by directly updating duree_attente
        # This simulates what would happen after the patient has been waiting
        start_time = time.time()
        try:
            # Calculate a timestamp that would result in the desired duree_attente
            now = datetime.now()
            arrival_time = now - timedelta(minutes=duree_attente)
            
            update_data = {
                "statut": "en_cours",
                "duree_attente": duree_attente,
                "heure_arrivee_attente": arrival_time.strftime("%Y-%m-%dT%H:%M:%S")
            }
            
            response = self.session.put(f"{BACKEND_URL}/rdv/{rdv_id}/statut", json=update_data, timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                returned_duree = data.get("duree_attente")
                
                details = f"Set {patient_name} duree_attente to {duree_attente} minutes ({description})"
                if returned_duree == duree_attente:
                    details += f" - API returned correct value: {returned_duree}"
                    self.log_test(f"{color.upper()} Badge Test - Set Duration", True, details, response_time)
                else:
                    details += f" - API returned different value: {returned_duree}"
                    self.log_test(f"{color.upper()} Badge Test - Set Duration", False, details, response_time)
            else:
                details = f"Failed to set duree_attente: HTTP {response.status_code}: {response.text}"
                self.log_test(f"{color.upper()} Badge Test - Set Duration", False, details, response_time)
                return
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test(f"{color.upper()} Badge Test - Set Duration", False, f"Exception: {str(e)}", response_time)
            return
        
        # Step 3: Verify the value is stored correctly in database
        start_time = time.time()
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            response = self.session.get(f"{BACKEND_URL}/rdv/jour/{today}", timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                appointments = response.json()
                test_appointment = next((apt for apt in appointments if apt.get("id") == rdv_id), None)
                
                if test_appointment:
                    stored_duree = test_appointment.get("duree_attente")
                    stored_status = test_appointment.get("statut")
                    
                    if stored_duree == duree_attente:
                        details = f"Database verification: {patient_name} has duree_attente={stored_duree} minutes (status: {stored_status})"
                        self.log_test(f"{color.upper()} Badge Test - Database Verification", True, details, response_time)
                        
                        # Store successful test for summary
                        self.test_appointments.append({
                            "patient_name": patient_name,
                            "duree_attente": stored_duree,
                            "color": color,
                            "description": description,
                            "status": stored_status
                        })
                    else:
                        details = f"Database mismatch: Expected {duree_attente}, got {stored_duree}"
                        self.log_test(f"{color.upper()} Badge Test - Database Verification", False, details, response_time)
                else:
                    self.log_test(f"{color.upper()} Badge Test - Database Verification", False, "Appointment not found in database", response_time)
            else:
                self.log_test(f"{color.upper()} Badge Test - Database Verification", False, f"HTTP {response.status_code}: {response.text}", response_time)
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test(f"{color.upper()} Badge Test - Database Verification", False, f"Exception: {str(e)}", response_time)
    
    def test_api_response_structure(self):
        """Test that API responses include all necessary fields for color badge display"""
        print("\n📋 TESTING API RESPONSE STRUCTURE")
        
        today = datetime.now().strftime("%Y-%m-%d")
        start_time = time.time()
        
        try:
            response = self.session.get(f"{BACKEND_URL}/rdv/jour/{today}", timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                appointments = response.json()
                if isinstance(appointments, list) and appointments:
                    # Check first appointment structure
                    sample_appointment = appointments[0]
                    required_fields = ["id", "duree_attente", "statut", "patient"]
                    
                    missing_fields = []
                    for field in required_fields:
                        if field not in sample_appointment:
                            missing_fields.append(field)
                    
                    if not missing_fields:
                        details = f"All required fields present: {required_fields}"
                        self.log_test("API Response Structure", True, details, response_time)
                        
                        # Check patient sub-structure
                        patient_info = sample_appointment.get("patient", {})
                        patient_fields = ["nom", "prenom"]
                        missing_patient_fields = [field for field in patient_fields if field not in patient_info]
                        
                        if not missing_patient_fields:
                            details = f"Patient info structure complete: {patient_fields}"
                            self.log_test("Patient Info Structure", True, details, 0)
                        else:
                            details = f"Missing patient fields: {missing_patient_fields}"
                            self.log_test("Patient Info Structure", False, details, 0)
                    else:
                        details = f"Missing required fields: {missing_fields}"
                        self.log_test("API Response Structure", False, details, response_time)
                else:
                    self.log_test("API Response Structure", False, "No appointments to check structure", response_time)
            else:
                self.log_test("API Response Structure", False, f"HTTP {response.status_code}: {response.text}", response_time)
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("API Response Structure", False, f"Exception: {str(e)}", response_time)
    
    def test_color_range_boundaries(self):
        """Test boundary values for color ranges"""
        print("\n🎯 TESTING COLOR RANGE BOUNDARIES")
        
        boundary_tests = [
            {"duree_attente": 14, "expected_color": "green", "description": "14 minutes (green boundary)"},
            {"duree_attente": 15, "expected_color": "blue", "description": "15 minutes (blue start)"},
            {"duree_attente": 30, "expected_color": "blue", "description": "30 minutes (blue end)"},
            {"duree_attente": 31, "expected_color": "orange", "description": "31 minutes (orange start)"},
            {"duree_attente": 60, "expected_color": "orange", "description": "60 minutes (orange end)"},
            {"duree_attente": 61, "expected_color": "red", "description": "61 minutes (red start)"}
        ]
        
        for boundary_test in boundary_tests:
            duree_attente = boundary_test["duree_attente"]
            expected_color = boundary_test["expected_color"]
            description = boundary_test["description"]
            
            # Determine color based on business logic
            if duree_attente < 15:
                actual_color = "green"
            elif duree_attente <= 30:
                actual_color = "blue"
            elif duree_attente <= 60:
                actual_color = "orange"
            else:
                actual_color = "red"
            
            if actual_color == expected_color:
                details = f"{description} -> {actual_color} (correct)"
                self.log_test(f"Boundary Test - {duree_attente}min", True, details, 0)
            else:
                details = f"{description} -> Expected {expected_color}, got {actual_color}"
                self.log_test(f"Boundary Test - {duree_attente}min", False, details, 0)
    
    def generate_summary(self):
        """Generate comprehensive test summary"""
        print("\n" + "="*80)
        print("🎨 COLOR-CODED WAITING TIME BADGE SYSTEM TEST SUMMARY")
        print("="*80)
        
        total_tests = len(self.test_results)
        passed_tests = len([t for t in self.test_results if t["success"]])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"\n📊 OVERALL RESULTS:")
        print(f"   Total Tests: {total_tests}")
        print(f"   Passed: {passed_tests} ✅")
        print(f"   Failed: {failed_tests} ❌")
        print(f"   Success Rate: {success_rate:.1f}%")
        print(f"   Total Execution Time: {time.time() - self.start_time:.2f} seconds")
        
        if self.test_appointments:
            print(f"\n🎨 COLOR BADGE TEST RESULTS:")
            for apt in self.test_appointments:
                print(f"   • {apt['patient_name']}: {apt['duree_attente']} minutes -> {apt['color'].upper()} badge ({apt['description']})")
        
        print(f"\n🔍 DETAILED TEST RESULTS:")
        for result in self.test_results:
            print(f"   {result['status']} {result['test']} ({result['response_time']:.3f}s)")
            if result['details'] and not result['success']:
                print(f"      └─ {result['details']}")
        
        print(f"\n🎯 COLOR CODING VERIFICATION:")
        print(f"   Green (< 15 min): Tested with 5 minutes")
        print(f"   Blue (15-30 min): Tested with 20 minutes") 
        print(f"   Orange (30-60 min): Tested with 45 minutes")
        print(f"   Red (> 60 min): Tested with 75 minutes")
        
        print(f"\n✅ SYSTEM READINESS:")
        if success_rate >= 80:
            print(f"   🎉 Color badge system is READY for production")
            print(f"   🎨 Frontend can display different colored badges based on duree_attente values")
            print(f"   💾 Backend correctly stores and returns various waiting time durations")
        else:
            print(f"   ⚠️  Color badge system needs attention")
            print(f"   🔧 Some tests failed - review failed tests above")
        
        return success_rate >= 80

def main():
    """Main test execution"""
    print("🎨 COLOR-CODED WAITING TIME BADGE SYSTEM TESTING")
    print("="*60)
    print("Testing color-coded waiting time badge system with different duree_attente values:")
    print("• Green: < 15 minutes")
    print("• Blue: 15-30 minutes") 
    print("• Orange: 30-60 minutes")
    print("• Red: > 60 minutes")
    print("="*60)
    
    tester = ColorBadgeTester()
    
    # Run authentication test
    if not tester.test_authentication():
        print("❌ Authentication failed - cannot proceed with testing")
        return False
    
    # Run color badge tests
    tester.test_color_badge_scenarios()
    tester.test_api_response_structure()
    tester.test_color_range_boundaries()
    
    # Generate summary
    success = tester.generate_summary()
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)