import requests
import unittest
import json
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/frontend/.env')

class MultiModalConsultationTest(unittest.TestCase):
    def setUp(self):
        # Use the correct backend URL from environment
        backend_url = os.getenv('REACT_APP_BACKEND_URL', 'https://0f556255-778a-43ef-b1e4-2e04fe02d592.preview.emergentagent.com')
        self.base_url = backend_url
        print(f"Testing backend at: {self.base_url}")
    
    def test_init_demo_data_for_multi_modal(self):
        """Test GET /api/init-demo to create demo patients and appointments for multi-modal testing"""
        print("\n=== TESTING DEMO DATA INITIALIZATION FOR MULTI-MODAL FUNCTIONALITY ===")
        
        # Initialize demo data
        response = requests.get(f"{self.base_url}/api/init-demo")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("message", data)
        print(f"✅ Demo data initialized: {data['message']}")
        
        # Verify we have patients
        response = requests.get(f"{self.base_url}/api/patients")
        self.assertEqual(response.status_code, 200)
        patients_data = response.json()
        patients = patients_data["patients"]
        self.assertGreaterEqual(len(patients), 3, "Should have at least 3 demo patients")
        print(f"✅ Found {len(patients)} demo patients")
        
        # Verify patient information is complete
        for patient in patients:
            self.assertIn("id", patient)
            self.assertIn("nom", patient)
            self.assertIn("prenom", patient)
            self.assertIn("numero_whatsapp", patient)
            print(f"   - Patient: {patient['prenom']} {patient['nom']} (ID: {patient['id']})")
        
        return patients
    
    def test_calendar_data_today(self):
        """Test GET /api/rdv/jour/{today_date} to get today's appointments"""
        print("\n=== TESTING CALENDAR DATA FOR TODAY ===")
        
        today = datetime.now().strftime("%Y-%m-%d")
        response = requests.get(f"{self.base_url}/api/rdv/jour/{today}")
        self.assertEqual(response.status_code, 200)
        appointments = response.json()
        self.assertIsInstance(appointments, list)
        print(f"✅ Found {len(appointments)} appointments for today ({today})")
        
        # Verify appointment structure and patient linkage
        for appointment in appointments:
            self.assertIn("id", appointment)
            self.assertIn("patient_id", appointment)
            self.assertIn("statut", appointment)
            self.assertIn("type_rdv", appointment)
            self.assertIn("patient", appointment)
            
            patient_info = appointment["patient"]
            self.assertIn("nom", patient_info)
            self.assertIn("prenom", patient_info)
            
            print(f"   - {appointment['heure']} | {patient_info['prenom']} {patient_info['nom']} | {appointment['type_rdv']} | {appointment['statut']}")
        
        return appointments
    
    def test_create_en_cours_appointments_for_multi_modal(self):
        """Create at least 2 appointments in 'en_cours' status for different patients to test multi-modal functionality"""
        print("\n=== CREATING EN_COURS APPOINTMENTS FOR MULTI-MODAL TESTING ===")
        
        # Get available patients
        response = requests.get(f"{self.base_url}/api/patients")
        self.assertEqual(response.status_code, 200)
        patients_data = response.json()
        patients = patients_data["patients"]
        self.assertGreaterEqual(len(patients), 2, "Need at least 2 patients for multi-modal testing")
        
        today = datetime.now().strftime("%Y-%m-%d")
        created_appointments = []
        
        # Create appointments for first 2 patients in "en_cours" status
        for i in range(min(2, len(patients))):
            patient = patients[i]
            appointment_time = f"{10 + i}:00"
            
            appointment_data = {
                "patient_id": patient["id"],
                "date": today,
                "heure": appointment_time,
                "type_rdv": "visite",
                "statut": "programme",  # Will update to en_cours after creation
                "motif": f"Consultation en cours pour test multi-modal - Patient {i+1}",
                "notes": f"Test consultation simultanée pour {patient['prenom']} {patient['nom']}"
            }
            
            # Create appointment
            response = requests.post(f"{self.base_url}/api/appointments", json=appointment_data)
            self.assertEqual(response.status_code, 200)
            create_data = response.json()
            appointment_id = create_data["appointment_id"]
            
            # Update status to "en_cours"
            response = requests.put(f"{self.base_url}/api/rdv/{appointment_id}/statut", 
                                  json={"statut": "en_cours"})
            self.assertEqual(response.status_code, 200)
            
            created_appointments.append({
                "id": appointment_id,
                "patient": patient,
                "time": appointment_time
            })
            
            print(f"✅ Created en_cours appointment for {patient['prenom']} {patient['nom']} at {appointment_time}")
        
        # Verify appointments are in "en_cours" status
        response = requests.get(f"{self.base_url}/api/rdv/jour/{today}")
        self.assertEqual(response.status_code, 200)
        appointments = response.json()
        
        en_cours_count = 0
        for appointment in appointments:
            if appointment["statut"] == "en_cours":
                en_cours_count += 1
                patient_info = appointment["patient"]
                print(f"   ✓ Confirmed en_cours: {patient_info['prenom']} {patient_info['nom']} at {appointment['heure']}")
        
        self.assertGreaterEqual(en_cours_count, 2, "Should have at least 2 appointments in en_cours status")
        print(f"✅ Total appointments in 'en_cours' status: {en_cours_count}")
        
        return created_appointments
    
    def test_patient_data_verification(self):
        """Verify we have complete patient information linked to appointments"""
        print("\n=== VERIFYING PATIENT DATA LINKAGE ===")
        
        today = datetime.now().strftime("%Y-%m-%d")
        response = requests.get(f"{self.base_url}/api/rdv/jour/{today}")
        self.assertEqual(response.status_code, 200)
        appointments = response.json()
        
        verified_patients = []
        
        for appointment in appointments:
            # Verify patient info in appointment
            self.assertIn("patient", appointment)
            patient_info = appointment["patient"]
            
            # Verify required patient fields
            required_fields = ["nom", "prenom", "numero_whatsapp", "lien_whatsapp"]
            for field in required_fields:
                self.assertIn(field, patient_info)
                self.assertIsNotNone(patient_info[field])
            
            # Get full patient data
            patient_id = appointment["patient_id"]
            response = requests.get(f"{self.base_url}/api/patients/{patient_id}")
            self.assertEqual(response.status_code, 200)
            full_patient = response.json()
            
            # Verify full patient data structure
            patient_verification = {
                "id": patient_id,
                "nom": full_patient["nom"],
                "prenom": full_patient["prenom"],
                "age": full_patient.get("age", ""),
                "numero_whatsapp": full_patient.get("numero_whatsapp", ""),
                "lien_whatsapp": full_patient.get("lien_whatsapp", ""),
                "appointment_time": appointment["heure"],
                "appointment_status": appointment["statut"]
            }
            
            verified_patients.append(patient_verification)
            print(f"✅ Verified patient: {patient_verification['prenom']} {patient_verification['nom']}")
            print(f"   - Age: {patient_verification['age']}")
            print(f"   - WhatsApp: {patient_verification['numero_whatsapp']}")
            print(f"   - Appointment: {patient_verification['appointment_time']} ({patient_verification['appointment_status']})")
        
        self.assertGreater(len(verified_patients), 0, "Should have verified at least one patient")
        print(f"✅ Total verified patients with appointments: {len(verified_patients)}")
        
        return verified_patients
    
    def test_multi_modal_backend_readiness(self):
        """Comprehensive test to ensure backend is ready for multi-instance consultation modal testing"""
        print("\n=== COMPREHENSIVE MULTI-MODAL BACKEND READINESS TEST ===")
        
        # Step 1: Initialize demo data
        print("\n1. Initializing demo data...")
        patients = self.test_init_demo_data_for_multi_modal()
        
        # Step 2: Get today's calendar data
        print("\n2. Getting today's calendar data...")
        appointments = self.test_calendar_data_today()
        
        # Step 3: Create en_cours appointments for multi-modal testing
        print("\n3. Creating en_cours appointments...")
        en_cours_appointments = self.test_create_en_cours_appointments_for_multi_modal()
        
        # Step 4: Verify patient data linkage
        print("\n4. Verifying patient data linkage...")
        verified_patients = self.test_patient_data_verification()
        
        # Step 5: Final verification for multi-modal readiness
        print("\n5. Final multi-modal readiness verification...")
        
        # Verify we have at least 2 different patients with en_cours appointments
        en_cours_patient_ids = set()
        today = datetime.now().strftime("%Y-%m-%d")
        response = requests.get(f"{self.base_url}/api/rdv/jour/{today}")
        self.assertEqual(response.status_code, 200)
        appointments = response.json()
        
        for appointment in appointments:
            if appointment["statut"] == "en_cours":
                en_cours_patient_ids.add(appointment["patient_id"])
        
        self.assertGreaterEqual(len(en_cours_patient_ids), 2, 
                               "Need at least 2 different patients with en_cours appointments for multi-modal testing")
        
        # Summary
        print(f"\n=== MULTI-MODAL BACKEND READINESS SUMMARY ===")
        print(f"✅ Demo patients available: {len(patients)}")
        print(f"✅ Total appointments today: {len(appointments)}")
        print(f"✅ Patients with en_cours appointments: {len(en_cours_patient_ids)}")
        print(f"✅ Verified patient data linkage: {len(verified_patients)}")
        print(f"✅ Backend ready for multi-instance consultation modal testing!")
        
        # Return summary for potential use
        return {
            "patients_count": len(patients),
            "appointments_count": len(appointments),
            "en_cours_patients": len(en_cours_patient_ids),
            "verified_patients": len(verified_patients),
            "ready_for_testing": True
        }


if __name__ == '__main__':
    unittest.main()