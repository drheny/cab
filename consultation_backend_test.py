#!/usr/bin/env python3

import requests
import sys
from datetime import datetime
import json

class ConsultationAPITester:
    def __init__(self, base_url="https://3389e576-bdbc-485e-bdc3-00374f489362.preview.emergentagent.com"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.today = datetime.now().strftime("%Y-%m-%d")

    def run_test(self, name, method, endpoint, expected_status, data=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    return True, response.json()
                except:
                    return True, response.text
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    print(f"   Response: {response.json()}")
                except:
                    print(f"   Response: {response.text}")

            return success, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_init_demo_data(self):
        """Initialize demo data"""
        return self.run_test(
            "Initialize Demo Data",
            "GET",
            "api/init-demo",
            200
        )

    def test_get_today_appointments(self):
        """Get today's appointments"""
        return self.run_test(
            "Get Today's Appointments",
            "GET",
            f"api/rdv/jour/{self.today}",
            200
        )

    def test_get_patient_details(self, patient_id):
        """Get specific patient details"""
        return self.run_test(
            f"Get Patient Details ({patient_id})",
            "GET",
            f"api/patients/{patient_id}",
            200
        )

    def test_get_patient_consultations(self, patient_id):
        """Get patient consultation history"""
        return self.run_test(
            f"Get Patient Consultations ({patient_id})",
            "GET",
            f"api/patients/{patient_id}/consultations",
            200
        )

    def test_update_appointment_status(self, appointment_id, status, salle=""):
        """Update appointment status"""
        data = {"statut": status}
        if salle:
            data["salle"] = salle
            
        return self.run_test(
            f"Update Appointment Status ({appointment_id} -> {status})",
            "PUT",
            f"api/rdv/{appointment_id}/statut",
            200,
            data
        )

    def setup_test_data(self):
        """Setup test data with 2 appointments in 'en_cours' status"""
        print("\n🔧 Setting up test data...")
        
        # Initialize demo data
        success, _ = self.test_init_demo_data()
        if not success:
            return False
            
        # Get today's appointments
        success, appointments_data = self.test_get_today_appointments()
        if not success:
            return False
            
        appointments = appointments_data if isinstance(appointments_data, list) else []
        print(f"   Found {len(appointments)} appointments for today")
        
        # Update first two appointments to 'en_cours' status
        en_cours_count = 0
        for apt in appointments[:2]:  # Take first 2 appointments
            apt_id = apt.get('id')
            if apt_id:
                salle = "salle1" if en_cours_count == 0 else "salle2"
                success, _ = self.test_update_appointment_status(apt_id, "en_cours", salle)
                if success:
                    en_cours_count += 1
                    print(f"   ✅ Set appointment {apt_id} to en_cours in {salle}")
                else:
                    print(f"   ❌ Failed to update appointment {apt_id}")
        
        print(f"   📊 Successfully set {en_cours_count} appointments to 'en_cours' status")
        return en_cours_count >= 2

    def test_consultation_workflow(self):
        """Test the complete consultation workflow"""
        print("\n🏥 Testing Consultation Workflow...")
        
        # Get today's appointments after setup
        success, appointments_data = self.test_get_today_appointments()
        if not success:
            return False
            
        appointments = appointments_data if isinstance(appointments_data, list) else []
        en_cours_appointments = [apt for apt in appointments if apt.get('statut') == 'en_cours']
        
        print(f"   Found {len(en_cours_appointments)} appointments in 'en_cours' status")
        
        if len(en_cours_appointments) < 2:
            print("   ❌ Expected at least 2 appointments in 'en_cours' status")
            return False
            
        # Test patient data enrichment for each en_cours appointment
        for i, apt in enumerate(en_cours_appointments):
            patient_id = apt.get('patient_id')
            if not patient_id:
                print(f"   ❌ Appointment {i+1} missing patient_id")
                continue
                
            # Test patient details
            success, patient_data = self.test_get_patient_details(patient_id)
            if success:
                patient = patient_data
                print(f"   ✅ Patient {i+1}: {patient.get('prenom', 'N/A')} {patient.get('nom', 'N/A')}")
                print(f"      Age: {patient.get('age', 'N/A')}")
                print(f"      Address: {patient.get('adresse', 'N/A')}")
                print(f"      Phone: {patient.get('numero_whatsapp', 'N/A')}")
                
                # Check parent information
                pere = patient.get('pere', {})
                mere = patient.get('mere', {})
                print(f"      Father: {pere.get('nom', 'N/A')} ({pere.get('fonction', 'N/A')})")
                print(f"      Mother: {mere.get('nom', 'N/A')} ({mere.get('fonction', 'N/A')})")
            else:
                print(f"   ❌ Failed to get patient details for {patient_id}")
                
            # Test patient consultation history
            success, history_data = self.test_get_patient_consultations(patient_id)
            if success:
                history = history_data if isinstance(history_data, list) else []
                print(f"   ✅ Patient {i+1} has {len(history)} consultations in history")
                for j, consultation in enumerate(history):
                    print(f"      History {j+1}: {consultation.get('date', 'N/A')} - {consultation.get('type', 'N/A')}")
            else:
                print(f"   ❌ Failed to get consultation history for {patient_id}")
        
        return True

def main():
    print("🏥 Cabinet Médical - Consultation Panel Testing")
    print("=" * 60)
    
    tester = ConsultationAPITester()
    
    # Setup test data
    if not tester.setup_test_data():
        print("\n❌ Failed to setup test data")
        return 1
    
    # Test consultation workflow
    if not tester.test_consultation_workflow():
        print("\n❌ Consultation workflow test failed")
        return 1
    
    # Print final results
    print(f"\n📊 Test Results: {tester.tests_passed}/{tester.tests_run} tests passed")
    
    if tester.tests_passed == tester.tests_run:
        print("✅ All backend tests passed!")
        return 0
    else:
        print("❌ Some backend tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())