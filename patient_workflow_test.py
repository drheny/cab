#!/usr/bin/env python3
"""
Patient Creation and Retrieval Workflow Testing
Focus: Testing the patient creation and retrieval workflow that's causing the "undefined undefined" bug in the consultation modal.
"""

import requests
import unittest
import json
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/frontend/.env')

class PatientWorkflowTest(unittest.TestCase):
    def setUp(self):
        # Use the correct backend URL from environment
        backend_url = os.getenv('REACT_APP_BACKEND_URL', 'https://0f556255-778a-43ef-b1e4-2e04fe02d592.preview.emergentagent.com')
        self.base_url = backend_url
        print(f"Testing backend at: {self.base_url}")
        
        # Authentication token for testing
        self.auth_token = "auto-login-token"
        self.headers = {"Authorization": f"Bearer {self.auth_token}"}
    
    def test_patient_creation_minimal_data(self):
        """Test POST /api/patients with minimal patient data (nom, prenom only)"""
        print("\n🔍 Testing Patient Creation - Minimal Data (nom, prenom only)")
        
        # Test with minimal data that would be used in consultation modal
        minimal_patient = {
            "nom": "Dupont",
            "prenom": "Marie"
        }
        
        response = requests.post(f"{self.base_url}/api/patients", json=minimal_patient, headers=self.headers)
        print(f"Response status: {response.status_code}")
        print(f"Response body: {response.text}")
        
        self.assertEqual(response.status_code, 200, f"Patient creation failed: {response.text}")
        
        create_data = response.json()
        self.assertIn("patient_id", create_data)
        self.assertIn("message", create_data)
        
        patient_id = create_data["patient_id"]
        print(f"✅ Patient created successfully with ID: {patient_id}")
        
        return patient_id
    
    def test_patient_creation_complete_data(self):
        """Test POST /api/patients with complete patient data"""
        print("\n🔍 Testing Patient Creation - Complete Data")
        
        # Test with complete data including all fields
        complete_patient = {
            "nom": "Martin",
            "prenom": "Jean",
            "date_naissance": "2020-05-15",
            "telephone": "21612345678",
            "adresse": "123 Rue de la Paix, Tunis",
            "numero_whatsapp": "21612345678",
            "notes": "Patient créé via test complet",
            "antecedents": "Aucun antécédent particulier"
        }
        
        response = requests.post(f"{self.base_url}/api/patients", json=complete_patient, headers=self.headers)
        print(f"Response status: {response.status_code}")
        print(f"Response body: {response.text}")
        
        self.assertEqual(response.status_code, 200, f"Patient creation failed: {response.text}")
        
        create_data = response.json()
        self.assertIn("patient_id", create_data)
        patient_id = create_data["patient_id"]
        
        print(f"✅ Patient created successfully with ID: {patient_id}")
        
        return patient_id
    
    def test_patient_retrieval_by_id(self):
        """Test GET /api/patients/{patient_id} endpoint after creating a patient"""
        print("\n🔍 Testing Patient Retrieval by ID")
        
        # First create a patient
        test_patient = {
            "nom": "TestRetrieval",
            "prenom": "Patient",
            "date_naissance": "2019-08-22",
            "telephone": "21698765432"
        }
        
        create_response = requests.post(f"{self.base_url}/api/patients", json=test_patient, headers=self.headers)
        self.assertEqual(create_response.status_code, 200)
        patient_id = create_response.json()["patient_id"]
        
        # Now retrieve the patient
        response = requests.get(f"{self.base_url}/api/patients/{patient_id}", headers=self.headers)
        print(f"Retrieval response status: {response.status_code}")
        print(f"Retrieval response body: {response.text}")
        
        self.assertEqual(response.status_code, 200, f"Patient retrieval failed: {response.text}")
        
        patient_data = response.json()
        
        # Verify all required fields are present
        required_fields = ["id", "nom", "prenom"]
        for field in required_fields:
            self.assertIn(field, patient_data, f"Missing required field: {field}")
            self.assertIsNotNone(patient_data[field], f"Field {field} is None")
            if field in ["nom", "prenom"]:
                self.assertNotEqual(patient_data[field], "", f"Field {field} is empty")
        
        # Verify the data matches what we created
        self.assertEqual(patient_data["nom"], "TestRetrieval")
        self.assertEqual(patient_data["prenom"], "Patient")
        self.assertEqual(patient_data["date_naissance"], "2019-08-22")
        
        # Check computed fields
        self.assertIn("age", patient_data)
        self.assertIn("lien_whatsapp", patient_data)
        
        print(f"✅ Patient retrieved successfully:")
        print(f"   - ID: {patient_data['id']}")
        print(f"   - Nom: {patient_data['nom']}")
        print(f"   - Prenom: {patient_data['prenom']}")
        print(f"   - Age: {patient_data.get('age', 'N/A')}")
        
        return patient_id
    
    def test_complete_workflow_minimal_patient(self):
        """Test complete workflow: Create patient → Get patient_id → Retrieve complete patient data (minimal)"""
        print("\n🔍 Testing Complete Workflow - Minimal Patient Data")
        
        # Step 1: Create patient with minimal data (as would happen in consultation modal)
        print("  Step 1: Creating patient with minimal data...")
        minimal_patient = {
            "nom": "WorkflowTest",
            "prenom": "Minimal"
        }
        
        create_response = requests.post(f"{self.base_url}/api/patients", json=minimal_patient, headers=self.headers)
        self.assertEqual(create_response.status_code, 200, f"Patient creation failed: {create_response.text}")
        
        create_data = create_response.json()
        self.assertIn("patient_id", create_data)
        patient_id = create_data["patient_id"]
        print(f"  ✅ Patient created with ID: {patient_id}")
        
        # Step 2: Retrieve complete patient data
        print("  Step 2: Retrieving complete patient data...")
        retrieve_response = requests.get(f"{self.base_url}/api/patients/{patient_id}", headers=self.headers)
        self.assertEqual(retrieve_response.status_code, 200, f"Patient retrieval failed: {retrieve_response.text}")
        
        patient_data = retrieve_response.json()
        print(f"  ✅ Patient data retrieved successfully")
        
        # Step 3: Verify data structure for consultation modal
        print("  Step 3: Verifying data structure for consultation modal...")
        
        # Critical fields that must be present and not undefined
        critical_fields = {
            "id": patient_id,
            "nom": "WorkflowTest", 
            "prenom": "Minimal"
        }
        
        for field, expected_value in critical_fields.items():
            self.assertIn(field, patient_data, f"Missing critical field: {field}")
            self.assertIsNotNone(patient_data[field], f"Critical field {field} is None")
            self.assertNotEqual(patient_data[field], "", f"Critical field {field} is empty")
            if expected_value:
                self.assertEqual(patient_data[field], expected_value, f"Critical field {field} has wrong value")
        
        # Check that nom and prenom are not undefined (this is the bug we're testing)
        nom = patient_data.get("nom")
        prenom = patient_data.get("prenom")
        
        self.assertIsNotNone(nom, "nom field is None - this would cause 'undefined' in frontend")
        self.assertIsNotNone(prenom, "prenom field is None - this would cause 'undefined' in frontend")
        self.assertNotEqual(nom, "", "nom field is empty - this would cause display issues")
        self.assertNotEqual(prenom, "", "prenom field is empty - this would cause display issues")
        
        print(f"  ✅ Data structure verification passed:")
        print(f"     - nom: '{nom}' (not undefined)")
        print(f"     - prenom: '{prenom}' (not undefined)")
        print(f"     - Full name would display as: '{prenom} {nom}'")
        
        # Clean up
        requests.delete(f"{self.base_url}/api/patients/{patient_id}", headers=self.headers)
        
        print(f"🎉 Complete Workflow Test (Minimal): PASSED")
    
    def test_complete_workflow_full_patient(self):
        """Test complete workflow: Create patient → Get patient_id → Retrieve complete patient data (full)"""
        print("\n🔍 Testing Complete Workflow - Full Patient Data")
        
        # Step 1: Create patient with full data
        print("  Step 1: Creating patient with full data...")
        full_patient = {
            "nom": "WorkflowTest",
            "prenom": "Complete",
            "date_naissance": "2020-03-15",
            "telephone": "21655443322",
            "adresse": "456 Avenue Test, Sfax",
            "numero_whatsapp": "21655443322",
            "notes": "Patient créé pour test workflow complet",
            "antecedents": "Aucun antécédent"
        }
        
        create_response = requests.post(f"{self.base_url}/api/patients", json=full_patient, headers=self.headers)
        self.assertEqual(create_response.status_code, 200, f"Patient creation failed: {create_response.text}")
        
        create_data = create_response.json()
        patient_id = create_data["patient_id"]
        print(f"  ✅ Patient created with ID: {patient_id}")
        
        # Step 2: Retrieve complete patient data
        print("  Step 2: Retrieving complete patient data...")
        retrieve_response = requests.get(f"{self.base_url}/api/patients/{patient_id}", headers=self.headers)
        self.assertEqual(retrieve_response.status_code, 200, f"Patient retrieval failed: {retrieve_response.text}")
        
        patient_data = retrieve_response.json()
        print(f"  ✅ Patient data retrieved successfully")
        
        # Step 3: Verify all fields are properly populated
        print("  Step 3: Verifying all fields are properly populated...")
        
        # Verify basic fields
        self.assertEqual(patient_data["nom"], "WorkflowTest")
        self.assertEqual(patient_data["prenom"], "Complete")
        self.assertEqual(patient_data["date_naissance"], "2020-03-15")
        self.assertEqual(patient_data["telephone"], "21655443322")
        self.assertEqual(patient_data["numero_whatsapp"], "21655443322")
        
        # Verify computed fields
        self.assertIn("age", patient_data)
        self.assertIn("lien_whatsapp", patient_data)
        
        # Verify age calculation
        age = patient_data["age"]
        self.assertIsNotNone(age, "Age should be calculated")
        self.assertTrue("4 ans" in age or "5 ans" in age, f"Age calculation seems incorrect: {age}")
        
        # Verify WhatsApp link
        whatsapp_link = patient_data["lien_whatsapp"]
        expected_link = "https://wa.me/21655443322"
        self.assertEqual(whatsapp_link, expected_link, f"WhatsApp link incorrect: {whatsapp_link}")
        
        print(f"  ✅ All fields verification passed:")
        print(f"     - nom: '{patient_data['nom']}'")
        print(f"     - prenom: '{patient_data['prenom']}'")
        print(f"     - age: '{patient_data['age']}'")
        print(f"     - WhatsApp: '{patient_data['lien_whatsapp']}'")
        
        # Clean up
        requests.delete(f"{self.base_url}/api/patients/{patient_id}", headers=self.headers)
        
        print(f"🎉 Complete Workflow Test (Full): PASSED")
    
    def test_edge_case_special_characters(self):
        """Test patient creation with special characters and accents"""
        print("\n🔍 Testing Edge Case - Special Characters and Accents")
        
        # Test with French accents and special characters
        special_patient = {
            "nom": "Bénaïssa",
            "prenom": "Amélie-Rose",
            "date_naissance": "2021-12-25",
            "telephone": "21677889900",
            "adresse": "789 Rue de l'Étoile, Monastir",
            "notes": "Patient avec caractères spéciaux: àáâãäåæçèéêëìíîïñòóôõöøùúûüý"
        }
        
        create_response = requests.post(f"{self.base_url}/api/patients", json=special_patient, headers=self.headers)
        self.assertEqual(create_response.status_code, 200, f"Patient creation with special chars failed: {create_response.text}")
        
        patient_id = create_response.json()["patient_id"]
        
        # Retrieve and verify
        retrieve_response = requests.get(f"{self.base_url}/api/patients/{patient_id}", headers=self.headers)
        self.assertEqual(retrieve_response.status_code, 200)
        
        patient_data = retrieve_response.json()
        
        # Verify special characters are preserved
        self.assertEqual(patient_data["nom"], "Bénaïssa")
        self.assertEqual(patient_data["prenom"], "Amélie-Rose")
        
        print(f"  ✅ Special characters preserved:")
        print(f"     - nom: '{patient_data['nom']}'")
        print(f"     - prenom: '{patient_data['prenom']}'")
        print(f"     - Full name: '{patient_data['prenom']} {patient_data['nom']}'")
        
        # Clean up
        requests.delete(f"{self.base_url}/api/patients/{patient_id}", headers=self.headers)
        
        print(f"🎉 Special Characters Test: PASSED")
    
    def test_edge_case_empty_optional_fields(self):
        """Test patient creation with empty optional fields"""
        print("\n🔍 Testing Edge Case - Empty Optional Fields")
        
        # Test with empty optional fields
        patient_with_empty_fields = {
            "nom": "EmptyFields",
            "prenom": "Test",
            "date_naissance": "",  # Empty
            "telephone": "",       # Empty
            "adresse": "",         # Empty
            "numero_whatsapp": "", # Empty
            "notes": "",           # Empty
            "antecedents": ""      # Empty
        }
        
        create_response = requests.post(f"{self.base_url}/api/patients", json=patient_with_empty_fields, headers=self.headers)
        self.assertEqual(create_response.status_code, 200, f"Patient creation with empty fields failed: {create_response.text}")
        
        patient_id = create_response.json()["patient_id"]
        
        # Retrieve and verify
        retrieve_response = requests.get(f"{self.base_url}/api/patients/{patient_id}", headers=self.headers)
        self.assertEqual(retrieve_response.status_code, 200)
        
        patient_data = retrieve_response.json()
        
        # Verify required fields are still present and not undefined
        self.assertEqual(patient_data["nom"], "EmptyFields")
        self.assertEqual(patient_data["prenom"], "Test")
        
        # Verify empty fields don't cause issues
        self.assertIn("date_naissance", patient_data)
        self.assertIn("telephone", patient_data)
        self.assertIn("age", patient_data)  # Should be calculated even with empty birth date
        self.assertIn("lien_whatsapp", patient_data)  # Should be empty but present
        
        print(f"  ✅ Empty optional fields handled correctly:")
        print(f"     - nom: '{patient_data['nom']}'")
        print(f"     - prenom: '{patient_data['prenom']}'")
        print(f"     - age: '{patient_data.get('age', 'N/A')}'")
        print(f"     - WhatsApp link: '{patient_data.get('lien_whatsapp', 'N/A')}'")
        
        # Clean up
        requests.delete(f"{self.base_url}/api/patients/{patient_id}", headers=self.headers)
        
        print(f"🎉 Empty Optional Fields Test: PASSED")
    
    def test_data_structure_verification(self):
        """Verify patient data structure matches what frontend expects"""
        print("\n🔍 Testing Data Structure Verification")
        
        # Create a patient and verify the complete data structure
        test_patient = {
            "nom": "StructureTest",
            "prenom": "Verification",
            "date_naissance": "2018-06-10",
            "telephone": "21644556677"
        }
        
        create_response = requests.post(f"{self.base_url}/api/patients", json=test_patient, headers=self.headers)
        self.assertEqual(create_response.status_code, 200)
        patient_id = create_response.json()["patient_id"]
        
        # Retrieve patient data
        retrieve_response = requests.get(f"{self.base_url}/api/patients/{patient_id}", headers=self.headers)
        self.assertEqual(retrieve_response.status_code, 200)
        patient_data = retrieve_response.json()
        
        # Verify expected structure for consultation modal
        expected_fields = {
            "id": str,
            "nom": str,
            "prenom": str,
            "date_naissance": str,
            "age": str,
            "telephone": str,
            "adresse": str,
            "numero_whatsapp": str,
            "lien_whatsapp": str,
            "notes": str,
            "antecedents": str,
            "created_at": str,
            "updated_at": str
        }
        
        print("  Verifying field presence and types:")
        for field, expected_type in expected_fields.items():
            self.assertIn(field, patient_data, f"Missing field: {field}")
            
            field_value = patient_data[field]
            if field in ["nom", "prenom", "id"]:  # Critical fields must not be None or empty
                self.assertIsNotNone(field_value, f"Critical field {field} is None")
                self.assertNotEqual(field_value, "", f"Critical field {field} is empty")
            
            # Type checking (allowing None for optional fields)
            if field_value is not None:
                self.assertIsInstance(field_value, expected_type, f"Field {field} has wrong type")
            
            print(f"     - {field}: {type(field_value).__name__} = '{field_value}'")
        
        # Verify the data that would be displayed in consultation modal
        display_name = f"{patient_data['prenom']} {patient_data['nom']}"
        self.assertEqual(display_name, "Verification StructureTest")
        self.assertNotIn("undefined", display_name.lower())
        self.assertNotIn("null", display_name.lower())
        
        print(f"  ✅ Data structure verification passed")
        print(f"     - Display name: '{display_name}'")
        print(f"     - No 'undefined' or 'null' values found")
        
        # Clean up
        requests.delete(f"{self.base_url}/api/patients/{patient_id}", headers=self.headers)
        
        print(f"🎉 Data Structure Verification Test: PASSED")
    
    def test_consultation_modal_simulation(self):
        """Simulate the exact workflow that happens in consultation modal"""
        print("\n🔍 Testing Consultation Modal Simulation")
        
        print("  Simulating consultation modal workflow:")
        print("  1. User clicks 'Nouveau patient' checkbox")
        print("  2. User enters nom and prenom")
        print("  3. User clicks 'Commencer Consultation'")
        print("  4. Frontend creates patient via POST /api/patients")
        print("  5. Frontend gets patient_id from response")
        print("  6. Frontend retrieves patient data via GET /api/patients/{id}")
        print("  7. Frontend displays patient name in consultation header")
        
        # Step 4: Frontend creates patient
        print("\n  Step 4: Creating patient (as frontend would)...")
        new_patient_data = {
            "nom": "ConsultationModal",
            "prenom": "TestPatient"
            # Note: Only nom and prenom provided, as in consultation modal
        }
        
        create_response = requests.post(f"{self.base_url}/api/patients", json=new_patient_data, headers=self.headers)
        self.assertEqual(create_response.status_code, 200, f"Patient creation failed: {create_response.text}")
        
        # Step 5: Frontend gets patient_id
        create_data = create_response.json()
        self.assertIn("patient_id", create_data)
        patient_id = create_data["patient_id"]
        print(f"  ✅ Patient created with ID: {patient_id}")
        
        # Step 6: Frontend retrieves patient data
        print("  Step 6: Retrieving patient data (as frontend would)...")
        retrieve_response = requests.get(f"{self.base_url}/api/patients/{patient_id}", headers=self.headers)
        self.assertEqual(retrieve_response.status_code, 200, f"Patient retrieval failed: {retrieve_response.text}")
        
        patient_data = retrieve_response.json()
        print(f"  ✅ Patient data retrieved")
        
        # Step 7: Simulate frontend display logic
        print("  Step 7: Simulating frontend display logic...")
        
        # This is what the frontend would do to display the patient name
        nom = patient_data.get("nom")
        prenom = patient_data.get("prenom")
        
        # Check for the "undefined undefined" bug
        if nom is None:
            display_nom = "undefined"
        else:
            display_nom = str(nom)
            
        if prenom is None:
            display_prenom = "undefined"
        else:
            display_prenom = str(prenom)
        
        display_name = f"{display_prenom} {display_nom}"
        
        # Verify the bug is NOT present
        self.assertNotEqual(display_name, "undefined undefined", "Found the 'undefined undefined' bug!")
        self.assertNotIn("undefined", display_name, f"Found 'undefined' in display name: {display_name}")
        
        # Verify correct display
        expected_display = "TestPatient ConsultationModal"
        self.assertEqual(display_name, expected_display, f"Display name incorrect: {display_name}")
        
        print(f"  ✅ Frontend display simulation passed:")
        print(f"     - nom from API: '{nom}'")
        print(f"     - prenom from API: '{prenom}'")
        print(f"     - Display name: '{display_name}'")
        print(f"     - Expected: '{expected_display}'")
        print(f"     - Bug check: NO 'undefined undefined' found ✅")
        
        # Clean up
        requests.delete(f"{self.base_url}/api/patients/{patient_id}", headers=self.headers)
        
        print(f"🎉 Consultation Modal Simulation Test: PASSED")

def run_patient_workflow_tests():
    """Run all patient workflow tests"""
    print("=" * 80)
    print("PATIENT CREATION AND RETRIEVAL WORKFLOW TESTING")
    print("Focus: Testing the workflow that causes 'undefined undefined' bug")
    print("=" * 80)
    
    # Create test suite
    suite = unittest.TestSuite()
    
    # Add all test methods
    test_methods = [
        'test_patient_creation_minimal_data',
        'test_patient_creation_complete_data', 
        'test_patient_retrieval_by_id',
        'test_complete_workflow_minimal_patient',
        'test_complete_workflow_full_patient',
        'test_edge_case_special_characters',
        'test_edge_case_empty_optional_fields',
        'test_data_structure_verification',
        'test_consultation_modal_simulation'
    ]
    
    for method in test_methods:
        suite.addTest(PatientWorkflowTest(method))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 80)
    print("PATIENT WORKFLOW TESTING SUMMARY")
    print("=" * 80)
    
    total_tests = result.testsRun
    failures = len(result.failures)
    errors = len(result.errors)
    passed = total_tests - failures - errors
    
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed}")
    print(f"Failed: {failures}")
    print(f"Errors: {errors}")
    
    if failures > 0:
        print("\nFAILURES:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")
    
    if errors > 0:
        print("\nERRORS:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")
    
    success_rate = (passed / total_tests) * 100 if total_tests > 0 else 0
    print(f"\nSuccess Rate: {success_rate:.1f}%")
    
    if success_rate == 100:
        print("🎉 ALL PATIENT WORKFLOW TESTS PASSED!")
        print("✅ No 'undefined undefined' bug found in patient creation/retrieval workflow")
    else:
        print("❌ Some tests failed - patient workflow issues detected")
    
    return result

if __name__ == "__main__":
    run_patient_workflow_tests()