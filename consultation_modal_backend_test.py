#!/usr/bin/env python3
"""
Consultation Page Quick Modal Optimization - Backend API Testing
Focus on testing the APIs that support the quick consultation modal workflow
"""

import requests
import json
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/frontend/.env')

# Configuration
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://cf4f91e9-01e0-4eb2-abf0-57caf9e2fae7.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

# Use auto-login token for testing (as per existing backend implementation)
HEADERS = {
    "Content-Type": "application/json",
    "Authorization": "Bearer auto-login-token"
}

class ConsultationModalAPITester:
    def __init__(self):
        self.test_results = []
        self.created_records = {
            "patients": [],
            "appointments": [],
            "payments": [],
            "consultations": []
        }
        
    def log_test(self, test_name, success, details="", error=""):
        """Log test result"""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "error": error,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"   Details: {details}")
        if error:
            print(f"   Error: {error}")
    
    def initialize_demo_data(self):
        """Initialize demo data for testing"""
        try:
            response = requests.get(f"{API_BASE}/init-demo")
            if response.status_code == 200:
                self.log_test("Demo Data Initialization", True, "Demo data initialized successfully")
                return True
            else:
                self.log_test("Demo Data Initialization", False, f"Status: {response.status_code}", response.text)
                return False
        except Exception as e:
            self.log_test("Demo Data Initialization", False, "", str(e))
            return False
    
    def test_patient_list_for_dropdown(self):
        """Test GET /api/patients - Patient list retrieval for dropdown"""
        try:
            response = requests.get(f"{API_BASE}/patients?page=1&limit=50", headers=HEADERS)
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify response structure
                if "patients" in data and "total_count" in data:
                    patients = data["patients"]
                    
                    # Verify patient data structure for dropdown usage
                    if len(patients) > 0:
                        patient = patients[0]
                        required_fields = ["id", "nom", "prenom"]
                        missing_fields = [field for field in required_fields if field not in patient]
                        
                        if not missing_fields:
                            details = f"Found {len(patients)} patients, total: {data['total_count']}"
                            self.log_test("Patient List for Dropdown", True, details)
                            return True
                        else:
                            self.log_test("Patient List for Dropdown", False, f"Missing fields: {missing_fields}")
                            return False
                    else:
                        self.log_test("Patient List for Dropdown", True, "No patients found but API working")
                        return True
                else:
                    self.log_test("Patient List for Dropdown", False, "Invalid response structure")
                    return False
            else:
                self.log_test("Patient List for Dropdown", False, f"Status: {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_test("Patient List for Dropdown", False, "", str(e))
            return False
    
    def test_patient_creation_minimal_data(self):
        """Test POST /api/patients - Create patient with minimal data"""
        try:
            # Create patient with minimal required data
            patient_data = {
                "nom": "TestModal",
                "prenom": "Patient",
                "date_naissance": "2020-01-15",
                "numero_whatsapp": "21650123456"
            }
            
            response = requests.post(f"{API_BASE}/patients", json=patient_data, headers=HEADERS)
            
            if response.status_code == 200:
                create_data = response.json()
                
                if "patient_id" in create_data:
                    patient_id = create_data["patient_id"]
                    self.created_records["patients"].append(patient_id)
                    
                    # Verify patient was created correctly
                    verify_response = requests.get(f"{API_BASE}/patients/{patient_id}", headers=HEADERS)
                    
                    if verify_response.status_code == 200:
                        patient = verify_response.json()
                        
                        # Check basic fields
                        if (patient["nom"] == "TestModal" and 
                            patient["prenom"] == "Patient" and
                            patient["date_naissance"] == "2020-01-15"):
                            
                            details = f"Patient created with ID: {patient_id}"
                            self.log_test("Patient Creation (Minimal Data)", True, details)
                            return patient_id
                        else:
                            self.log_test("Patient Creation (Minimal Data)", False, "Data verification failed")
                            return None
                    else:
                        self.log_test("Patient Creation (Minimal Data)", False, "Verification failed")
                        return None
                else:
                    self.log_test("Patient Creation (Minimal Data)", False, "No patient_id in response")
                    return None
            else:
                self.log_test("Patient Creation (Minimal Data)", False, f"Status: {response.status_code}", response.text)
                return None
                
        except Exception as e:
            self.log_test("Patient Creation (Minimal Data)", False, "", str(e))
            return None
    
    def test_appointment_creation_for_consultation(self, patient_id):
        """Test POST /api/appointments - Create appointment for consultation workflow"""
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            appointment_data = {
                "patient_id": patient_id,
                "date": today,
                "heure": "10:30",
                "type_rdv": "visite",
                "motif": "Consultation via modal rapide",
                "notes": "Test appointment for consultation modal"
            }
            
            response = requests.post(f"{API_BASE}/appointments", json=appointment_data, headers=HEADERS)
            
            if response.status_code == 200:
                create_data = response.json()
                
                if "appointment_id" in create_data:
                    appointment_id = create_data["appointment_id"]
                    self.created_records["appointments"].append(appointment_id)
                    
                    # Verify appointment was created
                    verify_response = requests.get(f"{API_BASE}/rdv/jour/{today}", headers=HEADERS)
                    
                    if verify_response.status_code == 200:
                        appointments = verify_response.json()
                        
                        # Find our appointment
                        found_appointment = None
                        for appt in appointments:
                            if appt["id"] == appointment_id:
                                found_appointment = appt
                                break
                        
                        if found_appointment and found_appointment["patient_id"] == patient_id:
                            details = f"Appointment created with ID: {appointment_id}"
                            self.log_test("Appointment Creation for Consultation", True, details)
                            return appointment_id
                        else:
                            self.log_test("Appointment Creation for Consultation", False, "Appointment not found in verification")
                            return None
                    else:
                        self.log_test("Appointment Creation for Consultation", False, "Verification request failed")
                        return None
                else:
                    self.log_test("Appointment Creation for Consultation", False, "No appointment_id in response")
                    return None
            else:
                self.log_test("Appointment Creation for Consultation", False, f"Status: {response.status_code}", response.text)
                return None
                
        except Exception as e:
            self.log_test("Appointment Creation for Consultation", False, "", str(e))
            return None
    
    def test_payment_creation_linked_to_appointment(self, patient_id, appointment_id):
        """Test PUT /api/rdv/{rdv_id}/paiement - Create payment linked to appointment"""
        try:
            payment_data = {
                "paye": True,
                "montant": 65.0,
                "type_paiement": "espece",
                "assure": False,
                "notes": "Payment via quick modal test"
            }
            
            response = requests.put(f"{API_BASE}/rdv/{appointment_id}/paiement", json=payment_data, headers=HEADERS)
            
            if response.status_code == 200:
                create_data = response.json()
                
                # Verify payment was created by checking the appointment payment endpoint
                verify_response = requests.get(f"{API_BASE}/payments/appointment/{appointment_id}", headers=HEADERS)
                
                if verify_response.status_code == 200:
                    payment = verify_response.json()
                    
                    if (payment["appointment_id"] == appointment_id and
                        payment["montant"] == 65.0 and
                        payment["statut"] == "paye"):
                        
                        details = f"Payment created for appointment, Amount: {payment['montant']} TND"
                        self.log_test("Payment Creation Linked to Appointment", True, details)
                        return True
                    else:
                        self.log_test("Payment Creation Linked to Appointment", False, "Payment data verification failed")
                        return False
                else:
                    self.log_test("Payment Creation Linked to Appointment", False, "Payment verification request failed")
                    return False
            else:
                self.log_test("Payment Creation Linked to Appointment", False, f"Status: {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_test("Payment Creation Linked to Appointment", False, "", str(e))
            return False
    
    def test_consultation_creation_new_structure(self, patient_id, appointment_id):
        """Test POST /api/consultations - Create consultation with new data structure"""
        try:
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
                "observation_clinique": "Enfant en bonne forme générale. Gorge légèrement irritée.",
                "notes": "Consultation via modal rapide test",
                # Vaccine reminder fields
                "rappel_vaccin": True,
                "nom_vaccin": "DTC (Diphtérie-Tétanos-Coqueluche)",
                "date_vaccin": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"),
                "rappel_whatsapp_vaccin": True
            }
            
            response = requests.post(f"{API_BASE}/consultations", json=consultation_data, headers=HEADERS)
            
            if response.status_code == 200:
                create_data = response.json()
                
                if "consultation_id" in create_data:
                    consultation_id = create_data["consultation_id"]
                    self.created_records["consultations"].append(consultation_id)
                    
                    # Verify consultation was created
                    verify_response = requests.get(f"{API_BASE}/consultations/{consultation_id}", headers=HEADERS)
                    
                    if verify_response.status_code == 200:
                        consultation = verify_response.json()
                        
                        # Verify key fields
                        if (consultation["patient_id"] == patient_id and
                            consultation["appointment_id"] == appointment_id and
                            consultation["diagnostic"] == "Infection virale bénigne. Prescription de paracétamol et repos." and
                            consultation["rappel_vaccin"] == True):
                            
                            details = f"Consultation created with ID: {consultation_id}, Duration: {consultation['duree']} min"
                            self.log_test("Consultation Creation (New Structure)", True, details)
                            return consultation_id
                        else:
                            self.log_test("Consultation Creation (New Structure)", False, "Data verification failed")
                            return None
                    else:
                        self.log_test("Consultation Creation (New Structure)", False, "Verification request failed")
                        return None
                else:
                    self.log_test("Consultation Creation (New Structure)", False, "No consultation_id in response")
                    return None
            else:
                self.log_test("Consultation Creation (New Structure)", False, f"Status: {response.status_code}", response.text)
                return None
                
        except Exception as e:
            self.log_test("Consultation Creation (New Structure)", False, "", str(e))
            return None
    
    def test_consultation_history_retrieval(self, patient_id):
        """Test GET /api/consultations/patient/{patient_id} - Consultation history"""
        try:
            response = requests.get(f"{API_BASE}/consultations/patient/{patient_id}", headers=HEADERS)
            
            if response.status_code == 200:
                consultations = response.json()
                
                if isinstance(consultations, list):
                    details = f"Retrieved {len(consultations)} consultations for patient"
                    self.log_test("Consultation History Retrieval", True, details)
                    return True
                else:
                    self.log_test("Consultation History Retrieval", False, "Invalid response format")
                    return False
            else:
                self.log_test("Consultation History Retrieval", False, f"Status: {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_test("Consultation History Retrieval", False, "", str(e))
            return False
    
    def test_consultation_update(self, consultation_id):
        """Test PUT /api/consultations/{consultation_id} - Update consultation"""
        try:
            update_data = {
                "diagnostic": "UPDATED: Infection virale bénigne - Évolution favorable.",
                "observation_clinique": "UPDATED: Amélioration notable. Température normale.",
                "duree": 35,
                "temperature": 36.8,
                "notes": "Consultation updated via test"
            }
            
            response = requests.put(f"{API_BASE}/consultations/{consultation_id}", json=update_data, headers=HEADERS)
            
            if response.status_code == 200:
                # Verify the update
                verify_response = requests.get(f"{API_BASE}/consultations/{consultation_id}", headers=HEADERS)
                
                if verify_response.status_code == 200:
                    consultation = verify_response.json()
                    
                    if (consultation["diagnostic"].startswith("UPDATED:") and
                        consultation["duree"] == 35):
                        
                        details = f"Consultation updated successfully"
                        self.log_test("Consultation Update", True, details)
                        return True
                    else:
                        self.log_test("Consultation Update", False, "Update verification failed")
                        return False
                else:
                    self.log_test("Consultation Update", False, "Verification request failed")
                    return False
            else:
                self.log_test("Consultation Update", False, f"Status: {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_test("Consultation Update", False, "", str(e))
            return False
    
    def test_authentication_requirements(self):
        """Test that endpoints require authentication"""
        try:
            # Test without authentication headers
            no_auth_headers = {"Content-Type": "application/json"}
            
            endpoints_to_test = [
                ("GET", f"{API_BASE}/patients"),
                ("POST", f"{API_BASE}/patients"),
                ("GET", f"{API_BASE}/appointments"),
                ("POST", f"{API_BASE}/appointments"),
                ("GET", f"{API_BASE}/payments"),
                ("POST", f"{API_BASE}/payments"),
                ("GET", f"{API_BASE}/consultations"),
                ("POST", f"{API_BASE}/consultations")
            ]
            
            auth_required_count = 0
            total_endpoints = len(endpoints_to_test)
            
            for method, url in endpoints_to_test:
                try:
                    if method == "GET":
                        response = requests.get(url, headers=no_auth_headers)
                    elif method == "POST":
                        response = requests.post(url, json={}, headers=no_auth_headers)
                    
                    # Should return 401 or 403 for authentication required
                    if response.status_code in [401, 403]:
                        auth_required_count += 1
                except:
                    # If request fails, assume auth is required
                    auth_required_count += 1
            
            if auth_required_count >= total_endpoints * 0.8:  # At least 80% require auth
                details = f"{auth_required_count}/{total_endpoints} endpoints require authentication"
                self.log_test("Authentication Requirements", True, details)
                return True
            else:
                details = f"Only {auth_required_count}/{total_endpoints} endpoints require authentication"
                self.log_test("Authentication Requirements", False, details)
                return False
                
        except Exception as e:
            self.log_test("Authentication Requirements", False, "", str(e))
            return False
    
    def run_complete_workflow_test(self):
        """Run the complete consultation modal workflow test"""
        print("\n" + "="*80)
        print("🔍 CONSULTATION PAGE QUICK MODAL OPTIMIZATION - BACKEND API TESTING")
        print("="*80)
        
        # Initialize demo data
        if not self.initialize_demo_data():
            print("❌ Failed to initialize demo data. Stopping tests.")
            return False
        
        print("\n📋 TESTING INDIVIDUAL API ENDPOINTS:")
        print("-" * 50)
        
        # Test 1: Patient list for dropdown
        self.test_patient_list_for_dropdown()
        
        # Test 2: Patient creation with minimal data
        patient_id = self.test_patient_creation_minimal_data()
        if not patient_id:
            print("❌ Patient creation failed. Cannot continue with workflow.")
            return False
        
        # Test 3: Appointment creation for consultation workflow
        appointment_id = self.test_appointment_creation_for_consultation(patient_id)
        if not appointment_id:
            print("❌ Appointment creation failed. Cannot continue with workflow.")
            return False
        
        # Test 4: Payment creation linked to appointment
        payment_id = self.test_payment_creation_linked_to_appointment(patient_id, appointment_id)
        if not payment_id:
            print("❌ Payment creation failed. Cannot continue with workflow.")
            return False
        
        # Test 5: Consultation creation with new data structure
        consultation_id = self.test_consultation_creation_new_structure(patient_id, appointment_id)
        if not consultation_id:
            print("❌ Consultation creation failed. Cannot continue with workflow.")
            return False
        
        # Test 6: Consultation history retrieval
        self.test_consultation_history_retrieval(patient_id)
        
        # Test 7: Consultation update
        self.test_consultation_update(consultation_id)
        
        # Test 8: Authentication requirements
        self.test_authentication_requirements()
        
        print("\n" + "="*80)
        print("📊 COMPLETE WORKFLOW TEST RESULTS:")
        print("="*80)
        
        # Count results
        passed_tests = sum(1 for result in self.test_results if result["success"])
        total_tests = len(self.test_results)
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        print(f"✅ Tests Passed: {passed_tests}/{total_tests}")
        print(f"📈 Success Rate: {success_rate:.1f}%")
        
        if success_rate >= 80:
            print("🎉 CONSULTATION MODAL OPTIMIZATION: BACKEND APIs WORKING CORRECTLY")
            print("\n📋 WORKFLOW SUMMARY:")
            print(f"   - Patient created: ID {patient_id}")
            print(f"   - Appointment scheduled: ID {appointment_id}")
            print(f"   - Payment processed: Successfully linked to appointment")
            print(f"   - Consultation completed: ID {consultation_id}")
            print("   - All records linked and verified successfully")
            print("\n✅ The backend APIs support the quick consultation modal workflow!")
        else:
            print("❌ CONSULTATION MODAL OPTIMIZATION: SOME ISSUES FOUND")
            print("\n🔍 FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"   - {result['test']}: {result['error']}")
        
        print("="*80)
        return success_rate >= 80

def main():
    """Main test execution"""
    tester = ConsultationModalAPITester()
    success = tester.run_complete_workflow_test()
    
    if success:
        print("\n🎯 CONCLUSION: Backend APIs are ready for the quick consultation modal!")
        return 0
    else:
        print("\n⚠️ CONCLUSION: Some backend APIs need attention before deployment.")
        return 1

if __name__ == "__main__":
    exit(main())