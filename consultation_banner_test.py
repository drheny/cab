#!/usr/bin/env python3

import requests
import sys
from datetime import datetime
import json

class ConsultationBannerTester:
    def __init__(self, base_url="https://3389e576-bdbc-485e-bdc3-00374f489362.preview.emergentagent.com"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        if headers is None:
            headers = {'Content-Type': 'application/json'}

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        
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
                    response_data = response.json()
                    return success, response_data
                except:
                    return success, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                print(f"   Response: {response.text[:200]}...")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_consultation_banner_data(self):
        """Test the specific data needed for the enhanced consultation banner"""
        print("\n" + "="*60)
        print("TESTING CONSULTATION BANNER DATA FOR YASSINE BEN AHMED")
        print("="*60)
        
        # Initialize demo data
        self.run_test("Initialize demo data", "GET", "api/init-demo", 200)
        
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Get today's appointments to find Yassine Ben Ahmed
        success, appointments = self.run_test("Get today's appointments", "GET", f"api/rdv/jour/{today}", 200)
        
        if not success or not appointments:
            print("❌ Could not retrieve today's appointments")
            return False
        
        # Look for Yassine Ben Ahmed appointment
        yassine_appointment = None
        for apt in appointments:
            if (apt.get('patient', {}).get('prenom') == 'Yassine' and 
                apt.get('patient', {}).get('nom') == 'Ben Ahmed'):
                yassine_appointment = apt
                break
        
        if not yassine_appointment:
            print("❌ Yassine Ben Ahmed appointment not found")
            print("   Available appointments:")
            for apt in appointments:
                patient = apt.get('patient', {})
                print(f"   - {patient.get('prenom', 'No name')} {patient.get('nom', 'No name')} at {apt.get('heure', 'No time')}")
            return False
        
        print(f"✅ Found Yassine Ben Ahmed appointment: {yassine_appointment['id']}")
        
        # Test banner data requirements
        banner_data = {
            "patient_name": f"{yassine_appointment['patient']['prenom']} {yassine_appointment['patient']['nom']}",
            "appointment_time": yassine_appointment['heure'],
            "room": yassine_appointment.get('salle', ''),
            "type": yassine_appointment.get('type_rdv', ''),
            "status": yassine_appointment.get('statut', ''),
            "waiting_time_data": yassine_appointment.get('heure_arrivee_attente', '')
        }
        
        print(f"\n📋 BANNER DATA VERIFICATION:")
        print(f"   ✓ Patient Name: '{banner_data['patient_name']}'")
        print(f"   ✓ Appointment Time: '{banner_data['appointment_time']}'")
        print(f"   ✓ Room: '{banner_data['room']}'")
        print(f"   ✓ Type: '{banner_data['type']}'")
        print(f"   ✓ Status: '{banner_data['status']}'")
        print(f"   ✓ Waiting Time Data: '{banner_data['waiting_time_data']}'")
        
        # Verify expected values
        expected_values = {
            "patient_name": "Yassine Ben Ahmed",
            "appointment_time": "09:00",
            "room": "salle1",
            "type": "visite"
        }
        
        all_correct = True
        for key, expected in expected_values.items():
            actual = banner_data[key]
            if actual == expected:
                print(f"   ✅ {key}: Expected '{expected}', Got '{actual}' ✓")
            else:
                print(f"   ❌ {key}: Expected '{expected}', Got '{actual}' ✗")
                all_correct = False
        
        # Update appointment to 'en_cours' status for consultation testing
        if yassine_appointment['statut'] != 'en_cours':
            print(f"\n🔄 Updating appointment status to 'en_cours' for consultation testing...")
            status_data = {
                "statut": "en_cours",
                "salle": "salle1",
                "heure_arrivee_attente": datetime.now().isoformat()
            }
            success, _ = self.run_test("Update to en_cours status", "PUT", 
                                     f"api/rdv/{yassine_appointment['id']}/statut", 200, status_data)
            
            if success:
                # Get updated appointment data
                success, updated_appointments = self.run_test("Get updated appointments", "GET", f"api/rdv/jour/{today}", 200)
                
                if success:
                    for apt in updated_appointments:
                        if apt['id'] == yassine_appointment['id']:
                            yassine_appointment = apt
                            break
                    
                    print(f"   ✅ Status updated to: '{yassine_appointment['statut']}'")
                    print(f"   ✅ Waiting time data: '{yassine_appointment.get('heure_arrivee_attente', 'No data')}'")
        
        # Test consultation endpoint that the frontend uses
        success, today_appointments = self.run_test("Get today's appointments for consultation", "GET", "api/appointments/today", 200)
        
        if success:
            en_cours_appointments = [apt for apt in today_appointments if apt.get('statut') == 'en_cours']
            print(f"\n🏥 CONSULTATION READY APPOINTMENTS:")
            print(f"   Found {len(en_cours_appointments)} appointments with 'en_cours' status")
            
            for apt in en_cours_appointments:
                if apt.get('patient', {}).get('prenom') == 'Yassine':
                    print(f"   ✅ Yassine's appointment ready for consultation:")
                    print(f"      - ID: {apt['id']}")
                    print(f"      - Patient: {apt['patient']['prenom']} {apt['patient']['nom']}")
                    print(f"      - Time: {apt['heure']}")
                    print(f"      - Room: {apt.get('salle', 'No room')}")
                    print(f"      - Type: {apt.get('type_rdv', 'No type')}")
                    print(f"      - Status: {apt['statut']}")
                    print(f"      - Waiting data: {apt.get('heure_arrivee_attente', 'No data')}")
                    break
        
        return all_correct

    def run_all_tests(self):
        """Run all consultation banner tests"""
        print("🚀 Starting Consultation Banner Tests")
        print(f"Testing against: {self.base_url}")
        
        success = self.test_consultation_banner_data()
        
        # Print final results
        print("\n" + "="*60)
        print("CONSULTATION BANNER TEST RESULTS")
        print("="*60)
        print(f"📊 Tests passed: {self.tests_passed}/{self.tests_run}")
        
        if success and self.tests_passed == self.tests_run:
            print("🎉 All consultation banner data tests passed!")
            print("✅ Backend is ready for enhanced consultation banner testing")
            return 0
        else:
            print("⚠️  Some tests failed or data doesn't match expectations")
            return 1

def main():
    tester = ConsultationBannerTester()
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())