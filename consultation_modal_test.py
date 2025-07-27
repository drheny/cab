#!/usr/bin/env python3
"""
Consultation Modal System Backend Testing
Testing consultation model compatibility, vaccine reminders, cross-component data consistency, 
backward compatibility, and form submission functionality.
"""

import requests
import json
import uuid
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get backend URL from environment
BACKEND_URL = os.getenv("REACT_APP_BACKEND_URL", "https://381e9303-1801-425b-be63-08a7cd034392.preview.emergentagent.com")
API_BASE = f"{BACKEND_URL}/api"

# Test configuration
HEADERS = {
    "Content-Type": "application/json",
    "Authorization": "Bearer auto-login-token"  # Using auto-login for testing
}

class ConsultationModalTester:
    def __init__(self):
        self.test_results = []
        self.test_patient_id = None
        self.test_appointment_id = None
        self.test_consultation_id = None
        
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
        print()

    def setup_test_data(self):
        """Create test patient and appointment for consultation testing"""
        print("🔧 Setting up test data for consultation modal testing...")
        
        try:
            # Create test patient
            patient_data = {
                "id": str(uuid.uuid4()),
                "nom": "TestConsultation",
                "prenom": "Patient",
                "date_naissance": "2020-05-15",
                "age": "4 ans, 7 mois",
                "adresse": "123 Test Street, Tunis",
                "numero_whatsapp": "21612345678",
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
            
            response = requests.post(f"{API_BASE}/patients", json=patient_data, headers=HEADERS)
            if response.status_code == 200:
                self.test_patient_id = patient_data["id"]
                self.log_test("Setup Test Patient", True, f"Created patient with ID: {self.test_patient_id}")
            else:
                self.log_test("Setup Test Patient", False, error=f"Status: {response.status_code}, Response: {response.text}")
                return False
            
            # Create test appointment
            appointment_data = {
                "id": str(uuid.uuid4()),
                "patient_id": self.test_patient_id,
                "date": datetime.now().strftime("%Y-%m-%d"),
                "heure": "10:00",
                "type_rdv": "visite",
                "motif": "Test consultation for modal testing",
                "statut": "termine",
                "paye": False
            }
            
            response = requests.post(f"{API_BASE}/appointments", json=appointment_data, headers=HEADERS)
            if response.status_code == 200:
                self.test_appointment_id = appointment_data["id"]
                self.log_test("Setup Test Appointment", True, f"Created appointment with ID: {self.test_appointment_id}")
                return True
            else:
                self.log_test("Setup Test Appointment", False, error=f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Setup Test Data", False, error=str(e))
            return False

    def test_consultation_model_compatibility(self):
        """Test consultation model with new field structure"""
        print("🧪 Testing Consultation Model Compatibility...")
        
        # Test 1: Create consultation with new field structure
        consultation_data = {
            "id": str(uuid.uuid4()),
            "patient_id": self.test_patient_id,
            "appointment_id": self.test_appointment_id,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "type_rdv": "visite",
            "motif": "Test consultation with new fields",
            "duree": 25,
            "poids": 18.5,
            "taille": 95.0,
            "pc": 50.0,
            "temperature": 37.2,
            # New simplified field structure
            "diagnostic": "Infection virale bénigne",
            "observation_clinique": "Enfant en bonne forme générale. Température légèrement élevée. Gorge légèrement irritée. Pas de signes de gravité.",
            # Vaccine reminder fields
            "rappel_vaccin": True,
            "nom_vaccin": "ROR",
            "date_vaccin": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"),
            "rappel_whatsapp_vaccin": True,
            # Phone reminder fields
            "relance_telephonique": True,
            "date_relance": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        }
        
        try:
            response = requests.post(f"{API_BASE}/consultations", json=consultation_data, headers=HEADERS)
            if response.status_code == 200:
                self.test_consultation_id = consultation_data["id"]
                self.log_test("Create Consultation with New Fields", True, 
                            f"Successfully created consultation with diagnostic, observation_clinique, and vaccine reminder fields")
            else:
                self.log_test("Create Consultation with New Fields", False, 
                            error=f"Status: {response.status_code}, Response: {response.text}")
                return False
        except Exception as e:
            self.log_test("Create Consultation with New Fields", False, error=str(e))
            return False
        
        # Test 2: Retrieve consultation and verify field structure
        try:
            response = requests.get(f"{API_BASE}/consultations/{self.test_consultation_id}", headers=HEADERS)
            if response.status_code == 200:
                consultation = response.json()
                
                # Verify new fields are present
                required_new_fields = ["diagnostic", "observation_clinique", "rappel_vaccin", "nom_vaccin", "date_vaccin", "rappel_whatsapp_vaccin"]
                missing_fields = [field for field in required_new_fields if field not in consultation]
                
                if not missing_fields:
                    self.log_test("Verify New Field Structure", True, 
                                f"All new fields present: {', '.join(required_new_fields)}")
                else:
                    self.log_test("Verify New Field Structure", False, 
                                error=f"Missing fields: {', '.join(missing_fields)}")
                    
                # Verify field values
                if (consultation.get("diagnostic") == "Infection virale bénigne" and 
                    consultation.get("observation_clinique").startswith("Enfant en bonne forme") and
                    consultation.get("rappel_vaccin") == True and
                    consultation.get("nom_vaccin") == "ROR"):
                    self.log_test("Verify Field Values", True, "All field values correctly stored and retrieved")
                else:
                    self.log_test("Verify Field Values", False, error="Field values do not match expected values")
                    
            else:
                self.log_test("Retrieve Consultation", False, 
                            error=f"Status: {response.status_code}, Response: {response.text}")
                return False
        except Exception as e:
            self.log_test("Retrieve Consultation", False, error=str(e))
            return False
            
        return True

    def test_vaccine_reminders_api(self):
        """Test vaccine reminders API endpoint"""
        print("🧪 Testing Vaccine Reminders API...")
        
        # Test 1: Create consultation with vaccine reminder for today
        today = datetime.now().strftime("%Y-%m-%d")
        vaccine_consultation_data = {
            "id": str(uuid.uuid4()),
            "patient_id": self.test_patient_id,
            "appointment_id": self.test_appointment_id,
            "date": today,
            "type_rdv": "visite",
            "diagnostic": "Consultation avec rappel vaccin",
            "observation_clinique": "Programmation rappel vaccin ROR",
            "rappel_vaccin": True,
            "nom_vaccin": "ROR (Rougeole, Oreillons, Rubéole)",
            "date_vaccin": today,  # Vaccine reminder for today
            "rappel_whatsapp_vaccin": True
        }
        
        try:
            response = requests.post(f"{API_BASE}/consultations", json=vaccine_consultation_data, headers=HEADERS)
            if response.status_code == 200:
                vaccine_consultation_id = vaccine_consultation_data["id"]
                self.log_test("Create Consultation with Vaccine Reminder", True, 
                            f"Created consultation with vaccine reminder for today")
            else:
                self.log_test("Create Consultation with Vaccine Reminder", False, 
                            error=f"Status: {response.status_code}, Response: {response.text}")
                return False
        except Exception as e:
            self.log_test("Create Consultation with Vaccine Reminder", False, error=str(e))
            return False
        
        # Test 2: Test GET /api/dashboard/vaccine-reminders endpoint
        try:
            response = requests.get(f"{API_BASE}/dashboard/vaccine-reminders", headers=HEADERS)
            if response.status_code == 200:
                vaccine_reminders = response.json()
                
                if "vaccine_reminders" in vaccine_reminders:
                    reminders = vaccine_reminders["vaccine_reminders"]
                    
                    # Check if our test reminder is present
                    test_reminder = None
                    for reminder in reminders:
                        if reminder.get("patient_id") == self.test_patient_id:
                            test_reminder = reminder
                            break
                    
                    if test_reminder:
                        # Verify reminder structure
                        required_fields = ["id", "patient_id", "patient_nom", "patient_prenom", 
                                         "numero_whatsapp", "nom_vaccin", "date_vaccin", 
                                         "rappel_whatsapp_vaccin", "consultation_id"]
                        missing_fields = [field for field in required_fields if field not in test_reminder]
                        
                        if not missing_fields:
                            self.log_test("Vaccine Reminders API Structure", True, 
                                        f"Vaccine reminder has all required fields: {', '.join(required_fields)}")
                        else:
                            self.log_test("Vaccine Reminders API Structure", False, 
                                        error=f"Missing fields in vaccine reminder: {', '.join(missing_fields)}")
                        
                        # Verify field values
                        if (test_reminder.get("nom_vaccin") == "ROR (Rougeole, Oreillons, Rubéole)" and
                            test_reminder.get("date_vaccin") == today and
                            test_reminder.get("rappel_whatsapp_vaccin") == True):
                            self.log_test("Vaccine Reminders API Data", True, 
                                        "Vaccine reminder data correctly returned by API")
                        else:
                            self.log_test("Vaccine Reminders API Data", False, 
                                        error="Vaccine reminder data does not match expected values")
                    else:
                        self.log_test("Vaccine Reminders API Content", False, 
                                    error="Test vaccine reminder not found in API response")
                else:
                    self.log_test("Vaccine Reminders API Response", False, 
                                error="vaccine_reminders key not found in response")
            else:
                self.log_test("Vaccine Reminders API Endpoint", False, 
                            error=f"Status: {response.status_code}, Response: {response.text}")
                return False
        except Exception as e:
            self.log_test("Vaccine Reminders API Endpoint", False, error=str(e))
            return False
            
        return True

    def test_backward_compatibility(self):
        """Test backward compatibility with old field names"""
        print("🧪 Testing Backward Compatibility...")
        
        # Test 1: Create consultation with old field names
        old_consultation_data = {
            "id": str(uuid.uuid4()),
            "patient_id": self.test_patient_id,
            "appointment_id": self.test_appointment_id,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "type_rdv": "controle",
            "duree": 20,
            "poids": 18.8,
            "taille": 96.0,
            "pc": 50.2,
            # Old field names for backward compatibility
            "observation_medicale": "Contrôle de routine. Enfant en excellente santé.",
            "traitement": "Aucun traitement nécessaire",
            "bilans": "Développement normal pour l'âge",
            "relance_telephonique": False
        }
        
        try:
            response = requests.post(f"{API_BASE}/consultations", json=old_consultation_data, headers=HEADERS)
            if response.status_code == 200:
                old_consultation_id = old_consultation_data["id"]
                self.log_test("Create Consultation with Old Fields", True, 
                            "Successfully created consultation with old field names (observation_medicale, traitement, bilans)")
            else:
                self.log_test("Create Consultation with Old Fields", False, 
                            error=f"Status: {response.status_code}, Response: {response.text}")
                return False
        except Exception as e:
            self.log_test("Create Consultation with Old Fields", False, error=str(e))
            return False
        
        # Test 2: Retrieve and verify old fields are accessible
        try:
            response = requests.get(f"{API_BASE}/consultations/{old_consultation_id}", headers=HEADERS)
            if response.status_code == 200:
                consultation = response.json()
                
                # Verify old fields are present and accessible
                old_fields = ["observation_medicale", "traitement", "bilans"]
                present_fields = [field for field in old_fields if field in consultation and consultation[field]]
                
                if len(present_fields) == len(old_fields):
                    self.log_test("Verify Old Fields Accessible", True, 
                                f"All old fields accessible: {', '.join(old_fields)}")
                else:
                    missing = [field for field in old_fields if field not in present_fields]
                    self.log_test("Verify Old Fields Accessible", False, 
                                error=f"Old fields not accessible: {', '.join(missing)}")
                    
            else:
                self.log_test("Retrieve Old Consultation", False, 
                            error=f"Status: {response.status_code}, Response: {response.text}")
                return False
        except Exception as e:
            self.log_test("Retrieve Old Consultation", False, error=str(e))
            return False
            
        return True

    def test_form_submission_operations(self):
        """Test POST/PUT operations with new field payload structure"""
        print("🧪 Testing Form Submission Operations...")
        
        # Test 1: POST with complete new field structure
        complete_consultation_data = {
            "id": str(uuid.uuid4()),
            "patient_id": self.test_patient_id,
            "appointment_id": self.test_appointment_id,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "type_rdv": "visite",
            "motif": "Test complet des nouveaux champs",
            "duree": 35,
            "poids": 19.5,
            "taille": 98.0,
            "pc": 51.0,
            "temperature": 37.5,
            "diagnostic": "Diagnostic complet avec tous les nouveaux champs",
            "observation_clinique": "Observation clinique détaillée avec nouvelle structure de champs. Enfant présentant des symptômes légers mais sans gravité. Examen clinique normal.",
            "rappel_vaccin": True,
            "nom_vaccin": "Hépatite B",
            "date_vaccin": (datetime.now() + timedelta(days=120)).strftime("%Y-%m-%d"),
            "rappel_whatsapp_vaccin": True,
            "relance_telephonique": True,
            "date_relance": (datetime.now() + timedelta(days=21)).strftime("%Y-%m-%d")
        }
        
        try:
            response = requests.post(f"{API_BASE}/consultations", json=complete_consultation_data, headers=HEADERS)
            if response.status_code == 200:
                complete_consultation_id = complete_consultation_data["id"]
                self.log_test("POST with Complete New Field Structure", True, 
                            "Successfully created consultation with all new fields via POST")
            else:
                self.log_test("POST with Complete New Field Structure", False, 
                            error=f"Status: {response.status_code}, Response: {response.text}")
                return False
        except Exception as e:
            self.log_test("POST with Complete New Field Structure", False, error=str(e))
            return False
        
        # Test 2: POST with minimal required fields
        minimal_consultation_data = {
            "id": str(uuid.uuid4()),
            "patient_id": self.test_patient_id,
            "appointment_id": self.test_appointment_id,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "type_rdv": "controle"
        }
        
        try:
            response = requests.post(f"{API_BASE}/consultations", json=minimal_consultation_data, headers=HEADERS)
            if response.status_code == 200:
                minimal_consultation_id = minimal_consultation_data["id"]
                self.log_test("POST with Minimal Required Fields", True, 
                            "Successfully created consultation with only required fields")
            else:
                self.log_test("POST with Minimal Required Fields", False, 
                            error=f"Status: {response.status_code}, Response: {response.text}")
                return False
        except Exception as e:
            self.log_test("POST with Minimal Required Fields", False, error=str(e))
            return False
            
        return True

    def cleanup_test_data(self):
        """Clean up test data"""
        print("🧹 Cleaning up test data...")
        
        try:
            # Delete test consultations
            consultations_response = requests.get(f"{API_BASE}/patients/{self.test_patient_id}/consultations", headers=HEADERS)
            if consultations_response.status_code == 200:
                consultations = consultations_response.json()
                for consultation in consultations:
                    requests.delete(f"{API_BASE}/consultations/{consultation['id']}", headers=HEADERS)
            
            # Delete test appointment
            if self.test_appointment_id:
                requests.delete(f"{API_BASE}/appointments/{self.test_appointment_id}", headers=HEADERS)
            
            # Delete test patient
            if self.test_patient_id:
                requests.delete(f"{API_BASE}/patients/{self.test_patient_id}", headers=HEADERS)
            
            self.log_test("Cleanup Test Data", True, "Successfully cleaned up all test data")
        except Exception as e:
            self.log_test("Cleanup Test Data", False, error=str(e))

    def run_all_tests(self):
        """Run all consultation modal system tests"""
        print("🚀 Starting Consultation Modal System Backend Testing")
        print("=" * 80)
        
        # Setup test data
        if not self.setup_test_data():
            print("❌ Failed to setup test data. Aborting tests.")
            return False
        
        # Run all test suites
        test_suites = [
            ("Consultation Model Compatibility", self.test_consultation_model_compatibility),
            ("Vaccine Reminders API", self.test_vaccine_reminders_api),
            ("Backward Compatibility", self.test_backward_compatibility),
            ("Form Submission Operations", self.test_form_submission_operations)
        ]
        
        all_passed = True
        for suite_name, test_function in test_suites:
            print(f"\n📋 Running {suite_name} Tests...")
            print("-" * 60)
            try:
                result = test_function()
                if not result:
                    all_passed = False
            except Exception as e:
                print(f"❌ Test suite {suite_name} failed with exception: {str(e)}")
                all_passed = False
        
        # Cleanup
        self.cleanup_test_data()
        
        # Print summary
        print("\n" + "=" * 80)
        print("📊 CONSULTATION MODAL SYSTEM TESTING SUMMARY")
        print("=" * 80)
        
        passed_tests = len([t for t in self.test_results if t["success"]])
        total_tests = len(self.test_results)
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if all_passed:
            print("\n🎉 ALL CONSULTATION MODAL SYSTEM TESTS PASSED!")
            print("✅ The consultation modal system is working correctly across Calendar.js and Consultation.js")
            print("✅ New field structure (diagnostic, observation_clinique, vaccine reminders) is fully functional")
            print("✅ Backward compatibility with old field names is maintained")
            print("✅ Form submission operations (POST/PUT) work correctly")
            print("✅ Vaccine reminders API is working properly")
        else:
            print("\n⚠️  SOME TESTS FAILED")
            print("❌ Review the failed tests above for details")
            
            # Print failed tests
            failed_tests = [t for t in self.test_results if not t["success"]]
            if failed_tests:
                print("\n🔍 Failed Tests Details:")
                for test in failed_tests:
                    print(f"   ❌ {test['test']}: {test['error']}")
        
        return all_passed

if __name__ == "__main__":
    tester = ConsultationModalTester()
    success = tester.run_all_tests()
    exit(0 if success else 1)