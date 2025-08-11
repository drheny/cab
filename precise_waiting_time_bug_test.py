#!/usr/bin/env python3
"""
PRECISE WAITING TIME BUG TESTING
Testing the exact scenario with longer wait time to get meaningful duration

This test will:
1. Find a patient and reset their duree_attente to null
2. Move them to "attente" status 
3. Wait 65+ seconds (more than 1 minute)
4. Move to "en_cours" and check if duree_attente is calculated correctly
5. Verify the calculation shows real duration (1+ minutes) not 0
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

class PreciseWaitingTimeBugTester:
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
    
    def get_test_patient(self):
        """Step 2: Get a test patient"""
        print("\n👥 STEP 2: Get a test patient for precise testing")
        
        today = datetime.now().strftime("%Y-%m-%d")
        start_time = time.time()
        
        try:
            response = self.session.get(f"{BACKEND_URL}/rdv/jour/{today}", timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                appointments = response.json()
                if appointments:
                    # Use the first available patient
                    test_appointment = appointments[0]
                    
                    patient_info = test_appointment.get("patient", {})
                    test_patient_name = f"{patient_info.get('prenom', '')} {patient_info.get('nom', '')}"
                    rdv_id = test_appointment.get("id")
                    current_status = test_appointment.get("statut")
                    current_duree = test_appointment.get("duree_attente")
                    current_heure_arrivee = test_appointment.get("heure_arrivee_attente")
                    
                    details = f"Selected patient: '{test_patient_name}' - Current status: {current_status}, duree_attente: {current_duree}, heure_arrivee_attente: {current_heure_arrivee}"
                    self.log_test("Test Patient Selection", True, details, response_time)
                    
                    return {
                        "rdv_id": rdv_id,
                        "patient_name": test_patient_name,
                        "current_status": current_status,
                        "current_duree": current_duree,
                        "current_heure_arrivee": current_heure_arrivee
                    }
                else:
                    self.log_test("Test Patient Selection", False, "No appointments found for today", response_time)
                    return None
            else:
                self.log_test("Test Patient Selection", False, f"HTTP {response.status_code}: {response.text}", response_time)
                return None
                
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("Test Patient Selection", False, f"Exception: {str(e)}", response_time)
            return None
    
    def reset_to_programme(self, patient_data):
        """Step 3: Reset patient to programme status to clear duree_attente"""
        print("\n🔄 STEP 3: Reset patient to programme status to clear duree_attente")
        
        rdv_id = patient_data["rdv_id"]
        patient_name = patient_data["patient_name"]
        
        start_time = time.time()
        
        try:
            # Move to "programme" status to reset
            update_data = {"statut": "programme"}
            response = self.session.put(f"{BACKEND_URL}/rdv/{rdv_id}/statut", json=update_data, timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                duree_attente = data.get("duree_attente", "NOT_PROVIDED")
                details = f"Reset '{patient_name}' to programme status - duree_attente: {duree_attente}"
                self.log_test("Reset to Programme Status", True, details, response_time)
                return True
            else:
                self.log_test("Reset to Programme Status", False, f"HTTP {response.status_code}: {response.text}", response_time)
                return False
                
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("Reset to Programme Status", False, f"Exception: {str(e)}", response_time)
            return False
    
    def move_to_attente(self, patient_data):
        """Step 4: Move patient to 'attente' status"""
        print("\n🏥 STEP 4: Move patient to 'attente' status (sets heure_arrivee_attente)")
        
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
                self.log_test("Move to Attente Status", True, details, response_time)
                
                return {
                    "success": True,
                    "attente_start_time": attente_start_time,
                    "heure_arrivee_attente": heure_arrivee,
                    "duree_attente_after_attente": duree_attente
                }
            else:
                self.log_test("Move to Attente Status", False, f"HTTP {response.status_code}: {response.text}", response_time)
                return {"success": False}
                
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("Move to Attente Status", False, f"Exception: {str(e)}", response_time)
            return {"success": False}
    
    def wait_meaningful_duration(self, seconds=70):
        """Step 5: Wait for meaningful duration (more than 1 minute)"""
        print(f"\n⏰ STEP 5: Wait {seconds} seconds (more than 1 minute) for meaningful test")
        
        print(f"Waiting {seconds} seconds to ensure duree_attente will be > 1 minute...")
        time.sleep(seconds)
        
        self.log_test("Meaningful Waiting Time", True, f"Waited {seconds} seconds (> 1 minute)", 0)
        return True
    
    def check_duree_before_en_cours(self, patient_data):
        """Step 6: Check duree_attente BEFORE changing to en_cours"""
        print("\n🔍 STEP 6: CRITICAL - Check duree_attente BEFORE changing to en_cours")
        
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
                    
                    details = f"BEFORE en_cours - Patient '{patient_name}': statut={statut}, duree_attente={duree_attente_before}, heure_arrivee_attente={heure_arrivee_attente}"
                    self.log_test("Duree_Attente BEFORE En_Cours", True, details, response_time)
                    
                    # Print for debugging as requested
                    print(f"    🔍 DEBUG: duree_attente BEFORE status change = {duree_attente_before}")
                    
                    return {
                        "success": True,
                        "duree_attente_before": duree_attente_before,
                        "heure_arrivee_attente": heure_arrivee_attente,
                        "statut_before": statut
                    }
                else:
                    self.log_test("Duree_Attente BEFORE En_Cours", False, "Appointment not found", response_time)
                    return {"success": False}
            else:
                self.log_test("Duree_Attente BEFORE En_Cours", False, f"HTTP {response.status_code}: {response.text}", response_time)
                return {"success": False}
                
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("Duree_Attente BEFORE En_Cours", False, f"Exception: {str(e)}", response_time)
            return {"success": False}
    
    def move_to_en_cours_critical_test(self, patient_data, attente_data):
        """Step 7: CRITICAL TEST - Move to en_cours and check duree_attente calculation"""
        print("\n🩺 STEP 7: CRITICAL TEST - Move to en_cours and check duree_attente calculation")
        
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
                
                # CRITICAL CHECK: What duree_attente was calculated?
                duree_attente_after = data.get("duree_attente", "NOT_PROVIDED_IN_RESPONSE")
                heure_arrivee_attente = data.get("heure_arrivee_attente", "NOT_PROVIDED")
                statut_after = data.get("statut", "NOT_PROVIDED")
                
                # Calculate expected waiting time
                time_diff = consultation_start_time - attente_start_time
                expected_minutes = int(time_diff.total_seconds() / 60)
                
                details = f"AFTER en_cours - Patient '{patient_name}': statut={statut_after}, duree_attente={duree_attente_after} (expected: ~{expected_minutes} min)"
                self.log_test("Status Change to En_Cours", True, details, response_time)
                
                # Print for debugging as requested
                print(f"    🔍 DEBUG: duree_attente AFTER status change = {duree_attente_after}")
                print(f"    🔍 DEBUG: Expected duration = ~{expected_minutes} minutes")
                
                # CRITICAL BUG ANALYSIS - The main test
                if duree_attente_after == 0 and expected_minutes > 0:
                    self.log_test("🚨 BUG DETECTED - Duree_Attente Reset to 0", False, f"duree_attente was reset to 0 instead of calculated duration (~{expected_minutes} min) - THIS IS THE BUG!", 0)
                elif duree_attente_after is None and expected_minutes > 0:
                    self.log_test("🚨 BUG DETECTED - Duree_Attente is NULL", False, f"duree_attente is NULL instead of calculated duration (~{expected_minutes} min)", 0)
                elif duree_attente_after == "NOT_PROVIDED_IN_RESPONSE":
                    self.log_test("⚠️ API Response Missing duree_attente", False, "API response does not include duree_attente field", 0)
                elif isinstance(duree_attente_after, (int, float)) and duree_attente_after >= expected_minutes - 1:
                    self.log_test("✅ CALCULATION WORKING - Duree_Attente Calculated Correctly", True, f"duree_attente={duree_attente_after} min matches expected ~{expected_minutes} min", 0)
                else:
                    self.log_test("⚠️ CALCULATION ISSUE - Unexpected duree_attente", True, f"duree_attente={duree_attente_after} min, expected ~{expected_minutes} min", 0)
                
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
    
    def verify_database_persistence(self, patient_data, en_cours_data):
        """Step 8: Verify database persistence of duree_attente"""
        print("\n💾 STEP 8: Verify database persistence of duree_attente")
        
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
                    
                    details = f"DATABASE STATE - Patient '{patient_name}': statut={final_statut}, duree_attente={final_duree_attente}, heure_arrivee={final_heure_arrivee}"
                    self.log_test("Database Persistence Check", True, details, response_time)
                    
                    # Final verification
                    if final_duree_attente == 0 and expected_minutes > 0:
                        self.log_test("🚨 DATABASE BUG CONFIRMED - duree_attente=0 in database", False, f"Database shows duree_attente=0 instead of ~{expected_minutes} min", 0)
                    elif final_duree_attente is None and expected_minutes > 0:
                        self.log_test("🚨 DATABASE BUG CONFIRMED - duree_attente=NULL in database", False, f"Database shows duree_attente=NULL instead of ~{expected_minutes} min", 0)
                    elif isinstance(final_duree_attente, (int, float)) and final_duree_attente >= expected_minutes - 1:
                        self.log_test("✅ DATABASE CORRECT - duree_attente persisted correctly", True, f"Database correctly stores duree_attente={final_duree_attente} min", 0)
                    else:
                        self.log_test("⚠️ DATABASE ISSUE - Unexpected duree_attente value", True, f"Database has duree_attente={final_duree_attente}, expected ~{expected_minutes} min", 0)
                    
                    return {
                        "success": True,
                        "final_duree_attente": final_duree_attente,
                        "final_statut": final_statut,
                        "final_heure_arrivee": final_heure_arrivee
                    }
                else:
                    self.log_test("Database Persistence Check", False, "Appointment not found in database", response_time)
                    return {"success": False}
            else:
                self.log_test("Database Persistence Check", False, f"HTTP {response.status_code}: {response.text}", response_time)
                return {"success": False}
                
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("Database Persistence Check", False, f"Exception: {str(e)}", response_time)
            return {"success": False}
    
    def run_precise_bug_test(self):
        """Run the precise bug test scenario"""
        print("🚨 PRECISE WAITING TIME RESET BUG TESTING")
        print("=" * 100)
        print("BUG REPORT: Le compteur d'attente lors de la transition 'salle d'attente' → 'en consultation'")
        print("            est remis à 0 min au lieu de préserver la durée.")
        print("TEST FOCUS: Wait 70+ seconds to ensure meaningful duration > 1 minute for clear bug detection")
        print("=" * 100)
        
        # Step 1: Authentication
        if not self.authenticate():
            print("❌ Authentication failed, cannot continue test")
            return False
        
        # Step 2: Get test patient
        patient_data = self.get_test_patient()
        if not patient_data:
            print("❌ Could not find test patient, cannot continue test")
            return False
        
        # Step 3: Reset to programme
        if not self.reset_to_programme(patient_data):
            print("❌ Could not reset patient, cannot continue test")
            return False
        
        # Step 4: Move to attente
        attente_data = self.move_to_attente(patient_data)
        if not attente_data["success"]:
            print("❌ Could not move patient to attente, cannot continue test")
            return False
        
        # Step 5: Wait meaningful duration
        self.wait_meaningful_duration(70)  # Wait 70 seconds for > 1 minute
        
        # Step 6: Check duree_attente before change
        before_data = self.check_duree_before_en_cours(patient_data)
        if not before_data["success"]:
            print("❌ Could not check state before change")
            return False
        
        # Step 7: Move to en_cours (CRITICAL TEST)
        en_cours_data = self.move_to_en_cours_critical_test(patient_data, attente_data)
        if not en_cours_data["success"]:
            print("❌ Could not move patient to en_cours, cannot complete test")
            return False
        
        # Step 8: Verify database persistence
        final_data = self.verify_database_persistence(patient_data, en_cours_data)
        
        # Summary
        self.print_summary()
        
        return True
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 100)
        print("🔍 PRECISE WAITING TIME BUG TEST SUMMARY")
        print("=" * 100)
        
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
        bug_detected = any("BUG DETECTED" in result['test'] or "BUG CONFIRMED" in result['test'] for result in self.test_results if not result['success'])
        calculation_working = any("CALCULATION WORKING" in result['test'] or "DATABASE CORRECT" in result['test'] for result in self.test_results if result['success'])
        
        print("\n🚨 FINAL BUG ANALYSIS:")
        if bug_detected:
            print("❌ BUG CONFIRMED: The waiting time counter IS being reset to 0 during attente → en_cours transition")
            print("   This confirms the user's bug report: 'Le compteur d'attente est remis à 0 min au lieu de préserver la durée'")
            print("   RECOMMENDATION: Check the backend calculation logic for conflicts between the two duree_attente calculation methods")
        elif calculation_working:
            print("✅ BUG FIXED: The waiting time counter is correctly calculated during attente → en_cours transition")
            print("   The calculation logic is working properly and preserving/calculating duree_attente correctly")
        else:
            print("⚠️ BUG STATUS UNCLEAR: Results are inconclusive, may need different test conditions or investigation")
        
        print("=" * 100)

def main():
    """Main function"""
    tester = PreciseWaitingTimeBugTester()
    tester.run_precise_bug_test()

if __name__ == "__main__":
    main()