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
        """Test CRUD operations for patients with new model structure"""
        # Test GET /api/patients with pagination and search
        response = requests.get(f"{self.base_url}/api/patients?page=1&limit=10")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify pagination structure
        self.assertIn("patients", data)
        self.assertIn("total_count", data)
        self.assertIn("page", data)
        self.assertIn("limit", data)
        self.assertIn("total_pages", data)
        self.assertIsInstance(data["patients"], list)
        self.assertEqual(data["page"], 1)
        self.assertEqual(data["limit"], 10)
        
        # Test search functionality
        response = requests.get(f"{self.base_url}/api/patients?search=Ben Ahmed")
        self.assertEqual(response.status_code, 200)
        search_data = response.json()
        self.assertIn("patients", search_data)
        
        # Create a new patient with enhanced model structure
        new_patient = {
            "nom": "Testeur",
            "prenom": "Patient",
            "date_naissance": "2020-06-15",
            "adresse": "123 Rue Test, Tunis",
            "pere": {
                "nom": "Ahmed Testeur",
                "telephone": "21650987654",
                "fonction": "Ingénieur"
            },
            "mere": {
                "nom": "Fatima Testeur", 
                "telephone": "21650987655",
                "fonction": "Médecin"
            },
            "numero_whatsapp": "21650987654",
            "notes": "Patient de test pour validation",
            "antecedents": "Aucun antécédent particulier",
            "consultations": [
                {
                    "date": "2024-01-15",
                    "type": "visite",
                    "id_consultation": "test_cons_1"
                }
            ]
        }
        
        response = requests.post(f"{self.base_url}/api/patients", json=new_patient)
        self.assertEqual(response.status_code, 200)
        create_data = response.json()
        self.assertIn("patient_id", create_data)
        patient_id = create_data["patient_id"]
        
        # Get the created patient and verify computed fields
        response = requests.get(f"{self.base_url}/api/patients/{patient_id}")
        self.assertEqual(response.status_code, 200)
        patient_data = response.json()
        
        # Verify basic fields
        self.assertEqual(patient_data["nom"], "Testeur")
        self.assertEqual(patient_data["prenom"], "Patient")
        self.assertEqual(patient_data["date_naissance"], "2020-06-15")
        
        # Verify parent info structure
        self.assertIn("pere", patient_data)
        self.assertIn("mere", patient_data)
        self.assertEqual(patient_data["pere"]["nom"], "Ahmed Testeur")
        self.assertEqual(patient_data["mere"]["nom"], "Fatima Testeur")
        
        # Verify computed fields
        self.assertIn("age", patient_data)
        self.assertIn("lien_whatsapp", patient_data)
        self.assertIn("date_premiere_consultation", patient_data)
        self.assertIn("date_derniere_consultation", patient_data)
        
        # Verify age calculation (should be around 4-5 years)
        age = patient_data["age"]
        self.assertTrue("4 ans" in age or "5 ans" in age, f"Age calculation incorrect: {age}")
        
        # Verify WhatsApp link generation
        expected_whatsapp_link = "https://wa.me/21650987654"
        self.assertEqual(patient_data["lien_whatsapp"], expected_whatsapp_link)
        
        # Verify consultation dates
        self.assertEqual(patient_data["date_premiere_consultation"], "2024-01-15")
        self.assertEqual(patient_data["date_derniere_consultation"], "2024-01-15")
        
        # Update the patient with new consultation
        updated_patient = patient_data.copy()
        updated_patient["consultations"].append({
            "date": "2024-12-01",
            "type": "controle", 
            "id_consultation": "test_cons_2"
        })
        
        response = requests.put(f"{self.base_url}/api/patients/{patient_id}", json=updated_patient)
        self.assertEqual(response.status_code, 200)
        
        # Verify the update and computed fields recalculation
        response = requests.get(f"{self.base_url}/api/patients/{patient_id}")
        self.assertEqual(response.status_code, 200)
        updated_data = response.json()
        
        # Verify consultation dates were updated
        self.assertEqual(updated_data["date_premiere_consultation"], "2024-01-15")
        self.assertEqual(updated_data["date_derniere_consultation"], "2024-12-01")
        
        # Delete the patient
        response = requests.delete(f"{self.base_url}/api/patients/{patient_id}")
        self.assertEqual(response.status_code, 200)
        
        # Verify deletion
        response = requests.get(f"{self.base_url}/api/patients/{patient_id}")
        self.assertEqual(response.status_code, 404)
    
    def test_patients_count_endpoint(self):
        """Test GET /api/patients/count endpoint"""
        response = requests.get(f"{self.base_url}/api/patients/count")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("count", data)
        self.assertIsInstance(data["count"], int)
        self.assertGreaterEqual(data["count"], 0)
    
    def test_patient_consultations_endpoint(self):
        """Test GET /api/patients/{id}/consultations endpoint"""
        # Get a patient with consultations
        response = requests.get(f"{self.base_url}/api/patients")
        self.assertEqual(response.status_code, 200)
        patients_data = response.json()
        patients = patients_data["patients"]
        
        # Find a patient with consultations
        patient_with_consultations = None
        for patient in patients:
            if patient.get("consultations") and len(patient["consultations"]) > 0:
                patient_with_consultations = patient
                break
        
        if patient_with_consultations:
            patient_id = patient_with_consultations["id"]
            response = requests.get(f"{self.base_url}/api/patients/{patient_id}/consultations")
            self.assertEqual(response.status_code, 200)
            consultations = response.json()
            self.assertIsInstance(consultations, list)
            
            # Verify consultation structure
            if len(consultations) > 0:
                consultation = consultations[0]
                self.assertIn("id", consultation)
                self.assertIn("date", consultation)
                self.assertIn("type", consultation)
                self.assertIn("duree", consultation)
                self.assertIn("observations", consultation)
                self.assertIn("traitement", consultation)
                self.assertIn("bilan", consultation)
    
    def test_helper_functions_via_api(self):
        """Test helper functions through API responses"""
        # Test age calculation with different birth dates
        test_cases = [
            {
                "date_naissance": "2020-01-01",
                "expected_age_contains": ["4 ans", "5 ans"]  # Should be around 4-5 years
            },
            {
                "date_naissance": "2023-06-15", 
                "expected_age_contains": ["1 an", "2 ans"]  # Should be around 1-2 years
            }
        ]
        
        for i, test_case in enumerate(test_cases):
            # Create patient with specific birth date
            test_patient = {
                "nom": f"TestAge{i}",
                "prenom": "Patient",
                "date_naissance": test_case["date_naissance"],
                "numero_whatsapp": "21650123456"
            }
            
            response = requests.post(f"{self.base_url}/api/patients", json=test_patient)
            self.assertEqual(response.status_code, 200)
            patient_id = response.json()["patient_id"]
            
            # Get patient and verify age calculation
            response = requests.get(f"{self.base_url}/api/patients/{patient_id}")
            self.assertEqual(response.status_code, 200)
            patient_data = response.json()
            
            age = patient_data["age"]
            age_valid = any(expected in age for expected in test_case["expected_age_contains"])
            self.assertTrue(age_valid, f"Age calculation failed for {test_case['date_naissance']}: got '{age}'")
            
            # Verify WhatsApp link generation
            expected_link = "https://wa.me/21650123456"
            self.assertEqual(patient_data["lien_whatsapp"], expected_link)
            
            # Clean up
            requests.delete(f"{self.base_url}/api/patients/{patient_id}")
    
    def test_demo_data_structure(self):
        """Test that demo data has proper structure and computed fields"""
        response = requests.get(f"{self.base_url}/api/patients")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        patients = data["patients"]
        
        # Verify we have demo patients
        self.assertGreater(len(patients), 0, "No demo patients found")
        
        for patient in patients:
            # Verify required fields
            self.assertIn("nom", patient)
            self.assertIn("prenom", patient)
            self.assertIn("id", patient)
            
            # Verify new model structure
            self.assertIn("pere", patient)
            self.assertIn("mere", patient)
            self.assertIn("numero_whatsapp", patient)
            self.assertIn("lien_whatsapp", patient)
            self.assertIn("notes", patient)
            self.assertIn("antecedents", patient)
            self.assertIn("consultations", patient)
            
            # Verify computed fields
            self.assertIn("age", patient)
            self.assertIn("date_premiere_consultation", patient)
            self.assertIn("date_derniere_consultation", patient)
            
            # Verify parent info structure
            if patient["pere"]:
                self.assertIn("nom", patient["pere"])
                self.assertIn("telephone", patient["pere"])
                self.assertIn("fonction", patient["pere"])
            
            if patient["mere"]:
                self.assertIn("nom", patient["mere"])
                self.assertIn("telephone", patient["mere"])
                self.assertIn("fonction", patient["mere"])
            
            # Verify WhatsApp link format if number exists
            if patient.get("numero_whatsapp"):
                numero = patient["numero_whatsapp"]
                if numero.startswith("216") and len(numero) == 11:
                    expected_link = f"https://wa.me/{numero}"
                    self.assertEqual(patient["lien_whatsapp"], expected_link)
            
            # Verify consultation dates if consultations exist
            if patient.get("consultations") and len(patient["consultations"]) > 0:
                dates = [c["date"] for c in patient["consultations"] if c.get("date")]
                if dates:
                    sorted_dates = sorted(dates)
                    self.assertEqual(patient["date_premiere_consultation"], sorted_dates[0])
                    self.assertEqual(patient["date_derniere_consultation"], sorted_dates[-1])
    
    def test_pagination_functionality(self):
        """Test pagination with different page sizes and pages"""
        # Test different page sizes
        for limit in [5, 10, 20]:
            response = requests.get(f"{self.base_url}/api/patients?page=1&limit={limit}")
            self.assertEqual(response.status_code, 200)
            data = response.json()
            
            self.assertEqual(data["limit"], limit)
            self.assertEqual(data["page"], 1)
            self.assertLessEqual(len(data["patients"]), limit)
        
        # Test different pages
        response = requests.get(f"{self.base_url}/api/patients?page=1&limit=2")
        self.assertEqual(response.status_code, 200)
        page1_data = response.json()
        
        if page1_data["total_pages"] > 1:
            response = requests.get(f"{self.base_url}/api/patients?page=2&limit=2")
            self.assertEqual(response.status_code, 200)
            page2_data = response.json()
            
            # Verify different patients on different pages
            page1_ids = [p["id"] for p in page1_data["patients"]]
            page2_ids = [p["id"] for p in page2_data["patients"]]
            self.assertEqual(len(set(page1_ids) & set(page2_ids)), 0, "Same patients on different pages")
    
    def test_search_functionality(self):
        """Test search functionality by name and birth date"""
        # Search by nom
        response = requests.get(f"{self.base_url}/api/patients?search=Ben Ahmed")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify search results contain the search term
        for patient in data["patients"]:
            found = ("Ben Ahmed" in patient.get("nom", "") or 
                    "Ben Ahmed" in patient.get("prenom", "") or
                    "Ben Ahmed" in patient.get("date_naissance", ""))
            self.assertTrue(found, f"Search result doesn't contain 'Ben Ahmed': {patient}")
        
        # Search by prenom
        response = requests.get(f"{self.base_url}/api/patients?search=Yassine")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Search by birth date
        response = requests.get(f"{self.base_url}/api/patients?search=2020")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Search with no results
        response = requests.get(f"{self.base_url}/api/patients?search=NonExistentName")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data["patients"]), 0)
    
    def test_appointments_crud(self):
        """Test CRUD operations for appointments"""
        # Get all patients to use a valid patient_id
        response = requests.get(f"{self.base_url}/api/patients")
        self.assertEqual(response.status_code, 200)
        patients_data = response.json()
        patients = patients_data["patients"]
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
        patients_data = patients_response.json()
        patients = patients_data["patients"]
        
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