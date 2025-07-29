#!/usr/bin/env python3
"""
Comprehensive Consultation Page Quick Modal Optimization Testing
Testing the complete workflow for the new quick consultation modal implementation
"""

import requests
import unittest
import json
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/frontend/.env')

class QuickConsultationModalTest(unittest.TestCase):
    """
    Test suite for Consultation Page Quick Modal Optimization Implementation
    
    This test suite focuses on testing the complete workflow for the new quick consultation modal:
    1. Patient Management APIs (GET/POST)
    2. Appointment Management APIs (GET/POST)
    3. Payment Management APIs (GET/POST)
    4. Consultation Management APIs (GET/POST/PUT)
    5. Authentication and Security
    6. Complete workflow integration
    """
    
    def setUp(self):
        # Use the correct backend URL from environment
        backend_url = os.getenv('REACT_APP_BACKEND_URL', 'https://b41bbcdf-8fee-41b8-8d35-533fd4cb83fc.preview.emergentagent.com')
        self.base_url = backend_url
        print(f"Testing backend at: {self.base_url}")
        
        # Initialize demo data for testing
        self.init_demo_data()
        
        # Get authentication token for medecin
        self.auth_token = self.get_medecin_auth_token()
        self.auth_headers = {"Authorization": f"Bearer {self.auth_token}"}
    
    def init_demo_data(self):
        """Initialize demo data for testing"""
        try:
            response = requests.get(f"{self.base_url}/api/init-demo")
            self.assertEqual(response.status_code, 200)
            print("✅ Demo data initialized successfully")
        except Exception as e:
            print(f"❌ Error initializing demo data: {e}")
    
    def get_medecin_auth_token(self):
        """Get authentication token for medecin user"""
        login_data = {
            "username": "medecin",
            "password": "medecin123"
        }
        
        response = requests.post(f"{self.base_url}/api/auth/login", json=login_data)
        self.assertEqual(response.status_code, 200, f"Medecin login failed: {response.text}")
        
        data = response.json()
        self.assertIn("access_token", data)
        print("✅ Medecin authentication successful")
        return data["access_token"]
    
    # ========== PATIENT MANAGEMENT APIs TESTING ==========
    
    def test_patient_list_retrieval_for_dropdown(self):
        """Test GET /api/patients - verify patient list retrieval for dropdown"""
        print("\n🔍 Testing Patient List Retrieval for Dropdown")
        
        # Test patient list with pagination for dropdown
        response = requests.get(f"{self.base_url}/api/patients?page=1&limit=50", headers=self.auth_headers)
        self.assertEqual(response.status_code, 200, f"Patient list retrieval failed: {response.text}")
        
        data = response.json()
        
        # Verify response structure for dropdown usage
        self.assertIn("patients", data)
        self.assertIn("total_count", data)
        self.assertIsInstance(data["patients"], list)
        
        # Verify patient data structure for dropdown
        if len(data["patients"]) > 0:
            patient = data["patients"][0]
            required_fields = ["id", "nom", "prenom", "age", "numero_whatsapp"]
            for field in required_fields:
                self.assertIn(field, patient, f"Missing required field for dropdown: {field}")
            
            # Verify computed fields are present
            self.assertIn("age", patient)
            if patient.get("date_naissance"):
                self.assertTrue(len(patient["age"]) > 0, "Age should be calculated")
        
        print(f"✅ Patient list retrieved successfully")
        print(f"   - Total patients: {data['total_count']}")
        print(f"   - Patients in response: {len(data['patients'])}")
        print(f"🎉 Patient List Retrieval Test: PASSED")
    
    def test_new_patient_creation_minimal_data(self):
        """Test POST /api/patients - test new patient creation with minimal data (prenom, nom)"""
        print("\n🔍 Testing New Patient Creation with Minimal Data")
        
        # Test patient creation with only required fields (nom, prenom)
        minimal_patient_data = {
            "nom": "Nouveau",
            "prenom": "Patient",
            "date_naissance": "2020-01-15",  # Required for age calculation
            "numero_whatsapp": "21650123456"  # For WhatsApp functionality
        }
        
        response = requests.post(f"{self.base_url}/api/patients", json=minimal_patient_data, headers=self.auth_headers)
        self.assertEqual(response.status_code, 200, f"Patient creation failed: {response.text}")
        
        create_data = response.json()
        self.assertIn("patient_id", create_data)
        self.assertIn("message", create_data)
        
        patient_id = create_data["patient_id"]
        
        # Verify patient was created correctly
        response = requests.get(f"{self.base_url}/api/patients/{patient_id}", headers=self.auth_headers)
        self.assertEqual(response.status_code, 200)
        
        patient_data = response.json()
        
        # Verify basic fields
        self.assertEqual(patient_data["nom"], "Nouveau")
        self.assertEqual(patient_data["prenom"], "Patient")
        self.assertEqual(patient_data["date_naissance"], "2020-01-15")
        self.assertEqual(patient_data["numero_whatsapp"], "21650123456")
        
        # Verify computed fields are generated
        self.assertIn("age", patient_data)
        self.assertTrue(len(patient_data["age"]) > 0, "Age should be calculated")
        self.assertIn("lien_whatsapp", patient_data)
        self.assertEqual(patient_data["lien_whatsapp"], "https://wa.me/21650123456")
        
        # Verify default values for optional fields
        self.assertIn("pere", patient_data)
        self.assertIn("mere", patient_data)
        self.assertIn("consultations", patient_data)
        self.assertIsInstance(patient_data["consultations"], list)
        
        print(f"✅ Patient created successfully with minimal data")
        print(f"   - Patient ID: {patient_id}")
        print(f"   - Name: {patient_data['prenom']} {patient_data['nom']}")
        print(f"   - Age: {patient_data['age']}")
        print(f"   - WhatsApp: {patient_data['lien_whatsapp']}")
        
        # Clean up
        requests.delete(f"{self.base_url}/api/patients/{patient_id}", headers=self.auth_headers)
        
        print(f"🎉 Minimal Patient Creation Test: PASSED")
        
        return patient_id
    
    # ========== APPOINTMENT MANAGEMENT APIs TESTING ==========
    
    def test_appointment_creation_for_consultation_workflow(self):
        """Test POST /api/appointments - test appointment creation for consultation workflow"""
        print("\n🔍 Testing Appointment Creation for Consultation Workflow")
        
        # Get a patient for testing
        response = requests.get(f"{self.base_url}/api/patients", headers=self.auth_headers)
        self.assertEqual(response.status_code, 200)
        patients_data = response.json()
        patients = patients_data["patients"]
        self.assertTrue(len(patients) > 0, "No patients found for testing")
        
        patient_id = patients[0]["id"]
        
        # Test appointment creation for consultation workflow
        today = datetime.now().strftime("%Y-%m-%d")
        appointment_data = {
            "patient_id": patient_id,
            "date": today,
            "heure": "10:30",
            "type_rdv": "visite",  # For consultation workflow
            "motif": "Consultation via modal rapide",
            "notes": "Créé via le modal de consultation rapide",
            "statut": "programme"
        }
        
        response = requests.post(f"{self.base_url}/api/appointments", json=appointment_data, headers=self.auth_headers)
        self.assertEqual(response.status_code, 200, f"Appointment creation failed: {response.text}")
        
        create_data = response.json()
        self.assertIn("appointment_id", create_data)
        self.assertIn("message", create_data)
        
        appointment_id = create_data["appointment_id"]
        
        # Verify appointment was created correctly
        response = requests.get(f"{self.base_url}/api/rdv/jour/{today}", headers=self.auth_headers)
        self.assertEqual(response.status_code, 200)
        
        appointments = response.json()
        created_appointment = None
        for appt in appointments:
            if appt["id"] == appointment_id:
                created_appointment = appt
                break
        
        self.assertIsNotNone(created_appointment, "Created appointment not found")
        self.assertEqual(created_appointment["patient_id"], patient_id)
        self.assertEqual(created_appointment["type_rdv"], "visite")
        self.assertEqual(created_appointment["motif"], "Consultation via modal rapide")
        self.assertEqual(created_appointment["statut"], "programme")
        
        # Verify patient info is included
        self.assertIn("patient", created_appointment)
        patient_info = created_appointment["patient"]
        self.assertIn("nom", patient_info)
        self.assertIn("prenom", patient_info)
        
        print(f"✅ Appointment created successfully for consultation workflow")
        print(f"   - Appointment ID: {appointment_id}")
        print(f"   - Patient: {patient_info['prenom']} {patient_info['nom']}")
        print(f"   - Type: {created_appointment['type_rdv']}")
        print(f"   - Date: {created_appointment['date']} {created_appointment['heure']}")
        
        print(f"🎉 Appointment Creation Test: PASSED")
        
        return appointment_id, patient_id
    
    def test_appointment_retrieval(self):
        """Test GET /api/appointments - verify appointment retrieval"""
        print("\n🔍 Testing Appointment Retrieval")
        
        # Test all appointments retrieval
        response = requests.get(f"{self.base_url}/api/appointments", headers=self.auth_headers)
        self.assertEqual(response.status_code, 200, f"Appointment retrieval failed: {response.text}")
        
        appointments = response.json()
        self.assertIsInstance(appointments, list)
        
        # Test today's appointments
        today = datetime.now().strftime("%Y-%m-%d")
        response = requests.get(f"{self.base_url}/api/appointments/today", headers=self.auth_headers)
        self.assertEqual(response.status_code, 200)
        
        today_appointments = response.json()
        self.assertIsInstance(today_appointments, list)
        
        # Test specific day appointments
        response = requests.get(f"{self.base_url}/api/rdv/jour/{today}", headers=self.auth_headers)
        self.assertEqual(response.status_code, 200)
        
        day_appointments = response.json()
        self.assertIsInstance(day_appointments, list)
        
        # Verify appointment structure
        if len(day_appointments) > 0:
            appointment = day_appointments[0]
            required_fields = ["id", "patient_id", "date", "heure", "type_rdv", "statut"]
            for field in required_fields:
                self.assertIn(field, appointment, f"Missing required field: {field}")
            
            # Verify patient info is included
            self.assertIn("patient", appointment)
            patient_info = appointment["patient"]
            self.assertIn("nom", patient_info)
            self.assertIn("prenom", patient_info)
        
        print(f"✅ Appointment retrieval working correctly")
        print(f"   - Total appointments: {len(appointments)}")
        print(f"   - Today's appointments: {len(today_appointments)}")
        print(f"🎉 Appointment Retrieval Test: PASSED")
    
    # ========== PAYMENT MANAGEMENT APIs TESTING ==========
    
    def test_payment_creation_linked_to_appointments(self):
        """Test POST /api/payments - test payment creation linked to appointments"""
        print("\n🔍 Testing Payment Creation Linked to Appointments")
        
        # First create an appointment
        appointment_id, patient_id = self.test_appointment_creation_for_consultation_workflow()
        
        # Create payment linked to the appointment
        today = datetime.now().strftime("%Y-%m-%d")
        payment_data = {
            "patient_id": patient_id,
            "appointment_id": appointment_id,
            "montant": 65.0,
            "type_paiement": "espece",
            "statut": "paye",
            "assure": False,
            "date": today,
            "notes": "Paiement via modal rapide"
        }
        
        response = requests.post(f"{self.base_url}/api/payments", json=payment_data, headers=self.auth_headers)
        self.assertEqual(response.status_code, 200, f"Payment creation failed: {response.text}")
        
        create_data = response.json()
        self.assertIn("payment_id", create_data)
        self.assertIn("message", create_data)
        
        payment_id = create_data["payment_id"]
        
        # Verify payment was created correctly
        response = requests.get(f"{self.base_url}/api/payments", headers=self.auth_headers)
        self.assertEqual(response.status_code, 200)
        
        payments = response.json()
        created_payment = None
        for payment in payments:
            if payment["id"] == payment_id:
                created_payment = payment
                break
        
        self.assertIsNotNone(created_payment, "Created payment not found")
        self.assertEqual(created_payment["patient_id"], patient_id)
        self.assertEqual(created_payment["appointment_id"], appointment_id)
        self.assertEqual(created_payment["montant"], 65.0)
        self.assertEqual(created_payment["type_paiement"], "espece")
        self.assertEqual(created_payment["statut"], "paye")
        
        print(f"✅ Payment created successfully and linked to appointment")
        print(f"   - Payment ID: {payment_id}")
        print(f"   - Appointment ID: {appointment_id}")
        print(f"   - Amount: {created_payment['montant']} TND")
        print(f"   - Type: {created_payment['type_paiement']}")
        
        print(f"🎉 Payment Creation Test: PASSED")
        
        return payment_id, appointment_id, patient_id
    
    def test_payment_retrieval_by_appointment(self):
        """Test GET /api/payments/appointment/{appointment_id} - verify payment retrieval"""
        print("\n🔍 Testing Payment Retrieval by Appointment")
        
        # Create payment linked to appointment
        payment_id, appointment_id, patient_id = self.test_payment_creation_linked_to_appointments()
        
        # Test payment retrieval by appointment
        response = requests.get(f"{self.base_url}/api/payments/appointment/{appointment_id}", headers=self.auth_headers)
        self.assertEqual(response.status_code, 200, f"Payment retrieval by appointment failed: {response.text}")
        
        payments = response.json()
        self.assertIsInstance(payments, list)
        self.assertTrue(len(payments) > 0, "No payments found for appointment")
        
        # Verify payment data
        payment = payments[0]
        self.assertEqual(payment["appointment_id"], appointment_id)
        self.assertEqual(payment["patient_id"], patient_id)
        
        # Test general payment retrieval
        response = requests.get(f"{self.base_url}/api/payments", headers=self.auth_headers)
        self.assertEqual(response.status_code, 200)
        
        all_payments = response.json()
        self.assertIsInstance(all_payments, list)
        
        # Verify payment structure
        if len(all_payments) > 0:
            payment = all_payments[0]
            required_fields = ["id", "patient_id", "appointment_id", "montant", "type_paiement", "statut", "date"]
            for field in required_fields:
                self.assertIn(field, payment, f"Missing required field: {field}")
        
        print(f"✅ Payment retrieval working correctly")
        print(f"   - Payments for appointment: {len(payments)}")
        print(f"   - Total payments: {len(all_payments)}")
        print(f"🎉 Payment Retrieval Test: PASSED")
    
    # ========== CONSULTATION MANAGEMENT APIs TESTING ==========
    
    def test_consultation_creation_with_new_data_structure(self):
        """Test POST /api/consultations - test consultation creation with new data structure"""
        print("\n🔍 Testing Consultation Creation with New Data Structure")
        
        # Create payment and get appointment/patient IDs
        payment_id, appointment_id, patient_id = self.test_payment_creation_linked_to_appointments()
        
        # Create consultation with new data structure
        today = datetime.now().strftime("%Y-%m-%d")
        consultation_data = {
            "patient_id": patient_id,
            "appointment_id": appointment_id,
            "date": today,
            "type_rdv": "visite",
            "duree": 30,
            "poids": 18.5,
            "taille": 95.0,
            "pc": 50.0,
            "temperature": 37.2,
            # New simplified fields
            "diagnostic": "Infection virale bénigne. Prescription de paracétamol et repos.",
            "observation_clinique": "Enfant en bonne forme générale. Gorge légèrement irritée. Température 37.2°C. Pas de signes de gravité.",
            # Legacy fields for compatibility
            "notes": "Consultation via modal rapide",
            "bilans": "Aucun bilan nécessaire",
            # Vaccine reminder fields
            "rappel_vaccin": True,
            "nom_vaccin": "DTC (Diphtérie-Tétanos-Coqueluche)",
            "date_vaccin": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"),
            "rappel_whatsapp_vaccin": True
        }
        
        response = requests.post(f"{self.base_url}/api/consultations", json=consultation_data, headers=self.auth_headers)
        self.assertEqual(response.status_code, 200, f"Consultation creation failed: {response.text}")
        
        create_data = response.json()
        self.assertIn("consultation_id", create_data)
        self.assertIn("message", create_data)
        
        consultation_id = create_data["consultation_id"]
        
        # Verify consultation was created correctly
        response = requests.get(f"{self.base_url}/api/consultations/{consultation_id}", headers=self.auth_headers)
        self.assertEqual(response.status_code, 200)
        
        consultation = response.json()
        
        # Verify basic fields
        self.assertEqual(consultation["patient_id"], patient_id)
        self.assertEqual(consultation["appointment_id"], appointment_id)
        self.assertEqual(consultation["type_rdv"], "visite")
        self.assertEqual(consultation["duree"], 30)
        
        # Verify measurements
        self.assertEqual(consultation["poids"], 18.5)
        self.assertEqual(consultation["taille"], 95.0)
        self.assertEqual(consultation["pc"], 50.0)
        self.assertEqual(consultation["temperature"], 37.2)
        
        # Verify new simplified fields
        self.assertEqual(consultation["diagnostic"], "Infection virale bénigne. Prescription de paracétamol et repos.")
        self.assertEqual(consultation["observation_clinique"], "Enfant en bonne forme générale. Gorge légèrement irritée. Température 37.2°C. Pas de signes de gravité.")
        
        # Verify vaccine reminder fields
        self.assertEqual(consultation["rappel_vaccin"], True)
        self.assertEqual(consultation["nom_vaccin"], "DTC (Diphtérie-Tétanos-Coqueluche)")
        self.assertEqual(consultation["rappel_whatsapp_vaccin"], True)
        
        print(f"✅ Consultation created successfully with new data structure")
        print(f"   - Consultation ID: {consultation_id}")
        print(f"   - Patient ID: {patient_id}")
        print(f"   - Appointment ID: {appointment_id}")
        print(f"   - Duration: {consultation['duree']} minutes")
        print(f"   - Diagnostic: {consultation['diagnostic'][:50]}...")
        print(f"   - Vaccine reminder: {consultation['rappel_vaccin']}")
        
        print(f"🎉 Consultation Creation Test: PASSED")
        
        return consultation_id, patient_id, appointment_id
    
    def test_consultation_history_retrieval(self):
        """Test GET /api/consultations/patient/{patient_id} - verify consultation history retrieval"""
        print("\n🔍 Testing Consultation History Retrieval")
        
        # Create consultation and get patient ID
        consultation_id, patient_id, appointment_id = self.test_consultation_creation_with_new_data_structure()
        
        # Test consultation history retrieval
        response = requests.get(f"{self.base_url}/api/consultations/patient/{patient_id}", headers=self.auth_headers)
        self.assertEqual(response.status_code, 200, f"Consultation history retrieval failed: {response.text}")
        
        consultations = response.json()
        self.assertIsInstance(consultations, list)
        self.assertTrue(len(consultations) > 0, "No consultations found for patient")
        
        # Find our created consultation
        created_consultation = None
        for consultation in consultations:
            if consultation["id"] == consultation_id:
                created_consultation = consultation
                break
        
        self.assertIsNotNone(created_consultation, "Created consultation not found in history")
        
        # Verify consultation structure in history
        required_fields = ["id", "date", "type_rdv", "duree", "diagnostic", "observation_clinique"]
        for field in required_fields:
            self.assertIn(field, created_consultation, f"Missing required field in history: {field}")
        
        # Test alternative endpoint for patient consultations
        response = requests.get(f"{self.base_url}/api/patients/{patient_id}/consultations", headers=self.auth_headers)
        self.assertEqual(response.status_code, 200)
        
        patient_consultations = response.json()
        self.assertIsInstance(patient_consultations, list)
        
        print(f"✅ Consultation history retrieved successfully")
        print(f"   - Patient ID: {patient_id}")
        print(f"   - Consultations found: {len(consultations)}")
        print(f"   - Created consultation found: {created_consultation is not None}")
        print(f"🎉 Consultation History Test: PASSED")
    
    def test_consultation_updates(self):
        """Test PUT /api/consultations/{consultation_id} - test consultation updates"""
        print("\n🔍 Testing Consultation Updates")
        
        # Create consultation
        consultation_id, patient_id, appointment_id = self.test_consultation_creation_with_new_data_structure()
        
        # Update consultation data
        update_data = {
            "diagnostic": "Infection virale bénigne - MISE À JOUR. Évolution favorable, continuer traitement.",
            "observation_clinique": "MISE À JOUR: Amélioration notable. Température normale. Gorge moins irritée.",
            "duree": 35,  # Updated duration
            "temperature": 36.8,  # Updated temperature
            "notes": "Consultation mise à jour via tests",
            # Update vaccine reminder
            "rappel_vaccin": True,
            "nom_vaccin": "ROR (Rougeole-Oreillons-Rubéole)",
            "date_vaccin": (datetime.now() + timedelta(days=45)).strftime("%Y-%m-%d")
        }
        
        response = requests.put(f"{self.base_url}/api/consultations/{consultation_id}", json=update_data, headers=self.auth_headers)
        self.assertEqual(response.status_code, 200, f"Consultation update failed: {response.text}")
        
        update_response = response.json()
        self.assertIn("message", update_response)
        
        # Verify consultation was updated
        response = requests.get(f"{self.base_url}/api/consultations/{consultation_id}", headers=self.auth_headers)
        self.assertEqual(response.status_code, 200)
        
        updated_consultation = response.json()
        
        # Verify updates
        self.assertEqual(updated_consultation["diagnostic"], "Infection virale bénigne - MISE À JOUR. Évolution favorable, continuer traitement.")
        self.assertEqual(updated_consultation["observation_clinique"], "MISE À JOUR: Amélioration notable. Température normale. Gorge moins irritée.")
        self.assertEqual(updated_consultation["duree"], 35)
        self.assertEqual(updated_consultation["temperature"], 36.8)
        self.assertEqual(updated_consultation["nom_vaccin"], "ROR (Rougeole-Oreillons-Rubéole)")
        
        # Verify updated_at timestamp was updated
        self.assertIn("updated_at", updated_consultation)
        
        print(f"✅ Consultation updated successfully")
        print(f"   - Consultation ID: {consultation_id}")
        print(f"   - Updated diagnostic: {updated_consultation['diagnostic'][:50]}...")
        print(f"   - Updated duration: {updated_consultation['duree']} minutes")
        print(f"   - Updated temperature: {updated_consultation['temperature']}°C")
        print(f"   - Updated vaccine: {updated_consultation['nom_vaccin']}")
        
        print(f"🎉 Consultation Update Test: PASSED")
    
    # ========== AUTHENTICATION AND SECURITY TESTING ==========
    
    def test_endpoints_require_authentication(self):
        """Verify all endpoints require proper authentication"""
        print("\n🔍 Testing Authentication Requirements for All Endpoints")
        
        # Test endpoints without authentication token
        endpoints_to_test = [
            ("GET", "/api/patients"),
            ("POST", "/api/patients"),
            ("GET", "/api/appointments"),
            ("POST", "/api/appointments"),
            ("GET", "/api/payments"),
            ("POST", "/api/payments"),
            ("GET", "/api/consultations"),
            ("POST", "/api/consultations")
        ]
        
        for method, endpoint in endpoints_to_test:
            print(f"  Testing {method} {endpoint} without auth...")
            
            if method == "GET":
                response = requests.get(f"{self.base_url}{endpoint}")
            elif method == "POST":
                response = requests.post(f"{self.base_url}{endpoint}", json={})
            
            # Should return 401 Unauthorized or 403 Forbidden
            self.assertIn(response.status_code, [401, 403], 
                         f"Endpoint {method} {endpoint} should require authentication, got {response.status_code}")
        
        print(f"✅ All endpoints properly require authentication")
        print(f"🎉 Authentication Requirements Test: PASSED")
    
    def test_medecin_role_authentication(self):
        """Test with medecin role authentication"""
        print("\n🔍 Testing Medecin Role Authentication")
        
        # Verify medecin token works for all endpoints
        endpoints_to_test = [
            ("GET", "/api/patients"),
            ("GET", "/api/appointments"),
            ("GET", "/api/payments"),
            ("GET", "/api/consultations")
        ]
        
        for method, endpoint in endpoints_to_test:
            print(f"  Testing {method} {endpoint} with medecin auth...")
            
            if method == "GET":
                response = requests.get(f"{self.base_url}{endpoint}", headers=self.auth_headers)
            
            self.assertEqual(response.status_code, 200, 
                           f"Medecin should have access to {method} {endpoint}, got {response.status_code}")
        
        # Test medecin permissions
        response = requests.get(f"{self.base_url}/api/auth/me", headers=self.auth_headers)
        self.assertEqual(response.status_code, 200)
        
        user_data = response.json()
        self.assertEqual(user_data["role"], "medecin")
        
        permissions = user_data["permissions"]
        self.assertTrue(permissions["administration"], "Medecin should have administration access")
        self.assertTrue(permissions["manage_users"], "Medecin should be able to manage users")
        self.assertTrue(permissions["delete_appointment"], "Medecin should be able to delete appointments")
        self.assertFalse(permissions["consultation_read_only"], "Medecin should have full consultation access")
        
        print(f"✅ Medecin role authentication working correctly")
        print(f"   - Role: {user_data['role']}")
        print(f"   - Administration access: {permissions['administration']}")
        print(f"   - Full consultation access: {not permissions['consultation_read_only']}")
        print(f"🎉 Medecin Role Authentication Test: PASSED")
    
    # ========== COMPLETE WORKFLOW TESTING ==========
    
    def test_complete_consultation_workflow(self):
        """Test the complete workflow: Login → Create Patient → Create Appointment → Create Payment → Create Consultation → Retrieve Records"""
        print("\n🔍 Testing Complete Consultation Workflow")
        print("=" * 80)
        
        # Step 1: Login with medecin credentials (already done in setUp)
        print("Step 1: ✅ Medecin login successful")
        
        # Step 2: Create a new patient through the quick modal workflow
        print("Step 2: Creating new patient...")
        patient_data = {
            "nom": "Workflow",
            "prenom": "Test",
            "date_naissance": "2019-06-15",
            "numero_whatsapp": "21650999888",
            "adresse": "123 Rue Test Workflow, Tunis",
            "notes": "Patient créé via workflow de test complet"
        }
        
        response = requests.post(f"{self.base_url}/api/patients", json=patient_data, headers=self.auth_headers)
        self.assertEqual(response.status_code, 200)
        patient_id = response.json()["patient_id"]
        print(f"Step 2: ✅ Patient created - ID: {patient_id}")
        
        # Step 3: Create an appointment for the new patient
        print("Step 3: Creating appointment...")
        today = datetime.now().strftime("%Y-%m-%d")
        appointment_data = {
            "patient_id": patient_id,
            "date": today,
            "heure": "11:00",
            "type_rdv": "visite",
            "motif": "Consultation complète via workflow test",
            "notes": "RDV créé dans le cadre du test workflow complet"
        }
        
        response = requests.post(f"{self.base_url}/api/appointments", json=appointment_data, headers=self.auth_headers)
        self.assertEqual(response.status_code, 200)
        appointment_id = response.json()["appointment_id"]
        print(f"Step 3: ✅ Appointment created - ID: {appointment_id}")
        
        # Step 4: Create a payment record for the appointment
        print("Step 4: Creating payment record...")
        payment_data = {
            "patient_id": patient_id,
            "appointment_id": appointment_id,
            "montant": 65.0,
            "type_paiement": "espece",
            "statut": "paye",
            "assure": False,
            "date": today,
            "notes": "Paiement workflow test complet"
        }
        
        response = requests.post(f"{self.base_url}/api/payments", json=payment_data, headers=self.auth_headers)
        self.assertEqual(response.status_code, 200)
        payment_id = response.json()["payment_id"]
        print(f"Step 4: ✅ Payment created - ID: {payment_id}")
        
        # Step 5: Create a consultation linked to the appointment
        print("Step 5: Creating consultation...")
        consultation_data = {
            "patient_id": patient_id,
            "appointment_id": appointment_id,
            "date": today,
            "type_rdv": "visite",
            "duree": 25,
            "poids": 16.8,
            "taille": 92.0,
            "pc": 49.0,
            "temperature": 36.9,
            "diagnostic": "Bilan de santé complet. Enfant en excellente santé. Croissance normale pour l'âge.",
            "observation_clinique": "Examen clinique normal. Développement psychomoteur adapté. Aucun signe pathologique.",
            "notes": "Consultation workflow test complet",
            "rappel_vaccin": True,
            "nom_vaccin": "Hépatite B",
            "date_vaccin": (datetime.now() + timedelta(days=60)).strftime("%Y-%m-%d"),
            "rappel_whatsapp_vaccin": True
        }
        
        response = requests.post(f"{self.base_url}/api/consultations", json=consultation_data, headers=self.auth_headers)
        self.assertEqual(response.status_code, 200)
        consultation_id = response.json()["consultation_id"]
        print(f"Step 5: ✅ Consultation created - ID: {consultation_id}")
        
        # Step 6: Retrieve and verify all created records
        print("Step 6: Verifying all created records...")
        
        # Verify patient
        response = requests.get(f"{self.base_url}/api/patients/{patient_id}", headers=self.auth_headers)
        self.assertEqual(response.status_code, 200)
        patient = response.json()
        self.assertEqual(patient["nom"], "Workflow")
        self.assertEqual(patient["prenom"], "Test")
        print(f"Step 6a: ✅ Patient verified - {patient['prenom']} {patient['nom']}")
        
        # Verify appointment
        response = requests.get(f"{self.base_url}/api/rdv/jour/{today}", headers=self.auth_headers)
        self.assertEqual(response.status_code, 200)
        appointments = response.json()
        found_appointment = None
        for appt in appointments:
            if appt["id"] == appointment_id:
                found_appointment = appt
                break
        self.assertIsNotNone(found_appointment)
        self.assertEqual(found_appointment["patient_id"], patient_id)
        print(f"Step 6b: ✅ Appointment verified - {found_appointment['date']} {found_appointment['heure']}")
        
        # Verify payment
        response = requests.get(f"{self.base_url}/api/payments/appointment/{appointment_id}", headers=self.auth_headers)
        self.assertEqual(response.status_code, 200)
        payments = response.json()
        self.assertTrue(len(payments) > 0)
        payment = payments[0]
        self.assertEqual(payment["appointment_id"], appointment_id)
        self.assertEqual(payment["montant"], 65.0)
        print(f"Step 6c: ✅ Payment verified - {payment['montant']} TND ({payment['type_paiement']})")
        
        # Verify consultation
        response = requests.get(f"{self.base_url}/api/consultations/{consultation_id}", headers=self.auth_headers)
        self.assertEqual(response.status_code, 200)
        consultation = response.json()
        self.assertEqual(consultation["patient_id"], patient_id)
        self.assertEqual(consultation["appointment_id"], appointment_id)
        print(f"Step 6d: ✅ Consultation verified - {consultation['duree']} min, {consultation['diagnostic'][:30]}...")
        
        # Verify consultation history
        response = requests.get(f"{self.base_url}/api/consultations/patient/{patient_id}", headers=self.auth_headers)
        self.assertEqual(response.status_code, 200)
        consultations = response.json()
        found_consultation = None
        for cons in consultations:
            if cons["id"] == consultation_id:
                found_consultation = cons
                break
        self.assertIsNotNone(found_consultation)
        print(f"Step 6e: ✅ Consultation history verified - {len(consultations)} consultations found")
        
        print("=" * 80)
        print(f"🎉 COMPLETE CONSULTATION WORKFLOW TEST: PASSED")
        print(f"   - Patient created: {patient['prenom']} {patient['nom']} (ID: {patient_id})")
        print(f"   - Appointment scheduled: {found_appointment['date']} {found_appointment['heure']} (ID: {appointment_id})")
        print(f"   - Payment processed: {payment['montant']} TND (ID: {payment_id})")
        print(f"   - Consultation completed: {consultation['duree']} min (ID: {consultation_id})")
        print(f"   - All records linked and verified successfully")
        print("=" * 80)
        
        # Clean up (optional - comment out if you want to keep test data)
        # requests.delete(f"{self.base_url}/api/patients/{patient_id}", headers=self.auth_headers)
        
        return {
            "patient_id": patient_id,
            "appointment_id": appointment_id,
            "payment_id": payment_id,
            "consultation_id": consultation_id
        }

if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2)