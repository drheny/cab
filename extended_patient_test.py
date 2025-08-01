#!/usr/bin/env python3
"""
Extended Patient Workflow Testing - Deep Dive Analysis
Focus: Comprehensive testing to identify any potential causes of "undefined undefined" bug
"""

import requests
import unittest
import json
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/frontend/.env')

class ExtendedPatientWorkflowTest(unittest.TestCase):
    def setUp(self):
        backend_url = os.getenv('REACT_APP_BACKEND_URL', 'https://f310bc43-97b2-405e-8eb3-271aa9c20e28.preview.emergentagent.com')
        self.base_url = backend_url
        self.auth_token = "auto-login-token"
        self.headers = {"Authorization": f"Bearer {self.auth_token}"}
    
    def test_patient_search_endpoint(self):
        """Test GET /api/patients/search endpoint used in consultation modal"""
        print("\n🔍 Testing Patient Search Endpoint (used in consultation modal)")
        
        # First create a test patient
        test_patient = {
            "nom": "SearchTest",
            "prenom": "Patient",
            "date_naissance": "2020-01-15",
            "telephone": "21611223344"
        }
        
        create_response = requests.post(f"{self.base_url}/api/patients", json=test_patient, headers=self.headers)
        self.assertEqual(create_response.status_code, 200)
        patient_id = create_response.json()["patient_id"]
        
        # Test search functionality
        search_response = requests.get(f"{self.base_url}/api/patients/search?q=SearchTest", headers=self.headers)
        print(f"Search response status: {search_response.status_code}")
        print(f"Search response body: {search_response.text}")
        
        self.assertEqual(search_response.status_code, 200)
        search_data = search_response.json()
        
        self.assertIn("patients", search_data)
        patients = search_data["patients"]
        
        # Find our test patient in search results
        found_patient = None
        for patient in patients:
            if patient.get("id") == patient_id:
                found_patient = patient
                break
        
        self.assertIsNotNone(found_patient, "Created patient not found in search results")
        
        # Verify search result structure
        required_fields = ["id", "nom", "prenom", "age", "numero_whatsapp"]
        for field in required_fields:
            self.assertIn(field, found_patient, f"Missing field in search result: {field}")
        
        # Verify no undefined values
        self.assertEqual(found_patient["nom"], "SearchTest")
        self.assertEqual(found_patient["prenom"], "Patient")
        self.assertIsNotNone(found_patient["nom"])
        self.assertIsNotNone(found_patient["prenom"])
        
        print(f"✅ Search endpoint working correctly:")
        print(f"   - Found patient: {found_patient['prenom']} {found_patient['nom']}")
        print(f"   - Age: {found_patient.get('age', 'N/A')}")
        
        # Clean up
        requests.delete(f"{self.base_url}/api/patients/{patient_id}", headers=self.headers)
        
        print(f"🎉 Patient Search Test: PASSED")
    
    def test_patient_list_pagination(self):
        """Test GET /api/patients with pagination (used in patient selection)"""
        print("\n🔍 Testing Patient List with Pagination")
        
        # Test default pagination
        response = requests.get(f"{self.base_url}/api/patients", headers=self.headers)
        print(f"Pagination response status: {response.status_code}")
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify pagination structure
        self.assertIn("patients", data)
        self.assertIn("total_count", data)
        self.assertIn("page", data)
        self.assertIn("limit", data)
        self.assertIn("total_pages", data)
        
        patients = data["patients"]
        
        # Verify each patient has required fields for consultation modal
        for patient in patients:
            # Critical fields that must not be undefined
            self.assertIn("id", patient)
            self.assertIn("nom", patient)
            self.assertIn("prenom", patient)
            
            # Verify no None values for critical fields
            self.assertIsNotNone(patient["id"], f"Patient ID is None: {patient}")
            self.assertIsNotNone(patient["nom"], f"Patient nom is None: {patient}")
            self.assertIsNotNone(patient["prenom"], f"Patient prenom is None: {patient}")
            
            # Verify no empty strings for critical fields
            self.assertNotEqual(patient["nom"], "", f"Patient nom is empty: {patient}")
            self.assertNotEqual(patient["prenom"], "", f"Patient prenom is empty: {patient}")
            
            print(f"   - Patient: {patient['prenom']} {patient['nom']} (ID: {patient['id']})")
        
        print(f"✅ Patient list pagination working correctly")
        print(f"   - Total patients: {data['total_count']}")
        print(f"   - Page: {data['page']}")
        print(f"   - Limit: {data['limit']}")
        
        print(f"🎉 Patient List Pagination Test: PASSED")
    
    def test_appointment_creation_with_patient(self):
        """Test appointment creation workflow that might be related to the bug"""
        print("\n🔍 Testing Appointment Creation with Patient")
        
        # Create a patient first
        test_patient = {
            "nom": "AppointmentTest",
            "prenom": "Patient",
            "date_naissance": "2019-05-20",
            "telephone": "21699887766"
        }
        
        create_response = requests.post(f"{self.base_url}/api/patients", json=test_patient, headers=self.headers)
        self.assertEqual(create_response.status_code, 200)
        patient_id = create_response.json()["patient_id"]
        
        # Create an appointment for this patient
        appointment_data = {
            "patient_id": patient_id,
            "date": "2025-07-30",
            "heure": "10:00",
            "type_rdv": "visite",
            "motif": "Consultation test",
            "notes": "Test appointment creation"
        }
        
        appt_response = requests.post(f"{self.base_url}/api/appointments", json=appointment_data, headers=self.headers)
        print(f"Appointment creation status: {appt_response.status_code}")
        print(f"Appointment creation response: {appt_response.text}")
        
        self.assertEqual(appt_response.status_code, 200)
        appointment_id = appt_response.json()["appointment_id"]
        
        # Get appointments for the day to verify patient info is included
        day_response = requests.get(f"{self.base_url}/api/rdv/jour/2025-07-30", headers=self.headers)
        self.assertEqual(day_response.status_code, 200)
        appointments = day_response.json()
        
        # Find our appointment
        found_appointment = None
        for appt in appointments:
            if appt["id"] == appointment_id:
                found_appointment = appt
                break
        
        self.assertIsNotNone(found_appointment, "Created appointment not found")
        
        # Verify patient info is included and correct
        self.assertIn("patient", found_appointment)
        patient_info = found_appointment["patient"]
        
        self.assertIn("nom", patient_info)
        self.assertIn("prenom", patient_info)
        self.assertEqual(patient_info["nom"], "AppointmentTest")
        self.assertEqual(patient_info["prenom"], "Patient")
        
        print(f"✅ Appointment creation with patient info working:")
        print(f"   - Patient in appointment: {patient_info['prenom']} {patient_info['nom']}")
        print(f"   - Appointment ID: {appointment_id}")
        
        # Clean up
        requests.delete(f"{self.base_url}/api/appointments/{appointment_id}", headers=self.headers)
        requests.delete(f"{self.base_url}/api/patients/{patient_id}", headers=self.headers)
        
        print(f"🎉 Appointment Creation Test: PASSED")
    
    def test_consultation_creation_workflow(self):
        """Test consultation creation workflow"""
        print("\n🔍 Testing Consultation Creation Workflow")
        
        # Create patient and appointment first
        test_patient = {
            "nom": "ConsultationTest",
            "prenom": "Patient",
            "date_naissance": "2020-03-10"
        }
        
        create_response = requests.post(f"{self.base_url}/api/patients", json=test_patient, headers=self.headers)
        self.assertEqual(create_response.status_code, 200)
        patient_id = create_response.json()["patient_id"]
        
        # Create appointment
        appointment_data = {
            "patient_id": patient_id,
            "date": "2025-07-30",
            "heure": "11:00",
            "type_rdv": "visite"
        }
        
        appt_response = requests.post(f"{self.base_url}/api/appointments", json=appointment_data, headers=self.headers)
        self.assertEqual(appt_response.status_code, 200)
        appointment_id = appt_response.json()["appointment_id"]
        
        # Create consultation
        consultation_data = {
            "patient_id": patient_id,
            "appointment_id": appointment_id,
            "date": "2025-07-30",
            "type_rdv": "visite",
            "duree": 30,
            "diagnostic": "Test diagnostic",
            "observation_clinique": "Test observation"
        }
        
        cons_response = requests.post(f"{self.base_url}/api/consultations", json=consultation_data, headers=self.headers)
        print(f"Consultation creation status: {cons_response.status_code}")
        print(f"Consultation creation response: {cons_response.text}")
        
        self.assertEqual(cons_response.status_code, 200)
        consultation_id = cons_response.json()["consultation_id"]
        
        # Get consultation to verify data
        get_cons_response = requests.get(f"{self.base_url}/api/consultations/{consultation_id}", headers=self.headers)
        self.assertEqual(get_cons_response.status_code, 200)
        consultation_data = get_cons_response.json()
        
        # Verify consultation has correct patient_id
        self.assertEqual(consultation_data["patient_id"], patient_id)
        
        # Get patient consultations to verify relationship
        patient_cons_response = requests.get(f"{self.base_url}/api/patients/{patient_id}/consultations", headers=self.headers)
        self.assertEqual(patient_cons_response.status_code, 200)
        patient_consultations = patient_cons_response.json()
        
        # Verify consultation appears in patient's consultation list
        found_consultation = False
        for cons in patient_consultations:
            if cons["id"] == consultation_id:
                found_consultation = True
                break
        
        self.assertTrue(found_consultation, "Consultation not found in patient's consultation list")
        
        print(f"✅ Consultation creation workflow working:")
        print(f"   - Consultation ID: {consultation_id}")
        print(f"   - Patient ID: {patient_id}")
        print(f"   - Patient consultations count: {len(patient_consultations)}")
        
        # Clean up
        requests.delete(f"{self.base_url}/api/consultations/{consultation_id}", headers=self.headers)
        requests.delete(f"{self.base_url}/api/appointments/{appointment_id}", headers=self.headers)
        requests.delete(f"{self.base_url}/api/patients/{patient_id}", headers=self.headers)
        
        print(f"🎉 Consultation Creation Test: PASSED")
    
    def test_null_and_undefined_handling(self):
        """Test how the API handles null and undefined values"""
        print("\n🔍 Testing Null and Undefined Value Handling")
        
        # Test with null values in JSON
        patient_with_nulls = {
            "nom": "NullTest",
            "prenom": "Patient",
            "date_naissance": None,
            "telephone": None,
            "adresse": None,
            "numero_whatsapp": None,
            "notes": None,
            "antecedents": None
        }
        
        create_response = requests.post(f"{self.base_url}/api/patients", json=patient_with_nulls, headers=self.headers)
        print(f"Creation with nulls status: {create_response.status_code}")
        print(f"Creation with nulls response: {create_response.text}")
        
        self.assertEqual(create_response.status_code, 200)
        patient_id = create_response.json()["patient_id"]
        
        # Retrieve and verify null handling
        retrieve_response = requests.get(f"{self.base_url}/api/patients/{patient_id}", headers=self.headers)
        self.assertEqual(retrieve_response.status_code, 200)
        patient_data = retrieve_response.json()
        
        # Verify critical fields are not null
        self.assertIsNotNone(patient_data["nom"])
        self.assertIsNotNone(patient_data["prenom"])
        self.assertEqual(patient_data["nom"], "NullTest")
        self.assertEqual(patient_data["prenom"], "Patient")
        
        # Verify null fields are handled properly (converted to empty strings)
        nullable_fields = ["date_naissance", "telephone", "adresse", "numero_whatsapp", "notes", "antecedents"]
        for field in nullable_fields:
            field_value = patient_data.get(field)
            # Should be either empty string or None, but not undefined
            self.assertTrue(field_value is None or field_value == "", 
                          f"Field {field} has unexpected value: {field_value}")
        
        print(f"✅ Null value handling working correctly:")
        print(f"   - nom: '{patient_data['nom']}'")
        print(f"   - prenom: '{patient_data['prenom']}'")
        print(f"   - Null fields handled properly")
        
        # Clean up
        requests.delete(f"{self.base_url}/api/patients/{patient_id}", headers=self.headers)
        
        print(f"🎉 Null Handling Test: PASSED")
    
    def test_concurrent_patient_operations(self):
        """Test concurrent patient creation and retrieval"""
        print("\n🔍 Testing Concurrent Patient Operations")
        
        # Create multiple patients quickly
        patients_to_create = [
            {"nom": "Concurrent1", "prenom": "Patient"},
            {"nom": "Concurrent2", "prenom": "Patient"},
            {"nom": "Concurrent3", "prenom": "Patient"}
        ]
        
        created_patient_ids = []
        
        # Create patients
        for i, patient_data in enumerate(patients_to_create):
            create_response = requests.post(f"{self.base_url}/api/patients", json=patient_data, headers=self.headers)
            self.assertEqual(create_response.status_code, 200, f"Failed to create patient {i+1}")
            patient_id = create_response.json()["patient_id"]
            created_patient_ids.append(patient_id)
        
        # Retrieve all patients immediately
        for i, patient_id in enumerate(created_patient_ids):
            retrieve_response = requests.get(f"{self.base_url}/api/patients/{patient_id}", headers=self.headers)
            self.assertEqual(retrieve_response.status_code, 200, f"Failed to retrieve patient {i+1}")
            
            patient_data = retrieve_response.json()
            expected_nom = f"Concurrent{i+1}"
            
            self.assertEqual(patient_data["nom"], expected_nom)
            self.assertEqual(patient_data["prenom"], "Patient")
            self.assertIsNotNone(patient_data["nom"])
            self.assertIsNotNone(patient_data["prenom"])
            
            print(f"   - Patient {i+1}: {patient_data['prenom']} {patient_data['nom']}")
        
        print(f"✅ Concurrent operations working correctly")
        print(f"   - Created and retrieved {len(created_patient_ids)} patients")
        
        # Clean up
        for patient_id in created_patient_ids:
            requests.delete(f"{self.base_url}/api/patients/{patient_id}", headers=self.headers)
        
        print(f"🎉 Concurrent Operations Test: PASSED")
    
    def test_patient_update_workflow(self):
        """Test patient update workflow that might affect consultation display"""
        print("\n🔍 Testing Patient Update Workflow")
        
        # Create initial patient
        initial_patient = {
            "nom": "UpdateTest",
            "prenom": "Initial",
            "date_naissance": "2020-01-01"
        }
        
        create_response = requests.post(f"{self.base_url}/api/patients", json=initial_patient, headers=self.headers)
        self.assertEqual(create_response.status_code, 200)
        patient_id = create_response.json()["patient_id"]
        
        # Update patient data
        updated_patient = {
            "id": patient_id,
            "nom": "UpdateTest",
            "prenom": "Updated",
            "date_naissance": "2020-01-01",
            "telephone": "21655443322",
            "adresse": "Updated address",
            "numero_whatsapp": "21655443322",
            "notes": "Updated notes",
            "antecedents": "Updated antecedents",
            "pere": {"nom": "", "telephone": "", "fonction": ""},
            "mere": {"nom": "", "telephone": "", "fonction": ""},
            "consultations": [],
            "date_premiere_consultation": "",
            "date_derniere_consultation": "",
            "sexe": "",
            "nom_parent": "",
            "telephone_parent": "",
            "assurance": "",
            "numero_assurance": "",
            "allergies": "",
            "photo_url": "",
            "created_at": "2025-07-29T04:43:59.072000",
            "updated_at": "2025-07-29T04:43:59.072000"
        }
        
        update_response = requests.put(f"{self.base_url}/api/patients/{patient_id}", json=updated_patient, headers=self.headers)
        print(f"Update response status: {update_response.status_code}")
        print(f"Update response: {update_response.text}")
        
        self.assertEqual(update_response.status_code, 200)
        
        # Retrieve updated patient
        retrieve_response = requests.get(f"{self.base_url}/api/patients/{patient_id}", headers=self.headers)
        self.assertEqual(retrieve_response.status_code, 200)
        updated_data = retrieve_response.json()
        
        # Verify update worked correctly
        self.assertEqual(updated_data["nom"], "UpdateTest")
        self.assertEqual(updated_data["prenom"], "Updated")  # This should be updated
        self.assertEqual(updated_data["telephone"], "21655443322")
        
        # Verify no undefined values
        self.assertIsNotNone(updated_data["nom"])
        self.assertIsNotNone(updated_data["prenom"])
        
        print(f"✅ Patient update working correctly:")
        print(f"   - Original: Initial UpdateTest")
        print(f"   - Updated: {updated_data['prenom']} {updated_data['nom']}")
        
        # Clean up
        requests.delete(f"{self.base_url}/api/patients/{patient_id}", headers=self.headers)
        
        print(f"🎉 Patient Update Test: PASSED")

def run_extended_tests():
    """Run extended patient workflow tests"""
    print("=" * 80)
    print("EXTENDED PATIENT WORKFLOW TESTING")
    print("Deep dive analysis for 'undefined undefined' bug")
    print("=" * 80)
    
    # Create test suite
    suite = unittest.TestSuite()
    
    # Add all test methods
    test_methods = [
        'test_patient_search_endpoint',
        'test_patient_list_pagination',
        'test_appointment_creation_with_patient',
        'test_consultation_creation_workflow',
        'test_null_and_undefined_handling',
        'test_concurrent_patient_operations',
        'test_patient_update_workflow'
    ]
    
    for method in test_methods:
        suite.addTest(ExtendedPatientWorkflowTest(method))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 80)
    print("EXTENDED TESTING SUMMARY")
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
    
    return result

if __name__ == "__main__":
    run_extended_tests()