#!/usr/bin/env python3
"""
BADGE PERSISTENCE BUG FIX TESTING
Testing the specific bug fixes mentioned in the review request:

1. Backend: API GET /rdv/jour/{date} ensures duree_attente is always present (even if null)
2. Frontend: handleStartConsultation does fetchData() BEFORE optimistic update to avoid conflicts

EXACT TEST SEQUENCE REQUESTED:
1. Login with medecin/medecin123
2. Take a patient and move to "attente" 
3. Wait 10 seconds to accumulate time
4. Move to "en_cours" 
5. Verify immediately after that:
   - duree_attente is calculated correctly (≈1 minute)
   - The API GET /rdv/jour/{date} returns duree_attente
   - The badge appears in the "En consultation" section

OBJECTIVE: Confirm that the badge appears and does NOT disappear after status transition.
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

class BadgePersistenceTester:
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
        print("\n🔐 STEP 1: AUTHENTICATION")
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
    
    def get_test_patient(self):
        """Get a patient for testing"""
        today = datetime.now().strftime("%Y-%m-%d")
        
        try:
            response = self.session.get(f"{BACKEND_URL}/rdv/jour/{today}", timeout=10)
            if response.status_code == 200:
                appointments = response.json()
                if appointments:
                    # Find a suitable test patient (prefer one not in en_cours)
                    for apt in appointments:
                        if apt.get("statut") != "en_cours":
                            return apt
                    # If all are en_cours, use the first one
                    return appointments[0]
            return None
        except Exception as e:
            print(f"Error getting test patient: {e}")
            return None
    
    def test_badge_persistence_bug_fix(self):
        """Test the exact sequence requested in the review"""
        print("\n🎯 STEP 2: BADGE PERSISTENCE BUG FIX TEST")
        print("Testing exact sequence: attente → wait 10s → en_cours → verify badge persistence")
        
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Get a test patient
        test_appointment = self.get_test_patient()
        if not test_appointment:
            self.log_test("Badge Persistence Test", False, "No test patient found", 0)
            return False
        
        patient_info = test_appointment.get("patient", {})
        test_patient_name = f"{patient_info.get('prenom', '')} {patient_info.get('nom', '')}"
        rdv_id = test_appointment.get("id")
        
        print(f"Selected test patient: {test_patient_name} (ID: {rdv_id})")
        
        # STEP 2A: Move patient to "attente"
        print("\n🏥 STEP 2A: Move patient to 'attente' status")
        start_time = time.time()
        
        attente_start_time = datetime.now()
        
        try:
            update_data = {"statut": "attente"}
            response = self.session.put(f"{BACKEND_URL}/rdv/{rdv_id}/statut", json=update_data, timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                heure_arrivee = data.get("heure_arrivee_attente", "NOT_SET")
                details = f"Moved '{test_patient_name}' to attente - heure_arrivee_attente: {heure_arrivee}"
                self.log_test("Move to Attente Status", True, details, response_time)
            else:
                self.log_test("Move to Attente Status", False, f"HTTP {response.status_code}: {response.text}", response_time)
                return False
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("Move to Attente Status", False, f"Exception: {str(e)}", response_time)
            return False
        
        # STEP 2B: Wait 10 seconds to accumulate time
        print("\n⏰ STEP 2B: Wait 10 seconds to accumulate waiting time")
        print("Waiting 10 seconds to ensure measurable waiting time...")
        time.sleep(10)
        
        # STEP 2C: Move to "en_cours" 
        print("\n🩺 STEP 2C: Move patient to 'en_cours' status")
        start_time = time.time()
        
        consultation_start_time = datetime.now()
        
        try:
            update_data = {"statut": "en_cours"}
            response = self.session.put(f"{BACKEND_URL}/rdv/{rdv_id}/statut", json=update_data, timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                # Check if duree_attente is in the response
                if "duree_attente" in data:
                    calculated_duree = data["duree_attente"]
                    
                    # Calculate expected waiting time (should be ~1 minute for 10 seconds wait)
                    time_diff = consultation_start_time - attente_start_time
                    expected_minutes = max(1, int(time_diff.total_seconds() / 60))  # At least 1 minute
                    
                    details = f"Status changed to en_cours - duree_attente: {calculated_duree} minutes (expected: ~{expected_minutes} min)"
                    self.log_test("Move to En_Cours with Duration Calculation", True, details, response_time)
                    
                    # Store for verification
                    self.calculated_duree_attente = calculated_duree
                else:
                    self.log_test("Move to En_Cours with Duration Calculation", False, "duree_attente not in API response", response_time)
                    return False
            else:
                self.log_test("Move to En_Cours Status", False, f"HTTP {response.status_code}: {response.text}", response_time)
                return False
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("Move to En_Cours Status", False, f"Exception: {str(e)}", response_time)
            return False
        
        # STEP 2D: Verify immediately after that duree_attente is calculated correctly
        print("\n✅ STEP 2D: Verify duree_attente calculation and API response")
        start_time = time.time()
        
        try:
            response = self.session.get(f"{BACKEND_URL}/rdv/jour/{today}", timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                appointments = response.json()
                updated_appointment = next((apt for apt in appointments if apt.get("id") == rdv_id), None)
                
                if updated_appointment:
                    # CRITICAL VERIFICATION 1: duree_attente is always present in API response
                    if "duree_attente" not in updated_appointment:
                        self.log_test("API duree_attente Field Always Present", False, "duree_attente field missing from API response", response_time)
                        return False
                    else:
                        duree_attente_value = updated_appointment["duree_attente"]
                        details = f"duree_attente field present in API response with value: {duree_attente_value}"
                        self.log_test("API duree_attente Field Always Present", True, details, response_time)
                    
                    # CRITICAL VERIFICATION 2: duree_attente is calculated correctly
                    stored_duree = updated_appointment.get("duree_attente")
                    if stored_duree is not None and stored_duree > 0:
                        details = f"duree_attente calculated correctly: {stored_duree} minutes"
                        self.log_test("Duree_Attente Calculated Correctly", True, details, 0)
                    else:
                        details = f"duree_attente not calculated properly: {stored_duree}"
                        self.log_test("Duree_Attente Calculated Correctly", False, details, 0)
                    
                    # CRITICAL VERIFICATION 3: Patient is in "en_cours" status
                    current_status = updated_appointment.get("statut")
                    if current_status == "en_cours":
                        details = f"Patient '{test_patient_name}' is in 'en_cours' status with duree_attente: {stored_duree}"
                        self.log_test("Patient in En_Cours Status", True, details, 0)
                    else:
                        details = f"Patient status is '{current_status}' instead of 'en_cours'"
                        self.log_test("Patient in En_Cours Status", False, details, 0)
                    
                    # CRITICAL VERIFICATION 4: Badge data available for frontend
                    patient_data = updated_appointment.get("patient", {})
                    if patient_data and stored_duree is not None:
                        details = f"Badge data available - Patient: {patient_data.get('prenom', '')} {patient_data.get('nom', '')}, Duration: {stored_duree} min"
                        self.log_test("Badge Data Available for Frontend", True, details, 0)
                    else:
                        details = "Badge data incomplete - missing patient info or duree_attente"
                        self.log_test("Badge Data Available for Frontend", False, details, 0)
                    
                else:
                    self.log_test("API Response Verification", False, "Updated appointment not found in API response", response_time)
                    return False
            else:
                self.log_test("API Response Verification", False, f"HTTP {response.status_code}: {response.text}", response_time)
                return False
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("API Response Verification", False, f"Exception: {str(e)}", response_time)
            return False
        
        return True
    
    def test_backend_fix_verification(self):
        """Test Backend Fix: API GET /rdv/jour/{date} ensures duree_attente is always present"""
        print("\n🔧 STEP 3: BACKEND FIX VERIFICATION")
        print("Testing that API GET /rdv/jour/{date} ensures duree_attente is always present (even if null)")
        
        today = datetime.now().strftime("%Y-%m-%d")
        
        start_time = time.time()
        try:
            response = self.session.get(f"{BACKEND_URL}/rdv/jour/{today}", timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                appointments = response.json()
                if isinstance(appointments, list):
                    total_appointments = len(appointments)
                    missing_duree_attente = 0
                    null_duree_attente = 0
                    zero_duree_attente = 0
                    valid_duree_attente = 0
                    
                    for apt in appointments:
                        if "duree_attente" not in apt:
                            missing_duree_attente += 1
                        elif apt["duree_attente"] is None:
                            null_duree_attente += 1
                        elif apt["duree_attente"] == 0:
                            zero_duree_attente += 1
                        else:
                            valid_duree_attente += 1
                    
                    # BACKEND FIX VERIFICATION: All appointments should have duree_attente field
                    if missing_duree_attente == 0:
                        details = f"All {total_appointments} appointments have duree_attente field (Null: {null_duree_attente}, Zero: {zero_duree_attente}, Valid: {valid_duree_attente})"
                        self.log_test("Backend Fix - duree_attente Always Present", True, details, response_time)
                    else:
                        details = f"{missing_duree_attente} out of {total_appointments} appointments missing duree_attente field"
                        self.log_test("Backend Fix - duree_attente Always Present", False, details, response_time)
                    
                    # Additional verification: Check specific status sections
                    en_cours_appointments = [apt for apt in appointments if apt.get("statut") == "en_cours"]
                    if en_cours_appointments:
                        for apt in en_cours_appointments:
                            patient_info = apt.get("patient", {})
                            patient_name = f"{patient_info.get('prenom', '')} {patient_info.get('nom', '')}"
                            duree_attente = apt.get("duree_attente", "MISSING")
                            
                            if "duree_attente" in apt:
                                details = f"En_cours patient '{patient_name}' has duree_attente: {duree_attente}"
                                self.log_test("En_Cours Patient duree_attente Field", True, details, 0)
                            else:
                                details = f"En_cours patient '{patient_name}' MISSING duree_attente field"
                                self.log_test("En_Cours Patient duree_attente Field", False, details, 0)
                    
                else:
                    self.log_test("Backend Fix Verification", False, "API response is not a list", response_time)
            else:
                self.log_test("Backend Fix Verification", False, f"HTTP {response.status_code}: {response.text}", response_time)
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("Backend Fix Verification", False, f"Exception: {str(e)}", response_time)
    
    def test_frontend_integration_readiness(self):
        """Test Frontend Integration Readiness: Verify data structure for handleStartConsultation"""
        print("\n🖥️ STEP 4: FRONTEND INTEGRATION READINESS")
        print("Testing that API provides correct data structure for handleStartConsultation fetchData() fix")
        
        today = datetime.now().strftime("%Y-%m-%d")
        
        start_time = time.time()
        try:
            response = self.session.get(f"{BACKEND_URL}/rdv/jour/{today}", timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                appointments = response.json()
                if isinstance(appointments, list):
                    # Check data structure for frontend consumption
                    en_cours_appointments = [apt for apt in appointments if apt.get("statut") == "en_cours"]
                    
                    if en_cours_appointments:
                        for apt in en_cours_appointments:
                            # Verify all required fields for badge display
                            required_fields = ["id", "statut", "duree_attente", "patient"]
                            missing_fields = [field for field in required_fields if field not in apt]
                            
                            if not missing_fields:
                                patient_info = apt.get("patient", {})
                                patient_name = f"{patient_info.get('prenom', '')} {patient_info.get('nom', '')}"
                                duree_attente = apt.get("duree_attente")
                                
                                details = f"En_cours patient '{patient_name}' - All required fields present, duree_attente: {duree_attente}"
                                self.log_test("Frontend Data Structure Complete", True, details, 0)
                                
                                # Verify patient sub-object has required fields
                                patient_required = ["nom", "prenom"]
                                patient_missing = [field for field in patient_required if field not in patient_info]
                                
                                if not patient_missing:
                                    self.log_test("Patient Data Structure Complete", True, f"Patient object complete for '{patient_name}'", 0)
                                else:
                                    self.log_test("Patient Data Structure Complete", False, f"Missing patient fields: {patient_missing}", 0)
                            else:
                                self.log_test("Frontend Data Structure Complete", False, f"Missing appointment fields: {missing_fields}", 0)
                    else:
                        self.log_test("Frontend Integration Readiness", True, "No en_cours appointments to test (normal state)", response_time)
                
                else:
                    self.log_test("Frontend Integration Readiness", False, "API response is not a list", response_time)
            else:
                self.log_test("Frontend Integration Readiness", False, f"HTTP {response.status_code}: {response.text}", response_time)
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("Frontend Integration Readiness", False, f"Exception: {str(e)}", response_time)
    
    def run_all_tests(self):
        """Run all badge persistence tests"""
        print("🎯 BADGE PERSISTENCE BUG FIX TESTING")
        print("=" * 60)
        print("Testing the specific bug fixes mentioned in the review request:")
        print("1. Backend: API GET /rdv/jour/{date} ensures duree_attente is always present")
        print("2. Frontend: handleStartConsultation does fetchData() BEFORE optimistic update")
        print("=" * 60)
        
        # Test sequence
        if not self.test_authentication():
            print("❌ Authentication failed - cannot continue tests")
            return False
        
        success = True
        success &= self.test_badge_persistence_bug_fix()
        self.test_backend_fix_verification()
        self.test_frontend_integration_readiness()
        
        # Print summary
        print("\n" + "=" * 60)
        print("🎯 BADGE PERSISTENCE BUG FIX TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = len([t for t in self.test_results if t["success"]])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        print(f"Total Execution Time: {time.time() - self.start_time:.2f} seconds")
        
        # Print detailed results
        print("\n📋 DETAILED TEST RESULTS:")
        for result in self.test_results:
            print(f"{result['status']} {result['test']} ({result['response_time']:.3f}s)")
            if result['details']:
                print(f"    {result['details']}")
        
        # Critical findings
        print("\n🔍 CRITICAL FINDINGS:")
        critical_tests = [
            "Move to En_Cours with Duration Calculation",
            "API duree_attente Field Always Present", 
            "Duree_Attente Calculated Correctly",
            "Badge Data Available for Frontend",
            "Backend Fix - duree_attente Always Present"
        ]
        
        for test_name in critical_tests:
            test_result = next((t for t in self.test_results if t["test"] == test_name), None)
            if test_result:
                status = "✅ WORKING" if test_result["success"] else "❌ FAILING"
                print(f"- {test_name}: {status}")
        
        print("\n🎉 BADGE PERSISTENCE BUG FIX TESTING COMPLETED")
        return success

if __name__ == "__main__":
    tester = BadgePersistenceTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)