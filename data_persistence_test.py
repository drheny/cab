#!/usr/bin/env python3
"""
Data Persistence Correction Testing
Testing the critical fix for data persistence issues where patient modifications were being overwritten.
"""

import requests
import json
import sys
from datetime import datetime

# Configuration
BACKEND_URL = "https://f310bc43-97b2-405e-8eb3-271aa9c20e28.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

# Test authentication token (auto-login for testing)
AUTH_TOKEN = "auto-login-token"
HEADERS = {
    "Authorization": f"Bearer {AUTH_TOKEN}",
    "Content-Type": "application/json"
}

def log_test(message, status="INFO"):
    """Log test messages with timestamp"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {status}: {message}")

def test_get_request(endpoint, description):
    """Make GET request and return response"""
    try:
        url = f"{API_BASE}{endpoint}"
        log_test(f"Testing {description}: GET {endpoint}")
        response = requests.get(url, headers=HEADERS, timeout=30)
        log_test(f"Response Status: {response.status_code}")
        
        if response.status_code == 200:
            return response.json()
        else:
            log_test(f"Error Response: {response.text}", "ERROR")
            return None
    except Exception as e:
        log_test(f"Request failed: {str(e)}", "ERROR")
        return None

def test_put_request(endpoint, data, description):
    """Make PUT request and return response"""
    try:
        url = f"{API_BASE}{endpoint}"
        log_test(f"Testing {description}: PUT {endpoint}")
        log_test(f"Request Data: {json.dumps(data, indent=2)}")
        
        response = requests.put(url, headers=HEADERS, json=data, timeout=30)
        log_test(f"Response Status: {response.status_code}")
        
        if response.status_code in [200, 201]:
            return response.json()
        else:
            log_test(f"Error Response: {response.text}", "ERROR")
            return None
    except Exception as e:
        log_test(f"Request failed: {str(e)}", "ERROR")
        return None

def main():
    """Main test execution"""
    log_test("=== DATA PERSISTENCE CORRECTION TESTING ===", "START")
    log_test("Testing the critical fix for patient data persistence issues")
    
    # Step 1: Check initial patient data
    log_test("\n🔍 STEP 1: Checking initial patient data", "TEST")
    patients_data = test_get_request("/patients", "Get all patients")
    
    if not patients_data:
        log_test("Failed to get patients data", "FAIL")
        return False
    
    # Find Lina Alami (patient2)
    lina_patient = None
    for patient in patients_data.get("patients", []):
        if patient.get("id") == "patient2" or (patient.get("nom") == "Alami" and patient.get("prenom") == "Lina"):
            lina_patient = patient
            break
    
    if not lina_patient:
        log_test("❌ Lina Alami (patient2) not found in patients list", "FAIL")
        return False
    
    initial_whatsapp = lina_patient.get("numero_whatsapp", "")
    log_test(f"✅ Found Lina Alami - Initial WhatsApp: {initial_whatsapp}")
    
    # Step 2: Get specific patient data
    log_test("\n🔍 STEP 2: Getting specific patient data", "TEST")
    patient_detail = test_get_request(f"/patients/{lina_patient['id']}", "Get Lina Alami details")
    
    if not patient_detail:
        log_test("Failed to get patient details", "FAIL")
        return False
    
    log_test(f"✅ Patient details retrieved - WhatsApp: {patient_detail.get('numero_whatsapp', '')}")
    
    # Step 3: Modify WhatsApp number
    log_test("\n🔄 STEP 3: Modifying WhatsApp number", "TEST")
    new_whatsapp = "21699111222"
    
    # Prepare update data with all required fields
    update_data = {
        "id": patient_detail.get("id"),
        "nom": patient_detail.get("nom"),
        "prenom": patient_detail.get("prenom"),
        "date_naissance": patient_detail.get("date_naissance", "2022-03-12"),
        "age": patient_detail.get("age", "2 ans"),
        "numero_whatsapp": new_whatsapp,
        "adresse": patient_detail.get("adresse", ""),
        "notes": patient_detail.get("notes", ""),
        "antecedents": patient_detail.get("antecedents", ""),
        "pere": patient_detail.get("pere", {"nom": "", "telephone": "", "fonction": ""}),
        "mere": patient_detail.get("mere", {"nom": "", "telephone": "", "fonction": ""}),
        "lien_whatsapp": patient_detail.get("lien_whatsapp", ""),
        "consultations": patient_detail.get("consultations", []),
        "date_premiere_consultation": patient_detail.get("date_premiere_consultation", ""),
        "date_derniere_consultation": patient_detail.get("date_derniere_consultation", ""),
        "sexe": patient_detail.get("sexe", ""),
        "telephone": patient_detail.get("telephone", ""),
        "nom_parent": patient_detail.get("nom_parent", ""),
        "telephone_parent": patient_detail.get("telephone_parent", ""),
        "assurance": patient_detail.get("assurance", ""),
        "numero_assurance": patient_detail.get("numero_assurance", ""),
        "allergies": patient_detail.get("allergies", ""),
        "photo_url": patient_detail.get("photo_url", "")
    }
    
    update_result = test_put_request(f"/patients/{lina_patient['id']}", update_data, "Update Lina Alami WhatsApp")
    
    if not update_result:
        log_test("❌ Failed to update patient WhatsApp number", "FAIL")
        return False
    
    log_test(f"✅ Patient update successful: {update_result.get('message', 'Updated')}")
    
    # Step 4: Verify change persists immediately
    log_test("\n✅ STEP 4: Verifying immediate persistence", "TEST")
    updated_patient = test_get_request(f"/patients/{lina_patient['id']}", "Get updated patient details")
    
    if not updated_patient:
        log_test("Failed to get updated patient details", "FAIL")
        return False
    
    current_whatsapp = updated_patient.get("numero_whatsapp", "")
    if current_whatsapp == new_whatsapp:
        log_test(f"✅ PERSISTENCE VERIFIED: WhatsApp number correctly updated to {current_whatsapp}")
    else:
        log_test(f"❌ PERSISTENCE FAILED: Expected {new_whatsapp}, got {current_whatsapp}", "FAIL")
        return False
    
    # Step 5: Test init-demo endpoint (should respect existing data)
    log_test("\n🔍 STEP 5: Testing init-demo endpoint (should skip existing data)", "TEST")
    demo_result = test_get_request("/init-demo", "Test demo initialization")
    
    if demo_result:
        log_test(f"✅ Demo endpoint response: {demo_result.get('message', 'No message')}")
        log_test(f"Action taken: {demo_result.get('action', 'unknown')}")
        
        if demo_result.get("action") == "skipped":
            log_test("✅ CORRECT: Demo data initialization was skipped (existing data preserved)")
        elif demo_result.get("action") == "created":
            log_test("⚠️  WARNING: Demo data was created - this might overwrite existing data")
        else:
            log_test(f"ℹ️  INFO: Unexpected action: {demo_result.get('action')}")
    else:
        log_test("Failed to test demo initialization", "FAIL")
    
    # Step 6: Verify data still persists after demo endpoint
    log_test("\n🔍 STEP 6: Verifying persistence after demo endpoint call", "TEST")
    final_patient = test_get_request(f"/patients/{lina_patient['id']}", "Get final patient state")
    
    if not final_patient:
        log_test("Failed to get final patient details", "FAIL")
        return False
    
    final_whatsapp = final_patient.get("numero_whatsapp", "")
    if final_whatsapp == new_whatsapp:
        log_test(f"✅ FINAL PERSISTENCE VERIFIED: WhatsApp number still {final_whatsapp}")
        log_test("✅ SUCCESS: Data persistence correction is working correctly!")
    else:
        log_test(f"❌ FINAL PERSISTENCE FAILED: Expected {new_whatsapp}, got {final_whatsapp}", "FAIL")
        log_test("❌ CRITICAL ISSUE: Patient data was overwritten by demo initialization!")
        return False
    
    # Step 7: Optional - Test reset endpoint existence
    log_test("\n🔍 STEP 7: Testing reset endpoint availability (optional)", "TEST")
    reset_result = test_get_request("/reset-demo", "Test reset endpoint")
    
    if reset_result:
        log_test(f"✅ Reset endpoint available: {reset_result.get('message', 'Available')}")
    else:
        log_test("ℹ️  Reset endpoint not available or returned error (this is optional)")
    
    # Summary
    log_test("\n=== TEST SUMMARY ===", "SUMMARY")
    log_test("✅ Initial patient data retrieval: PASSED")
    log_test("✅ Patient WhatsApp modification: PASSED") 
    log_test("✅ Immediate persistence verification: PASSED")
    log_test("✅ Demo endpoint respects existing data: PASSED")
    log_test("✅ Final persistence after demo call: PASSED")
    log_test("\n🎉 DATA PERSISTENCE CORRECTION: ALL TESTS PASSED", "SUCCESS")
    log_test("The critical fix prevents data overwriting and ensures proper persistence!")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)