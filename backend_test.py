import requests
import unittest
import json
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/frontend/.env')

class CabinetMedicalAPITest(unittest.TestCase):
    def setUp(self):
        # Use the correct backend URL from environment
        backend_url = os.getenv('REACT_APP_BACKEND_URL', 'https://d4210c95-944d-4c06-b93f-bb8c2c6cfe69.preview.emergentagent.com')
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
    
    def test_root_endpoint(self):
        """Test the root endpoint"""
        response = requests.get(f"{self.base_url}/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["message"], "Cabinet Médical API")
    
    def test_dashboard_endpoint(self):
        """Test the dashboard endpoint"""
        response = requests.get(f"{self.base_url}/api/dashboard")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify dashboard data structure
        self.assertIn("total_rdv", data)
        self.assertIn("rdv_restants", data)
        self.assertIn("rdv_attente", data)
        self.assertIn("rdv_en_cours", data)
        self.assertIn("rdv_termines", data)
        self.assertIn("recette_jour", data)
        self.assertIn("total_patients", data)
        self.assertIn("duree_attente_moyenne", data)
    
    def test_patients_crud(self):
        """Test CRUD operations for patients"""
        # Get all patients
        response = requests.get(f"{self.base_url}/api/patients")
        self.assertEqual(response.status_code, 200)
        initial_patients = response.json()
        self.assertIsInstance(initial_patients, list)
        
        # Create a new patient
        new_patient = {
            "nom": "Test",
            "prenom": "Patient",
            "date_naissance": "2020-01-01",
            "sexe": "M",
            "telephone": "0600000000",
            "adresse": "123 Test Street",
            "nom_parent": "Parent Test",
            "telephone_parent": "0600000001",
            "assurance": "Test Assurance",
            "numero_assurance": "12345",
            "allergies": "None",
            "antecedents": "None"
        }
        
        response = requests.post(f"{self.base_url}/api/patients", json=new_patient)
        self.assertEqual(response.status_code, 200)
        create_data = response.json()
        self.assertIn("patient_id", create_data)
        patient_id = create_data["patient_id"]
        
        # Get the created patient
        response = requests.get(f"{self.base_url}/api/patients/{patient_id}")
        self.assertEqual(response.status_code, 200)
        patient_data = response.json()
        self.assertEqual(patient_data["nom"], "Test")
        self.assertEqual(patient_data["prenom"], "Patient")
        
        # Update the patient
        updated_patient = patient_data.copy()
        updated_patient["nom"] = "Updated"
        updated_patient["prenom"] = "Name"
        
        response = requests.put(f"{self.base_url}/api/patients/{patient_id}", json=updated_patient)
        self.assertEqual(response.status_code, 200)
        
        # Verify the update
        response = requests.get(f"{self.base_url}/api/patients/{patient_id}")
        self.assertEqual(response.status_code, 200)
        updated_data = response.json()
        self.assertEqual(updated_data["nom"], "Updated")
        self.assertEqual(updated_data["prenom"], "Name")
        
        # Delete the patient
        response = requests.delete(f"{self.base_url}/api/patients/{patient_id}")
        self.assertEqual(response.status_code, 200)
        
        # Verify deletion
        response = requests.get(f"{self.base_url}/api/patients/{patient_id}")
        self.assertEqual(response.status_code, 404)
    
    def test_appointments_crud(self):
        """Test CRUD operations for appointments"""
        # Get all patients to use a valid patient_id
        response = requests.get(f"{self.base_url}/api/patients")
        self.assertEqual(response.status_code, 200)
        patients = response.json()
        self.assertTrue(len(patients) > 0, "No patients found for testing appointments")
        
        patient_id = patients[0]["id"]
        
        # Get all appointments
        response = requests.get(f"{self.base_url}/api/appointments")
        self.assertEqual(response.status_code, 200)
        initial_appointments = response.json()
        self.assertIsInstance(initial_appointments, list)
        
        # Create a new appointment
        today = datetime.now().strftime("%Y-%m-%d")
        new_appointment = {
            "patient_id": patient_id,
            "date": today,
            "heure": "14:30",
            "type_rdv": "visite",
            "motif": "Test appointment",
            "notes": "Test notes"
        }
        
        response = requests.post(f"{self.base_url}/api/appointments", json=new_appointment)
        self.assertEqual(response.status_code, 200)
        create_data = response.json()
        self.assertIn("appointment_id", create_data)
        appointment_id = create_data["appointment_id"]
        
        # Get today's appointments
        response = requests.get(f"{self.base_url}/api/appointments/today")
        self.assertEqual(response.status_code, 200)
        today_appointments = response.json()
        self.assertIsInstance(today_appointments, list)
        
        # Update the appointment status
        appointment_to_update = None
        for appt in today_appointments:
            if appt["id"] == appointment_id:
                appointment_to_update = appt
                break
        
        self.assertIsNotNone(appointment_to_update, "Created appointment not found in today's appointments")
        
        appointment_to_update["statut"] = "attente"
        appointment_to_update["salle"] = "salle1"
        
        response = requests.put(f"{self.base_url}/api/appointments/{appointment_id}", json=appointment_to_update)
        self.assertEqual(response.status_code, 200)
        
        # Verify the update
        response = requests.get(f"{self.base_url}/api/appointments/today")
        self.assertEqual(response.status_code, 200)
        updated_appointments = response.json()
        
        updated_appointment = None
        for appt in updated_appointments:
            if appt["id"] == appointment_id:
                updated_appointment = appt
                break
        
        self.assertIsNotNone(updated_appointment, "Updated appointment not found")
        self.assertEqual(updated_appointment["statut"], "attente")
        self.assertEqual(updated_appointment["salle"], "salle1")
        
        # Delete the appointment
        response = requests.delete(f"{self.base_url}/api/appointments/{appointment_id}")
        self.assertEqual(response.status_code, 200)
    
    def test_consultations(self):
        """Test consultations endpoints"""
        # Get all consultations
        response = requests.get(f"{self.base_url}/api/consultations")
        self.assertEqual(response.status_code, 200)
        consultations = response.json()
        self.assertIsInstance(consultations, list)
        
        # Get patients and appointments to create a new consultation
        patients_response = requests.get(f"{self.base_url}/api/patients")
        self.assertEqual(patients_response.status_code, 200)
        patients = patients_response.json()
        
        appointments_response = requests.get(f"{self.base_url}/api/appointments/today")
        self.assertEqual(appointments_response.status_code, 200)
        appointments = appointments_response.json()
        
        if len(patients) > 0 and len(appointments) > 0:
            patient_id = patients[0]["id"]
            appointment_id = appointments[0]["id"]
            
            # Create a new consultation
            today = datetime.now().strftime("%Y-%m-%d")
            new_consultation = {
                "patient_id": patient_id,
                "appointment_id": appointment_id,
                "date": today,
                "duree": 20,
                "poids": 12.5,
                "taille": 85.0,
                "pc": 47.0,
                "observations": "Test observation",
                "traitement": "Test treatment",
                "bilan": "Test results",
                "relance_date": ""
            }
            
            response = requests.post(f"{self.base_url}/api/consultations", json=new_consultation)
            self.assertEqual(response.status_code, 200)
            
            # Get patient consultations
            response = requests.get(f"{self.base_url}/api/consultations/patient/{patient_id}")
            self.assertEqual(response.status_code, 200)
            patient_consultations = response.json()
            self.assertIsInstance(patient_consultations, list)
    
    def test_payments(self):
        """Test payments endpoints"""
        # Get all payments
        response = requests.get(f"{self.base_url}/api/payments")
        self.assertEqual(response.status_code, 200)
        payments = response.json()
        self.assertIsInstance(payments, list)
        
        # Get patients and appointments to create a new payment
        patients_response = requests.get(f"{self.base_url}/api/patients")
        self.assertEqual(patients_response.status_code, 200)
        patients = patients_response.json()
        
        appointments_response = requests.get(f"{self.base_url}/api/appointments/today")
        self.assertEqual(appointments_response.status_code, 200)
        appointments = appointments_response.json()
        
        if len(patients) > 0 and len(appointments) > 0:
            patient_id = patients[0]["id"]
            appointment_id = appointments[0]["id"]
            
            # Create a new payment
            today = datetime.now().strftime("%Y-%m-%d")
            new_payment = {
                "patient_id": patient_id,
                "appointment_id": appointment_id,
                "montant": 300.0,
                "type_paiement": "espece",
                "statut": "paye",
                "date": today
            }
            
            response = requests.post(f"{self.base_url}/api/payments", json=new_payment)
            self.assertEqual(response.status_code, 200)

if __name__ == "__main__":
    unittest.main()