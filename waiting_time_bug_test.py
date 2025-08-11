#!/usr/bin/env python3
"""
SPECIFIC WAITING TIME RESET BUG TESTING
Testing the exact scenario described in the review request:

BUG REPORT: "Le compteur d'attente lors de la transition 'salle d'attente' → 'en consultation' 
est remis à 0 min au lieu de préserver la durée."

EXACT TEST SCENARIO:
1. Login avec medecin/medecin123
2. Prendre un patient et le mettre en statut "attente" (cela définit heure_arrivee_attente)
3. Attendre au moins 10 secondes pour simuler du temps en attente
4. IMPORTANT: Imprimer la durée_attente AVANT le changement de statut (devrait être null)
5. Changer le statut de "attente" à "en_cours" (consultation)
6. IMPORTANT: Vérifier immédiatement après le changement quelle est la durée_attente calculée
7. Tester si la durée_attente est correctement calculée ou si elle est 0

FOCUS: Vérifier particulièrement:
- La logique pour calculer duree_attente quand on va vers "en_cours"
- Y a-t-il un conflit entre mes deux logiques de calcul?
- Le timing du calcul - est-ce que ça arrive au bon moment?
- Les logs DEBUG pour voir quelle logique s'exécute
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

class WaitingTimeBugTester:
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
        """Step 2: Prendre un patient pour le test"""
        print("\n👥 STEP 2: Prendre un patient et le mettre en statut 'attente'")
        
        today = datetime.now().strftime("%Y-%m-%d")
        start_time = time.time()
        
        try:
            response = self.session.get(f"{BACKEND_URL}/rdv/jour/{today}", timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                appointments = response.json()
                if appointments:
                    # Find a suitable test patient
                    test_appointment = None
                    for apt in appointments:
                        if apt.get("statut") in ["programme", "attente", "termine", "en_cours"]:
                            test_appointment = apt
                            break
                    
                    if not test_appointment:
                        test_appointment = appointments[0]
                    
                    patient_info = test_appointment.get("patient", {})
                    test_patient_name = f"{patient_info.get('prenom', '')} {patient_info.get('nom', '')}"
                    rdv_id = test_appointment.get("id")
                    current_status = test_appointment.get("statut")
                    current_duree = test_appointment.get("duree_attente")
                    current_heure_arrivee = test_appointment.get("heure_arrivee_attente")
                    
                    details = f"Selected patient: '{test_patient_name}' - Current status: {current_status}, duree_attente: {current_duree}, heure_arrivee_attente: {current_heure_arrivee}"
                    self.log_test("Patient Selection", True, details, response_time)
                    
                    return {
                        "rdv_id": rdv_id,
                        "patient_name": test_patient_name,
                        "current_status": current_status,
                        "current_duree": current_duree,
                        "current_heure_arrivee": current_heure_arrivee
                    }
                else:
                    self.log_test("Patient Selection", False, "No appointments found for today", response_time)
                    return None
            else:
                self.log_test("Patient Selection", False, f"HTTP {response.status_code}: {response.text}", response_time)
                return None
                
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("Patient Selection", False, f"Exception: {str(e)}", response_time)
            return None
    
    def move_to_attente(self, patient_data):
        """Step 3: Mettre le patient en statut 'attente' (définit heure_arrivee_attente)"""
        print("\n🏥 STEP 3: Mettre le patient en statut 'attente' (définit heure_arrivee_attente)")
        
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
    
    def wait_for_duration(self, seconds=10):
        """Step 4: Attendre au moins 10 secondes pour simuler du temps en attente"""
        print(f"\n⏰ STEP 4: Attendre {seconds} secondes pour simuler du temps en attente")
        
        print(f"Waiting {seconds} seconds to simulate waiting time...")
        time.sleep(seconds)
        
        self.log_test("Waiting Time Simulation", True, f"Waited {seconds} seconds", 0)
        return True
    
    def check_duree_before_change(self, patient_data):
        """Step 5: IMPORTANT - Imprimer la durée_attente AVANT le changement de statut"""
        print("\n🔍 STEP 5: IMPORTANT - Vérifier la durée_attente AVANT le changement de statut")
        
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
                    
                    details = f"AVANT changement - Patient '{patient_name}': statut={statut}, duree_attente={duree_attente_before}, heure_arrivee_attente={heure_arrivee_attente}"
                    self.log_test("Duree_Attente BEFORE Status Change", True, details, response_time)
                    
                    return {
                        "success": True,
                        "duree_attente_before": duree_attente_before,
                        "heure_arrivee_attente": heure_arrivee_attente,
                        "statut_before": statut
                    }
                else:
                    self.log_test("Duree_Attente BEFORE Status Change", False, "Appointment not found", response_time)
                    return {"success": False}
            else:
                self.log_test("Duree_Attente BEFORE Status Change", False, f"HTTP {response.status_code}: {response.text}", response_time)
                return {"success": False}
                
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("Duree_Attente BEFORE Status Change", False, f"Exception: {str(e)}", response_time)
            return {"success": False}
    
    def move_to_en_cours(self, patient_data, attente_data):
        """Step 6: CRITICAL - Changer le statut de 'attente' à 'en_cours' et vérifier duree_attente"""
        print("\n🩺 STEP 6: CRITICAL - Changer le statut de 'attente' à 'en_cours' (consultation)")
        
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
                
                # CRITICAL CHECK: Vérifier immédiatement après le changement quelle est la durée_attente calculée
                duree_attente_after = data.get("duree_attente", "NOT_PROVIDED_IN_RESPONSE")
                heure_arrivee_attente = data.get("heure_arrivee_attente", "NOT_PROVIDED")
                statut_after = data.get("statut", "NOT_PROVIDED")
                
                # Calculate expected waiting time
                time_diff = consultation_start_time - attente_start_time
                expected_minutes = int(time_diff.total_seconds() / 60)
                
                details = f"APRÈS changement - Patient '{patient_name}': statut={statut_after}, duree_attente={duree_attente_after} (expected: ~{expected_minutes} min), heure_arrivee={heure_arrivee_attente}"
                self.log_test("Status Change to En_Cours - API Response", True, details, response_time)
                
                # CRITICAL BUG CHECK: Est-ce que la durée_attente est correctement calculée ou si elle est 0?
                if duree_attente_after == 0:
                    self.log_test("🚨 BUG DETECTED - Duree_Attente Reset to 0", False, f"duree_attente was reset to 0 instead of calculated duration (~{expected_minutes} min)", 0)
                elif duree_attente_after is None:
                    self.log_test("🚨 BUG DETECTED - Duree_Attente is NULL", False, f"duree_attente is NULL instead of calculated duration (~{expected_minutes} min)", 0)
                elif duree_attente_after == "NOT_PROVIDED_IN_RESPONSE":
                    self.log_test("⚠️ API Response Missing duree_attente", False, "API response does not include duree_attente field", 0)
                elif isinstance(duree_attente_after, (int, float)) and duree_attente_after > 0:
                    if abs(duree_attente_after - expected_minutes) <= 1:  # Allow 1 minute tolerance
                        self.log_test("✅ CORRECT - Duree_Attente Calculated Properly", True, f"duree_attente={duree_attente_after} min matches expected ~{expected_minutes} min", 0)
                    else:
                        self.log_test("⚠️ UNEXPECTED - Duree_Attente Calculation", True, f"duree_attente={duree_attente_after} min differs from expected ~{expected_minutes} min", 0)
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
    
    def verify_database_state(self, patient_data, en_cours_data):
        """Step 7: Vérifier l'état final dans la base de données"""
        print("\n💾 STEP 7: Vérifier l'état final dans la base de données")
        
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
                    
                    details = f"DATABASE FINAL STATE - Patient '{patient_name}': statut={final_statut}, duree_attente={final_duree_attente}, heure_arrivee={final_heure_arrivee}"
                    self.log_test("Database Final State", True, details, response_time)
                    
                    # Final bug verification
                    if final_duree_attente == 0:
                        self.log_test("🚨 FINAL BUG CONFIRMATION - Database has duree_attente=0", False, f"Database shows duree_attente=0 instead of ~{expected_minutes} min", 0)
                    elif final_duree_attente is None:
                        self.log_test("🚨 FINAL BUG CONFIRMATION - Database has duree_attente=NULL", False, f"Database shows duree_attente=NULL instead of ~{expected_minutes} min", 0)
                    elif isinstance(final_duree_attente, (int, float)) and final_duree_attente > 0:
                        self.log_test("✅ FINAL VERIFICATION - Database has correct duree_attente", True, f"Database correctly stores duree_attente={final_duree_attente} min", 0)
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
    
    def run_bug_test(self):
        """Run the complete bug test scenario"""
        print("🚨 TESTING SPECIFIC WAITING TIME RESET BUG")
        print("=" * 80)
        print("BUG: Le compteur d'attente lors de la transition 'salle d'attente' → 'en consultation'")
        print("     est remis à 0 min au lieu de préserver la durée.")
        print("=" * 80)
        
        # Step 1: Authentication
        if not self.authenticate():
            print("❌ Authentication failed, cannot continue test")
            return False
        
        # Step 2: Get test patient
        patient_data = self.get_test_patient()
        if not patient_data:
            print("❌ Could not find test patient, cannot continue test")
            return False
        
        # Step 3: Move to attente
        attente_data = self.move_to_attente(patient_data)
        if not attente_data["success"]:
            print("❌ Could not move patient to attente, cannot continue test")
            return False
        
        # Step 4: Wait for duration
        self.wait_for_duration(10)  # Wait 10 seconds as requested
        
        # Step 5: Check duree_attente before change
        before_data = self.check_duree_before_change(patient_data)
        if not before_data["success"]:
            print("❌ Could not check state before change")
            return False
        
        # Step 6: Move to en_cours (CRITICAL TEST)
        en_cours_data = self.move_to_en_cours(patient_data, attente_data)
        if not en_cours_data["success"]:
            print("❌ Could not move patient to en_cours, cannot complete test")
            return False
        
        # Step 7: Verify final database state
        final_data = self.verify_database_state(patient_data, en_cours_data)
        
        # Summary
        self.print_summary()
        
        return True
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 80)
        print("🔍 WAITING TIME BUG TEST SUMMARY")
        print("=" * 80)
        
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
        bug_detected = any("BUG DETECTED" in result['test'] for result in self.test_results if not result['success'])
        bug_fixed = any("CORRECT" in result['test'] or "VERIFICATION" in result['test'] for result in self.test_results if result['success'])
        
        print("\n🚨 BUG ANALYSIS:")
        if bug_detected:
            print("❌ BUG CONFIRMED: Waiting time counter is being reset to 0 during attente → en_cours transition")
        elif bug_fixed:
            print("✅ BUG FIXED: Waiting time counter is correctly calculated during attente → en_cours transition")
        else:
            print("⚠️ BUG STATUS UNCLEAR: Need more investigation")
        
        print("=" * 80)

def main():
    """Main function"""
    tester = WaitingTimeBugTester()
    tester.run_bug_test()

if __name__ == "__main__":
    main()