#!/usr/bin/env python3
"""
CRITICAL WAITING TIME WORKFLOW DEBUGGING
Backend API Testing Suite for Cabinet Médical

FOCUS: Debug the exact user workflow issue where waiting time is NOT appearing next to patient names
when moved from waiting room to "en cours" or "terminés" sections.

Critical Investigation Points:
1. Real Data Examination: Check current appointments and their EXACT duree_attente values
2. Status Change Debugging: Test the EXACT sequence: patient to "attente" → patient to "en_cours"  
3. Data Flow Investigation: Check if PUT /api/rdv/{id}/statut properly updates duree_attente
4. Real User Workflow Simulation: Find a real appointment and move it through the exact user workflow
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

class CriticalWaitingTimeDebugger:
    def __init__(self):
        self.session = requests.Session()
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
        if details and not success:
            print(f"    Details: {details}")
    
    def test_authentication(self):
        """Test authentication"""
        print("\n🔐 TESTING AUTHENTICATION")
        start_time = time.time()
        
        try:
            response = self.session.post(
                f"{BACKEND_URL}/auth/login",
                json=TEST_CREDENTIALS,
                timeout=10
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
                self.log_test("Authentication Login", False, f"HTTP {response.status_code}: {response.text}", response_time)
                return False
                
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("Authentication Login", False, f"Exception: {str(e)}", response_time)
            return False
    
    def test_critical_waiting_time_workflow_debugging(self):
        """CRITICAL: Debug the exact user workflow issue - waiting time NOT appearing next to patient names"""
        print("\n🚨 CRITICAL WAITING TIME WORKFLOW DEBUGGING")
        print("Testing the EXACT user workflow: patient to 'attente' → patient to 'en_cours' → check duree_attente")
        
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Step 1: Get current state and select a patient for testing
        print("\n📋 STEP 1: Current State Check")
        start_time = time.time()
        try:
            response = self.session.get(f"{BACKEND_URL}/rdv/jour/{today}", timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                appointments = response.json()
                if appointments and len(appointments) > 0:
                    # Select a patient for testing (prefer one not in attente/en_cours already)
                    test_appointment = None
                    for apt in appointments:
                        if apt.get("statut") not in ["attente", "en_cours"]:
                            test_appointment = apt
                            break
                    
                    if not test_appointment:
                        test_appointment = appointments[0]  # Use first available
                    
                    rdv_id = test_appointment.get("id")
                    original_status = test_appointment.get("statut")
                    original_duree = test_appointment.get("duree_attente")
                    original_heure_arrivee = test_appointment.get("heure_arrivee_attente")
                    patient_info = test_appointment.get("patient", {})
                    patient_name = f"{patient_info.get('prenom', '')} {patient_info.get('nom', '')}"
                    
                    details = f"Selected patient '{patient_name}' - Current: status={original_status}, duree_attente={original_duree}, heure_arrivee={original_heure_arrivee}"
                    self.log_test("Critical Workflow Step 1 - Current State Check", True, details, response_time)
                    
                    # Step 2: Move patient to waiting room (attente) with timestamp
                    print("\n⏰ STEP 2: Move Patient to Waiting Room")
                    start_time = time.time()
                    current_time = datetime.now()
                    arrival_time = current_time.strftime("%H:%M")
                    
                    # Try different endpoints to update status
                    endpoints_to_try = [
                        f"{BACKEND_URL}/rdv/{rdv_id}/statut",
                        f"{BACKEND_URL}/rdv/{rdv_id}",
                        f"{BACKEND_URL}/rdv/{rdv_id}/status"
                    ]
                    
                    step2_success = False
                    for endpoint in endpoints_to_try:
                        try:
                            update_data = {
                                "statut": "attente",
                                "heure_arrivee_attente": arrival_time,
                                "duree_attente": 0
                            }
                            response = self.session.put(endpoint, json=update_data, timeout=10)
                            if response.status_code == 200:
                                step2_success = True
                                response_time = time.time() - start_time
                                details = f"Successfully moved '{patient_name}' to attente at {arrival_time} via {endpoint.split('/')[-1]}"
                                self.log_test("Critical Workflow Step 2 - Move to Waiting Room", True, details, response_time)
                                break
                            elif response.status_code == 404:
                                continue
                        except Exception:
                            continue
                    
                    if not step2_success:
                        response_time = time.time() - start_time
                        self.log_test("Critical Workflow Step 2 - Move to Waiting Room", False, "No working status update endpoint found", response_time)
                        return
                    
                    # Step 3: Move patient to consultation (en_cours) and check duree_attente calculation
                    print("\n🏥 STEP 3: Move Patient to Consultation")
                    # Wait a moment to simulate waiting time
                    time.sleep(3)  # 3 seconds for testing
                    
                    start_time = time.time()
                    consultation_time = datetime.now()
                    
                    step3_success = False
                    for endpoint in endpoints_to_try:
                        try:
                            update_data = {
                                "statut": "en_cours"
                            }
                            response = self.session.put(endpoint, json=update_data, timeout=10)
                            if response.status_code == 200:
                                step3_success = True
                                response_time = time.time() - start_time
                                
                                # Get updated appointment data
                                response = self.session.get(f"{BACKEND_URL}/rdv/jour/{today}", timeout=10)
                                if response.status_code == 200:
                                    updated_appointments = response.json()
                                    updated_appointment = next((apt for apt in updated_appointments if apt.get("id") == rdv_id), None)
                                    
                                    if updated_appointment:
                                        new_duree = updated_appointment.get("duree_attente")
                                        new_status = updated_appointment.get("statut")
                                        new_heure_arrivee = updated_appointment.get("heure_arrivee_attente")
                                        
                                        # Calculate expected waiting time
                                        time_diff = consultation_time - current_time
                                        expected_minutes = max(1, int(time_diff.total_seconds() / 60))
                                        
                                        details = f"'{patient_name}' moved to {new_status}, duree_attente: {new_duree}, heure_arrivee: {new_heure_arrivee}, expected: ~{expected_minutes} min"
                                        
                                        # CRITICAL CHECK: Is duree_attente actually calculated?
                                        if new_duree is None:
                                            self.log_test("Critical Workflow Step 3 - DUREE_ATTENTE IS NULL", False, f"duree_attente is None for {patient_name} - this is the bug!", response_time)
                                        elif new_duree == 0:
                                            self.log_test("Critical Workflow Step 3 - DUREE_ATTENTE IS ZERO", False, f"duree_attente is 0 for {patient_name} - calculation failed!", response_time)
                                        else:
                                            self.log_test("Critical Workflow Step 3 - DUREE_ATTENTE CALCULATED", True, f"duree_attente calculated correctly: {new_duree} minutes", response_time)
                                        
                                        self.log_test("Critical Workflow Step 3 - Move to Consultation", True, details, response_time)
                                        
                                        # Store for next step
                                        self.test_patient_data = {
                                            "rdv_id": rdv_id,
                                            "patient_name": patient_name,
                                            "duree_attente": new_duree,
                                            "status": new_status
                                        }
                                    else:
                                        self.log_test("Critical Workflow Step 3 - Move to Consultation", False, "Updated appointment not found", response_time)
                                else:
                                    self.log_test("Critical Workflow Step 3 - Move to Consultation", False, "Failed to retrieve updated appointments", response_time)
                                break
                        except Exception:
                            continue
                    
                    if not step3_success:
                        response_time = time.time() - start_time
                        self.log_test("Critical Workflow Step 3 - Move to Consultation", False, "Failed to move to consultation", response_time)
                        return
                    
                    # Step 4: Verify data structure and field presence
                    print("\n🔍 STEP 4: Data Structure Verification")
                    start_time = time.time()
                    try:
                        response = self.session.get(f"{BACKEND_URL}/rdv/jour/{today}", timeout=10)
                        response_time = time.time() - start_time
                        
                        if response.status_code == 200:
                            appointments = response.json()
                            current_appointment = next((apt for apt in appointments if apt.get("id") == rdv_id), None)
                            
                            if current_appointment:
                                # Check all relevant fields
                                fields_check = {
                                    "duree_attente": current_appointment.get("duree_attente"),
                                    "heure_arrivee_attente": current_appointment.get("heure_arrivee_attente"),
                                    "statut": current_appointment.get("statut"),
                                    "patient": current_appointment.get("patient", {})
                                }
                                
                                details = f"Data structure for '{patient_name}': {fields_check}"
                                self.log_test("Critical Workflow Step 4 - Data Structure Verification", True, details, response_time)
                            else:
                                self.log_test("Critical Workflow Step 4 - Data Structure Verification", False, "Appointment not found", response_time)
                        else:
                            self.log_test("Critical Workflow Step 4 - Data Structure Verification", False, f"HTTP {response.status_code}", response_time)
                    except Exception as e:
                        response_time = time.time() - start_time
                        self.log_test("Critical Workflow Step 4 - Data Structure Verification", False, f"Exception: {str(e)}", response_time)
                    
                    # Step 5: Move to terminés and verify duree_attente is preserved
                    print("\n✅ STEP 5: Move to Terminés")
                    start_time = time.time()
                    
                    step5_success = False
                    for endpoint in endpoints_to_try:
                        try:
                            update_data = {
                                "statut": "termine"
                            }
                            response = self.session.put(endpoint, json=update_data, timeout=10)
                            if response.status_code == 200:
                                step5_success = True
                                response_time = time.time() - start_time
                                
                                # Get final appointment data
                                response = self.session.get(f"{BACKEND_URL}/rdv/jour/{today}", timeout=10)
                                if response.status_code == 200:
                                    final_appointments = response.json()
                                    final_appointment = next((apt for apt in final_appointments if apt.get("id") == rdv_id), None)
                                    
                                    if final_appointment:
                                        final_duree = final_appointment.get("duree_attente")
                                        final_status = final_appointment.get("statut")
                                        
                                        details = f"'{patient_name}' moved to {final_status}, duree_attente preserved: {final_duree} minutes"
                                        self.log_test("Critical Workflow Step 5 - Move to Terminés", True, details, response_time)
                                    else:
                                        self.log_test("Critical Workflow Step 5 - Move to Terminés", False, "Final appointment not found", response_time)
                                else:
                                    self.log_test("Critical Workflow Step 5 - Move to Terminés", False, "Failed to retrieve final appointments", response_time)
                                break
                        except Exception:
                            continue
                    
                    if not step5_success:
                        response_time = time.time() - start_time
                        self.log_test("Critical Workflow Step 5 - Move to Terminés", False, "Failed to move to terminés", response_time)
                
                else:
                    self.log_test("Critical Waiting Time Workflow Debugging", False, "No appointments found for testing", response_time)
            else:
                self.log_test("Critical Waiting Time Workflow Debugging", False, f"HTTP {response.status_code}: {response.text}", response_time)
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("Critical Waiting Time Workflow Debugging", False, f"Exception: {str(e)}", response_time)
    
    def test_dashboard_duree_attente_moyenne_real_calculation(self):
        """Test Dashboard duree_attente_moyenne - Verify it shows real calculated values instead of mock data"""
        print("\n📊 TESTING DASHBOARD DUREE_ATTENTE_MOYENNE REAL CALCULATION")
        
        start_time = time.time()
        try:
            response = self.session.get(f"{BACKEND_URL}/dashboard", timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                if "duree_attente_moyenne" in data:
                    duree_attente_moyenne = data["duree_attente_moyenne"]
                    
                    # Check if it's the old mock value (15) or real calculation
                    if duree_attente_moyenne == 15:
                        details = f"duree_attente_moyenne: {duree_attente_moyenne} (WARNING: appears to be mock data, not real calculation)"
                        self.log_test("Dashboard Duree_Attente_Moyenne - Mock Data Detected", False, details, response_time)
                    else:
                        details = f"duree_attente_moyenne: {duree_attente_moyenne} (SUCCESS: calculated from real data)"
                        self.log_test("Dashboard Duree_Attente_Moyenne - Real Calculation", True, details, response_time)
                    
                    # Get context stats
                    total_rdv = data.get("total_rdv", 0)
                    rdv_attente = data.get("rdv_attente", 0)
                    rdv_en_cours = data.get("rdv_en_cours", 0)
                    rdv_termines = data.get("rdv_termines", 0)
                    
                    context_details = f"Context - Total RDV: {total_rdv}, Attente: {rdv_attente}, En cours: {rdv_en_cours}, Terminés: {rdv_termines}"
                    self.log_test("Dashboard Stats Context", True, context_details, 0)
                    
                else:
                    self.log_test("Dashboard Duree_Attente_Moyenne", False, "duree_attente_moyenne field missing from dashboard response", response_time)
                
            else:
                self.log_test("Dashboard Duree_Attente_Moyenne", False, f"HTTP {response.status_code}: {response.text}", response_time)
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("Dashboard Duree_Attente_Moyenne", False, f"Exception: {str(e)}", response_time)

    def test_current_appointments_data_analysis(self):
        """Analyze current appointments data structure to find the root cause"""
        print("\n🔍 ANALYZING CURRENT APPOINTMENTS DATA STRUCTURE")
        
        today = datetime.now().strftime("%Y-%m-%d")
        
        start_time = time.time()
        try:
            response = self.session.get(f"{BACKEND_URL}/rdv/jour/{today}", timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                appointments = response.json()
                if appointments and len(appointments) > 0:
                    print(f"    📊 Found {len(appointments)} appointments for today")
                    
                    # Analyze each appointment's duree_attente field
                    for i, apt in enumerate(appointments):
                        patient_info = apt.get("patient", {})
                        patient_name = f"{patient_info.get('prenom', '')} {patient_info.get('nom', '')}"
                        
                        duree_attente = apt.get("duree_attente")
                        heure_arrivee = apt.get("heure_arrivee_attente")
                        statut = apt.get("statut")
                        heure = apt.get("heure")
                        
                        # Detailed analysis
                        if duree_attente is None:
                            details = f"Patient '{patient_name}' ({statut}) - duree_attente=None, heure_arrivee='{heure_arrivee}', heure='{heure}'"
                            self.log_test(f"Data Analysis - {patient_name} (NULL duree_attente)", True, details, 0)
                        elif duree_attente == 0:
                            details = f"Patient '{patient_name}' ({statut}) - duree_attente=0, heure_arrivee='{heure_arrivee}', heure='{heure}'"
                            self.log_test(f"Data Analysis - {patient_name} (ZERO duree_attente)", True, details, 0)
                        else:
                            details = f"Patient '{patient_name}' ({statut}) - duree_attente={duree_attente} min, heure_arrivee='{heure_arrivee}', heure='{heure}'"
                            self.log_test(f"Data Analysis - {patient_name} (VALID duree_attente)", True, details, 0)
                    
                    # Summary statistics
                    total_appointments = len(appointments)
                    null_duree = len([apt for apt in appointments if apt.get("duree_attente") is None])
                    zero_duree = len([apt for apt in appointments if apt.get("duree_attente") == 0])
                    valid_duree = len([apt for apt in appointments if apt.get("duree_attente", 0) > 0])
                    
                    summary = f"Total: {total_appointments}, Null: {null_duree}, Zero: {zero_duree}, Valid: {valid_duree}"
                    self.log_test("Data Analysis Summary", True, summary, response_time)
                    
                else:
                    self.log_test("Current Appointments Data Analysis", False, "No appointments found", response_time)
            else:
                self.log_test("Current Appointments Data Analysis", False, f"HTTP {response.status_code}: {response.text}", response_time)
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("Current Appointments Data Analysis", False, f"Exception: {str(e)}", response_time)
    
    def test_status_change_endpoint_availability(self):
        """Test Status Change Endpoint Availability - Check if PUT /api/rdv/{id}/statut exists"""
        print("\n🔗 TESTING STATUS CHANGE ENDPOINT AVAILABILITY")
        
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Get an appointment to test with
        try:
            response = self.session.get(f"{BACKEND_URL}/rdv/jour/{today}", timeout=10)
            if response.status_code == 200:
                appointments = response.json()
                if appointments and len(appointments) > 0:
                    test_appointment = appointments[0]
                    rdv_id = test_appointment.get("id")
                    
                    # Test different endpoint variations
                    endpoints_to_test = [
                        f"{BACKEND_URL}/rdv/{rdv_id}/statut",
                        f"{BACKEND_URL}/rdv/{rdv_id}/status", 
                        f"{BACKEND_URL}/rdv/{rdv_id}"
                    ]
                    
                    for endpoint in endpoints_to_test:
                        start_time = time.time()
                        try:
                            # Test with minimal data to check endpoint availability
                            test_data = {"statut": test_appointment.get("statut", "programme")}
                            response = self.session.put(endpoint, json=test_data, timeout=10)
                            response_time = time.time() - start_time
                            
                            endpoint_name = endpoint.split('/')[-1]
                            if response.status_code == 200:
                                details = f"Endpoint /{endpoint_name} is available and working"
                                self.log_test(f"Status Endpoint - {endpoint_name}", True, details, response_time)
                            elif response.status_code == 404:
                                details = f"Endpoint /{endpoint_name} not found (HTTP 404)"
                                self.log_test(f"Status Endpoint - {endpoint_name}", False, details, response_time)
                            else:
                                details = f"Endpoint /{endpoint_name} responded with HTTP {response.status_code}"
                                self.log_test(f"Status Endpoint - {endpoint_name}", False, details, response_time)
                        except Exception as e:
                            response_time = time.time() - start_time
                            self.log_test(f"Status Endpoint - {endpoint_name}", False, f"Exception: {str(e)}", response_time)
                
                else:
                    self.log_test("Status Change Endpoint Availability", False, "No appointments found for testing", 0)
            else:
                self.log_test("Status Change Endpoint Availability", False, f"Failed to get appointments: HTTP {response.status_code}", 0)
        except Exception as e:
            self.log_test("Status Change Endpoint Availability", False, f"Exception getting appointments: {str(e)}", 0)

    def run_critical_tests(self):
        """Run all critical waiting time tests"""
        print("🚨 STARTING CRITICAL WAITING TIME WORKFLOW DEBUGGING")
        print("=" * 80)
        
        # Authentication first
        if not self.test_authentication():
            print("❌ Authentication failed - cannot proceed with testing")
            return
        
        # Critical waiting time workflow tests
        self.test_current_appointments_data_analysis()
        self.test_critical_waiting_time_workflow_debugging()
        self.test_dashboard_duree_attente_moyenne_real_calculation()
        self.test_status_change_endpoint_availability()
        
        # Print summary
        self.print_summary()

    def print_summary(self):
        """Print test summary"""
        total_time = time.time() - self.start_time
        total_tests = len(self.test_results)
        passed_tests = len([t for t in self.test_results if t["success"]])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print("\n" + "=" * 80)
        print("🏁 CRITICAL WAITING TIME WORKFLOW DEBUGGING SUMMARY")
        print("=" * 80)
        print(f"⏱️  Total execution time: {total_time:.2f} seconds")
        print(f"📊 Total tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"📈 Success rate: {success_rate:.1f}%")
        
        if failed_tests > 0:
            print(f"\n❌ FAILED TESTS ({failed_tests}):")
            for result in self.test_results:
                if not result["success"]:
                    print(f"   • {result['test']}: {result['details']}")
        
        print("\n🎯 CRITICAL FINDINGS:")
        print("   • Focus on duree_attente field values in appointments")
        print("   • Check if status change endpoints properly calculate waiting time")
        print("   • Verify dashboard shows real calculated values, not mock data")
        print("   • Test the exact user workflow: attente → en_cours → termine")
        
        print("\n" + "=" * 80)

if __name__ == "__main__":
    debugger = CriticalWaitingTimeDebugger()
    debugger.run_critical_tests()