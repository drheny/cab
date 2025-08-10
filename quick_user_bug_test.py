#!/usr/bin/env python3
"""
QUICK USER BUG TEST - 15 Second Scenario
Test the exact sequence described by the user with 15-second wait
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

class QuickUserBugTester:
    def __init__(self):
        self.session = requests.Session()
        # Disable SSL verification for testing environment
        self.session.verify = False
        # Disable SSL warnings
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        self.auth_token = None
        
    def authenticate(self):
        """Authenticate with the backend"""
        print("🔐 Authenticating...")
        try:
            response = self.session.post(
                f"{BACKEND_URL}/auth/login",
                json=TEST_CREDENTIALS,
                timeout=30,
                verify=False
            )
            
            if response.status_code == 200:
                data = response.json()
                if "access_token" in data:
                    self.auth_token = data["access_token"]
                    self.session.headers.update({
                        "Authorization": f"Bearer {self.auth_token}"
                    })
                    print("✅ Authentication successful")
                    return True
                else:
                    print("❌ Authentication failed - no access token")
                    return False
            else:
                print(f"❌ Authentication failed - HTTP {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Authentication error: {str(e)}")
            return False
    
    def test_user_bug_sequence(self):
        """Test the EXACT sequence described by the user"""
        print("\n🐛 TESTING USER'S EXACT BUG SEQUENCE")
        print("=" * 60)
        print("User reported: Le compteur se remet encore à zéro quand on passe de 'salle d'attente' à 'en consultation'")
        print("\nTesting EXACT sequence:")
        print("1. Login avec medecin/medecin123 ✅")
        print("2. Trouver un patient actuellement en consultation ou terminé")
        print("3. Le déplacer vers 'attente' (cela devrait définir heure_arrivee_attente)")
        print("4. Attendre exactement 15 secondes pour que du temps s'accumule")
        print("5. Déplacer de 'attente' vers 'en_cours'")
        print("6. VÉRIFIER IMMÉDIATEMENT: Quelle est la duree_attente stockée dans la base de données?")
        print("7. VÉRIFIER: Quelle valeur duree_attente l'API renvoie au frontend?")
        
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Step 2: Find a patient currently in consultation or terminated
        print("\n🔍 STEP 2: Trouver un patient actuellement en consultation ou terminé")
        try:
            response = self.session.get(f"{BACKEND_URL}/rdv/jour/{today}", timeout=10)
            
            if response.status_code == 200:
                appointments = response.json()
                
                # Look for patient in "en_cours" or "termine" status
                test_patient = None
                for apt in appointments:
                    if apt.get("statut") in ["en_cours", "termine"]:
                        test_patient = apt
                        break
                
                # If no en_cours/termine patient, use any patient
                if not test_patient and appointments:
                    test_patient = appointments[0]
                
                if test_patient:
                    patient_info = test_patient.get("patient", {})
                    patient_name = f"{patient_info.get('prenom', '')} {patient_info.get('nom', '')}"
                    rdv_id = test_patient.get("id")
                    current_status = test_patient.get("statut")
                    current_duree = test_patient.get("duree_attente")
                    
                    print(f"✅ Found patient: '{patient_name}' - Status: {current_status}, duree_attente: {current_duree}")
                    
                    # Step 3: Move to "attente" (should set heure_arrivee_attente)
                    print("\n🏥 STEP 3: Le déplacer vers 'attente' (cela devrait définir heure_arrivee_attente)")
                    
                    # Record the exact time we move to attente
                    attente_start_time = datetime.now()
                    print(f"⏰ Recording attente start time: {attente_start_time.strftime('%H:%M:%S')}")
                    
                    update_data = {"statut": "attente"}
                    response = self.session.put(f"{BACKEND_URL}/rdv/{rdv_id}/statut", json=update_data, timeout=10)
                    
                    if response.status_code == 200:
                        data = response.json()
                        heure_arrivee = data.get("heure_arrivee_attente", "NOT_SET")
                        duree_attente_after_attente = data.get("duree_attente", "NOT_PROVIDED")
                        
                        print(f"✅ Moved '{patient_name}' to attente")
                        print(f"   - heure_arrivee_attente: {heure_arrivee}")
                        print(f"   - duree_attente: {duree_attente_after_attente}")
                        
                        # Step 4: Wait EXACTLY 15 seconds
                        print("\n⏰ STEP 4: Attendre exactement 15 secondes pour que du temps s'accumule")
                        print("Waiting exactly 15 seconds...")
                        for i in range(15, 0, -1):
                            print(f"   {i} seconds remaining...", end='\r')
                            time.sleep(1)
                        print("   ✅ 15 seconds completed!")
                        
                        # Step 5: Move from "attente" to "en_cours"
                        print("\n🩺 STEP 5: Déplacer de 'attente' vers 'en_cours'")
                        
                        # Record the exact time we move to en_cours
                        en_cours_start_time = datetime.now()
                        print(f"⏰ Recording en_cours start time: {en_cours_start_time.strftime('%H:%M:%S')}")
                        
                        update_data = {"statut": "en_cours"}
                        response = self.session.put(f"{BACKEND_URL}/rdv/{rdv_id}/statut", json=update_data, timeout=10)
                        
                        if response.status_code == 200:
                            data = response.json()
                            
                            # Step 6 & 7: CRITICAL VERIFICATION
                            print("\n🔍 STEP 6 & 7: VÉRIFICATION CRITIQUE - duree_attente dans API et base de données")
                            
                            # Check API response
                            api_duree_attente = data.get("duree_attente", "NOT_PROVIDED")
                            api_heure_arrivee = data.get("heure_arrivee_attente", "NOT_PROVIDED")
                            
                            # Calculate expected duration (should be ~15 seconds / 60 = 0 or 1 minute)
                            time_diff = en_cours_start_time - attente_start_time
                            expected_seconds = int(time_diff.total_seconds())
                            expected_minutes = max(0, int(expected_seconds / 60))  # Should be 0 or 1
                            
                            print(f"📊 API Response Analysis:")
                            print(f"   - duree_attente: {api_duree_attente}")
                            print(f"   - heure_arrivee_attente: {api_heure_arrivee}")
                            print(f"   - Expected duration: ~{expected_minutes} min ({expected_seconds}s)")
                            
                            # Now check database state immediately
                            print("\n💾 VÉRIFICATION BASE DE DONNÉES IMMÉDIATE")
                            
                            response = self.session.get(f"{BACKEND_URL}/rdv/jour/{today}", timeout=10)
                            
                            if response.status_code == 200:
                                updated_appointments = response.json()
                                updated_appointment = next((apt for apt in updated_appointments if apt.get("id") == rdv_id), None)
                                
                                if updated_appointment:
                                    db_duree_attente = updated_appointment.get("duree_attente")
                                    db_heure_arrivee = updated_appointment.get("heure_arrivee_attente")
                                    db_status = updated_appointment.get("statut")
                                    
                                    print(f"📊 Database State Analysis:")
                                    print(f"   - Status: {db_status}")
                                    print(f"   - duree_attente: {db_duree_attente}")
                                    print(f"   - heure_arrivee_attente: {db_heure_arrivee}")
                                    
                                    # CRITICAL BUG ANALYSIS
                                    print("\n🚨 ANALYSE CRITIQUE DU BUG")
                                    print("=" * 50)
                                    
                                    # Check if duree_attente was reset to 0
                                    if db_duree_attente == 0 and expected_minutes >= 0:
                                        print("❌ BUG CONFIRMED: duree_attente reset to 0")
                                        print(f"   Expected: {expected_minutes} min ({expected_seconds}s)")
                                        print(f"   Actual: {db_duree_attente} min")
                                        print("   🐛 Le compteur se remet à zéro - BUG REPRODUCED!")
                                    elif db_duree_attente == expected_minutes:
                                        print("✅ BUG FIXED: duree_attente correctly calculated")
                                        print(f"   Expected: {expected_minutes} min")
                                        print(f"   Actual: {db_duree_attente} min")
                                    else:
                                        print("⚠️  UNEXPECTED: duree_attente has unexpected value")
                                        print(f"   Expected: {expected_minutes} min")
                                        print(f"   Actual: {db_duree_attente} min")
                                    
                                    # Check API vs Database consistency
                                    print(f"\n📊 API vs Database Consistency:")
                                    if api_duree_attente == db_duree_attente:
                                        print(f"✅ CONSISTENT: Both show {api_duree_attente} min")
                                    else:
                                        print(f"❌ INCONSISTENT: API shows {api_duree_attente}, Database shows {db_duree_attente}")
                                    
                                    # Final summary
                                    print("\n📋 RÉSUMÉ DE L'ANALYSE")
                                    print("=" * 50)
                                    print(f"Patient testé: {patient_name}")
                                    print(f"Temps d'attente réel: {expected_seconds} secondes ({expected_minutes} minutes)")
                                    print(f"API duree_attente: {api_duree_attente}")
                                    print(f"Database duree_attente: {db_duree_attente}")
                                    print(f"Statut final: {db_status}")
                                    
                                    # Conclusion
                                    if db_duree_attente == 0:
                                        print("\n🚨 CONCLUSION: BUG REPRODUCED")
                                        print("Le compteur d'attente se remet bien à zéro lors du passage de 'attente' à 'en_cours'")
                                        return False
                                    else:
                                        print("\n✅ CONCLUSION: BUG NOT REPRODUCED")
                                        print("Le compteur d'attente fonctionne correctement")
                                        return True
                                    
                                else:
                                    print("❌ Updated appointment not found in database")
                                    return False
                            else:
                                print(f"❌ Failed to get updated appointments: HTTP {response.status_code}")
                                return False
                        else:
                            print(f"❌ Failed to move to en_cours: HTTP {response.status_code}: {response.text}")
                            return False
                    else:
                        print(f"❌ Failed to move to attente: HTTP {response.status_code}: {response.text}")
                        return False
                else:
                    print("❌ No appointments found for testing")
                    return False
            else:
                print(f"❌ Failed to get appointments: HTTP {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Exception during test: {str(e)}")
            return False
    
    def run(self):
        """Run the quick user bug test"""
        print("🚀 QUICK USER BUG TEST - 15 Second Scenario")
        print("=" * 60)
        
        if not self.authenticate():
            return False
        
        return self.test_user_bug_sequence()

if __name__ == "__main__":
    tester = QuickUserBugTester()
    success = tester.run()
    
    if success:
        print("\n🎉 TEST COMPLETED SUCCESSFULLY")
        sys.exit(0)
    else:
        print("\n❌ TEST FAILED OR BUG REPRODUCED")
        sys.exit(1)