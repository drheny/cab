#!/usr/bin/env python3
"""
SPECIFIC WAITING TIME RESET BUG TESTING - FRESH PATIENT
Testing with a patient that has duree_attente=null to trigger the calculation logic

This test will:
1. Find a patient with duree_attente=null or create a fresh scenario
2. Move them to "attente" status 
3. Wait 10+ seconds
4. Move to "en_cours" and check if duree_attente is calculated correctly
5. Look for conflicts between the two calculation logics in the backend
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

class FreshWaitingTimeBugTester:
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
        """Step 1: Login avec medecin/medecin123"""
        print("\n🔐 STEP 1: Login avec medecin/medecin123")
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
    
    def find_fresh_patient(self):
        """Step 2: Find a patient with duree_attente=null or reset one"""
        print("\n👥 STEP 2: Find a patient with duree_attente=null for fresh testing")
        
        today = datetime.now().strftime("%Y-%m-%d")
        start_time = time.time()
        
        try:
            response = self.session.get(f"{BACKEND_URL}/rdv/jour/{today}", timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                appointments = response.json()
                if appointments:
                    # Look for a patient with duree_attente=null or 0
                    fresh_appointment = None
                    for apt in appointments:
                        duree_attente = apt.get("duree_attente")
                        if duree_attente is None or duree_attente == 0:
                            fresh_appointment = apt
                            break
                    
                    # If no fresh patient found, use the first one and reset it
                    if not fresh_appointment:
                        fresh_appointment = appointments[0]
                        print("No patient with duree_attente=null found, will reset first patient")
                    
                    patient_info = fresh_appointment.get("patient", {})
                    test_patient_name = f"{patient_info.get('prenom', '')} {patient_info.get('nom', '')}"
                    rdv_id = fresh_appointment.get("id")
                    current_status = fresh_appointment.get("statut")
                    current_duree = fresh_appointment.get("duree_attente")
                    current_heure_arrivee = fresh_appointment.get("heure_arrivee_attente")
                    
                    details = f"Selected patient: '{test_patient_name}' - Current status: {current_status}, duree_attente: {current_duree}, heure_arrivee_attente: {current_heure_arrivee}"
                    self.log_test("Fresh Patient Selection", True, details, response_time)
                    
                    return {
                        "rdv_id": rdv_id,
                        "patient_name": test_patient_name,
                        "current_status": current_status,
                        "current_duree": current_duree,
                        "current_heure_arrivee": current_heure_arrivee,
                        "needs_reset": current_duree is not None and current_duree != 0
                    }
                else:
                    self.log_test("Fresh Patient Selection", False, "No appointments found for today", response_time)
                    return None
            else:
                self.log_test("Fresh Patient Selection", False, f"HTTP {response.status_code}: {response.text}", response_time)
                return None
                
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("Fresh Patient Selection", False, f"Exception: {str(e)}", response_time)
            return None
    
    def reset_patient_duree_attente(self, patient_data):
        """Step 3: Reset patient's duree_attente to null for fresh testing"""
        if not patient_data.get("needs_reset"):
            self.log_test("Patient Reset", True, "Patient already has duree_attente=null, no reset needed", 0)
            return True
        
        print("\n🔄 STEP 3: Reset patient's duree_attente to null for fresh testing")
        
        rdv_id = patient_data["rdv_id"]
        patient_name = patient_data["patient_name"]
        
        # First, move to a different status to clear the waiting time
        start_time = time.time()
        
        try:
            # Move to "programme" status to reset
            update_data = {"statut": "programme"}
            response = self.session.put(f"{BACKEND_URL}/rdv/{rdv_id}/statut", json=update_data, timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                details = f"Reset '{patient_name}' to programme status to clear duree_attente"
                self.log_test("Patient Reset to Programme", True, details, response_time)
                return True
            else:
                self.log_test("Patient Reset to Programme", False, f"HTTP {response.status_code}: {response.text}", response_time)
                return False
                
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("Patient Reset to Programme", False, f"Exception: {str(e)}", response_time)
            return False
    
    def move_to_attente_fresh(self, patient_data):
        """Step 4: Move patient to 'attente' status with fresh duree_attente"""
        print("\n🏥 STEP 4: Move patient to 'attente' status (should set heure_arrivee_attente)")
        
        rdv_id = patient_data["rdv_id"]
        patient_name = patient_data["patient_name"]
        
        start_time = time.time()
        attente_start_time = datetime.now()
        
        try:
            update_data = {"statut": "attente"}
            response = self.session.put(f"{BACKEND_URL}/rdv/{rdv_id}/statut", json=update_data, timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                heure_arrivee = data.get("heure_arrivee_attente", "NOT_SET")
                duree_attente = data.get("duree_attente", "NOT_PROVIDED")
                
                details = f"Moved '{patient_name}' to attente - heure_arrivee_attente: {heure_arrivee}, duree_attente: {duree_attente}"
                self.log_test("Move to Attente Status (Fresh)", True, details, response_time)
                
                return {
                    "success": True,
                    "attente_start_time": attente_start_time,
                    "heure_arrivee_attente": heure_arrivee,
                    "duree_attente_after_attente": duree_attente
                }
            else:
                self.log_test("Move to Attente Status (Fresh)", False, f"HTTP {response.status_code}: {response.text}", response_time)
                return {"success": False}
                
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("Move to Attente Status (Fresh)", False, f"Exception: {str(e)}", response_time)
            return {"success": False}
    
    def wait_for_duration(self, seconds=15):
        """Step 5: Wait for a meaningful duration"""
        print(f"\n⏰ STEP 5: Wait {seconds} seconds to simulate meaningful waiting time")
        
        print(f"Waiting {seconds} seconds to simulate waiting time...")
        time.sleep(seconds)
        
        self.log_test("Waiting Time Simulation", True, f"Waited {seconds} seconds", 0)
        return True
    
    def check_duree_before_change(self, patient_data):
        """Step 6: Check duree_attente BEFORE changing to en_cours"""
        print("\n🔍 STEP 6: IMPORTANT - Check duree_attente BEFORE changing to en_cours")
        
        rdv_id = patient_data["rdv_id"]
        patient_name = patient_data["patient_name"]
        today = datetime.now().strftime("%Y-%m-%d")
        
        start_time = time.time()
        
        try:
            response = self.session.get(f"{BACKEND_URL}/rdv/jour/{today}", timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                appointments = response.json()
                current_appointment = next((apt for apt in appointments if apt.get("id") == rdv_id), None)
                
                if current_appointment:
                    duree_attente_before = current_appointment.get("duree_attente")
                    heure_arrivee_attente = current_appointment.get("heure_arrivee_attente")
                    statut = current_appointment.get("statut")
                    
                    details = f"BEFORE en_cours - Patient '{patient_name}': statut={statut}, duree_attente={duree_attente_before} (should be null), heure_arrivee_attente={heure_arrivee_attente}"
                    self.log_test("Duree_Attente BEFORE En_Cours Change", True, details, response_time)
                    
                    # Critical check: duree_attente should be null before calculation
                    if duree_attente_before is None:
                        self.log_test("✅ CORRECT - Duree_Attente is NULL before calculation", True, "duree_attente is null as expected", 0)
                    else:
                        self.log_test("⚠️ UNEXPECTED - Duree_Attente already has value", True, f"duree_attente={duree_attente_before} (expected null)", 0)
                    
                    return {
                        "success": True,
                        "duree_attente_before": duree_attente_before,
                        "heure_arrivee_attente": heure_arrivee_attente,
                        "statut_before": statut
                    }
                else:
                    self.log_test("Duree_Attente BEFORE En_Cours Change", False, "Appointment not found", response_time)
                    return {"success": False}
            else:
                self.log_test("Duree_Attente BEFORE En_Cours Change", False, f"HTTP {response.status_code}: {response.text}", response_time)
                return {"success": False}
                
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("Duree_Attente BEFORE En_Cours Change", False, f"Exception: {str(e)}", response_time)
            return {"success": False}
    
    def move_to_en_cours_and_analyze(self, patient_data, attente_data):
        """Step 7: CRITICAL - Move to en_cours and analyze the calculation logic"""
        print("\n🩺 STEP 7: CRITICAL - Move to en_cours and analyze duree_attente calculation")
        
        rdv_id = patient_data["rdv_id"]
        patient_name = patient_data["patient_name"]
        attente_start_time = attente_data["attente_start_time"]
        
        start_time = time.time()
        consultation_start_time = datetime.now()
        
        try:
            update_data = {"statut": "en_cours"}
            response = self.session.put(f"{BACKEND_URL}/rdv/{rdv_id}/statut", json=update_data, timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                # CRITICAL ANALYSIS: Check what duree_attente was calculated
                duree_attente_after = data.get("duree_attente", "NOT_PROVIDED_IN_RESPONSE")
                heure_arrivee_attente = data.get("heure_arrivee_attente", "NOT_PROVIDED")
                statut_after = data.get("statut", "NOT_PROVIDED")
                
                # Calculate expected waiting time
                time_diff = consultation_start_time - attente_start_time
                expected_minutes = int(time_diff.total_seconds() / 60)
                
                details = f"AFTER en_cours - Patient '{patient_name}': statut={statut_after}, duree_attente={duree_attente_after} (expected: ~{expected_minutes} min)"
                self.log_test("Status Change to En_Cours - API Response", True, details, response_time)
                
                # CRITICAL BUG ANALYSIS
                if duree_attente_after == 0:
                    self.log_test("🚨 BUG CONFIRMED - Duree_Attente Reset to 0", False, f"duree_attente was reset to 0 instead of calculated duration (~{expected_minutes} min)", 0)
                elif duree_attente_after is None:
                    self.log_test("🚨 BUG CONFIRMED - Duree_Attente is NULL", False, f"duree_attente is NULL instead of calculated duration (~{expected_minutes} min)", 0)
                elif duree_attente_after == "NOT_PROVIDED_IN_RESPONSE":
                    self.log_test("⚠️ API Response Missing duree_attente", False, "API response does not include duree_attente field", 0)
                elif isinstance(duree_attente_after, (int, float)) and duree_attente_after > 0:
                    if abs(duree_attente_after - expected_minutes) <= 1:  # Allow 1 minute tolerance
                        self.log_test("✅ CALCULATION WORKING - Duree_Attente Calculated Correctly", True, f"duree_attente={duree_attente_after} min matches expected ~{expected_minutes} min", 0)
                    else:
                        self.log_test("⚠️ CALCULATION ISSUE - Duree_Attente Unexpected", True, f"duree_attente={duree_attente_after} min differs from expected ~{expected_minutes} min", 0)
                else:
                    self.log_test("⚠️ UNEXPECTED - Duree_Attente Value", True, f"duree_attente has unexpected value: {duree_attente_after}", 0)
                
                return {
                    "success": True,
                    "duree_attente_after": duree_attente_after,
                    "expected_minutes": expected_minutes,
                    "consultation_start_time": consultation_start_time
                }
            else:
                self.log_test("Status Change to En_Cours", False, f"HTTP {response.status_code}: {response.text}", response_time)
                return {"success": False}
                
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("Status Change to En_Cours", False, f"Exception: {str(e)}", response_time)
            return {"success": False}
    
    def verify_final_database_state(self, patient_data, en_cours_data):
        """Step 8: Verify final database state and check for logic conflicts"""
        print("\n💾 STEP 8: Verify final database state and check for logic conflicts")
        
        rdv_id = patient_data["rdv_id"]
        patient_name = patient_data["patient_name"]
        expected_minutes = en_cours_data.get("expected_minutes", 0)
        today = datetime.now().strftime("%Y-%m-%d")
        
        start_time = time.time()
        
        try:
            response = self.session.get(f"{BACKEND_URL}/rdv/jour/{today}", timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                appointments = response.json()
                final_appointment = next((apt for apt in appointments if apt.get("id") == rdv_id), None)
                
                if final_appointment:
                    final_duree_attente = final_appointment.get("duree_attente")
                    final_heure_arrivee = final_appointment.get("heure_arrivee_attente")
                    final_statut = final_appointment.get("statut")
                    
                    details = f"FINAL DATABASE STATE - Patient '{patient_name}': statut={final_statut}, duree_attente={final_duree_attente}, heure_arrivee={final_heure_arrivee}"
                    self.log_test("Database Final State", True, details, response_time)
                    
                    # Final bug verification
                    if final_duree_attente == 0:
                        self.log_test("🚨 FINAL BUG CONFIRMATION - Database shows duree_attente=0", False, f"Database shows duree_attente=0 instead of ~{expected_minutes} min", 0)
                    elif final_duree_attente is None:
                        self.log_test("🚨 FINAL BUG CONFIRMATION - Database shows duree_attente=NULL", False, f"Database shows duree_attente=NULL instead of ~{expected_minutes} min", 0)
                    elif isinstance(final_duree_attente, (int, float)) and final_duree_attente > 0:
                        if abs(final_duree_attente - expected_minutes) <= 1:
                            self.log_test("✅ FINAL VERIFICATION - Database has correct duree_attente", True, f"Database correctly stores duree_attente={final_duree_attente} min", 0)
                        else:
                            self.log_test("⚠️ FINAL STATE - Duree_attente calculation discrepancy", True, f"Database has duree_attente={final_duree_attente} min, expected ~{expected_minutes} min", 0)
                    else:
                        self.log_test("⚠️ FINAL STATE - Unexpected duree_attente value", True, f"Database has unexpected duree_attente: {final_duree_attente}", 0)
                    
                    return {
                        "success": True,
                        "final_duree_attente": final_duree_attente,
                        "final_statut": final_statut,
                        "final_heure_arrivee": final_heure_arrivee
                    }
                else:
                    self.log_test("Database Final State", False, "Appointment not found in database", response_time)
                    return {"success": False}
            else:
                self.log_test("Database Final State", False, f"HTTP {response.status_code}: {response.text}", response_time)
                return {"success": False}
                
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("Database Final State", False, f"Exception: {str(e)}", response_time)
            return {"success": False}
    
    def run_fresh_bug_test(self):
        """Run the complete fresh bug test scenario"""
        print("🚨 TESTING SPECIFIC WAITING TIME RESET BUG - FRESH PATIENT SCENARIO")
        print("=" * 90)
        print("BUG: Le compteur d'attente lors de la transition 'salle d'attente' → 'en consultation'")
        print("     est remis à 0 min au lieu de préserver la durée.")
        print("FOCUS: Testing with fresh patient (duree_attente=null) to trigger calculation logic")
        print("=" * 90)
        
        # Step 1: Authentication
        if not self.authenticate():
            print("❌ Authentication failed, cannot continue test")
            return False
        
        # Step 2: Find fresh patient
        patient_data = self.find_fresh_patient()
        if not patient_data:
            print("❌ Could not find test patient, cannot continue test")
            return False
        
        # Step 3: Reset patient if needed
        if not self.reset_patient_duree_attente(patient_data):
            print("❌ Could not reset patient, cannot continue test")
            return False
        
        # Step 4: Move to attente
        attente_data = self.move_to_attente_fresh(patient_data)
        if not attente_data["success"]:
            print("❌ Could not move patient to attente, cannot continue test")
            return False
        
        # Step 5: Wait for meaningful duration
        self.wait_for_duration(15)  # Wait 15 seconds for meaningful test
        
        # Step 6: Check duree_attente before change
        before_data = self.check_duree_before_change(patient_data)
        if not before_data["success"]:
            print("❌ Could not check state before change")
            return False
        
        # Step 7: Move to en_cours (CRITICAL TEST)
        en_cours_data = self.move_to_en_cours_and_analyze(patient_data, attente_data)
        if not en_cours_data["success"]:
            print("❌ Could not move patient to en_cours, cannot complete test")
            return False
        
        # Step 8: Verify final database state
        final_data = self.verify_final_database_state(patient_data, en_cours_data)
        
        # Summary
        self.print_summary()
        
        return True
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 90)
        print("🔍 FRESH WAITING TIME BUG TEST SUMMARY")
        print("=" * 90)
        
        total_tests = len(self.test_results)
        passed_tests = len([t for t in self.test_results if t["success"]])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        print("\n📋 DETAILED RESULTS:")
        for result in self.test_results:
            print(f"{result['status']} {result['test']}")
            if result['details']:
                print(f"    {result['details']}")
        
        # Bug analysis
        bug_detected = any("BUG CONFIRMED" in result['test'] for result in self.test_results if not result['success'])
        calculation_working = any("CALCULATION WORKING" in result['test'] for result in self.test_results if result['success'])
        
        print("\n🚨 BUG ANALYSIS:")
        if bug_detected:
            print("❌ BUG CONFIRMED: Waiting time counter is being reset to 0 during attente → en_cours transition")
            print("   This confirms the user's bug report about duree_attente being reset instead of calculated")
        elif calculation_working:
            print("✅ CALCULATION WORKING: Waiting time counter is correctly calculated during attente → en_cours transition")
            print("   The bug may have been fixed or occurs under different conditions")
        else:
            print("⚠️ BUG STATUS UNCLEAR: Need more investigation or different test conditions")
        
        print("=" * 90)

def main():
    """Main function"""
    tester = FreshWaitingTimeBugTester()
    tester.run_fresh_bug_test()

if __name__ == "__main__":
    main()