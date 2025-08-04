import requests
import unittest
import json
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/frontend/.env')

class ConsultationSavingTest(unittest.TestCase):
    def setUp(self):
        # Use the correct backend URL from environment
        backend_url = os.getenv('REACT_APP_BACKEND_URL', 'https://b803181f-f839-43f3-84a6-878cc4b3cb9f.preview.emergentagent.com')
        self.base_url = backend_url
        print(f"Testing backend at: {self.base_url}")
        # Initialize demo data before running tests
        self.init_demo_data()
    
    def init_demo_data(self):
        """Initialize demo data for testing"""
        try:
            response = requests.get(f"{self.base_url}/api/init-demo")
            self.assertEqual(response.status_code, 200)
            print("Demo data initialized successfully")
        except Exception as e:
            print(f"Error initializing demo data: {e}")

    # ========== CONSULTATION SAVING FUNCTIONALITY TESTS ==========
    
    def test_consultation_saving_workflow_complete(self):
        """Test complete consultation saving workflow as reported in the review request"""
        print("\n🔍 Testing Consultation Saving Functionality - Complete Workflow")
        
        # Step 1: Initialize demo data and create test appointments in "en_cours" status
        response = requests.get(f"{self.base_url}/api/init-demo")
        self.assertEqual(response.status_code, 200)
        print("✅ Demo data initialized")
        
        # Get patients for testing
        response = requests.get(f"{self.base_url}/api/patients")
        self.assertEqual(response.status_code, 200)
        patients_data = response.json()
        patients = patients_data["patients"]
        self.assertTrue(len(patients) >= 2, "Need at least 2 patients for testing")
        
        patient1_id = patients[0]["id"]
        patient2_id = patients[1]["id"]
        
        # Create test appointments in "en_cours" status
        today = datetime.now().strftime("%Y-%m-%d")
        test_appointments = [
            {
                "patient_id": patient1_id,
                "date": today,
                "heure": "10:00",
                "type_rdv": "visite",
                "motif": "Consultation pédiatrique",
                "statut": "en_cours",
                "salle": "salle1"
            },
            {
                "patient_id": patient2_id,
                "date": today,
                "heure": "11:00", 
                "type_rdv": "controle",
                "motif": "Contrôle vaccination",
                "statut": "en_cours",
                "salle": "salle2"
            }
        ]
        
        created_appointments = []
        for appt_data in test_appointments:
            # Create appointment
            response = requests.post(f"{self.base_url}/api/appointments", json=appt_data)
            self.assertEqual(response.status_code, 200)
            appointment_id = response.json()["appointment_id"]
            created_appointments.append(appointment_id)
            
            # Update status to "en_cours"
            status_update = {"statut": "en_cours", "salle": appt_data["salle"]}
            response = requests.put(f"{self.base_url}/api/rdv/{appointment_id}/statut", json=status_update)
            self.assertEqual(response.status_code, 200)
            print(f"✅ Created appointment {appointment_id} in 'en_cours' status")
        
        # Step 2: Test consultation saving for each appointment
        consultation_test_cases = [
            {
                "appointment_id": created_appointments[0],
                "patient_id": patient1_id,
                "consultation_data": {
                    "patient_id": patient1_id,
                    "appointment_id": created_appointments[0],
                    "date": today,
                    "type_rdv": "visite",
                    "motif": "Fièvre et toux",
                    "poids": 18.5,
                    "taille": 95.0,
                    "pc": 50.2,
                    "temperature": 38.5,
                    "observation_medicale": "Enfant présente une fièvre modérée avec toux sèche. Gorge légèrement irritée. État général conservé.",
                    "traitement": "Paracétamol sirop 2.5ml toutes les 6h pendant 3 jours. Repos et hydratation abondante.",
                    "bilans": "Infection virale probable. Surveillance température. Retour si aggravation.",
                    "notes": "Parents informés des signes d'alarme. RDV contrôle si nécessaire.",
                    "relance_telephonique": True,
                    "date_relance": (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d")
                }
            },
            {
                "appointment_id": created_appointments[1],
                "patient_id": patient2_id,
                "consultation_data": {
                    "patient_id": patient2_id,
                    "appointment_id": created_appointments[1],
                    "date": today,
                    "type_rdv": "controle",
                    "motif": "Contrôle vaccination DTC",
                    "poids": 16.2,
                    "taille": 89.5,
                    "pc": 48.8,
                    "temperature": 36.8,
                    "observation_medicale": "Contrôle post-vaccination. Aucune réaction locale ou générale. Enfant en bonne santé.",
                    "traitement": "Aucun traitement nécessaire. Continuer surveillance habituelle.",
                    "bilans": "Vaccination bien tolérée. Développement normal pour l'âge.",
                    "notes": "Prochaine vaccination dans 2 mois selon calendrier vaccinal.",
                    "relance_telephonique": False,
                    "date_relance": ""
                }
            }
        ]
        
        saved_consultations = []
        
        for i, test_case in enumerate(consultation_test_cases):
            print(f"\n📋 Testing consultation saving for appointment {i+1}")
            
            # Step 3: Test POST /api/consultations - Create/save consultation
            consultation_payload = {
                "patient_id": test_case["consultation_data"]["patient_id"],
                "appointment_id": test_case["consultation_data"]["appointment_id"],
                "date": test_case["consultation_data"]["date"],
                "type_rdv": test_case["consultation_data"]["type_rdv"],
                "duree": 25,  # Default consultation duration
                "poids": test_case["consultation_data"]["poids"],
                "taille": test_case["consultation_data"]["taille"],
                "pc": test_case["consultation_data"]["pc"],
                "observations": test_case["consultation_data"]["observation_medicale"],
                "traitement": test_case["consultation_data"]["traitement"],
                "bilan": test_case["consultation_data"]["bilans"],
                "relance_date": test_case["consultation_data"]["date_relance"]
            }
            
            response = requests.post(f"{self.base_url}/api/consultations", json=consultation_payload)
            self.assertEqual(response.status_code, 200, f"Failed to create consultation: {response.text}")
            
            create_data = response.json()
            self.assertIn("message", create_data)
            self.assertIn("consultation_id", create_data)
            consultation_id = create_data["consultation_id"]
            saved_consultations.append(consultation_id)
            print(f"✅ Consultation saved successfully: {consultation_id}")
            
            # Step 4: Test PUT /api/rdv/{appointment_id}/statut - Update appointment status to "termine"
            status_update = {"statut": "termine"}
            response = requests.put(f"{self.base_url}/api/rdv/{test_case['appointment_id']}/statut", json=status_update)
            self.assertEqual(response.status_code, 200, f"Failed to update appointment status: {response.text}")
            
            status_data = response.json()
            self.assertIn("message", status_data)
            self.assertEqual(status_data["statut"], "termine")
            print(f"✅ Appointment status updated to 'termine'")
            
            # Step 5: Verify consultation was saved correctly
            response = requests.get(f"{self.base_url}/api/consultations")
            self.assertEqual(response.status_code, 200)
            all_consultations = response.json()
            
            # Find our saved consultation
            saved_consultation = None
            for consultation in all_consultations:
                if consultation["id"] == consultation_id:
                    saved_consultation = consultation
                    break
            
            self.assertIsNotNone(saved_consultation, "Saved consultation not found in database")
            
            # Verify consultation data
            self.assertEqual(saved_consultation["patient_id"], test_case["consultation_data"]["patient_id"])
            self.assertEqual(saved_consultation["appointment_id"], test_case["consultation_data"]["appointment_id"])
            self.assertEqual(saved_consultation["date"], test_case["consultation_data"]["date"])
            self.assertEqual(saved_consultation["type_rdv"], test_case["consultation_data"]["type_rdv"])
            self.assertEqual(saved_consultation["poids"], test_case["consultation_data"]["poids"])
            self.assertEqual(saved_consultation["taille"], test_case["consultation_data"]["taille"])
            self.assertEqual(saved_consultation["pc"], test_case["consultation_data"]["pc"])
            self.assertEqual(saved_consultation["observations"], test_case["consultation_data"]["observation_medicale"])
            self.assertEqual(saved_consultation["traitement"], test_case["consultation_data"]["traitement"])
            self.assertEqual(saved_consultation["bilan"], test_case["consultation_data"]["bilans"])
            self.assertEqual(saved_consultation["relance_date"], test_case["consultation_data"]["date_relance"])
            print(f"✅ Consultation data verified in database")
        
        # Step 6: Test GET /api/rdv/jour/{date} - Verify data refresh works after saving
        response = requests.get(f"{self.base_url}/api/rdv/jour/{today}")
        self.assertEqual(response.status_code, 200)
        appointments_today = response.json()
        
        # Verify appointments are now marked as "termine"
        for appointment_id in created_appointments:
            appointment_found = None
            for appt in appointments_today:
                if appt["id"] == appointment_id:
                    appointment_found = appt
                    break
            
            self.assertIsNotNone(appointment_found, f"Appointment {appointment_id} not found in today's appointments")
            self.assertEqual(appointment_found["statut"], "termine", f"Appointment {appointment_id} status not updated to 'termine'")
            print(f"✅ Appointment {appointment_id} status verified as 'termine' in daily view")
        
        print(f"✅ Data refresh verification completed")
        
        # Step 7: Test consultation retrieval by patient
        for i, test_case in enumerate(consultation_test_cases):
            patient_id = test_case["patient_id"]
            response = requests.get(f"{self.base_url}/api/patients/{patient_id}/consultations")
            self.assertEqual(response.status_code, 200)
            patient_consultations = response.json()
            
            # Find our consultation in patient's consultation history
            consultation_found = False
            for consultation in patient_consultations:
                if consultation["id"] == saved_consultations[i]:
                    consultation_found = True
                    break
            
            self.assertTrue(consultation_found, f"Consultation not found in patient {patient_id} history")
            print(f"✅ Consultation found in patient {patient_id} consultation history")
        
        # Clean up created data
        for consultation_id in saved_consultations:
            requests.delete(f"{self.base_url}/api/consultations/{consultation_id}")
        
        for appointment_id in created_appointments:
            requests.delete(f"{self.base_url}/api/appointments/{appointment_id}")
        
        print(f"\n🎉 CONSULTATION SAVING WORKFLOW TEST: ALL TESTS PASSED")
        print(f"✅ POST /api/consultations - Working correctly")
        print(f"✅ PUT /api/rdv/{{appointment_id}}/statut - Working correctly") 
        print(f"✅ GET /api/rdv/jour/{{date}} - Data refresh working correctly")
        print(f"✅ Complete consultation saving workflow functional")
    
    def test_consultation_saving_error_handling(self):
        """Test error handling in consultation saving process"""
        print("\n🔍 Testing Consultation Saving - Error Handling")
        
        # Test 1: Missing required fields
        invalid_consultation_data = [
            {
                "name": "Missing patient_id",
                "data": {
                    "appointment_id": "test_appt_id",
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "observations": "Test observation"
                }
            },
            {
                "name": "Missing appointment_id", 
                "data": {
                    "patient_id": "test_patient_id",
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "observations": "Test observation"
                }
            },
            {
                "name": "Missing date",
                "data": {
                    "patient_id": "test_patient_id",
                    "appointment_id": "test_appt_id",
                    "observations": "Test observation"
                }
            }
        ]
        
        for test_case in invalid_consultation_data:
            response = requests.post(f"{self.base_url}/api/consultations", json=test_case["data"])
            self.assertNotEqual(response.status_code, 200, f"Should reject consultation with {test_case['name']}")
            print(f"✅ Correctly rejected consultation with {test_case['name']}")
        
        # Test 2: Invalid appointment status update
        response = requests.put(f"{self.base_url}/api/rdv/nonexistent_appointment/statut", json={"statut": "termine"})
        self.assertEqual(response.status_code, 404, "Should return 404 for nonexistent appointment")
        print(f"✅ Correctly handled nonexistent appointment status update")
        
        # Test 3: Invalid status values
        # First create a valid appointment
        response = requests.get(f"{self.base_url}/api/patients")
        self.assertEqual(response.status_code, 200)
        patients = response.json()["patients"]
        if len(patients) > 0:
            patient_id = patients[0]["id"]
            
            # Create test appointment
            appointment_data = {
                "patient_id": patient_id,
                "date": datetime.now().strftime("%Y-%m-%d"),
                "heure": "15:00",
                "type_rdv": "visite",
                "motif": "Test error handling"
            }
            
            response = requests.post(f"{self.base_url}/api/appointments", json=appointment_data)
            self.assertEqual(response.status_code, 200)
            appointment_id = response.json()["appointment_id"]
            
            # Test invalid status
            invalid_statuses = ["invalid_status", "completed", "finished", ""]
            for invalid_status in invalid_statuses:
                response = requests.put(f"{self.base_url}/api/rdv/{appointment_id}/statut", json={"statut": invalid_status})
                self.assertEqual(response.status_code, 400, f"Should reject invalid status: {invalid_status}")
                print(f"✅ Correctly rejected invalid status: {invalid_status}")
            
            # Clean up
            requests.delete(f"{self.base_url}/api/appointments/{appointment_id}")
        
        print(f"🎉 CONSULTATION SAVING ERROR HANDLING: ALL TESTS PASSED")
    
    def test_consultation_saving_with_relance_fields(self):
        """Test consultation saving with relance_telephonique and date_relance fields"""
        print("\n🔍 Testing Consultation Saving - Relance Fields")
        
        # Get test data
        response = requests.get(f"{self.base_url}/api/patients")
        self.assertEqual(response.status_code, 200)
        patients = response.json()["patients"]
        self.assertTrue(len(patients) > 0, "Need at least 1 patient for testing")
        
        patient_id = patients[0]["id"]
        today = datetime.now().strftime("%Y-%m-%d")
        future_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        
        # Create test appointment
        appointment_data = {
            "patient_id": patient_id,
            "date": today,
            "heure": "14:00",
            "type_rdv": "visite",
            "motif": "Test relance fields"
        }
        
        response = requests.post(f"{self.base_url}/api/appointments", json=appointment_data)
        self.assertEqual(response.status_code, 200)
        appointment_id = response.json()["appointment_id"]
        
        # Test consultation with relance fields
        consultation_with_relance = {
            "patient_id": patient_id,
            "appointment_id": appointment_id,
            "date": today,
            "type_rdv": "visite",
            "duree": 30,
            "poids": 20.0,
            "taille": 100.0,
            "pc": 51.0,
            "observations": "Consultation avec relance programmée. Patient nécessite un suivi téléphonique.",
            "traitement": "Traitement prescrit avec surveillance nécessaire.",
            "bilan": "Évolution à surveiller. Relance téléphonique programmée.",
            "relance_date": future_date  # This is the key field for phone reminders
        }
        
        response = requests.post(f"{self.base_url}/api/consultations", json=consultation_with_relance)
        self.assertEqual(response.status_code, 200)
        consultation_id = response.json()["consultation_id"]
        print(f"✅ Consultation with relance_date saved successfully")
        
        # Verify consultation was saved with relance_date
        response = requests.get(f"{self.base_url}/api/consultations")
        self.assertEqual(response.status_code, 200)
        all_consultations = response.json()
        
        saved_consultation = None
        for consultation in all_consultations:
            if consultation["id"] == consultation_id:
                saved_consultation = consultation
                break
        
        self.assertIsNotNone(saved_consultation, "Consultation with relance not found")
        self.assertEqual(saved_consultation["relance_date"], future_date)
        print(f"✅ Relance date verified: {saved_consultation['relance_date']}")
        
        # Test consultation without relance (empty relance_date)
        consultation_without_relance = {
            "patient_id": patient_id,
            "appointment_id": appointment_id,
            "date": today,
            "type_rdv": "visite",
            "observations": "Consultation sans relance nécessaire.",
            "traitement": "Traitement standard sans suivi particulier.",
            "bilan": "Évolution normale, pas de relance nécessaire.",
            "relance_date": ""  # Empty relance_date
        }
        
        # Update the existing consultation
        response = requests.put(f"{self.base_url}/api/consultations/{consultation_id}", json=consultation_without_relance)
        self.assertEqual(response.status_code, 200)
        print(f"✅ Consultation updated without relance_date")
        
        # Verify update
        response = requests.get(f"{self.base_url}/api/consultations")
        self.assertEqual(response.status_code, 200)
        all_consultations = response.json()
        
        updated_consultation = None
        for consultation in all_consultations:
            if consultation["id"] == consultation_id:
                updated_consultation = consultation
                break
        
        self.assertIsNotNone(updated_consultation, "Updated consultation not found")
        self.assertEqual(updated_consultation["relance_date"], "")
        print(f"✅ Empty relance_date verified")
        
        # Clean up
        requests.delete(f"{self.base_url}/api/consultations/{consultation_id}")
        requests.delete(f"{self.base_url}/api/appointments/{appointment_id}")
        
        print(f"🎉 CONSULTATION RELANCE FIELDS TEST: ALL TESTS PASSED")
    
    def test_consultation_data_persistence_and_retrieval(self):
        """Test that consultation data persists correctly and can be retrieved"""
        print("\n🔍 Testing Consultation Data Persistence and Retrieval")
        
        # Get test data
        response = requests.get(f"{self.base_url}/api/patients")
        self.assertEqual(response.status_code, 200)
        patients = response.json()["patients"]
        self.assertTrue(len(patients) > 0, "Need at least 1 patient for testing")
        
        patient_id = patients[0]["id"]
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Create test appointment
        appointment_data = {
            "patient_id": patient_id,
            "date": today,
            "heure": "16:00",
            "type_rdv": "visite",
            "motif": "Test data persistence"
        }
        
        response = requests.post(f"{self.base_url}/api/appointments", json=appointment_data)
        self.assertEqual(response.status_code, 200)
        appointment_id = response.json()["appointment_id"]
        
        # Create comprehensive consultation data
        comprehensive_consultation = {
            "patient_id": patient_id,
            "appointment_id": appointment_id,
            "date": today,
            "type_rdv": "visite",
            "duree": 35,
            "poids": 22.5,
            "taille": 105.0,
            "pc": 52.0,
            "observations": "Consultation complète avec examen détaillé. Patient présente des symptômes légers mais nécessite surveillance. Température normale, état général bon. Examen clinique sans particularité notable.",
            "traitement": "Prescription de paracétamol en cas de fièvre. Repos recommandé. Hydratation abondante. Surveillance des symptômes pendant 48h.",
            "bilan": "Infection virale probable en cours de résolution. Pronostic favorable. Évolution attendue sous 3-5 jours. Pas de complications prévues.",
            "relance_date": (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d")
        }
        
        # Save consultation
        response = requests.post(f"{self.base_url}/api/consultations", json=comprehensive_consultation)
        self.assertEqual(response.status_code, 200)
        consultation_id = response.json()["consultation_id"]
        print(f"✅ Comprehensive consultation saved")
        
        # Test 1: Retrieve via general consultations endpoint
        response = requests.get(f"{self.base_url}/api/consultations")
        self.assertEqual(response.status_code, 200)
        all_consultations = response.json()
        
        found_consultation = None
        for consultation in all_consultations:
            if consultation["id"] == consultation_id:
                found_consultation = consultation
                break
        
        self.assertIsNotNone(found_consultation, "Consultation not found in general endpoint")
        
        # Verify all fields are preserved
        for field, expected_value in comprehensive_consultation.items():
            if field in found_consultation:
                self.assertEqual(found_consultation[field], expected_value, f"Field {field} not preserved correctly")
        
        print(f"✅ All consultation fields preserved in general endpoint")
        
        # Test 2: Retrieve via patient-specific consultations endpoint
        response = requests.get(f"{self.base_url}/api/patients/{patient_id}/consultations")
        self.assertEqual(response.status_code, 200)
        patient_consultations = response.json()
        
        found_in_patient_history = False
        for consultation in patient_consultations:
            if consultation["id"] == consultation_id:
                found_in_patient_history = True
                # Verify key fields are present
                self.assertIn("date", consultation)
                self.assertIn("type", consultation)
                self.assertIn("observations", consultation)
                self.assertIn("traitement", consultation)
                self.assertIn("bilan", consultation)
                break
        
        self.assertTrue(found_in_patient_history, "Consultation not found in patient history")
        print(f"✅ Consultation found in patient consultation history")
        
        # Test 3: Update consultation and verify persistence
        updated_data = {
            "observations": "Consultation mise à jour avec nouvelles observations. Amélioration notable des symptômes.",
            "traitement": "Traitement modifié selon évolution. Réduction posologie.",
            "bilan": "Évolution favorable confirmée. Guérison en cours.",
            "relance_date": ""  # Remove relance
        }
        
        response = requests.put(f"{self.base_url}/api/consultations/{consultation_id}", json=updated_data)
        self.assertEqual(response.status_code, 200)
        print(f"✅ Consultation updated successfully")
        
        # Verify update persistence
        response = requests.get(f"{self.base_url}/api/consultations")
        self.assertEqual(response.status_code, 200)
        all_consultations = response.json()
        
        updated_consultation = None
        for consultation in all_consultations:
            if consultation["id"] == consultation_id:
                updated_consultation = consultation
                break
        
        self.assertIsNotNone(updated_consultation, "Updated consultation not found")
        self.assertEqual(updated_consultation["observations"], updated_data["observations"])
        self.assertEqual(updated_consultation["traitement"], updated_data["traitement"])
        self.assertEqual(updated_consultation["bilan"], updated_data["bilan"])
        self.assertEqual(updated_consultation["relance_date"], updated_data["relance_date"])
        print(f"✅ Consultation updates verified")
        
        # Clean up
        requests.delete(f"{self.base_url}/api/consultations/{consultation_id}")
        requests.delete(f"{self.base_url}/api/appointments/{appointment_id}")
        
        print(f"🎉 CONSULTATION DATA PERSISTENCE TEST: ALL TESTS PASSED")

if __name__ == "__main__":
    unittest.main()