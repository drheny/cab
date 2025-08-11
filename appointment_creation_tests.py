import requests
import unittest
import json
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import re

# Load environment variables
load_dotenv('/app/frontend/.env')

class AppointmentCreationTest(unittest.TestCase):
    def setUp(self):
        # Use the correct backend URL from environment
        backend_url = os.getenv('REACT_APP_BACKEND_URL', 'https://e095a16b-4f79-4d50-8576-cad954291484.preview.emergentagent.com')
        self.base_url = backend_url
        print(f"Testing backend at: {self.base_url}")
    
    def test_appointment_creation_valid_data(self):
        """Test POST /api/appointments with valid complete data"""
        # Get a valid patient for testing
        response = requests.get(f"{self.base_url}/api/patients")
        self.assertEqual(response.status_code, 200)
        patients_data = response.json()
        patients = patients_data["patients"]
        self.assertTrue(len(patients) > 0, "No patients found for testing")
        
        patient_id = patients[0]["id"]
        
        # Test with complete valid data
        appointment_data = {
            "patient_id": patient_id,
            "date": "2025-01-25",
            "heure": "10:00",
            "type_rdv": "visite",
            "motif": "Consultation de routine",
            "notes": "RDV créé via bouton rapide",
            "salle": "salle1",
            "statut": "programme"
        }
        
        response = requests.post(f"{self.base_url}/api/appointments", json=appointment_data)
        self.assertEqual(response.status_code, 200)
        
        # Verify response structure
        create_data = response.json()
        self.assertIn("message", create_data)
        self.assertIn("appointment_id", create_data)
        self.assertIsInstance(create_data["appointment_id"], str)
        
        appointment_id = create_data["appointment_id"]
        
        # Verify appointment was created in database
        response = requests.get(f"{self.base_url}/api/rdv/jour/2025-01-25")
        self.assertEqual(response.status_code, 200)
        appointments = response.json()
        
        created_appointment = None
        for appt in appointments:
            if appt["id"] == appointment_id:
                created_appointment = appt
                break
        
        self.assertIsNotNone(created_appointment, "Created appointment not found in database")
        self.assertEqual(created_appointment["patient_id"], patient_id)
        self.assertEqual(created_appointment["date"], "2025-01-25")
        self.assertEqual(created_appointment["heure"], "10:00")
        self.assertEqual(created_appointment["type_rdv"], "visite")
        self.assertEqual(created_appointment["motif"], "Consultation de routine")
        
        # Clean up
        requests.delete(f"{self.base_url}/api/appointments/{appointment_id}")
    
    def test_appointment_creation_minimal_data(self):
        """Test POST /api/appointments with only required fields"""
        # Get a valid patient for testing
        response = requests.get(f"{self.base_url}/api/patients")
        self.assertEqual(response.status_code, 200)
        patients_data = response.json()
        patients = patients_data["patients"]
        self.assertTrue(len(patients) > 0, "No patients found for testing")
        
        patient_id = patients[0]["id"]
        
        # Test with minimal required data only
        minimal_appointment_data = {
            "patient_id": patient_id,
            "date": "2025-01-25",
            "heure": "14:30",
            "type_rdv": "controle"
        }
        
        response = requests.post(f"{self.base_url}/api/appointments", json=minimal_appointment_data)
        self.assertEqual(response.status_code, 200)
        
        # Verify response structure
        create_data = response.json()
        self.assertIn("message", create_data)
        self.assertIn("appointment_id", create_data)
        
        appointment_id = create_data["appointment_id"]
        
        # Verify appointment was created with defaults
        response = requests.get(f"{self.base_url}/api/rdv/jour/2025-01-25")
        self.assertEqual(response.status_code, 200)
        appointments = response.json()
        
        created_appointment = None
        for appt in appointments:
            if appt["id"] == appointment_id:
                created_appointment = appt
                break
        
        self.assertIsNotNone(created_appointment, "Created appointment not found")
        self.assertEqual(created_appointment["patient_id"], patient_id)
        self.assertEqual(created_appointment["date"], "2025-01-25")
        self.assertEqual(created_appointment["heure"], "14:30")
        self.assertEqual(created_appointment["type_rdv"], "controle")
        
        # Verify default values
        self.assertEqual(created_appointment["statut"], "programme")
        self.assertEqual(created_appointment["salle"], "")
        self.assertEqual(created_appointment["motif"], "")
        self.assertEqual(created_appointment["notes"], "")
        self.assertEqual(created_appointment["paye"], False)
        self.assertEqual(created_appointment["assure"], False)
        
        # Clean up
        requests.delete(f"{self.base_url}/api/appointments/{appointment_id}")
    
    def test_appointment_creation_validation_missing_patient_id(self):
        """Test POST /api/appointments with missing patient_id"""
        appointment_data = {
            "date": "2025-01-25",
            "heure": "10:00",
            "type_rdv": "visite",
            "motif": "Test sans patient_id"
        }
        
        response = requests.post(f"{self.base_url}/api/appointments", json=appointment_data)
        # Should return validation error
        self.assertNotEqual(response.status_code, 200)
        self.assertIn(response.status_code, [400, 422])  # Bad request or validation error
    
    def test_appointment_creation_validation_missing_date(self):
        """Test POST /api/appointments with missing date"""
        # Get a valid patient
        response = requests.get(f"{self.base_url}/api/patients")
        self.assertEqual(response.status_code, 200)
        patients_data = response.json()
        patients = patients_data["patients"]
        patient_id = patients[0]["id"]
        
        appointment_data = {
            "patient_id": patient_id,
            "heure": "10:00",
            "type_rdv": "visite",
            "motif": "Test sans date"
        }
        
        response = requests.post(f"{self.base_url}/api/appointments", json=appointment_data)
        # Should return validation error
        self.assertNotEqual(response.status_code, 200)
        self.assertIn(response.status_code, [400, 422])
    
    def test_appointment_creation_validation_missing_heure(self):
        """Test POST /api/appointments with missing heure"""
        # Get a valid patient
        response = requests.get(f"{self.base_url}/api/patients")
        self.assertEqual(response.status_code, 200)
        patients_data = response.json()
        patients = patients_data["patients"]
        patient_id = patients[0]["id"]
        
        appointment_data = {
            "patient_id": patient_id,
            "date": "2025-01-25",
            "type_rdv": "visite",
            "motif": "Test sans heure"
        }
        
        response = requests.post(f"{self.base_url}/api/appointments", json=appointment_data)
        # Should return validation error
        self.assertNotEqual(response.status_code, 200)
        self.assertIn(response.status_code, [400, 422])
    
    def test_appointment_creation_validation_missing_type_rdv(self):
        """Test POST /api/appointments with missing type_rdv"""
        # Get a valid patient
        response = requests.get(f"{self.base_url}/api/patients")
        self.assertEqual(response.status_code, 200)
        patients_data = response.json()
        patients = patients_data["patients"]
        patient_id = patients[0]["id"]
        
        appointment_data = {
            "patient_id": patient_id,
            "date": "2025-01-25",
            "heure": "10:00",
            "motif": "Test sans type_rdv"
        }
        
        response = requests.post(f"{self.base_url}/api/appointments", json=appointment_data)
        # Should return validation error
        self.assertNotEqual(response.status_code, 200)
        self.assertIn(response.status_code, [400, 422])
    
    def test_appointment_creation_response_structure(self):
        """Test POST /api/appointments response structure validation"""
        # Get a valid patient
        response = requests.get(f"{self.base_url}/api/patients")
        self.assertEqual(response.status_code, 200)
        patients_data = response.json()
        patients = patients_data["patients"]
        patient_id = patients[0]["id"]
        
        appointment_data = {
            "patient_id": patient_id,
            "date": "2025-01-25",
            "heure": "11:00",
            "type_rdv": "visite",
            "motif": "Test structure réponse"
        }
        
        response = requests.post(f"{self.base_url}/api/appointments", json=appointment_data)
        self.assertEqual(response.status_code, 200)
        
        # Verify response structure
        create_data = response.json()
        
        # Must contain message
        self.assertIn("message", create_data)
        self.assertIsInstance(create_data["message"], str)
        self.assertTrue(len(create_data["message"]) > 0)
        
        # Must contain appointment_id
        self.assertIn("appointment_id", create_data)
        self.assertIsInstance(create_data["appointment_id"], str)
        self.assertTrue(len(create_data["appointment_id"]) > 0)
        
        # appointment_id should be a valid UUID format
        appointment_id = create_data["appointment_id"]
        uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
        self.assertTrue(re.match(uuid_pattern, appointment_id, re.IGNORECASE), 
                       f"appointment_id should be UUID format: {appointment_id}")
        
        # Clean up
        requests.delete(f"{self.base_url}/api/appointments/{appointment_id}")
    
    def test_appointment_creation_realistic_data(self):
        """Test POST /api/appointments with realistic medical data"""
        # Get a valid patient
        response = requests.get(f"{self.base_url}/api/patients")
        self.assertEqual(response.status_code, 200)
        patients_data = response.json()
        patients = patients_data["patients"]
        patient_id = patients[0]["id"]
        
        # Test realistic appointment scenarios
        realistic_appointments = [
            {
                "patient_id": patient_id,
                "date": "2025-01-25",
                "heure": "09:00",
                "type_rdv": "visite",
                "motif": "Fièvre et toux depuis 3 jours",
                "notes": "Patient signale fatigue importante"
            },
            {
                "patient_id": patient_id,
                "date": "2025-01-25",
                "heure": "10:15",
                "type_rdv": "controle",
                "motif": "Contrôle vaccination DTC",
                "notes": "Vérifier réaction vaccinale"
            },
            {
                "patient_id": patient_id,
                "date": "2025-01-25",
                "heure": "14:00",
                "type_rdv": "visite",
                "motif": "Consultation de routine - bilan de santé",
                "notes": "Examen complet demandé par les parents"
            }
        ]
        
        created_appointments = []
        
        for appointment_data in realistic_appointments:
            response = requests.post(f"{self.base_url}/api/appointments", json=appointment_data)
            self.assertEqual(response.status_code, 200)
            
            create_data = response.json()
            self.assertIn("appointment_id", create_data)
            created_appointments.append(create_data["appointment_id"])
        
        # Verify all appointments were created
        response = requests.get(f"{self.base_url}/api/rdv/jour/2025-01-25")
        self.assertEqual(response.status_code, 200)
        appointments = response.json()
        
        for appointment_id in created_appointments:
            found = False
            for appt in appointments:
                if appt["id"] == appointment_id:
                    found = True
                    # Verify patient info is included
                    self.assertIn("patient", appt)
                    break
            self.assertTrue(found, f"Appointment {appointment_id} not found in database")
        
        # Clean up all created appointments
        for appointment_id in created_appointments:
            requests.delete(f"{self.base_url}/api/appointments/{appointment_id}")

if __name__ == '__main__':
    unittest.main()