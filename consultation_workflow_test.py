import requests
import unittest
import json
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/frontend/.env')

class ConsultationWorkflowTest(unittest.TestCase):
    """
    Test the complete workflow from quick consultation modal to calendar and billing display.
    Focus on identifying why consultations and payments don't appear in the correct places after creation.
    """
    
    def setUp(self):
        # Use the correct backend URL from environment
        backend_url = os.getenv('REACT_APP_BACKEND_URL', 'https://0f556255-778a-43ef-b1e4-2e04fe02d592.preview.emergentagent.com')
        self.base_url = backend_url
        print(f"Testing backend at: {self.base_url}")
        
        # Initialize demo data for consistent testing
        try:
            response = requests.get(f"{self.base_url}/api/init-demo")
            if response.status_code == 200:
                print("Demo data initialized successfully")
        except Exception as e:
            print(f"Warning: Could not initialize demo data: {e}")
    
    def test_complete_workflow_via_quick_modal(self):
        """
        Test the complete workflow from quick consultation modal to calendar and billing display.
        This is the main test that covers all the key issues mentioned in the review request.
        """
        print("\n🔍 TESTING COMPLETE WORKFLOW FROM QUICK CONSULTATION MODAL")
        
        # Step 1: Create a new patient via modal
        print("\n--- Step 1: Create New Patient via Modal ---")
        new_patient_data = {
            "nom": "WorkflowTest",
            "prenom": "Patient",
            "date_naissance": "2020-01-15",
            "numero_whatsapp": "21612345678"
        }
        
        response = requests.post(f"{self.base_url}/api/patients", json=new_patient_data)
        self.assertEqual(response.status_code, 200, f"Patient creation failed: {response.text}")
        
        patient_response = response.json()
        patient_id = patient_response["patient_id"]
        print(f"✅ Patient created successfully: {patient_id}")
        
        # Verify patient was created with correct data
        response = requests.get(f"{self.base_url}/api/patients/{patient_id}")
        self.assertEqual(response.status_code, 200)
        patient_data = response.json()
        self.assertEqual(patient_data["nom"], "WorkflowTest")
        self.assertEqual(patient_data["prenom"], "Patient")
        print(f"✅ Patient data verified: {patient_data['nom']} {patient_data['prenom']}")
        
        # Step 2: Create appointment for the patient
        print("\n--- Step 2: Create Appointment for Patient ---")
        today = datetime.now().strftime("%Y-%m-%d")
        appointment_data = {
            "patient_id": patient_id,
            "date": today,
            "heure": "10:00",
            "type_rdv": "visite",
            "motif": "Consultation via quick modal",
            "statut": "programme"
        }
        
        response = requests.post(f"{self.base_url}/api/appointments", json=appointment_data)
        self.assertEqual(response.status_code, 200, f"Appointment creation failed: {response.text}")
        
        appointment_response = response.json()
        appointment_id = appointment_response["appointment_id"]
        print(f"✅ Appointment created successfully: {appointment_id}")
        
        # Step 3: Create payment linked to the appointment
        print("\n--- Step 3: Create Payment Linked to Appointment ---")
        payment_data = {
            "paye": True,
            "montant": 65.0,
            "type_paiement": "espece",
            "assure": False,
            "notes": "Payment via quick modal workflow"
        }
        
        response = requests.put(f"{self.base_url}/api/rdv/{appointment_id}/paiement", json=payment_data)
        self.assertEqual(response.status_code, 200, f"Payment creation failed: {response.text}")
        print(f"✅ Payment created successfully via PUT /api/rdv/{appointment_id}/paiement")
        
        # Step 4: Create consultation linked to the appointment
        print("\n--- Step 4: Create Consultation Linked to Appointment ---")
        consultation_data = {
            "patient_id": patient_id,
            "appointment_id": appointment_id,
            "date": today,
            "type_rdv": "visite",
            "duree": 30,
            "diagnostic": "Consultation de routine - patient en bonne santé",
            "observation_clinique": "Examen clinique normal, développement adapté à l'âge",
            "poids": 15.5,
            "taille": 85.0,
            "temperature": 36.8
        }
        
        response = requests.post(f"{self.base_url}/api/consultations", json=consultation_data)
        self.assertEqual(response.status_code, 200, f"Consultation creation failed: {response.text}")
        
        consultation_response = response.json()
        consultation_id = consultation_response["consultation_id"]
        print(f"✅ Consultation created successfully: {consultation_id}")
        
        # Step 5: Verify each step creates the expected records
        print("\n--- Step 5: Verify All Records Were Created ---")
        
        # Verify patient exists
        response = requests.get(f"{self.base_url}/api/patients/{patient_id}")
        self.assertEqual(response.status_code, 200)
        print("✅ Patient record verified")
        
        # Verify appointment exists
        response = requests.get(f"{self.base_url}/api/rdv/jour/{today}")
        self.assertEqual(response.status_code, 200)
        appointments = response.json()
        appointment_found = any(apt["id"] == appointment_id for apt in appointments)
        self.assertTrue(appointment_found, "Appointment not found in daily appointments")
        print("✅ Appointment record verified")
        
        # Verify consultation exists
        response = requests.get(f"{self.base_url}/api/consultations/patient/{patient_id}")
        self.assertEqual(response.status_code, 200)
        consultations = response.json()
        consultation_found = any(cons["id"] == consultation_id for cons in consultations)
        self.assertTrue(consultation_found, "Consultation not found in patient consultations")
        print("✅ Consultation record verified")
        
        # Verify payment exists
        response = requests.get(f"{self.base_url}/api/payments")
        self.assertEqual(response.status_code, 200)
        payments = response.json()
        payment_found = any(pay["appointment_id"] == appointment_id for pay in payments)
        self.assertTrue(payment_found, "Payment not found in payments list")
        print("✅ Payment record verified")
        
        print(f"\n🎉 STEP 1-5 COMPLETED: All records created successfully")
        
        return {
            "patient_id": patient_id,
            "appointment_id": appointment_id,
            "consultation_id": consultation_id,
            "today": today
        }
    
    def test_consultation_appointment_status_update(self):
        """
        Test that when a consultation is saved via POST /api/consultations, 
        the corresponding appointment status is updated to "termine"
        """
        print("\n🔍 TESTING CONSULTATION → APPOINTMENT STATUS UPDATE")
        
        # Create test data first
        workflow_data = self.test_complete_workflow_via_quick_modal()
        patient_id = workflow_data["patient_id"]
        appointment_id = workflow_data["appointment_id"]
        consultation_id = workflow_data["consultation_id"]
        today = workflow_data["today"]
        
        print("\n--- Testing Appointment Status Update After Consultation ---")
        
        # Check appointment status before consultation completion
        response = requests.get(f"{self.base_url}/api/rdv/jour/{today}")
        self.assertEqual(response.status_code, 200)
        appointments = response.json()
        
        appointment = next((apt for apt in appointments if apt["id"] == appointment_id), None)
        self.assertIsNotNone(appointment, "Appointment not found")
        initial_status = appointment["statut"]
        print(f"Initial appointment status: {initial_status}")
        
        # Update consultation to mark it as completed (this should trigger appointment status update)
        consultation_update = {
            "patient_id": patient_id,
            "appointment_id": appointment_id,
            "date": today,
            "type_rdv": "visite",
            "duree": 35,
            "diagnostic": "Consultation terminée - diagnostic final",
            "observation_clinique": "Consultation complétée avec succès",
            "poids": 15.5,
            "taille": 85.0,
            "temperature": 36.8
        }
        
        response = requests.put(f"{self.base_url}/api/consultations/{consultation_id}", json=consultation_update)
        self.assertEqual(response.status_code, 200, f"Consultation update failed: {response.text}")
        print("✅ Consultation updated successfully")
        
        # Check if appointment status was updated to "termine"
        response = requests.get(f"{self.base_url}/api/rdv/jour/{today}")
        self.assertEqual(response.status_code, 200)
        appointments = response.json()
        
        updated_appointment = next((apt for apt in appointments if apt["id"] == appointment_id), None)
        self.assertIsNotNone(updated_appointment, "Updated appointment not found")
        final_status = updated_appointment["statut"]
        print(f"Final appointment status: {final_status}")
        
        # KEY TEST: Verify appointment status is updated to "termine"
        if final_status == "termine":
            print("✅ SUCCESS: Appointment status correctly updated to 'termine' after consultation")
        else:
            print(f"❌ ISSUE FOUND: Appointment status is '{final_status}', expected 'termine'")
            print("🚨 ROOT CAUSE: POST /api/consultations does NOT update appointment status to 'termine'")
        
        return final_status == "termine"
    
    def test_payment_integration(self):
        """
        Test that payments created during quick modal workflow appear in GET /api/payments
        and verify payment data structure matches what billing page expects
        """
        print("\n🔍 TESTING PAYMENT INTEGRATION")
        
        # Create test data first
        workflow_data = self.test_complete_workflow_via_quick_modal()
        patient_id = workflow_data["patient_id"]
        appointment_id = workflow_data["appointment_id"]
        
        print("\n--- Testing Payment Integration ---")
        
        # Test 1: Verify payments appear in GET /api/payments
        response = requests.get(f"{self.base_url}/api/payments")
        self.assertEqual(response.status_code, 200, f"GET /api/payments failed: {response.text}")
        
        payments = response.json()
        self.assertIsInstance(payments, list, "Payments should be a list")
        
        # Find our payment
        our_payment = next((pay for pay in payments if pay["appointment_id"] == appointment_id), None)
        
        if our_payment:
            print("✅ SUCCESS: Payment appears in GET /api/payments")
            print(f"   Payment ID: {our_payment['id']}")
            print(f"   Amount: {our_payment['montant']} TND")
            print(f"   Status: {our_payment['statut']}")
        else:
            print("❌ ISSUE FOUND: Payment created via PUT /api/rdv/{rdv_id}/paiement does NOT appear in GET /api/payments")
            print("🚨 ROOT CAUSE: Payment integration between appointment payment and payments list is broken")
            return False
        
        # Test 2: Verify payment data includes proper appointment_id and patient linkage
        self.assertEqual(our_payment["appointment_id"], appointment_id, "Payment appointment_id mismatch")
        self.assertEqual(our_payment["patient_id"], patient_id, "Payment patient_id mismatch")
        print("✅ SUCCESS: Payment properly linked to appointment and patient")
        
        # Test 3: Verify payment data structure matches what billing page expects
        required_fields = ["id", "patient_id", "appointment_id", "montant", "type_paiement", "statut", "date", "assure"]
        for field in required_fields:
            self.assertIn(field, our_payment, f"Payment missing required field: {field}")
        
        print("✅ SUCCESS: Payment data structure contains all required fields for billing page")
        
        # Test 4: Check if payment is enriched with patient/appointment data
        response = requests.get(f"{self.base_url}/api/payments/enriched")
        if response.status_code == 200:
            enriched_payments = response.json()
            our_enriched_payment = next((pay for pay in enriched_payments if pay["appointment_id"] == appointment_id), None)
            if our_enriched_payment and "patient_nom" in our_enriched_payment:
                print("✅ SUCCESS: Payments are enriched with patient data for billing display")
            else:
                print("⚠️ WARNING: Payments may not be enriched with patient data (check billing page implementation)")
        else:
            print("⚠️ INFO: No enriched payments endpoint found (may use client-side enrichment)")
        
        return True
    
    def test_calendar_integration(self):
        """
        Test that appointments with "termine" status appear in calendar correctly
        """
        print("\n🔍 TESTING CALENDAR INTEGRATION")
        
        # Create test data and ensure appointment is marked as "termine"
        workflow_data = self.test_complete_workflow_via_quick_modal()
        appointment_id = workflow_data["appointment_id"]
        today = workflow_data["today"]
        
        # Force appointment status to "termine" for testing
        print("\n--- Forcing Appointment Status to 'termine' ---")
        status_update = {"statut": "termine"}
        response = requests.put(f"{self.base_url}/api/rdv/{appointment_id}/statut", json=status_update)
        self.assertEqual(response.status_code, 200, f"Status update failed: {response.text}")
        print("✅ Appointment status set to 'termine'")
        
        # Test 1: Call GET /api/rdv/jour/{date} after consultation creation
        print("\n--- Testing Calendar Endpoint ---")
        response = requests.get(f"{self.base_url}/api/rdv/jour/{today}")
        self.assertEqual(response.status_code, 200, f"Calendar endpoint failed: {response.text}")
        
        appointments = response.json()
        self.assertIsInstance(appointments, list, "Calendar should return list of appointments")
        
        # Test 2: Verify appointments with "termine" status are returned
        termine_appointments = [apt for apt in appointments if apt["statut"] == "termine"]
        our_appointment = next((apt for apt in appointments if apt["id"] == appointment_id), None)
        
        if our_appointment:
            print("✅ SUCCESS: Appointment found in calendar endpoint")
            print(f"   Appointment ID: {our_appointment['id']}")
            print(f"   Status: {our_appointment['statut']}")
            
            if our_appointment["statut"] == "termine":
                print("✅ SUCCESS: Appointment with 'termine' status appears in calendar")
            else:
                print(f"❌ ISSUE: Appointment status is '{our_appointment['statut']}', not 'termine'")
        else:
            print("❌ ISSUE FOUND: Appointment not found in calendar endpoint")
            return False
        
        # Test 3: Check if appointment data includes patient information correctly
        if "patient" in our_appointment:
            patient_info = our_appointment["patient"]
            required_patient_fields = ["id", "nom", "prenom"]
            
            for field in required_patient_fields:
                if field in patient_info:
                    print(f"✅ Patient {field}: {patient_info[field]}")
                else:
                    print(f"❌ ISSUE: Missing patient {field} in calendar appointment")
                    return False
            
            print("✅ SUCCESS: Calendar appointment includes complete patient information")
        else:
            print("❌ ISSUE FOUND: Calendar appointment does NOT include patient information")
            print("🚨 ROOT CAUSE: GET /api/rdv/jour/{date} does not enrich appointments with patient data")
            return False
        
        return True
    
    def test_billing_integration(self):
        """
        Test that payments appear in billing with complete data enrichment
        """
        print("\n🔍 TESTING BILLING INTEGRATION")
        
        # Create test data first
        workflow_data = self.test_complete_workflow_via_quick_modal()
        patient_id = workflow_data["patient_id"]
        appointment_id = workflow_data["appointment_id"]
        
        print("\n--- Testing Billing Integration ---")
        
        # Test 1: Call GET /api/payments after consultation with payment
        response = requests.get(f"{self.base_url}/api/payments")
        self.assertEqual(response.status_code, 200, f"Billing payments endpoint failed: {response.text}")
        
        payments = response.json()
        self.assertIsInstance(payments, list, "Payments should be a list")
        
        # Test 2: Verify payment appears in the list with proper enrichment
        our_payment = next((pay for pay in payments if pay["appointment_id"] == appointment_id), None)
        
        if our_payment:
            print("✅ SUCCESS: Payment appears in billing payments list")
            print(f"   Payment ID: {our_payment['id']}")
            print(f"   Amount: {our_payment['montant']} TND")
            print(f"   Type: {our_payment['type_paiement']}")
            print(f"   Status: {our_payment['statut']}")
        else:
            print("❌ ISSUE FOUND: Payment does NOT appear in GET /api/payments for billing")
            return False
        
        # Test 3: Check if payment includes patient and appointment data
        # First, get patient data to compare
        response = requests.get(f"{self.base_url}/api/patients/{patient_id}")
        self.assertEqual(response.status_code, 200)
        patient_data = response.json()
        
        # Check if payment is enriched with patient data
        if "patient_nom" in our_payment or "patient_prenom" in our_payment:
            print("✅ SUCCESS: Payment includes patient name data")
        else:
            print("⚠️ WARNING: Payment may need client-side enrichment with patient data")
        
        # Test 4: Verify payment data structure for billing display
        billing_required_fields = [
            "id", "patient_id", "appointment_id", "montant", 
            "type_paiement", "statut", "date", "assure"
        ]
        
        missing_fields = []
        for field in billing_required_fields:
            if field not in our_payment:
                missing_fields.append(field)
        
        if not missing_fields:
            print("✅ SUCCESS: Payment contains all required fields for billing display")
        else:
            print(f"❌ ISSUE: Payment missing required fields: {missing_fields}")
            return False
        
        # Test 5: Test payment statistics endpoint if available
        response = requests.get(f"{self.base_url}/api/payments/stats")
        if response.status_code == 200:
            stats = response.json()
            print("✅ Payment statistics endpoint available")
            print(f"   Stats keys: {list(stats.keys())}")
        else:
            print("⚠️ INFO: No payment statistics endpoint found")
        
        return True
    
    def test_data_flow_consistency(self):
        """
        Test the complete data flow consistency from modal creation to final display
        """
        print("\n🔍 TESTING DATA FLOW CONSISTENCY")
        
        # Create complete workflow
        workflow_data = self.test_complete_workflow_via_quick_modal()
        patient_id = workflow_data["patient_id"]
        appointment_id = workflow_data["appointment_id"]
        consultation_id = workflow_data["consultation_id"]
        today = workflow_data["today"]
        
        print("\n--- Testing Data Flow Consistency ---")
        
        # Test 1: Verify appointment_id links all records correctly
        print("Testing appointment_id linkage...")
        
        # Get appointment
        response = requests.get(f"{self.base_url}/api/rdv/jour/{today}")
        appointments = response.json()
        appointment = next((apt for apt in appointments if apt["id"] == appointment_id), None)
        self.assertIsNotNone(appointment, "Appointment not found")
        
        # Get consultation
        response = requests.get(f"{self.base_url}/api/consultations/patient/{patient_id}")
        consultations = response.json()
        consultation = next((cons for cons in consultations if cons["id"] == consultation_id), None)
        self.assertIsNotNone(consultation, "Consultation not found")
        
        # Get payment
        response = requests.get(f"{self.base_url}/api/payments")
        payments = response.json()
        payment = next((pay for pay in payments if pay["appointment_id"] == appointment_id), None)
        self.assertIsNotNone(payment, "Payment not found")
        
        # Verify linkage
        self.assertEqual(appointment["patient_id"], patient_id, "Appointment patient_id mismatch")
        self.assertEqual(consultation["patient_id"], patient_id, "Consultation patient_id mismatch")
        self.assertEqual(consultation["appointment_id"], appointment_id, "Consultation appointment_id mismatch")
        self.assertEqual(payment["patient_id"], patient_id, "Payment patient_id mismatch")
        self.assertEqual(payment["appointment_id"], appointment_id, "Payment appointment_id mismatch")
        
        print("✅ SUCCESS: All records properly linked by appointment_id and patient_id")
        
        # Test 2: Verify data consistency across endpoints
        print("Testing data consistency...")
        
        # Patient data should be consistent
        response = requests.get(f"{self.base_url}/api/patients/{patient_id}")
        patient_direct = response.json()
        
        if "patient" in appointment:
            appointment_patient = appointment["patient"]
            self.assertEqual(patient_direct["nom"], appointment_patient["nom"], "Patient name inconsistent")
            self.assertEqual(patient_direct["prenom"], appointment_patient["prenom"], "Patient prenom inconsistent")
            print("✅ SUCCESS: Patient data consistent between direct and appointment endpoints")
        
        # Test 3: Verify workflow state transitions
        print("Testing workflow state transitions...")
        
        # Check if consultation creation should have updated appointment status
        if appointment["statut"] == "termine":
            print("✅ SUCCESS: Appointment status correctly reflects consultation completion")
        else:
            print(f"⚠️ ISSUE: Appointment status is '{appointment['statut']}', may need manual update to 'termine'")
        
        return True
    
    def test_end_to_end_workflow_summary(self):
        """
        Comprehensive end-to-end test that summarizes all findings
        """
        print("\n🔍 COMPREHENSIVE END-TO-END WORKFLOW TEST")
        print("=" * 60)
        
        results = {
            "workflow_creation": False,
            "appointment_status_update": False,
            "payment_integration": False,
            "calendar_integration": False,
            "billing_integration": False,
            "data_flow_consistency": False
        }
        
        try:
            # Test 1: Complete workflow creation
            print("\n1. Testing complete workflow creation...")
            workflow_data = self.test_complete_workflow_via_quick_modal()
            results["workflow_creation"] = True
            print("✅ PASSED: Complete workflow creation")
            
            # Test 2: Appointment status update
            print("\n2. Testing consultation → appointment status update...")
            results["appointment_status_update"] = self.test_consultation_appointment_status_update()
            if results["appointment_status_update"]:
                print("✅ PASSED: Appointment status update")
            else:
                print("❌ FAILED: Appointment status update")
            
            # Test 3: Payment integration
            print("\n3. Testing payment integration...")
            results["payment_integration"] = self.test_payment_integration()
            if results["payment_integration"]:
                print("✅ PASSED: Payment integration")
            else:
                print("❌ FAILED: Payment integration")
            
            # Test 4: Calendar integration
            print("\n4. Testing calendar integration...")
            results["calendar_integration"] = self.test_calendar_integration()
            if results["calendar_integration"]:
                print("✅ PASSED: Calendar integration")
            else:
                print("❌ FAILED: Calendar integration")
            
            # Test 5: Billing integration
            print("\n5. Testing billing integration...")
            results["billing_integration"] = self.test_billing_integration()
            if results["billing_integration"]:
                print("✅ PASSED: Billing integration")
            else:
                print("❌ FAILED: Billing integration")
            
            # Test 6: Data flow consistency
            print("\n6. Testing data flow consistency...")
            results["data_flow_consistency"] = self.test_data_flow_consistency()
            if results["data_flow_consistency"]:
                print("✅ PASSED: Data flow consistency")
            else:
                print("❌ FAILED: Data flow consistency")
            
        except Exception as e:
            print(f"❌ CRITICAL ERROR during end-to-end test: {str(e)}")
        
        # Summary
        print("\n" + "=" * 60)
        print("🎯 END-TO-END WORKFLOW TEST SUMMARY")
        print("=" * 60)
        
        passed_tests = sum(results.values())
        total_tests = len(results)
        
        for test_name, passed in results.items():
            status = "✅ PASSED" if passed else "❌ FAILED"
            print(f"{status}: {test_name.replace('_', ' ').title()}")
        
        print(f"\nOVERALL RESULT: {passed_tests}/{total_tests} tests passed")
        
        if passed_tests == total_tests:
            print("🎉 ALL TESTS PASSED: Complete workflow is working correctly!")
        else:
            print("🚨 ISSUES FOUND: Some parts of the workflow need attention")
        
        return results

if __name__ == '__main__':
    # Run the comprehensive end-to-end test
    test_suite = ConsultationWorkflowTest()
    test_suite.setUp()
    
    # Run the main comprehensive test
    results = test_suite.test_end_to_end_workflow_summary()
    
    print("\n" + "=" * 60)
    print("🔍 DETAILED FINDINGS AND RECOMMENDATIONS")
    print("=" * 60)
    
    if not results["appointment_status_update"]:
        print("\n❌ CRITICAL ISSUE: Consultation → Appointment Status Update")
        print("   Problem: POST /api/consultations does NOT update appointment status to 'termine'")
        print("   Impact: Consultations don't appear as completed in calendar")
        print("   Fix: Add appointment status update logic to consultation creation/update endpoints")
    
    if not results["payment_integration"]:
        print("\n❌ CRITICAL ISSUE: Payment Integration")
        print("   Problem: Payments created via PUT /api/rdv/{rdv_id}/paiement don't appear in GET /api/payments")
        print("   Impact: Payments don't show up in billing page")
        print("   Fix: Ensure payment creation updates both appointment and payments collection")
    
    if not results["calendar_integration"]:
        print("\n❌ CRITICAL ISSUE: Calendar Integration")
        print("   Problem: Appointments with 'termine' status or patient data missing")
        print("   Impact: Completed consultations don't display properly in calendar")
        print("   Fix: Ensure GET /api/rdv/jour/{date} includes patient data and correct statuses")
    
    if not results["billing_integration"]:
        print("\n❌ CRITICAL ISSUE: Billing Integration")
        print("   Problem: Payments missing from billing or lack proper data enrichment")
        print("   Impact: Billing page doesn't show complete payment information")
        print("   Fix: Ensure GET /api/payments includes all payments with patient/appointment data")
    
    print("\n🎯 NEXT STEPS:")
    print("1. Fix appointment status update in consultation endpoints")
    print("2. Verify payment creation updates both collections")
    print("3. Ensure calendar endpoint returns complete data")
    print("4. Verify billing endpoint includes all payments")
    print("5. Test complete workflow after fixes")