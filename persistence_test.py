import requests
import unittest
import json
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv('/app/frontend/.env')

class DataPersistenceTest(unittest.TestCase):
    """
    Test spécifiquement les problèmes de persistance de données rapportés :
    1. Test Consultation Creation - Persistance
    2. Test Patient Update - Persistance WhatsApp  
    3. Test Vaccine Reminders - Persistance et Visibilité
    """
    
    def setUp(self):
        # Use the correct backend URL from environment
        backend_url = os.getenv('REACT_APP_BACKEND_URL', 'https://0698237d-0754-4aa4-881e-3c8e5387d3e6.preview.emergentagent.com')
        self.base_url = backend_url
        print(f"Testing backend at: {self.base_url}")
        
        # Initialize demo data for consistent testing
        self.init_demo_data()
        
        # Get authentication token for protected endpoints
        self.auth_token = self.get_auth_token()
    
    def init_demo_data(self):
        """Initialize demo data for testing"""
        try:
            response = requests.get(f"{self.base_url}/api/init-demo")
            if response.status_code == 200:
                print("✅ Demo data initialized successfully")
            else:
                print(f"⚠️ Demo data initialization returned: {response.status_code}")
        except Exception as e:
            print(f"❌ Error initializing demo data: {e}")
    
    def get_auth_token(self):
        """Get authentication token for protected endpoints"""
        try:
            login_data = {"username": "medecin", "password": "medecin123"}
            response = requests.post(f"{self.base_url}/api/auth/login", json=login_data)
            if response.status_code == 200:
                token = response.json()["access_token"]
                print("✅ Authentication token obtained")
                return token
            else:
                print(f"⚠️ Using auto-login token as fallback")
                return "auto-login-token"
        except Exception as e:
            print(f"⚠️ Auth failed, using auto-login token: {e}")
            return "auto-login-token"
    
    def get_headers(self):
        """Get headers with authentication"""
        return {"Authorization": f"Bearer {self.auth_token}"}

    # ========== TEST 1: CONSULTATION CREATION - PERSISTANCE ==========
    
    def test_consultation_creation_persistence(self):
        """
        Test Consultation Creation - Persistance :
        - POST /api/consultations avec données complètes
        - Vérifier la réponse et l'ID généré
        - GET /api/consultations pour vérifier si la consultation persiste
        - GET /api/consultations/{consultation_id} pour vérifier les détails
        """
        print("\n🔍 TEST 1: CONSULTATION CREATION - PERSISTANCE")
        
        # Step 1: Get a valid patient and appointment for consultation
        print("  Step 1: Getting valid patient and appointment...")
        
        # Get patients
        response = requests.get(f"{self.base_url}/api/patients")
        self.assertEqual(response.status_code, 200, "Failed to get patients")
        patients_data = response.json()
        self.assertTrue(len(patients_data["patients"]) > 0, "No patients found")
        patient_id = patients_data["patients"][0]["id"]
        print(f"    ✅ Patient found: {patient_id}")
        
        # Create a test appointment first
        today = datetime.now().strftime("%Y-%m-%d")
        appointment_data = {
            "patient_id": patient_id,
            "date": today,
            "heure": "10:00",
            "type_rdv": "visite",
            "motif": "Test consultation persistence",
            "statut": "termine"
        }
        
        response = requests.post(f"{self.base_url}/api/appointments", json=appointment_data)
        self.assertEqual(response.status_code, 200, "Failed to create test appointment")
        appointment_id = response.json()["appointment_id"]
        print(f"    ✅ Test appointment created: {appointment_id}")
        
        # Step 2: Create consultation with complete data
        print("  Step 2: Creating consultation with complete data...")
        
        consultation_data = {
            "patient_id": patient_id,
            "appointment_id": appointment_id,
            "date": "2025-08-02", 
            "diagnostic": "Test persistance consultation",
            "observation_clinique": "Test observation clinique détaillée",
            "rappel_vaccin": True,
            "nom_vaccin": "Test Vaccin Persistance",
            "date_vaccin": "2025-08-03",
            "duree": 30,
            "poids": 15.5,
            "taille": 95.0,
            "temperature": 37.2
        }
        
        response = requests.post(f"{self.base_url}/api/consultations", json=consultation_data)
        print(f"    POST /api/consultations response: {response.status_code}")
        if response.status_code != 200:
            print(f"    Response content: {response.text}")
        
        self.assertEqual(response.status_code, 200, f"Failed to create consultation: {response.text}")
        
        # Verify response structure
        create_response = response.json()
        self.assertIn("message", create_response, "Response missing 'message' field")
        self.assertIn("consultation_id", create_response, "Response missing 'consultation_id' field")
        
        consultation_id = create_response["consultation_id"]
        print(f"    ✅ Consultation created with ID: {consultation_id}")
        
        # Step 3: Verify consultation persists in list
        print("  Step 3: Verifying consultation appears in consultations list...")
        
        response = requests.get(f"{self.base_url}/api/consultations")
        self.assertEqual(response.status_code, 200, "Failed to get consultations list")
        
        consultations_list = response.json()
        self.assertIsInstance(consultations_list, list, "Consultations response should be a list")
        
        # Find our consultation in the list
        found_consultation = None
        for consultation in consultations_list:
            if consultation.get("id") == consultation_id:
                found_consultation = consultation
                break
        
        self.assertIsNotNone(found_consultation, f"Consultation {consultation_id} not found in consultations list")
        print(f"    ✅ Consultation found in list with patient_id: {found_consultation.get('patient_id')}")
        
        # Step 4: Verify consultation details via direct GET
        print("  Step 4: Verifying consultation details via GET...")
        
        response = requests.get(f"{self.base_url}/api/consultations/{consultation_id}")
        self.assertEqual(response.status_code, 200, f"Failed to get consultation details: {response.text}")
        
        consultation_details = response.json()
        
        # Verify all data persisted correctly
        self.assertEqual(consultation_details["patient_id"], patient_id, "Patient ID mismatch")
        self.assertEqual(consultation_details["appointment_id"], appointment_id, "Appointment ID mismatch")
        self.assertEqual(consultation_details["date"], "2025-08-02", "Date mismatch")
        self.assertEqual(consultation_details["diagnostic"], "Test persistance consultation", "Diagnostic mismatch")
        self.assertEqual(consultation_details["observation_clinique"], "Test observation clinique détaillée", "Observation clinique mismatch")
        self.assertEqual(consultation_details["rappel_vaccin"], True, "Rappel vaccin mismatch")
        self.assertEqual(consultation_details["nom_vaccin"], "Test Vaccin Persistance", "Nom vaccin mismatch")
        self.assertEqual(consultation_details["date_vaccin"], "2025-08-03", "Date vaccin mismatch")
        self.assertEqual(consultation_details["duree"], 30, "Duree mismatch")
        self.assertEqual(consultation_details["poids"], 15.5, "Poids mismatch")
        self.assertEqual(consultation_details["taille"], 95.0, "Taille mismatch")
        self.assertEqual(consultation_details["temperature"], 37.2, "Temperature mismatch")
        
        print(f"    ✅ All consultation data persisted correctly")
        
        # Step 5: Verify consultation appears in patient's consultation history
        print("  Step 5: Verifying consultation in patient's history...")
        
        response = requests.get(f"{self.base_url}/api/patients/{patient_id}/consultations")
        self.assertEqual(response.status_code, 200, "Failed to get patient consultations")
        
        patient_consultations = response.json()
        self.assertIsInstance(patient_consultations, list, "Patient consultations should be a list")
        
        # Find our consultation in patient's history
        found_in_history = False
        for consultation in patient_consultations:
            if consultation.get("id") == consultation_id:
                found_in_history = True
                break
        
        self.assertTrue(found_in_history, f"Consultation {consultation_id} not found in patient's consultation history")
        print(f"    ✅ Consultation found in patient's consultation history")
        
        # Cleanup
        print("  Step 6: Cleaning up test data...")
        requests.delete(f"{self.base_url}/api/consultations/{consultation_id}")
        requests.delete(f"{self.base_url}/api/appointments/{appointment_id}")
        
        print("🎉 TEST 1 PASSED: Consultation Creation - Persistance ✅")

    # ========== TEST 2: PATIENT UPDATE - PERSISTANCE WHATSAPP ==========
    
    def test_patient_whatsapp_update_persistence(self):
        """
        Test Patient Update - Persistance WhatsApp :
        - GET /api/patients/{patient_id} pour récupérer les données actuelles
        - PUT /api/patients/{patient_id} avec nouveau numéro WhatsApp
        - GET /api/patients/{patient_id} immédiatement après pour vérifier persistance
        - GET /api/patients (liste) pour vérifier si les changements apparaissent dans la liste
        """
        print("\n🔍 TEST 2: PATIENT UPDATE - PERSISTANCE WHATSAPP")
        
        # Step 1: Get a patient to update
        print("  Step 1: Getting patient for WhatsApp update test...")
        
        response = requests.get(f"{self.base_url}/api/patients")
        self.assertEqual(response.status_code, 200, "Failed to get patients")
        patients_data = response.json()
        self.assertTrue(len(patients_data["patients"]) > 0, "No patients found")
        
        # Find a patient with existing WhatsApp number
        test_patient = None
        for patient in patients_data["patients"]:
            if patient.get("numero_whatsapp"):
                test_patient = patient
                break
        
        self.assertIsNotNone(test_patient, "No patient with WhatsApp number found")
        patient_id = test_patient["id"]
        original_whatsapp = test_patient["numero_whatsapp"]
        print(f"    ✅ Patient found: {patient_id}")
        print(f"    ✅ Original WhatsApp: {original_whatsapp}")
        
        # Step 2: Get current patient data
        print("  Step 2: Getting current patient data...")
        
        response = requests.get(f"{self.base_url}/api/patients/{patient_id}")
        self.assertEqual(response.status_code, 200, f"Failed to get patient {patient_id}")
        
        current_patient_data = response.json()
        self.assertEqual(current_patient_data["numero_whatsapp"], original_whatsapp, "WhatsApp number mismatch in current data")
        print(f"    ✅ Current patient data retrieved successfully")
        
        # Step 3: Update patient with new WhatsApp number
        print("  Step 3: Updating patient with new WhatsApp number...")
        
        new_whatsapp = "21699999999"  # Test number as specified in review request
        updated_patient_data = current_patient_data.copy()
        updated_patient_data["numero_whatsapp"] = new_whatsapp
        
        response = requests.put(f"{self.base_url}/api/patients/{patient_id}", json=updated_patient_data)
        self.assertEqual(response.status_code, 200, f"Failed to update patient: {response.text}")
        print(f"    ✅ Patient updated with new WhatsApp: {new_whatsapp}")
        
        # Step 4: Immediately verify persistence via direct GET
        print("  Step 4: Verifying immediate persistence via direct GET...")
        
        response = requests.get(f"{self.base_url}/api/patients/{patient_id}")
        self.assertEqual(response.status_code, 200, f"Failed to get updated patient {patient_id}")
        
        updated_patient = response.json()
        self.assertEqual(updated_patient["numero_whatsapp"], new_whatsapp, 
                        f"WhatsApp number not persisted. Expected: {new_whatsapp}, Got: {updated_patient.get('numero_whatsapp')}")
        
        # Verify WhatsApp link was also updated
        expected_whatsapp_link = f"https://wa.me/{new_whatsapp}"
        self.assertEqual(updated_patient["lien_whatsapp"], expected_whatsapp_link,
                        f"WhatsApp link not updated. Expected: {expected_whatsapp_link}, Got: {updated_patient.get('lien_whatsapp')}")
        
        print(f"    ✅ WhatsApp number persisted correctly: {updated_patient['numero_whatsapp']}")
        print(f"    ✅ WhatsApp link updated correctly: {updated_patient['lien_whatsapp']}")
        
        # Step 5: Verify persistence in patients list
        print("  Step 5: Verifying persistence in patients list...")
        
        response = requests.get(f"{self.base_url}/api/patients")
        self.assertEqual(response.status_code, 200, "Failed to get patients list")
        
        patients_list = response.json()["patients"]
        
        # Find our updated patient in the list
        found_patient = None
        for patient in patients_list:
            if patient["id"] == patient_id:
                found_patient = patient
                break
        
        self.assertIsNotNone(found_patient, f"Patient {patient_id} not found in patients list")
        self.assertEqual(found_patient["numero_whatsapp"], new_whatsapp,
                        f"WhatsApp number not persisted in list. Expected: {new_whatsapp}, Got: {found_patient.get('numero_whatsapp')}")
        
        print(f"    ✅ WhatsApp number persisted in patients list: {found_patient['numero_whatsapp']}")
        
        # Step 6: Test cross-page navigation persistence (simulate page refresh)
        print("  Step 6: Testing cross-page navigation persistence...")
        
        # Wait a moment to simulate navigation delay
        time.sleep(1)
        
        # Get patient data again (simulating page refresh)
        response = requests.get(f"{self.base_url}/api/patients/{patient_id}")
        self.assertEqual(response.status_code, 200, f"Failed to get patient after navigation simulation")
        
        navigation_patient = response.json()
        self.assertEqual(navigation_patient["numero_whatsapp"], new_whatsapp,
                        f"WhatsApp number lost after navigation. Expected: {new_whatsapp}, Got: {navigation_patient.get('numero_whatsapp')}")
        
        print(f"    ✅ WhatsApp number persisted after navigation simulation")
        
        # Step 7: Restore original WhatsApp number
        print("  Step 7: Restoring original WhatsApp number...")
        
        restore_patient_data = navigation_patient.copy()
        restore_patient_data["numero_whatsapp"] = original_whatsapp
        
        response = requests.put(f"{self.base_url}/api/patients/{patient_id}", json=restore_patient_data)
        self.assertEqual(response.status_code, 200, "Failed to restore original WhatsApp number")
        
        # Verify restoration
        response = requests.get(f"{self.base_url}/api/patients/{patient_id}")
        self.assertEqual(response.status_code, 200, "Failed to verify restoration")
        restored_patient = response.json()
        self.assertEqual(restored_patient["numero_whatsapp"], original_whatsapp, "Failed to restore original WhatsApp number")
        
        print(f"    ✅ Original WhatsApp number restored: {original_whatsapp}")
        
        print("🎉 TEST 2 PASSED: Patient Update - Persistance WhatsApp ✅")

    # ========== TEST 3: VACCINE REMINDERS - PERSISTANCE ET VISIBILITÉ ==========
    
    def test_vaccine_reminders_persistence_visibility(self):
        """
        Test Vaccine Reminders - Persistance et Visibilité :
        - Créer une consultation avec rappel_vaccin=true et date_vaccin future
        - GET /api/dashboard/vaccine-reminders pour voir si le rappel apparaît
        - Vérifier les paramètres de date (aujourd'hui vs date future)
        """
        print("\n🔍 TEST 3: VACCINE REMINDERS - PERSISTANCE ET VISIBILITÉ")
        
        # Step 1: Get patient and create appointment for vaccine reminder test
        print("  Step 1: Setting up patient and appointment for vaccine reminder...")
        
        response = requests.get(f"{self.base_url}/api/patients")
        self.assertEqual(response.status_code, 200, "Failed to get patients")
        patients_data = response.json()
        self.assertTrue(len(patients_data["patients"]) > 0, "No patients found")
        patient_id = patients_data["patients"][0]["id"]
        
        # Create test appointment
        today = datetime.now().strftime("%Y-%m-%d")
        appointment_data = {
            "patient_id": patient_id,
            "date": today,
            "heure": "11:00",
            "type_rdv": "visite",
            "motif": "Test vaccine reminder",
            "statut": "termine"
        }
        
        response = requests.post(f"{self.base_url}/api/appointments", json=appointment_data)
        self.assertEqual(response.status_code, 200, "Failed to create test appointment")
        appointment_id = response.json()["appointment_id"]
        print(f"    ✅ Test appointment created: {appointment_id}")
        
        # Step 2: Create consultation with vaccine reminder for TODAY
        print("  Step 2: Creating consultation with vaccine reminder for TODAY...")
        
        today_str = datetime.now().strftime("%Y-%m-%d")
        consultation_data = {
            "patient_id": patient_id,
            "appointment_id": appointment_id,
            "date": today_str,
            "diagnostic": "Test vaccine reminder consultation",
            "observation_clinique": "Test observation pour rappel vaccin",
            "rappel_vaccin": True,
            "nom_vaccin": "Test Vaccin Reminder",
            "date_vaccin": today_str,  # Set for TODAY to appear in reminders
            "duree": 25
        }
        
        response = requests.post(f"{self.base_url}/api/consultations", json=consultation_data)
        self.assertEqual(response.status_code, 200, f"Failed to create consultation with vaccine reminder: {response.text}")
        
        consultation_id = response.json()["consultation_id"]
        print(f"    ✅ Consultation with vaccine reminder created: {consultation_id}")
        print(f"    ✅ Vaccine reminder set for TODAY: {today_str}")
        
        # Step 3: Verify consultation was created with vaccine reminder data
        print("  Step 3: Verifying consultation vaccine reminder data...")
        
        response = requests.get(f"{self.base_url}/api/consultations/{consultation_id}")
        self.assertEqual(response.status_code, 200, "Failed to get consultation details")
        
        consultation_details = response.json()
        self.assertEqual(consultation_details["rappel_vaccin"], True, "Rappel vaccin not set to True")
        self.assertEqual(consultation_details["nom_vaccin"], "Test Vaccin Reminder", "Nom vaccin mismatch")
        self.assertEqual(consultation_details["date_vaccin"], today_str, "Date vaccin mismatch")
        
        print(f"    ✅ Vaccine reminder data persisted correctly")
        print(f"      - rappel_vaccin: {consultation_details['rappel_vaccin']}")
        print(f"      - nom_vaccin: {consultation_details['nom_vaccin']}")
        print(f"      - date_vaccin: {consultation_details['date_vaccin']}")
        
        # Step 4: Check if vaccine reminder appears in dashboard
        print("  Step 4: Checking vaccine reminder visibility in dashboard...")
        
        response = requests.get(f"{self.base_url}/api/dashboard/vaccine-reminders")
        self.assertEqual(response.status_code, 200, f"Failed to get vaccine reminders: {response.text}")
        
        vaccine_reminders = response.json()
        self.assertIn("vaccine_reminders", vaccine_reminders, "Response missing 'vaccine_reminders' field")
        
        reminders_list = vaccine_reminders["vaccine_reminders"]
        self.assertIsInstance(reminders_list, list, "Vaccine reminders should be a list")
        
        print(f"    ✅ Vaccine reminders endpoint accessible")
        print(f"    ✅ Found {len(reminders_list)} vaccine reminders for today")
        
        # Step 5: Verify our vaccine reminder appears in the list
        print("  Step 5: Verifying our vaccine reminder appears in the list...")
        
        found_reminder = None
        for reminder in reminders_list:
            if (reminder.get("patient_id") == patient_id and 
                reminder.get("nom_vaccin") == "Test Vaccin Reminder"):
                found_reminder = reminder
                break
        
        self.assertIsNotNone(found_reminder, f"Our vaccine reminder not found in dashboard list. Available reminders: {reminders_list}")
        
        # Verify reminder structure and data
        self.assertEqual(found_reminder["patient_id"], patient_id, "Patient ID mismatch in reminder")
        self.assertEqual(found_reminder["nom_vaccin"], "Test Vaccin Reminder", "Vaccine name mismatch in reminder")
        self.assertEqual(found_reminder["date_vaccin"], today_str, "Vaccine date mismatch in reminder")
        self.assertIn("patient_nom", found_reminder, "Patient nom missing in reminder")
        self.assertIn("patient_prenom", found_reminder, "Patient prenom missing in reminder")
        self.assertIn("numero_whatsapp", found_reminder, "WhatsApp number missing in reminder")
        
        print(f"    ✅ Our vaccine reminder found in dashboard list")
        print(f"      - Patient: {found_reminder.get('patient_prenom')} {found_reminder.get('patient_nom')}")
        print(f"      - Vaccine: {found_reminder['nom_vaccin']}")
        print(f"      - Date: {found_reminder['date_vaccin']}")
        print(f"      - WhatsApp: {found_reminder.get('numero_whatsapp')}")
        
        # Step 6: Test with future date (should NOT appear in today's reminders)
        print("  Step 6: Testing vaccine reminder with future date...")
        
        # Create another consultation with future vaccine date
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        # Create another appointment
        future_appointment_data = {
            "patient_id": patient_id,
            "date": today,
            "heure": "12:00",
            "type_rdv": "visite",
            "motif": "Test future vaccine reminder",
            "statut": "termine"
        }
        
        response = requests.post(f"{self.base_url}/api/appointments", json=future_appointment_data)
        self.assertEqual(response.status_code, 200, "Failed to create future test appointment")
        future_appointment_id = response.json()["appointment_id"]
        
        future_consultation_data = {
            "patient_id": patient_id,
            "appointment_id": future_appointment_id,
            "date": today_str,
            "diagnostic": "Test future vaccine reminder",
            "observation_clinique": "Test observation pour rappel vaccin futur",
            "rappel_vaccin": True,
            "nom_vaccin": "Future Vaccin Test",
            "date_vaccin": tomorrow,  # Set for TOMORROW
            "duree": 20
        }
        
        response = requests.post(f"{self.base_url}/api/consultations", json=future_consultation_data)
        self.assertEqual(response.status_code, 200, "Failed to create future consultation")
        future_consultation_id = response.json()["consultation_id"]
        
        print(f"    ✅ Future vaccine reminder created for: {tomorrow}")
        
        # Check that future reminder does NOT appear in today's reminders
        response = requests.get(f"{self.base_url}/api/dashboard/vaccine-reminders")
        self.assertEqual(response.status_code, 200, "Failed to get vaccine reminders after future creation")
        
        current_reminders = response.json()["vaccine_reminders"]
        
        # Verify future reminder is NOT in today's list
        future_found = False
        for reminder in current_reminders:
            if (reminder.get("patient_id") == patient_id and 
                reminder.get("nom_vaccin") == "Future Vaccin Test"):
                future_found = True
                break
        
        self.assertFalse(future_found, "Future vaccine reminder incorrectly appears in today's reminders")
        print(f"    ✅ Future vaccine reminder correctly excluded from today's list")
        
        # Step 7: Verify date filtering works correctly
        print("  Step 7: Verifying date filtering logic...")
        
        # Our original reminder for today should still be there
        today_found = False
        for reminder in current_reminders:
            if (reminder.get("patient_id") == patient_id and 
                reminder.get("nom_vaccin") == "Test Vaccin Reminder" and
                reminder.get("date_vaccin") == today_str):
                today_found = True
                break
        
        self.assertTrue(today_found, "Today's vaccine reminder missing after future reminder creation")
        print(f"    ✅ Today's vaccine reminder still present and correctly filtered")
        
        # Step 8: Cleanup test data
        print("  Step 8: Cleaning up test data...")
        
        requests.delete(f"{self.base_url}/api/consultations/{consultation_id}")
        requests.delete(f"{self.base_url}/api/consultations/{future_consultation_id}")
        requests.delete(f"{self.base_url}/api/appointments/{appointment_id}")
        requests.delete(f"{self.base_url}/api/appointments/{future_appointment_id}")
        
        print(f"    ✅ Test data cleaned up")
        
        print("🎉 TEST 3 PASSED: Vaccine Reminders - Persistance et Visibilité ✅")

    # ========== COMPREHENSIVE PERSISTENCE SUMMARY ==========
    
    def test_comprehensive_persistence_summary(self):
        """
        Comprehensive summary of all persistence tests
        """
        print("\n🔍 COMPREHENSIVE PERSISTENCE TEST SUMMARY")
        print("="*60)
        
        # Run all persistence tests and collect results
        test_results = {
            "consultation_creation": False,
            "patient_whatsapp_update": False,
            "vaccine_reminders": False
        }
        
        try:
            self.test_consultation_creation_persistence()
            test_results["consultation_creation"] = True
            print("✅ Consultation Creation Persistence: PASSED")
        except Exception as e:
            print(f"❌ Consultation Creation Persistence: FAILED - {str(e)}")
        
        try:
            self.test_patient_whatsapp_update_persistence()
            test_results["patient_whatsapp_update"] = True
            print("✅ Patient WhatsApp Update Persistence: PASSED")
        except Exception as e:
            print(f"❌ Patient WhatsApp Update Persistence: FAILED - {str(e)}")
        
        try:
            self.test_vaccine_reminders_persistence_visibility()
            test_results["vaccine_reminders"] = True
            print("✅ Vaccine Reminders Persistence: PASSED")
        except Exception as e:
            print(f"❌ Vaccine Reminders Persistence: FAILED - {str(e)}")
        
        # Summary
        passed_tests = sum(test_results.values())
        total_tests = len(test_results)
        
        print("\n" + "="*60)
        print(f"PERSISTENCE TESTS SUMMARY: {passed_tests}/{total_tests} PASSED")
        print("="*60)
        
        if passed_tests == total_tests:
            print("🎉 ALL PERSISTENCE TESTS PASSED - NO DATA LOSS ISSUES FOUND")
        else:
            print("⚠️ SOME PERSISTENCE ISSUES DETECTED - REVIEW FAILED TESTS")
        
        return test_results

if __name__ == '__main__':
    # Run the specific persistence tests
    unittest.main(verbosity=2)