#!/usr/bin/env python3
"""
Test spécifique pour le problème de mise à jour des numéros WhatsApp des patients
Test selon le scénario demandé dans la review request
"""

import requests
import json
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/frontend/.env')

class WhatsAppUpdateTest:
    def __init__(self):
        # Use the correct backend URL from environment
        backend_url = os.getenv('REACT_APP_BACKEND_URL', 'https://f310bc43-97b2-405e-8eb3-271aa9c20e28.preview.emergentagent.com')
        self.base_url = backend_url
        self.headers = {
            'Authorization': 'Bearer auto-login-token',
            'Content-Type': 'application/json'
        }
        print(f"🔧 Testing WhatsApp update at: {self.base_url}")
    
    def test_whatsapp_number_update_scenario(self):
        """Test complet du scénario de mise à jour des numéros WhatsApp"""
        print("\n" + "="*80)
        print("🧪 TEST SPÉCIFIQUE: MISE À JOUR NUMÉROS WHATSAPP PATIENTS")
        print("="*80)
        
        try:
            # Étape 1: Créer/Récupérer un patient
            print("\n📋 ÉTAPE 1: Récupération d'un patient existant")
            patients_response = requests.get(f"{self.base_url}/api/patients", headers=self.headers)
            
            if patients_response.status_code != 200:
                print(f"❌ Erreur lors de la récupération des patients: {patients_response.status_code}")
                return False
            
            patients_data = patients_response.json()
            patients = patients_data.get('patients', [])
            
            if not patients:
                print("❌ Aucun patient trouvé dans la base de données")
                return False
            
            # Prendre le premier patient
            patient = patients[0]
            patient_id = patient['id']
            original_whatsapp = patient.get('numero_whatsapp', '')
            original_lien = patient.get('lien_whatsapp', '')
            
            print(f"✅ Patient sélectionné: {patient.get('prenom', '')} {patient.get('nom', '')}")
            print(f"   ID: {patient_id}")
            print(f"   Numéro WhatsApp actuel: '{original_whatsapp}'")
            print(f"   Lien WhatsApp actuel: '{original_lien}'")
            
            # Étape 2: Mettre à jour le numéro WhatsApp
            print(f"\n📝 ÉTAPE 2: Mise à jour du numéro WhatsApp")
            new_whatsapp_number = "21698765432"  # Nouveau numéro de test
            
            # Préparer les données de mise à jour (garder toutes les données existantes)
            update_data = patient.copy()
            update_data['numero_whatsapp'] = new_whatsapp_number
            update_data['updated_at'] = datetime.now().isoformat()
            
            print(f"   Nouveau numéro: {new_whatsapp_number}")
            
            # Effectuer la mise à jour
            update_response = requests.put(
                f"{self.base_url}/api/patients/{patient_id}",
                headers=self.headers,
                json=update_data
            )
            
            print(f"   Statut de la réponse: {update_response.status_code}")
            
            if update_response.status_code != 200:
                print(f"❌ Erreur lors de la mise à jour: {update_response.text}")
                return False
            
            update_result = update_response.json()
            print(f"✅ Réponse API: {update_result}")
            
            # Étape 3: Vérifier la persistance
            print(f"\n🔍 ÉTAPE 3: Vérification de la persistance")
            
            # Récupérer le patient mis à jour
            patient_response = requests.get(f"{self.base_url}/api/patients/{patient_id}", headers=self.headers)
            
            if patient_response.status_code != 200:
                print(f"❌ Erreur lors de la récupération du patient mis à jour: {patient_response.status_code}")
                return False
            
            updated_patient = patient_response.json()
            updated_whatsapp = updated_patient.get('numero_whatsapp', '')
            updated_lien = updated_patient.get('lien_whatsapp', '')
            
            print(f"   Numéro WhatsApp après mise à jour: '{updated_whatsapp}'")
            print(f"   Lien WhatsApp après mise à jour: '{updated_lien}'")
            
            # Vérifications critiques
            whatsapp_persisted = updated_whatsapp == new_whatsapp_number
            lien_updated = updated_lien != original_lien and updated_lien != ""
            
            print(f"\n🔍 VÉRIFICATIONS CRITIQUES:")
            print(f"   ✅ Numéro WhatsApp persisté: {'OUI' if whatsapp_persisted else 'NON'}")
            print(f"   ✅ Lien WhatsApp recalculé: {'OUI' if lien_updated else 'NON'}")
            
            if not whatsapp_persisted:
                print(f"❌ PROBLÈME CRITIQUE: Le numéro WhatsApp n'a pas été sauvegardé!")
                print(f"   Attendu: {new_whatsapp_number}")
                print(f"   Reçu: {updated_whatsapp}")
                return False
            
            if not lien_updated:
                print(f"⚠️  PROBLÈME: Le lien WhatsApp n'a pas été recalculé!")
                print(f"   Lien original: {original_lien}")
                print(f"   Lien après mise à jour: {updated_lien}")
            
            # Étape 4: Tester les rappels
            print(f"\n📞 ÉTAPE 4: Test des rappels avec les données mises à jour")
            
            # Test des rappels vaccins
            print("   Test des rappels vaccins...")
            vaccine_response = requests.get(f"{self.base_url}/api/dashboard/vaccine-reminders", headers=self.headers)
            
            if vaccine_response.status_code == 200:
                vaccine_data = vaccine_response.json()
                vaccine_reminders = vaccine_data.get('vaccine_reminders', [])
                
                # Chercher des rappels pour ce patient
                patient_vaccine_reminders = [r for r in vaccine_reminders if r.get('patient_id') == patient_id]
                
                print(f"   Rappels vaccins trouvés pour ce patient: {len(patient_vaccine_reminders)}")
                
                for reminder in patient_vaccine_reminders:
                    reminder_whatsapp = reminder.get('numero_whatsapp', '')
                    uses_updated_number = reminder_whatsapp == new_whatsapp_number
                    print(f"   - Rappel vaccin: {reminder.get('nom_vaccin', 'N/A')}")
                    print(f"     Numéro utilisé: {reminder_whatsapp}")
                    print(f"     Utilise le nouveau numéro: {'OUI' if uses_updated_number else 'NON'}")
                    
                    if not uses_updated_number and reminder_whatsapp != '':
                        print(f"⚠️  PROBLÈME: Le rappel vaccin utilise l'ancien numéro!")
            else:
                print(f"   ⚠️  Impossible de récupérer les rappels vaccins: {vaccine_response.status_code}")
            
            # Test des rappels téléphoniques
            print("   Test des rappels téléphoniques...")
            phone_response = requests.get(f"{self.base_url}/api/dashboard/phone-reminders", headers=self.headers)
            
            if phone_response.status_code == 200:
                phone_data = phone_response.json()
                phone_reminders = phone_data.get('reminders', [])
                
                # Chercher des rappels pour ce patient
                patient_phone_reminders = [r for r in phone_reminders if r.get('patient_id') == patient_id]
                
                print(f"   Rappels téléphoniques trouvés pour ce patient: {len(patient_phone_reminders)}")
                
                for reminder in patient_phone_reminders:
                    reminder_whatsapp = reminder.get('numero_whatsapp', '')
                    uses_updated_number = reminder_whatsapp == new_whatsapp_number
                    print(f"   - Rappel téléphonique: {reminder.get('raison_relance', 'N/A')}")
                    print(f"     Numéro utilisé: {reminder_whatsapp}")
                    print(f"     Utilise le nouveau numéro: {'OUI' if uses_updated_number else 'NON'}")
                    
                    if not uses_updated_number and reminder_whatsapp != '':
                        print(f"⚠️  PROBLÈME: Le rappel téléphonique utilise l'ancien numéro!")
            else:
                print(f"   ⚠️  Impossible de récupérer les rappels téléphoniques: {phone_response.status_code}")
            
            # Résumé final
            print(f"\n📊 RÉSUMÉ DU TEST:")
            print(f"   Patient testé: {updated_patient.get('prenom', '')} {updated_patient.get('nom', '')}")
            print(f"   Ancien numéro: {original_whatsapp}")
            print(f"   Nouveau numéro: {new_whatsapp_number}")
            print(f"   Mise à jour réussie: {'✅ OUI' if whatsapp_persisted else '❌ NON'}")
            print(f"   Lien WhatsApp recalculé: {'✅ OUI' if lien_updated else '⚠️  NON'}")
            
            # Restaurer l'ancien numéro pour ne pas affecter les autres tests
            print(f"\n🔄 Restauration de l'ancien numéro...")
            restore_data = updated_patient.copy()
            restore_data['numero_whatsapp'] = original_whatsapp
            
            restore_response = requests.put(
                f"{self.base_url}/api/patients/{patient_id}",
                headers=self.headers,
                json=restore_data
            )
            
            if restore_response.status_code == 200:
                print(f"✅ Ancien numéro restauré avec succès")
            else:
                print(f"⚠️  Erreur lors de la restauration: {restore_response.status_code}")
            
            return whatsapp_persisted
            
        except Exception as e:
            print(f"❌ Erreur lors du test: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Exécuter tous les tests WhatsApp"""
        print("🚀 DÉBUT DES TESTS DE MISE À JOUR WHATSAPP")
        
        # Test principal
        success = self.test_whatsapp_number_update_scenario()
        
        print(f"\n{'='*80}")
        print(f"🏁 RÉSULTAT FINAL: {'✅ SUCCÈS' if success else '❌ ÉCHEC'}")
        print(f"{'='*80}")
        
        return success

if __name__ == "__main__":
    tester = WhatsAppUpdateTest()
    success = tester.run_all_tests()
    exit(0 if success else 1)