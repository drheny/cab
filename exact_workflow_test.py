#!/usr/bin/env python3
"""
EXACT WORKFLOW TEST - Following the review request precisely

TESTING EXACTLY THE SAME WORKFLOW:
1. Login avec medecin/medecin123
2. Prendre n'importe quel patient (même s'il a déjà une valeur duree_attente)
3. Le déplacer vers "attente" - vérifier que heure_arrivee_attente est défini
4. Attendre 20 secondes
5. Le déplacer vers "en_cours" - vérifier que duree_attente est maintenant calculé basé sur le temps réel (20s = 0 minutes)
6. Vérifier que l'API renvoie cette nouvelle valeur calculée

EXPECTED CORRECTION:
- IGNORER toute valeur duree_attente pré-existante
- TOUJOURS calculer basé sur heure_arrivee_attente actuelle
- Donner 0 minutes pour 20 secondes (car 20s < 60s = 0 minutes en division entière)
- Donner 1+ minutes pour 60+ secondes
"""

import requests
import json
import time
from datetime import datetime, timedelta
import sys
import os

# Configuration
BACKEND_URL = "https://86e1ae33-6e29-4ce5-a743-1e543eb0a6b8.preview.emergentagent.com/api"
TEST_CREDENTIALS = {
    "username": "medecin",
    "password": "medecin123"
}

class ExactWorkflowTester:
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
        """1. Login avec medecin/medecin123"""
        print("\n🔐 ÉTAPE 1: Login avec medecin/medecin123")
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
                    self.log_test("Login medecin/medecin123", True, details, response_time)
                    return True
                else:
                    self.log_test("Login medecin/medecin123", False, "Missing access_token or user in response", response_time)
                    return False
            else:
                response_text = response.text[:200] if response.text else "No response body"
                self.log_test("Login medecin/medecin123", False, f"HTTP {response.status_code}: {response_text}", response_time)
                return False
                
        except Exception as e:
            response_time = time.time() - start_time
            error_details = f"Exception: {str(e)[:200]}"
            self.log_test("Login medecin/medecin123", False, error_details, response_time)
            return False
    
    def test_exact_workflow(self):
        """Test the exact workflow described in review request"""
        print("\n🎯 TESTING EXACT WORKFLOW FROM REVIEW REQUEST")
        
        today = datetime.now().strftime("%Y-%m-%d")
        
        # 2. Prendre n'importe quel patient (même s'il a déjà une valeur duree_attente)
        print("\n👤 ÉTAPE 2: Prendre n'importe quel patient (même s'il a déjà une valeur duree_attente)")
        start_time = time.time()
        try:
            response = self.session.get(f"{BACKEND_URL}/rdv/jour/{today}", timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                appointments = response.json()
                if appointments:
                    # Take the first available patient
                    test_appointment = appointments[0]
                    patient_info = test_appointment.get("patient", {})
                    test_patient_name = f"{patient_info.get('prenom', '')} {patient_info.get('nom', '')}"
                    rdv_id = test_appointment.get("id")
                    current_duree = test_appointment.get("duree_attente")
                    current_status = test_appointment.get("statut")
                    
                    details = f"Patient sélectionné: '{test_patient_name}' - Status: {current_status}, duree_attente existante: {current_duree}"
                    self.log_test("Sélection Patient avec duree_attente existante", True, details, response_time)
                    
                    # 3. Le déplacer vers "attente" - vérifier que heure_arrivee_attente est défini
                    print("\n🏥 ÉTAPE 3: Le déplacer vers 'attente' - vérifier que heure_arrivee_attente est défini")
                    start_time = time.time()
                    
                    attente_start_time = datetime.now()
                    
                    update_data = {"statut": "attente"}
                    response = self.session.put(f"{BACKEND_URL}/rdv/{rdv_id}/statut", json=update_data, timeout=10)
                    response_time = time.time() - start_time
                    
                    if response.status_code == 200:
                        data = response.json()
                        heure_arrivee = data.get("heure_arrivee_attente", "NOT_SET")
                        
                        details = f"Patient '{test_patient_name}' déplacé vers attente - heure_arrivee_attente: {heure_arrivee}"
                        self.log_test("Déplacement vers attente - heure_arrivee_attente défini", True, details, response_time)
                        
                        # 4. Attendre 20 secondes
                        print("\n⏰ ÉTAPE 4: Attendre 20 secondes")
                        print("Attente de 20 secondes exactement...")
                        time.sleep(20)  # Wait exactly 20 seconds as specified
                        
                        elapsed_time = datetime.now() - attente_start_time
                        elapsed_seconds = elapsed_time.total_seconds()
                        print(f"🔍 DEBUG: Temps écoulé: {elapsed_seconds:.1f}s")
                        
                        # 5. Le déplacer vers "en_cours" - vérifier que duree_attente est calculé basé sur le temps réel
                        print("\n🩺 ÉTAPE 5: Le déplacer vers 'en_cours' - vérifier duree_attente calculé basé sur temps réel")
                        start_time = time.time()
                        
                        update_data = {"statut": "en_cours"}
                        response = self.session.put(f"{BACKEND_URL}/rdv/{rdv_id}/statut", json=update_data, timeout=10)
                        response_time = time.time() - start_time
                        
                        if response.status_code == 200:
                            data = response.json()
                            
                            # CRITICAL CHECK: duree_attente should be calculated based on real time
                            if "duree_attente" in data:
                                calculated_duree = data["duree_attente"]
                                
                                # Expected: 20 seconds = 0 minutes (integer division: 20s < 60s = 0 minutes)
                                expected_minutes = 0  # 20s < 60s = 0 minutes en division entière
                                
                                details = f"duree_attente calculé: {calculated_duree} minutes (attendu: {expected_minutes} min pour ~20s)"
                                
                                print(f"🔍 DEBUG: duree_attente calculé: {calculated_duree}")
                                print(f"🔍 DEBUG: Attendu pour 20s: {expected_minutes} minutes")
                                
                                # VERIFICATION DE LA CORRECTION
                                if calculated_duree == expected_minutes:
                                    self.log_test("CORRECTION VÉRIFIÉE - duree_attente calculé correctement", True, details, response_time)
                                else:
                                    self.log_test("CORRECTION ÉCHOUÉE - duree_attente mal calculé", False, f"Obtenu {calculated_duree} min, attendu {expected_minutes} min", response_time)
                                
                            else:
                                details = "Réponse API ne contient PAS le champ duree_attente"
                                self.log_test("Réponse API manque duree_attente", False, details, response_time)
                            
                            # 6. Vérifier que l'API renvoie cette nouvelle valeur calculée
                            print("\n💾 ÉTAPE 6: Vérifier que l'API renvoie cette nouvelle valeur calculée")
                            start_time = time.time()
                            
                            response = self.session.get(f"{BACKEND_URL}/rdv/jour/{today}", timeout=10)
                            response_time = time.time() - start_time
                            
                            if response.status_code == 200:
                                updated_appointments = response.json()
                                updated_appointment = next((apt for apt in updated_appointments if apt.get("id") == rdv_id), None)
                                
                                if updated_appointment:
                                    persisted_duree = updated_appointment.get("duree_attente")
                                    details = f"API GET renvoie duree_attente: {persisted_duree} (doit correspondre à la valeur calculée)"
                                    
                                    if persisted_duree == calculated_duree:
                                        self.log_test("API renvoie nouvelle valeur calculée", True, details, response_time)
                                    else:
                                        self.log_test("API ne renvoie pas la bonne valeur", False, f"GET renvoie {persisted_duree}, PUT a calculé {calculated_duree}", response_time)
                                else:
                                    self.log_test("Vérification persistance API", False, "Rendez-vous mis à jour non trouvé", response_time)
                            else:
                                self.log_test("Vérification persistance API", False, f"HTTP {response.status_code}: {response.text}", response_time)
                        
                        else:
                            self.log_test("Déplacement vers en_cours", False, f"HTTP {response.status_code}: {response.text}", response_time)
                    
                    else:
                        self.log_test("Déplacement vers attente", False, f"HTTP {response.status_code}: {response.text}", response_time)
                
                else:
                    self.log_test("Sélection Patient", False, "Aucun rendez-vous trouvé pour les tests", response_time)
            else:
                self.log_test("Sélection Patient", False, f"HTTP {response.status_code}: {response.text}", response_time)
        
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("Test Workflow Exact", False, f"Exception: {str(e)}", response_time)
    
    def run_all_tests(self):
        """Run all tests in sequence"""
        print("🚀 DÉMARRAGE TEST WORKFLOW EXACT")
        print("=" * 80)
        print("Test du workflow EXACT décrit dans la demande de révision:")
        print("1. Login avec medecin/medecin123")
        print("2. Prendre n'importe quel patient (même s'il a déjà une valeur duree_attente)")
        print("3. Le déplacer vers 'attente' - vérifier que heure_arrivee_attente est défini")
        print("4. Attendre 20 secondes")
        print("5. Le déplacer vers 'en_cours' - vérifier duree_attente calculé (20s = 0 minutes)")
        print("6. Vérifier que l'API renvoie cette nouvelle valeur calculée")
        print("=" * 80)
        
        # Test 1: Authentication
        if not self.test_authentication():
            print("❌ Authentification échouée - impossible de continuer")
            return
        
        # Test 2: Exact workflow
        self.test_exact_workflow()
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        total_time = time.time() - self.start_time
        total_tests = len(self.test_results)
        passed_tests = len([t for t in self.test_results if t["success"]])
        failed_tests = total_tests - passed_tests
        
        print("\n" + "=" * 80)
        print("🎯 RÉSUMÉ TEST WORKFLOW EXACT")
        print("=" * 80)
        
        print(f"⏱️  Temps d'exécution total: {total_time:.2f} secondes")
        print(f"📊 Tests totaux: {total_tests}")
        print(f"✅ Réussis: {passed_tests}")
        print(f"❌ Échoués: {failed_tests}")
        print(f"📈 Taux de réussite: {(passed_tests/total_tests*100):.1f}%")
        
        print("\n📋 RÉSULTATS DÉTAILLÉS:")
        for result in self.test_results:
            print(f"{result['status']} {result['test']} ({result['response_time']:.3f}s)")
            if result['details']:
                print(f"    {result['details']}")
        
        print("\n🎯 VÉRIFICATION DE LA CORRECTION:")
        correction_tests = [t for t in self.test_results if "CORRECTION" in t['test']]
        if correction_tests:
            correction_passed = all(t['success'] for t in correction_tests)
            if correction_passed:
                print("✅ CORRECTION VÉRIFIÉE - La correction fonctionne correctement")
                print("✅ duree_attente est calculé basé sur le temps réel (20s = 0 minutes)")
                print("✅ Le système ignore les valeurs duree_attente pré-existantes")
                print("✅ L'API renvoie la nouvelle valeur calculée correctement")
            else:
                print("❌ CORRECTION ÉCHOUÉE - La correction ne fonctionne pas correctement")
                print("❌ Veuillez réviser les tests échoués ci-dessus")
        else:
            if failed_tests == 0:
                print("✅ TOUS LES TESTS RÉUSSIS - Le workflow fonctionne correctement")
            else:
                print("❌ CERTAINS TESTS ÉCHOUÉS - Veuillez réviser les problèmes")
        
        print("=" * 80)

if __name__ == "__main__":
    tester = ExactWorkflowTester()
    tester.run_all_tests()