#!/usr/bin/env python3
"""
Backend Testing for Patient Model Cleanup and Export Functionality
Testing the removal of fields: assurance, numero_assurance, nom_parent, telephone_parent
Testing new admin export endpoints for patients, consultations, and payments
"""

import requests
import json
import sys
from datetime import datetime
import uuid

# Configuration
BACKEND_URL = "https://0698237d-0754-4aa4-881e-3c8e5387d3e6.preview.emergentagent.com/api"
AUTH_TOKEN = "auto-login-token"  # Using auto-login for testing

# Headers for authenticated requests
HEADERS = {
    "Authorization": f"Bearer {AUTH_TOKEN}",
    "Content-Type": "application/json"
}

def log_test(test_name, status, details=""):
    """Log test results"""
    status_symbol = "✅" if status else "❌"
    print(f"{status_symbol} {test_name}")
    if details:
        print(f"   {details}")
    return status

def test_patient_model_structure():
    """Test 1: Verify Patient model no longer contains removed fields"""
    print("\n🔍 TEST 1: Patient Model Structure Verification")
    
    try:
        # Create a test patient to verify model structure
        test_patient = {
            "nom": "TestCleanup",
            "prenom": "ModelTest",
            "date_naissance": "2020-01-01",
            "sexe": "M",
            "telephone": "21612345678",
            "adresse": "Test Address",
            "numero_whatsapp": "21612345678",
            "notes": "Test patient for model cleanup verification",
            "antecedents": "None",
            "allergies": "None"
        }
        
        # Try to create patient with clean model
        response = requests.post(f"{BACKEND_URL}/patients", json=test_patient, headers=HEADERS)
        
        if response.status_code == 200:
            patient_id = response.json().get("patient_id")
            log_test("Patient creation with clean model", True, f"Patient ID: {patient_id}")
            
            # Retrieve the created patient to verify structure
            get_response = requests.get(f"{BACKEND_URL}/patients/{patient_id}", headers=HEADERS)
            
            if get_response.status_code == 200:
                patient_data = get_response.json()
                
                # Check that removed fields are NOT present
                removed_fields = ["assurance", "numero_assurance", "nom_parent", "telephone_parent"]
                removed_fields_found = []
                
                for field in removed_fields:
                    if field in patient_data:
                        removed_fields_found.append(field)
                
                if not removed_fields_found:
                    log_test("Removed fields verification", True, "No removed fields found in patient data")
                else:
                    log_test("Removed fields verification", False, f"Found removed fields: {removed_fields_found}")
                
                # Check that required fields are present
                required_fields = ["id", "nom", "prenom", "date_naissance", "age", "sexe", "telephone", "adresse", "numero_whatsapp", "pere", "mere", "notes", "antecedents", "allergies"]
                missing_fields = []
                
                for field in required_fields:
                    if field not in patient_data:
                        missing_fields.append(field)
                
                if not missing_fields:
                    log_test("Required fields verification", True, f"All {len(required_fields)} required fields present")
                else:
                    log_test("Required fields verification", False, f"Missing fields: {missing_fields}")
                
                return True, patient_id
            else:
                log_test("Patient retrieval", False, f"Status: {get_response.status_code}")
                return False, None
        else:
            log_test("Patient creation with clean model", False, f"Status: {response.status_code}, Response: {response.text}")
            return False, None
            
    except Exception as e:
        log_test("Patient model structure test", False, f"Exception: {str(e)}")
        return False, None

def test_admin_export_patients():
    """Test 2: Test admin export patients endpoint"""
    print("\n🔍 TEST 2: Admin Export Patients Endpoint")
    
    try:
        response = requests.get(f"{BACKEND_URL}/admin/export/patients", headers=HEADERS)
        
        if response.status_code == 200:
            export_data = response.json()
            log_test("Patients export endpoint access", True, f"Status: {response.status_code}")
            
            # Verify response structure
            required_keys = ["data", "count", "collection", "fields"]
            missing_keys = [key for key in required_keys if key not in export_data]
            
            if not missing_keys:
                log_test("Export response structure", True, f"All required keys present: {required_keys}")
            else:
                log_test("Export response structure", False, f"Missing keys: {missing_keys}")
                return False
            
            # Verify collection name
            if export_data.get("collection") == "patients":
                log_test("Collection name verification", True, "Collection: patients")
            else:
                log_test("Collection name verification", False, f"Expected 'patients', got '{export_data.get('collection')}'")
            
            # Verify data count matches actual count
            data_count = len(export_data.get("data", []))
            reported_count = export_data.get("count", 0)
            
            if data_count == reported_count:
                log_test("Data count consistency", True, f"Count: {data_count}")
            else:
                log_test("Data count consistency", False, f"Data length: {data_count}, Reported count: {reported_count}")
            
            # Verify fields list contains expected fields and excludes removed fields
            fields_list = export_data.get("fields", [])
            expected_fields = ["id", "nom", "prenom", "date_naissance", "age", "sexe", "telephone", "adresse", "numero_whatsapp", "pere", "mere", "notes", "antecedents", "allergies"]
            removed_fields = ["assurance", "numero_assurance", "nom_parent", "telephone_parent"]
            
            # Check expected fields are in the list
            missing_expected = [field for field in expected_fields if field not in fields_list]
            if not missing_expected:
                log_test("Expected fields in export", True, f"All {len(expected_fields)} expected fields present")
            else:
                log_test("Expected fields in export", False, f"Missing expected fields: {missing_expected}")
            
            # Check removed fields are NOT in the list
            found_removed = [field for field in removed_fields if field in fields_list]
            if not found_removed:
                log_test("Removed fields excluded from export", True, "No removed fields in export fields list")
            else:
                log_test("Removed fields excluded from export", False, f"Found removed fields in export: {found_removed}")
            
            # Verify actual patient data doesn't contain removed fields
            if export_data.get("data"):
                sample_patient = export_data["data"][0]
                removed_in_data = [field for field in removed_fields if field in sample_patient]
                
                if not removed_in_data:
                    log_test("Patient data cleanup", True, "No removed fields in actual patient data")
                else:
                    log_test("Patient data cleanup", False, f"Found removed fields in patient data: {removed_in_data}")
            
            return True
        else:
            log_test("Patients export endpoint access", False, f"Status: {response.status_code}, Response: {response.text}")
            return False
            
    except Exception as e:
        log_test("Admin export patients test", False, f"Exception: {str(e)}")
        return False

def test_admin_export_consultations():
    """Test 3: Test admin export consultations endpoint"""
    print("\n🔍 TEST 3: Admin Export Consultations Endpoint")
    
    try:
        response = requests.get(f"{BACKEND_URL}/admin/export/consultations", headers=HEADERS)
        
        if response.status_code == 200:
            export_data = response.json()
            log_test("Consultations export endpoint access", True, f"Status: {response.status_code}")
            
            # Verify response structure
            required_keys = ["data", "count", "collection"]
            missing_keys = [key for key in required_keys if key not in export_data]
            
            if not missing_keys:
                log_test("Consultations export response structure", True, f"Required keys present: {required_keys}")
            else:
                log_test("Consultations export response structure", False, f"Missing keys: {missing_keys}")
                return False
            
            # Verify collection name
            if export_data.get("collection") == "consultations":
                log_test("Consultations collection name", True, "Collection: consultations")
            else:
                log_test("Consultations collection name", False, f"Expected 'consultations', got '{export_data.get('collection')}'")
            
            # Verify data count consistency
            data_count = len(export_data.get("data", []))
            reported_count = export_data.get("count", 0)
            
            if data_count == reported_count:
                log_test("Consultations data count consistency", True, f"Count: {data_count}")
            else:
                log_test("Consultations data count consistency", False, f"Data length: {data_count}, Reported count: {reported_count}")
            
            return True
        else:
            log_test("Consultations export endpoint access", False, f"Status: {response.status_code}, Response: {response.text}")
            return False
            
    except Exception as e:
        log_test("Admin export consultations test", False, f"Exception: {str(e)}")
        return False

def test_admin_export_payments():
    """Test 4: Test admin export payments endpoint"""
    print("\n🔍 TEST 4: Admin Export Payments Endpoint")
    
    try:
        response = requests.get(f"{BACKEND_URL}/admin/export/payments", headers=HEADERS)
        
        if response.status_code == 200:
            export_data = response.json()
            log_test("Payments export endpoint access", True, f"Status: {response.status_code}")
            
            # Verify response structure
            required_keys = ["data", "count", "collection"]
            missing_keys = [key for key in required_keys if key not in export_data]
            
            if not missing_keys:
                log_test("Payments export response structure", True, f"Required keys present: {required_keys}")
            else:
                log_test("Payments export response structure", False, f"Missing keys: {missing_keys}")
                return False
            
            # Verify collection name
            if export_data.get("collection") == "payments":
                log_test("Payments collection name", True, "Collection: payments")
            else:
                log_test("Payments collection name", False, f"Expected 'payments', got '{export_data.get('collection')}'")
            
            # Verify data count consistency
            data_count = len(export_data.get("data", []))
            reported_count = export_data.get("count", 0)
            
            if data_count == reported_count:
                log_test("Payments data count consistency", True, f"Count: {data_count}")
            else:
                log_test("Payments data count consistency", False, f"Data length: {data_count}, Reported count: {reported_count}")
            
            return True
        else:
            log_test("Payments export endpoint access", False, f"Status: {response.status_code}, Response: {response.text}")
            return False
            
    except Exception as e:
        log_test("Admin export payments test", False, f"Exception: {str(e)}")
        return False

def test_patient_crud_operations():
    """Test 5: Test patient CRUD operations with cleaned model"""
    print("\n🔍 TEST 5: Patient CRUD Operations with Cleaned Model")
    
    try:
        # Test CREATE
        test_patient = {
            "nom": "CRUDTest",
            "prenom": "Patient",
            "date_naissance": "2021-06-15",
            "sexe": "F",
            "telephone": "21687654321",
            "adresse": "CRUD Test Address",
            "numero_whatsapp": "21687654321",
            "notes": "Test patient for CRUD operations",
            "antecedents": "Test antecedents",
            "allergies": "Test allergies",
            "pere": {
                "nom": "Test Father",
                "telephone": "21612345678",
                "fonction": "Engineer"
            },
            "mere": {
                "nom": "Test Mother", 
                "telephone": "21612345679",
                "fonction": "Doctor"
            }
        }
        
        # CREATE
        create_response = requests.post(f"{BACKEND_URL}/patients", json=test_patient, headers=HEADERS)
        
        if create_response.status_code == 200:
            patient_id = create_response.json().get("patient_id")
            log_test("Patient CREATE operation", True, f"Patient ID: {patient_id}")
            
            # READ
            read_response = requests.get(f"{BACKEND_URL}/patients/{patient_id}", headers=HEADERS)
            
            if read_response.status_code == 200:
                patient_data = read_response.json()
                log_test("Patient READ operation", True, f"Retrieved patient: {patient_data.get('nom')} {patient_data.get('prenom')}")
                
                # Verify no removed fields in retrieved data
                removed_fields = ["assurance", "numero_assurance", "nom_parent", "telephone_parent"]
                found_removed = [field for field in removed_fields if field in patient_data]
                
                if not found_removed:
                    log_test("READ data cleanup verification", True, "No removed fields in retrieved data")
                else:
                    log_test("READ data cleanup verification", False, f"Found removed fields: {found_removed}")
                
                # UPDATE
                update_data = patient_data.copy()
                update_data["notes"] = "Updated notes for CRUD test"
                update_data["allergies"] = "Updated allergies"
                
                update_response = requests.put(f"{BACKEND_URL}/patients/{patient_id}", json=update_data, headers=HEADERS)
                
                if update_response.status_code == 200:
                    log_test("Patient UPDATE operation", True, "Patient updated successfully")
                    
                    # Verify update
                    verify_response = requests.get(f"{BACKEND_URL}/patients/{patient_id}", headers=HEADERS)
                    if verify_response.status_code == 200:
                        updated_data = verify_response.json()
                        if updated_data.get("notes") == "Updated notes for CRUD test":
                            log_test("UPDATE verification", True, "Update changes verified")
                        else:
                            log_test("UPDATE verification", False, "Update changes not reflected")
                    
                    # DELETE
                    delete_response = requests.delete(f"{BACKEND_URL}/patients/{patient_id}", headers=HEADERS)
                    
                    if delete_response.status_code == 200:
                        log_test("Patient DELETE operation", True, "Patient deleted successfully")
                        
                        # Verify deletion
                        verify_delete = requests.get(f"{BACKEND_URL}/patients/{patient_id}", headers=HEADERS)
                        if verify_delete.status_code == 404:
                            log_test("DELETE verification", True, "Patient not found after deletion")
                            return True
                        else:
                            log_test("DELETE verification", False, f"Patient still exists after deletion: {verify_delete.status_code}")
                    else:
                        log_test("Patient DELETE operation", False, f"Status: {delete_response.status_code}")
                else:
                    log_test("Patient UPDATE operation", False, f"Status: {update_response.status_code}")
            else:
                log_test("Patient READ operation", False, f"Status: {read_response.status_code}")
        else:
            log_test("Patient CREATE operation", False, f"Status: {create_response.status_code}, Response: {create_response.text}")
        
        return False
        
    except Exception as e:
        log_test("Patient CRUD operations test", False, f"Exception: {str(e)}")
        return False

def test_demo_data_initialization():
    """Test 6: Test demo data initialization without removed fields"""
    print("\n🔍 TEST 6: Demo Data Initialization Test")
    
    try:
        # Test demo data initialization endpoint
        response = requests.get(f"{BACKEND_URL}/init-demo", headers=HEADERS)
        
        if response.status_code == 200:
            init_result = response.json()
            log_test("Demo data initialization endpoint", True, f"Response: {init_result.get('message', 'Success')}")
            
            # Get patients to verify demo data structure
            patients_response = requests.get(f"{BACKEND_URL}/patients?limit=50", headers=HEADERS)
            
            if patients_response.status_code == 200:
                patients_data = patients_response.json()
                patients = patients_data.get("patients", [])
                
                if patients:
                    log_test("Demo patients created", True, f"Found {len(patients)} patients")
                    
                    # Check first patient for removed fields
                    sample_patient = patients[0]
                    removed_fields = ["assurance", "numero_assurance", "nom_parent", "telephone_parent"]
                    found_removed = [field for field in removed_fields if field in sample_patient]
                    
                    if not found_removed:
                        log_test("Demo data cleanup", True, "No removed fields in demo patient data")
                    else:
                        log_test("Demo data cleanup", False, f"Found removed fields in demo data: {found_removed}")
                    
                    # Verify required fields are present
                    required_fields = ["id", "nom", "prenom", "pere", "mere"]
                    missing_required = [field for field in required_fields if field not in sample_patient]
                    
                    if not missing_required:
                        log_test("Demo data completeness", True, "All required fields present in demo data")
                        return True
                    else:
                        log_test("Demo data completeness", False, f"Missing required fields: {missing_required}")
                else:
                    log_test("Demo patients created", False, "No patients found after demo initialization")
            else:
                log_test("Demo patients retrieval", False, f"Status: {patients_response.status_code}")
        else:
            log_test("Demo data initialization endpoint", False, f"Status: {response.status_code}, Response: {response.text}")
        
        return False
        
    except Exception as e:
        log_test("Demo data initialization test", False, f"Exception: {str(e)}")
        return False

def test_export_invalid_data_type():
    """Test 7: Test export endpoint with invalid data type"""
    print("\n🔍 TEST 7: Export Endpoint Error Handling")
    
    try:
        # Test with invalid data type
        response = requests.get(f"{BACKEND_URL}/admin/export/invalid_type", headers=HEADERS)
        
        if response.status_code == 400:
            log_test("Invalid data type handling", True, "Correctly returned 400 for invalid data type")
            return True
        else:
            log_test("Invalid data type handling", False, f"Expected 400, got {response.status_code}")
            return False
            
    except Exception as e:
        log_test("Export error handling test", False, f"Exception: {str(e)}")
        return False

def run_all_tests():
    """Run all patient model cleanup and export tests"""
    print("🚀 PATIENT MODEL CLEANUP AND EXPORT FUNCTIONALITY TESTING")
    print("=" * 70)
    
    test_results = []
    
    # Run all tests
    test_results.append(test_patient_model_structure())
    test_results.append(test_admin_export_patients())
    test_results.append(test_admin_export_consultations())
    test_results.append(test_admin_export_payments())
    test_results.append(test_patient_crud_operations())
    test_results.append(test_demo_data_initialization())
    test_results.append(test_export_invalid_data_type())
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 TEST SUMMARY")
    print("=" * 70)
    
    # Handle mixed return types (tuples and booleans)
    passed_tests = 0
    for result in test_results:
        if isinstance(result, tuple):
            if result[0]:
                passed_tests += 1
        elif result:
            passed_tests += 1
    
    total_tests = len(test_results)
    
    print(f"✅ Passed: {passed_tests}/{total_tests}")
    print(f"❌ Failed: {total_tests - passed_tests}/{total_tests}")
    
    if passed_tests == total_tests:
        print("\n🎉 ALL TESTS PASSED - Patient model cleanup and export functionality working correctly!")
        return True
    else:
        print(f"\n⚠️  {total_tests - passed_tests} TEST(S) FAILED - Issues found in patient model cleanup or export functionality")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)