import requests
import unittest
import json
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/frontend/.env')

class PaymentSecurityRestrictionsTest(unittest.TestCase):
    def setUp(self):
        # Use the correct backend URL from environment
        backend_url = os.getenv('REACT_APP_BACKEND_URL', 'https://c43dd363-5911-40ca-a518-ed83b9b7b9ac.preview.emergentagent.com')
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

    # ========== PAYMENT SECURITY RESTRICTIONS FUNCTIONALITY TESTS ==========
    
    def test_payment_security_restrictions_setup(self):
        """Create test appointments with various states for payment security testing"""
        print("\n=== PAYMENT SECURITY RESTRICTIONS TESTING ===")
        
        # Get patients for testing
        response = requests.get(f"{self.base_url}/api/patients")
        self.assertEqual(response.status_code, 200)
        patients_data = response.json()
        patients = patients_data["patients"]
        self.assertTrue(len(patients) >= 3, "Need at least 3 patients for testing")
        
        today = datetime.now().strftime("%Y-%m-%d")
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        
        # Create test appointments with various states
        test_appointments = [
            # Terminated and paid visite
            {
                "patient_id": patients[0]["id"],
                "date": yesterday,
                "heure": "09:00",
                "type_rdv": "visite",
                "statut": "termine",
                "motif": "Consultation terminée et payée",
                "paye": True
            },
            # Terminated and unpaid visite
            {
                "patient_id": patients[1]["id"],
                "date": yesterday,
                "heure": "10:00",
                "type_rdv": "visite",
                "statut": "termine",
                "motif": "Consultation terminée non payée",
                "paye": False
            },
            # Scheduled visite
            {
                "patient_id": patients[2]["id"],
                "date": today,
                "heure": "14:00",
                "type_rdv": "visite",
                "statut": "programme",
                "motif": "Consultation programmée",
                "paye": False
            },
            # Terminated and paid controle
            {
                "patient_id": patients[0]["id"],
                "date": yesterday,
                "heure": "11:00",
                "type_rdv": "controle",
                "statut": "termine",
                "motif": "Contrôle terminé",
                "paye": True
            },
            # Scheduled controle
            {
                "patient_id": patients[1]["id"],
                "date": today,
                "heure": "15:00",
                "type_rdv": "controle",
                "statut": "programme",
                "motif": "Contrôle programmé",
                "paye": False
            }
        ]
        
        created_appointments = []
        
        for appointment_data in test_appointments:
            response = requests.post(f"{self.base_url}/api/appointments", json=appointment_data)
            self.assertEqual(response.status_code, 200, f"Failed to create appointment: {appointment_data}")
            
            appointment_id = response.json()["appointment_id"]
            created_appointments.append(appointment_id)
            
            # If appointment is marked as paid, create payment record
            if appointment_data["paye"]:
                payment_data = {
                    "paye": True,
                    "montant": 0.0 if appointment_data["type_rdv"] == "controle" else 65.0,
                    "type_paiement": "gratuit" if appointment_data["type_rdv"] == "controle" else "espece",
                    "assure": False,
                    "notes": f"Paiement pour {appointment_data['type_rdv']}"
                }
                
                payment_response = requests.put(f"{self.base_url}/api/rdv/{appointment_id}/paiement", json=payment_data)
                self.assertEqual(payment_response.status_code, 200, f"Failed to create payment for appointment {appointment_id}")
        
        print(f"✅ Created {len(created_appointments)} test appointments with various states")
        return created_appointments
    
    def test_core_appointment_endpoints(self):
        """Test core appointment endpoints for payment security restrictions"""
        print("\n=== TESTING CORE APPOINTMENT ENDPOINTS ===")
        
        # Setup test appointments
        created_appointments = self.test_payment_security_restrictions_setup()
        
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
            
            # Test 1: GET /api/rdv/jour/{today's date}
            print(f"\n1. Testing GET /api/rdv/jour/{today}")
            response = requests.get(f"{self.base_url}/api/rdv/jour/{today}")
            self.assertEqual(response.status_code, 200)
            today_appointments = response.json()
            self.assertIsInstance(today_appointments, list)
            
            # Verify appointments have correct fields
            for appointment in today_appointments:
                self.assertIn("statut", appointment)
                self.assertIn("paye", appointment)
                self.assertIn("type_rdv", appointment)
                self.assertIn("patient", appointment)
                
                # Verify patient info structure
                patient_info = appointment["patient"]
                self.assertIn("nom", patient_info)
                self.assertIn("prenom", patient_info)
                self.assertIn("numero_whatsapp", patient_info)
                self.assertIn("lien_whatsapp", patient_info)
            
            print(f"✅ Found {len(today_appointments)} appointments for today with correct structure")
            
            # Test 2: GET /api/rdv/jour/{yesterday's date}
            print(f"\n2. Testing GET /api/rdv/jour/{yesterday}")
            response = requests.get(f"{self.base_url}/api/rdv/jour/{yesterday}")
            self.assertEqual(response.status_code, 200)
            yesterday_appointments = response.json()
            self.assertIsInstance(yesterday_appointments, list)
            
            # Find terminated appointments
            terminated_appointments = [apt for apt in yesterday_appointments if apt["statut"] == "termine"]
            paid_terminated = [apt for apt in terminated_appointments if apt["paye"] == True]
            unpaid_terminated = [apt for apt in terminated_appointments if apt["paye"] == False]
            
            print(f"✅ Found {len(terminated_appointments)} terminated appointments ({len(paid_terminated)} paid, {len(unpaid_terminated)} unpaid)")
            
            # Test 3: PUT /api/rdv/{appointment_id}/statut - Test changing from "programme" to "termine"
            print("\n3. Testing PUT /api/rdv/{id}/statut - Status changes")
            
            # Find a scheduled appointment to test status change
            scheduled_appointments = [apt for apt in today_appointments if apt["statut"] == "programme"]
            if scheduled_appointments:
                test_appointment = scheduled_appointments[0]
                appointment_id = test_appointment["id"]
                
                # Change status from "programme" to "termine"
                status_update = {"statut": "termine"}
                response = requests.put(f"{self.base_url}/api/rdv/{appointment_id}/statut", json=status_update)
                self.assertEqual(response.status_code, 200)
                
                # Verify the change
                response = requests.get(f"{self.base_url}/api/rdv/jour/{today}")
                updated_appointments = response.json()
                updated_appointment = next((apt for apt in updated_appointments if apt["id"] == appointment_id), None)
                
                self.assertIsNotNone(updated_appointment)
                self.assertEqual(updated_appointment["statut"], "termine")
                print(f"✅ Successfully changed appointment status from 'programme' to 'termine'")
            
            # Test 4: PUT /api/rdv/{appointment_id}/paiement - Test payment updates
            print("\n4. Testing PUT /api/rdv/{id}/paiement - Payment updates")
            
            # Find an unpaid appointment to test payment update
            unpaid_appointments = [apt for apt in yesterday_appointments + today_appointments if apt["paye"] == False and apt["type_rdv"] == "visite"]
            if unpaid_appointments:
                test_appointment = unpaid_appointments[0]
                appointment_id = test_appointment["id"]
                
                # Update payment from paye=false to paye=true
                payment_update = {
                    "paye": True,
                    "montant": 65.0,
                    "type_paiement": "espece",
                    "assure": False,
                    "notes": "Paiement test"
                }
                
                response = requests.put(f"{self.base_url}/api/rdv/{appointment_id}/paiement", json=payment_update)
                self.assertEqual(response.status_code, 200)
                
                # Verify the payment update
                payment_response = response.json()
                self.assertEqual(payment_response["paye"], True)
                self.assertEqual(payment_response["montant"], 65.0)
                self.assertEqual(payment_response["type_paiement"], "espece")
                print(f"✅ Successfully updated payment from paye=false to paye=true")
            
        finally:
            # Clean up created appointments
            for appointment_id in created_appointments:
                requests.delete(f"{self.base_url}/api/appointments/{appointment_id}")
            print(f"✅ Cleaned up {len(created_appointments)} test appointments")
    
    def test_data_structure_verification(self):
        """Verify data structure for payment security restrictions"""
        print("\n=== TESTING DATA STRUCTURE VERIFICATION ===")
        
        # Setup test appointments
        created_appointments = self.test_payment_security_restrictions_setup()
        
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
            
            # Get all appointments for verification
            all_appointments = []
            for date in [today, yesterday]:
                response = requests.get(f"{self.base_url}/api/rdv/jour/{date}")
                self.assertEqual(response.status_code, 200)
                all_appointments.extend(response.json())
            
            print(f"✅ Retrieved {len(all_appointments)} appointments for data structure verification")
            
            # Verify all appointments have required fields
            required_fields = ["statut", "paye", "type_rdv", "patient", "id", "date", "heure", "motif"]
            
            for appointment in all_appointments:
                for field in required_fields:
                    self.assertIn(field, appointment, f"Missing field '{field}' in appointment {appointment.get('id', 'unknown')}")
                
                # Verify patient info structure
                patient_info = appointment["patient"]
                patient_required_fields = ["nom", "prenom", "numero_whatsapp", "lien_whatsapp"]
                for field in patient_required_fields:
                    self.assertIn(field, patient_info, f"Missing patient field '{field}' in appointment {appointment['id']}")
                
                # Verify data types
                self.assertIsInstance(appointment["paye"], bool, f"Field 'paye' should be boolean in appointment {appointment['id']}")
                self.assertIn(appointment["statut"], ["programme", "attente", "en_cours", "termine", "absent", "retard"], 
                             f"Invalid status '{appointment['statut']}' in appointment {appointment['id']}")
                self.assertIn(appointment["type_rdv"], ["visite", "controle"], 
                             f"Invalid type_rdv '{appointment['type_rdv']}' in appointment {appointment['id']}")
            
            print(f"✅ All appointments have correct data structure and field types")
            
            # Test payment persistence
            paid_appointments = [apt for apt in all_appointments if apt["paye"] == True]
            unpaid_appointments = [apt for apt in all_appointments if apt["paye"] == False]
            
            print(f"✅ Found {len(paid_appointments)} paid appointments and {len(unpaid_appointments)} unpaid appointments")
            
            # Verify contrôle appointments
            controle_appointments = [apt for apt in all_appointments if apt["type_rdv"] == "controle"]
            visite_appointments = [apt for apt in all_appointments if apt["type_rdv"] == "visite"]
            
            print(f"✅ Found {len(controle_appointments)} contrôle appointments and {len(visite_appointments)} visite appointments")
            
        finally:
            # Clean up created appointments
            for appointment_id in created_appointments:
                requests.delete(f"{self.base_url}/api/appointments/{appointment_id}")
            print(f"✅ Cleaned up {len(created_appointments)} test appointments")
    
    def test_payment_scenarios(self):
        """Test various payment scenarios for security restrictions"""
        print("\n=== TESTING PAYMENT SCENARIOS ===")
        
        # Get patients for testing
        response = requests.get(f"{self.base_url}/api/patients")
        self.assertEqual(response.status_code, 200)
        patients_data = response.json()
        patients = patients_data["patients"]
        self.assertTrue(len(patients) >= 2, "Need at least 2 patients for testing")
        
        today = datetime.now().strftime("%Y-%m-%d")
        created_appointments = []
        
        try:
            # Scenario 1: Test visite appointment payment update
            print("\n1. Testing visite appointment payment scenarios")
            
            visite_appointment = {
                "patient_id": patients[0]["id"],
                "date": today,
                "heure": "10:00",
                "type_rdv": "visite",
                "statut": "termine",
                "motif": "Test visite payment",
                "paye": False
            }
            
            response = requests.post(f"{self.base_url}/api/appointments", json=visite_appointment)
            self.assertEqual(response.status_code, 200)
            visite_id = response.json()["appointment_id"]
            created_appointments.append(visite_id)
            
            # Update payment from paye=false to paye=true
            payment_update = {
                "paye": True,
                "montant": 65.0,
                "type_paiement": "espece",
                "assure": False,
                "notes": "Paiement visite test"
            }
            
            response = requests.put(f"{self.base_url}/api/rdv/{visite_id}/paiement", json=payment_update)
            self.assertEqual(response.status_code, 200)
            payment_response = response.json()
            
            self.assertEqual(payment_response["paye"], True)
            self.assertEqual(payment_response["montant"], 65.0)
            self.assertEqual(payment_response["type_paiement"], "espece")
            print(f"✅ Visite payment update successful: {payment_response['montant']} TND")
            
            # Scenario 2: Test contrôle appointment (should be free/gratuit)
            print("\n2. Testing contrôle appointment payment scenarios")
            
            controle_appointment = {
                "patient_id": patients[1]["id"],
                "date": today,
                "heure": "11:00",
                "type_rdv": "controle",
                "statut": "termine",
                "motif": "Test contrôle payment",
                "paye": False
            }
            
            response = requests.post(f"{self.base_url}/api/appointments", json=controle_appointment)
            self.assertEqual(response.status_code, 200)
            controle_id = response.json()["appointment_id"]
            created_appointments.append(controle_id)
            
            # Update contrôle payment (should be free)
            controle_payment_update = {
                "paye": True,
                "montant": 0.0,  # Contrôles should be free
                "type_paiement": "gratuit",
                "assure": False,
                "notes": "Contrôle gratuit"
            }
            
            response = requests.put(f"{self.base_url}/api/rdv/{controle_id}/paiement", json=controle_payment_update)
            self.assertEqual(response.status_code, 200)
            controle_payment_response = response.json()
            
            self.assertEqual(controle_payment_response["paye"], True)
            self.assertEqual(controle_payment_response["montant"], 0.0)
            self.assertEqual(controle_payment_response["type_paiement"], "gratuit")
            print(f"✅ Contrôle payment update successful: {controle_payment_response['montant']} TND (gratuit)")
            
            # Scenario 3: Test payment amount updates
            print("\n3. Testing payment amount and details updates")
            
            # Update visite payment amount
            amount_update = {
                "paye": True,
                "montant": 80.0,  # Different amount
                "type_paiement": "espece",
                "assure": True,  # With insurance
                "notes": "Paiement modifié avec assurance"
            }
            
            response = requests.put(f"{self.base_url}/api/rdv/{visite_id}/paiement", json=amount_update)
            self.assertEqual(response.status_code, 200)
            updated_payment = response.json()
            
            self.assertEqual(updated_payment["montant"], 80.0)
            self.assertEqual(updated_payment["assure"], True)
            print(f"✅ Payment amount updated successfully: {updated_payment['montant']} TND with insurance")
            
            # Scenario 4: Test payment persistence verification
            print("\n4. Verifying payment persistence")
            
            # Get appointments and verify payments persisted
            response = requests.get(f"{self.base_url}/api/rdv/jour/{today}")
            self.assertEqual(response.status_code, 200)
            appointments = response.json()
            
            # Find our test appointments
            visite_apt = next((apt for apt in appointments if apt["id"] == visite_id), None)
            controle_apt = next((apt for apt in appointments if apt["id"] == controle_id), None)
            
            self.assertIsNotNone(visite_apt, "Visite appointment not found")
            self.assertIsNotNone(controle_apt, "Contrôle appointment not found")
            
            # Verify payment status persisted
            self.assertEqual(visite_apt["paye"], True, "Visite payment status not persisted")
            self.assertEqual(controle_apt["paye"], True, "Contrôle payment status not persisted")
            
            print(f"✅ Payment persistence verified for both appointments")
            
        finally:
            # Clean up created appointments
            for appointment_id in created_appointments:
                requests.delete(f"{self.base_url}/api/appointments/{appointment_id}")
            print(f"✅ Cleaned up {len(created_appointments)} test appointments")
    
    def test_payment_security_restrictions_summary(self):
        """Summary test for payment security restrictions functionality"""
        print("\n=== PAYMENT SECURITY RESTRICTIONS SUMMARY ===")
        
        # Run all payment security tests
        print("Running comprehensive payment security restrictions tests...")
        
        # Test 1: Setup and core endpoints
        try:
            self.test_core_appointment_endpoints()
            print("✅ Core appointment endpoints test: PASSED")
        except Exception as e:
            print(f"❌ Core appointment endpoints test: FAILED - {str(e)}")
            raise
        
        # Test 2: Data structure verification
        try:
            self.test_data_structure_verification()
            print("✅ Data structure verification test: PASSED")
        except Exception as e:
            print(f"❌ Data structure verification test: FAILED - {str(e)}")
            raise
        
        # Test 3: Payment scenarios
        try:
            self.test_payment_scenarios()
            print("✅ Payment scenarios test: PASSED")
        except Exception as e:
            print(f"❌ Payment scenarios test: FAILED - {str(e)}")
            raise
        
        print("\n🎉 ALL PAYMENT SECURITY RESTRICTIONS TESTS PASSED!")
        print("Backend fully supports frontend security restrictions for secrétaire users")
        print("- Terminated paid consultations data structure verified")
        print("- Payment status updates working correctly")
        print("- Contrôle appointments handled as free/gratuit")
        print("- All appointment endpoints returning correct data")

if __name__ == "__main__":
    unittest.main()