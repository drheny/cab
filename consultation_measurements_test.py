#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime

class ConsultationMeasurementsTest:
    def __init__(self, base_url="https://3389e576-bdbc-485e-bdc3-00374f489362.preview.emergentagent.com"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.patient_id = None
        self.appointment_id = None
        self.consultation_id = None

    def log_test(self, name, success, details=""):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED")
        else:
            print(f"❌ {name} - FAILED")
        
        if details:
            print(f"   Details: {details}")
        print()

    def run_api_call(self, method, endpoint, data=None, expected_status=200):
        """Make API call and return response"""
        url = f"{self.base_url}/api/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers)
            
            success = response.status_code == expected_status
            return success, response
            
        except Exception as e:
            print(f"   Error: {str(e)}")
            return False, None

    def test_init_demo_data(self):
        """Test demo data initialization"""
        success, response = self.run_api_call('GET', 'init-demo')
        self.log_test("Initialize Demo Data", success, 
                     f"Status: {response.status_code if response else 'No response'}")
        return success

    def test_get_patients(self):
        """Test getting patients list"""
        success, response = self.run_api_call('GET', 'patients')
        
        if success and response:
            data = response.json()
            patients = data.get('patients', [])
            if patients:
                self.patient_id = patients[0]['id']  # Store first patient ID for later tests
                details = f"Found {len(patients)} patients. First patient: {patients[0]['nom']} {patients[0]['prenom']}"
            else:
                details = "No patients found"
                success = False
        else:
            details = f"Status: {response.status_code if response else 'No response'}"
            
        self.log_test("Get Patients List", success, details)
        return success

    def test_get_appointments_today(self):
        """Test getting today's appointments"""
        today = datetime.now().strftime("%Y-%m-%d")
        success, response = self.run_api_call('GET', f'rdv/jour/{today}')
        
        if success and response:
            appointments = response.json()
            if appointments:
                # Find an appointment for testing
                for apt in appointments:
                    if apt.get('patient_id') == self.patient_id:
                        self.appointment_id = apt['id']
                        break
                details = f"Found {len(appointments)} appointments for today"
            else:
                details = "No appointments found for today"
        else:
            details = f"Status: {response.status_code if response else 'No response'}"
            
        self.log_test("Get Today's Appointments", success, details)
        return success

    def test_create_consultation_with_measurements(self):
        """Test creating consultation with Poids/Taille/PC measurements"""
        if not self.patient_id or not self.appointment_id:
            self.log_test("Create Consultation with Measurements", False, 
                         "Missing patient_id or appointment_id from previous tests")
            return False

        consultation_data = {
            "patient_id": self.patient_id,
            "appointment_id": self.appointment_id,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "duree": 20,
            "poids": 16.5,  # Test decimal value
            "taille": 95.0,  # Test decimal value
            "pc": 49.0,     # Test decimal value
            "observations": "Test consultation with measurements",
            "traitement": "Test treatment",
            "bilan": "Test bilan",
            "relance_date": ""
        }

        print(f"   Sending consultation data: {json.dumps(consultation_data, indent=2)}")

        success, response = self.run_api_call('POST', 'consultations', consultation_data, 200)
        
        if success and response:
            result = response.json()
            self.consultation_id = result.get('consultation_id')
            details = f"Created consultation with ID: {self.consultation_id}"
        else:
            details = f"Status: {response.status_code if response else 'No response'}"
            if response:
                try:
                    error_details = response.json()
                    details += f", Error: {error_details}"
                except:
                    details += f", Response: {response.text}"
            
        self.log_test("Create Consultation with Measurements", success, details)
        return success

    def test_get_consultation_by_id(self):
        """Test retrieving consultation by ID to verify measurements are saved"""
        if not self.consultation_id:
            self.log_test("Get Consultation by ID", False, 
                         "No consultation_id from previous test")
            return False

        success, response = self.run_api_call('GET', f'consultations/{self.consultation_id}')
        
        if success and response:
            consultation = response.json()
            poids = consultation.get('poids')
            taille = consultation.get('taille')
            pc = consultation.get('pc')
            
            print(f"   Retrieved consultation: {json.dumps(consultation, indent=2)}")
            
            # Check if measurements are correctly saved
            measurements_correct = (
                poids == 16.5 and 
                taille == 95.0 and 
                pc == 49.0
            )
            
            details = f"Poids: {poids} (type: {type(poids)}), Taille: {taille} (type: {type(taille)}), PC: {pc} (type: {type(pc)})"
            if not measurements_correct:
                success = False
                details += " - MEASUREMENTS NOT SAVED CORRECTLY!"
        else:
            details = f"Status: {response.status_code if response else 'No response'}"
            
        self.log_test("Get Consultation by ID", success, details)
        return success

    def test_get_patient_consultations(self):
        """Test getting patient consultations to verify they appear in history"""
        if not self.patient_id:
            self.log_test("Get Patient Consultations", False, 
                         "No patient_id from previous tests")
            return False

        success, response = self.run_api_call('GET', f'patients/{self.patient_id}/consultations')
        
        if success and response:
            consultations = response.json()
            details = f"Found {len(consultations)} consultations for patient"
            
            print(f"   Patient consultations: {json.dumps(consultations, indent=2)}")
            
            # Look for our test consultation
            test_consultation_found = False
            for consultation in consultations:
                if consultation.get('id') == self.consultation_id:
                    test_consultation_found = True
                    details += f" - Test consultation found in history"
                    break
            
            if not test_consultation_found and self.consultation_id:
                details += f" - Test consultation NOT found in history!"
                success = False
        else:
            details = f"Status: {response.status_code if response else 'No response'}"
            
        self.log_test("Get Patient Consultations", success, details)
        return success

    def run_focused_tests(self):
        """Run focused tests for consultation measurements"""
        print("🔬 Starting Focused Consultation Measurements Tests")
        print("=" * 60)
        
        # Initialize demo data
        self.test_init_demo_data()
        
        # Get test data
        self.test_get_patients()
        self.test_get_appointments_today()
        
        # Test consultation creation with measurements
        self.test_create_consultation_with_measurements()
        self.test_get_consultation_by_id()
        self.test_get_patient_consultations()
        
        # Print summary
        print("=" * 60)
        print(f"📊 Test Summary: {self.tests_passed}/{self.tests_run} tests passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All tests passed!")
            return 0
        else:
            print("❌ Some tests failed!")
            return 1

def main():
    tester = ConsultationMeasurementsTest()
    return tester.run_focused_tests()

if __name__ == "__main__":
    sys.exit(main())