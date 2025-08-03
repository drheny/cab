#!/usr/bin/env python3
"""
Test approfondi pour les mises à jour WhatsApp - Edge cases et scénarios multiples
"""

import requests
import json
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/frontend/.env')

class WhatsAppComprehensiveTest:
    def __init__(self):
        backend_url = os.getenv('REACT_APP_BACKEND_URL', 'https://0698237d-0754-4aa4-881e-3c8e5387d3e6.preview.emergentagent.com')
        self.base_url = backend_url
        self.headers = {
            'Authorization': 'Bearer auto-login-token',
            'Content-Type': 'application/json'
        }
        print(f"🔧 Testing comprehensive WhatsApp scenarios at: {self.base_url}")
    
    def test_multiple_patients_whatsapp_update(self):
        """Test de mise à jour WhatsApp sur plusieurs patients"""
        print("\n" + "="*80)
        print("🧪 TEST COMPLET: MISE À JOUR WHATSAPP - SCÉNARIOS MULTIPLES")
        print("="*80)
        
        try:
            # Récupérer tous les patients
            print("\n📋 Récupération de tous les patients...")
            patients_response = requests.get(f"{self.base_url}/api/patients", headers=self.headers)
            
            if patients_response.status_code != 200:
                print(f"❌ Erreur lors de la récupération des patients: {patients_response.status_code}")
                return False
            
            patients_data = patients_response.json()
            patients = patients_data.get('patients', [])
            
            print(f"✅ {len(patients)} patients trouvés")
            
            test_results = []
            original_numbers = {}
            
            # Test sur chaque patient
            for i, patient in enumerate(patients):
                patient_id = patient['id']
                patient_name = f"{patient.get('prenom', '')} {patient.get('nom', '')}"
                original_whatsapp = patient.get('numero_whatsapp', '')
                original_lien = patient.get('lien_whatsapp', '')
                
                # Sauvegarder le numéro original
                original_numbers[patient_id] = original_whatsapp
                
                print(f"\n👤 PATIENT {i+1}: {patient_name}")
                print(f"   ID: {patient_id}")
                print(f"   Numéro original: '{original_whatsapp}'")
                
                # Générer un nouveau numéro de test
                new_number = f"21699{str(i+1).zfill(6)}"  # 21699000001, 21699000002, etc.
                
                print(f"   Nouveau numéro: {new_number}")
                
                # Mise à jour
                update_data = patient.copy()
                update_data['numero_whatsapp'] = new_number
                update_data['updated_at'] = datetime.now().isoformat()
                
                update_response = requests.put(
                    f"{self.base_url}/api/patients/{patient_id}",
                    headers=self.headers,
                    json=update_data
                )
                
                if update_response.status_code != 200:
                    print(f"   ❌ Erreur mise à jour: {update_response.status_code}")
                    test_results.append(False)
                    continue
                
                # Vérification immédiate
                check_response = requests.get(f"{self.base_url}/api/patients/{patient_id}", headers=self.headers)
                
                if check_response.status_code != 200:
                    print(f"   ❌ Erreur vérification: {check_response.status_code}")
                    test_results.append(False)
                    continue
                
                updated_patient = check_response.json()
                updated_whatsapp = updated_patient.get('numero_whatsapp', '')
                updated_lien = updated_patient.get('lien_whatsapp', '')
                
                # Vérifications
                number_persisted = updated_whatsapp == new_number
                link_updated = new_number in updated_lien if updated_lien else False
                
                print(f"   Persistance: {'✅' if number_persisted else '❌'}")
                print(f"   Lien mis à jour: {'✅' if link_updated else '❌'}")
                print(f"   Lien généré: '{updated_lien}'")
                
                test_results.append(number_persisted and link_updated)
            
            # Test des rappels après toutes les mises à jour
            print(f"\n📞 VÉRIFICATION DES RAPPELS APRÈS MISES À JOUR")
            
            # Rappels vaccins
            vaccine_response = requests.get(f"{self.base_url}/api/dashboard/vaccine-reminders", headers=self.headers)
            if vaccine_response.status_code == 200:
                vaccine_data = vaccine_response.json()
                vaccine_reminders = vaccine_data.get('vaccine_reminders', [])
                print(f"   Rappels vaccins: {len(vaccine_reminders)} trouvés")
                
                for reminder in vaccine_reminders:
                    patient_id = reminder.get('patient_id', '')
                    reminder_number = reminder.get('numero_whatsapp', '')
                    expected_number = f"21699{str([p['id'] for p in patients].index(patient_id) + 1).zfill(6)}"
                    
                    uses_updated = reminder_number == expected_number
                    print(f"   - Patient {patient_id}: {'✅' if uses_updated else '❌'} ({reminder_number})")
            
            # Rappels téléphoniques
            phone_response = requests.get(f"{self.base_url}/api/dashboard/phone-reminders", headers=self.headers)
            if phone_response.status_code == 200:
                phone_data = phone_response.json()
                phone_reminders = phone_data.get('reminders', [])
                print(f"   Rappels téléphoniques: {len(phone_reminders)} trouvés")
                
                for reminder in phone_reminders:
                    patient_id = reminder.get('patient_id', '')
                    reminder_number = reminder.get('numero_whatsapp', '')
                    expected_number = f"21699{str([p['id'] for p in patients].index(patient_id) + 1).zfill(6)}"
                    
                    uses_updated = reminder_number == expected_number
                    print(f"   - Patient {patient_id}: {'✅' if uses_updated else '❌'} ({reminder_number})")
            
            # Restauration des numéros originaux
            print(f"\n🔄 RESTAURATION DES NUMÉROS ORIGINAUX...")
            
            for patient in patients:
                patient_id = patient['id']
                original_number = original_numbers.get(patient_id, '')
                
                if original_number:
                    restore_data = patient.copy()
                    restore_data['numero_whatsapp'] = original_number
                    
                    restore_response = requests.put(
                        f"{self.base_url}/api/patients/{patient_id}",
                        headers=self.headers,
                        json=restore_data
                    )
                    
                    if restore_response.status_code == 200:
                        print(f"   ✅ {patient.get('prenom', '')} {patient.get('nom', '')}: restauré")
                    else:
                        print(f"   ❌ {patient.get('prenom', '')} {patient.get('nom', '')}: erreur restauration")
            
            # Résultats finaux
            success_count = sum(test_results)
            total_count = len(test_results)
            success_rate = (success_count / total_count * 100) if total_count > 0 else 0
            
            print(f"\n📊 RÉSULTATS FINAUX:")
            print(f"   Patients testés: {total_count}")
            print(f"   Mises à jour réussies: {success_count}")
            print(f"   Taux de succès: {success_rate:.1f}%")
            
            return success_rate == 100.0
            
        except Exception as e:
            print(f"❌ Erreur lors du test complet: {str(e)}")
            return False
    
    def test_edge_cases(self):
        """Test des cas limites pour les numéros WhatsApp"""
        print("\n" + "="*80)
        print("🧪 TEST DES CAS LIMITES WHATSAPP")
        print("="*80)
        
        try:
            # Récupérer un patient pour les tests
            patients_response = requests.get(f"{self.base_url}/api/patients", headers=self.headers)
            if patients_response.status_code != 200:
                return False
            
            patients = patients_response.json().get('patients', [])
            if not patients:
                return False
            
            patient = patients[0]
            patient_id = patient['id']
            original_number = patient.get('numero_whatsapp', '')
            
            print(f"👤 Patient de test: {patient.get('prenom', '')} {patient.get('nom', '')}")
            
            # Test cases
            test_cases = [
                ("", "Numéro vide"),
                ("invalid", "Numéro invalide"),
                ("21612345678", "Format Tunisien valide"),
                ("+21612345678", "Format avec +"),
                ("0612345678", "Format local"),
                ("216 12 34 56 78", "Format avec espaces"),
                ("216-12-34-56-78", "Format avec tirets"),
            ]
            
            results = []
            
            for test_number, description in test_cases:
                print(f"\n🔍 Test: {description}")
                print(f"   Numéro testé: '{test_number}'")
                
                # Mise à jour
                update_data = patient.copy()
                update_data['numero_whatsapp'] = test_number
                
                update_response = requests.put(
                    f"{self.base_url}/api/patients/{patient_id}",
                    headers=self.headers,
                    json=update_data
                )
                
                if update_response.status_code != 200:
                    print(f"   ❌ Erreur API: {update_response.status_code}")
                    results.append(False)
                    continue
                
                # Vérification
                check_response = requests.get(f"{self.base_url}/api/patients/{patient_id}", headers=self.headers)
                if check_response.status_code != 200:
                    results.append(False)
                    continue
                
                updated_patient = check_response.json()
                stored_number = updated_patient.get('numero_whatsapp', '')
                generated_link = updated_patient.get('lien_whatsapp', '')
                
                print(f"   Numéro stocké: '{stored_number}'")
                print(f"   Lien généré: '{generated_link}'")
                
                # Vérifier la cohérence
                number_stored = stored_number == test_number
                link_appropriate = (generated_link == "" and test_number in ["", "invalid"]) or \
                                 (generated_link != "" and test_number not in ["", "invalid"])
                
                print(f"   Stockage: {'✅' if number_stored else '❌'}")
                print(f"   Lien approprié: {'✅' if link_appropriate else '❌'}")
                
                results.append(number_stored)
            
            # Restaurer le numéro original
            restore_data = patient.copy()
            restore_data['numero_whatsapp'] = original_number
            requests.put(f"{self.base_url}/api/patients/{patient_id}", headers=self.headers, json=restore_data)
            
            success_count = sum(results)
            total_count = len(results)
            
            print(f"\n📊 RÉSULTATS CAS LIMITES:")
            print(f"   Tests effectués: {total_count}")
            print(f"   Tests réussis: {success_count}")
            print(f"   Taux de succès: {success_count/total_count*100:.1f}%")
            
            return success_count == total_count
            
        except Exception as e:
            print(f"❌ Erreur lors des tests cas limites: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Exécuter tous les tests complets"""
        print("🚀 DÉBUT DES TESTS COMPLETS WHATSAPP")
        
        # Test 1: Scénarios multiples
        test1_success = self.test_multiple_patients_whatsapp_update()
        
        # Test 2: Cas limites
        test2_success = self.test_edge_cases()
        
        overall_success = test1_success and test2_success
        
        print(f"\n{'='*80}")
        print(f"🏁 RÉSULTAT FINAL COMPLET:")
        print(f"   Test scénarios multiples: {'✅' if test1_success else '❌'}")
        print(f"   Test cas limites: {'✅' if test2_success else '❌'}")
        print(f"   SUCCÈS GLOBAL: {'✅' if overall_success else '❌'}")
        print(f"{'='*80}")
        
        return overall_success

if __name__ == "__main__":
    tester = WhatsAppComprehensiveTest()
    success = tester.run_all_tests()
    exit(0 if success else 1)