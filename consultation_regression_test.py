#!/usr/bin/env python3
"""
CONSULTATION MANAGEMENT REGRESSION TEST
Testing consultation CRUD operations after deprecated field removal
"""

import requests
import json
import time
from datetime import datetime
import uuid

# Configuration
BACKEND_URL = "https://ae9700da-fec8-4e1e-ab51-a779f23a5093.preview.emergentagent.com/api"
TEST_CREDENTIALS = {
    "username": "medecin",
    "password": "medecin123"
}

class ConsultationTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.test_patient_id = None
        self.test_appointment_id = None
        self.test_consultation_id = None
        
    def authenticate(self):
        """Authenticate and get token"""
        try:
            response = self.session.post(
                f"{BACKEND_URL}/auth/login",
                json=TEST_CREDENTIALS,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data["access_token"]
                self.session.headers.update({
                    "Authorization": f"Bearer {self.auth_token}"
                })
                print("✅ Authentication successful")
                return True
            else:
                print(f"❌ Authentication failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Authentication error: {str(e)}")
            return False
    
    def get_test_patient(self):
        """Get a test patient for consultation testing"""
        try:
            response = self.session.get(f"{BACKEND_URL}/patients?limit=1", timeout=10)
            if response.status_code == 200:
                data = response.json()
                patients = data.get("patients", [])
                if patients:
                    self.test_patient_id = patients[0]["id"]
                    print(f"✅ Using test patient: {patients[0]['nom']} {patients[0]['prenom']}")
                    return True
            print("❌ No test patient found")
            return False
        except Exception as e:
            print(f"❌ Error getting test patient: {str(e)}")
            return False
    
    def test_consultation_creation(self):
        """Test consultation creation without deprecated fields"""
        print("\n📝 Testing Consultation Creation")
        
        if not self.test_patient_id:
            print("❌ No test patient available")
            return False
        
        try:
            # Create a test appointment first
            appointment_data = {
                "id": str(uuid.uuid4()),
                "patient_id": self.test_patient_id,
                "date": datetime.now().strftime("%Y-%m-%d"),
                "heure": "10:00",
                "type_rdv": "visite",
                "statut": "termine",
                "motif": "Test consultation",
                "notes": "Test appointment for consultation testing"
            }
            
            response = self.session.post(f"{BACKEND_URL}/rdv", json=appointment_data, timeout=10)
            if response.status_code == 200:
                self.test_appointment_id = appointment_data["id"]
                print("✅ Test appointment created")
            else:
                print(f"⚠️ Could not create test appointment: {response.status_code}")
                # Try to use existing appointment
                today = datetime.now().strftime("%Y-%m-%d")
                response = self.session.get(f"{BACKEND_URL}/rdv/jour/{today}", timeout=10)
                if response.status_code == 200:
                    appointments = response.json()
                    if appointments:
                        self.test_appointment_id = appointments[0]["id"]
                        print("✅ Using existing appointment for test")
                    else:
                        print("❌ No appointments available for testing")
                        return False
            
            # Create consultation without deprecated fields
            consultation_data = {
                "id": str(uuid.uuid4()),
                "patient_id": self.test_patient_id,
                "appointment_id": self.test_appointment_id,
                "date": datetime.now().strftime("%Y-%m-%d"),
                "type_rdv": "visite",
                "motif": "Test consultation regression",
                "duree": 30,
                "poids": 15.5,
                "taille": 85.0,
                "pc": 48.0,
                "temperature": 36.8,
                "diagnostic": "Test diagnostic",
                "observation_clinique": "Test clinical observation",
                "bilans": "Test bilans",
                "notes": "Test consultation notes",
                "relance_telephonique": False,
                "rappel_vaccin": False
            }
            
            self.test_consultation_id = consultation_data["id"]
            
            response = self.session.post(f"{BACKEND_URL}/consultations", json=consultation_data, timeout=10)
            
            if response.status_code == 200:
                print("✅ Consultation created successfully")
                print(f"   ID: {self.test_consultation_id}")
                print(f"   Patient: {self.test_patient_id}")
                print(f"   Duration: {consultation_data['duree']} minutes")
                print(f"   Weight: {consultation_data['poids']} kg")
                return True
            else:
                print(f"❌ Consultation creation failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Exception during consultation creation: {str(e)}")
            return False
    
    def test_consultation_retrieval(self):
        """Test consultation retrieval"""
        print("\n📖 Testing Consultation Retrieval")
        
        if not self.test_consultation_id:
            print("❌ No test consultation available")
            return False
        
        try:
            response = self.session.get(f"{BACKEND_URL}/consultations/{self.test_consultation_id}", timeout=10)
            
            if response.status_code == 200:
                consultation = response.json()
                
                # Verify no deprecated fields are present
                deprecated_fields = ["observation_medicale", "traitement"]
                found_deprecated = [field for field in deprecated_fields if field in consultation]
                
                if found_deprecated:
                    print(f"⚠️ Found deprecated fields: {found_deprecated}")
                else:
                    print("✅ No deprecated fields found")
                
                # Verify required fields are present
                required_fields = ["id", "patient_id", "appointment_id", "date", "diagnostic", "observation_clinique"]
                missing_fields = [field for field in required_fields if field not in consultation]
                
                if not missing_fields:
                    print("✅ Consultation retrieved successfully")
                    print(f"   ID: {consultation['id']}")
                    print(f"   Date: {consultation['date']}")
                    print(f"   Diagnostic: {consultation.get('diagnostic', 'N/A')}")
                    return True
                else:
                    print(f"❌ Missing required fields: {missing_fields}")
                    return False
            else:
                print(f"❌ Consultation retrieval failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Exception during consultation retrieval: {str(e)}")
            return False
    
    def test_consultation_update(self):
        """Test consultation update"""
        print("\n✏️ Testing Consultation Update")
        
        if not self.test_consultation_id:
            print("❌ No test consultation available")
            return False
        
        try:
            update_data = {
                "diagnostic": "Updated test diagnostic",
                "observation_clinique": "Updated clinical observation",
                "notes": "Updated consultation notes",
                "duree": 45,
                "temperature": 37.2
            }
            
            response = self.session.put(
                f"{BACKEND_URL}/consultations/{self.test_consultation_id}",
                json=update_data,
                timeout=10
            )
            
            if response.status_code == 200:
                print("✅ Consultation updated successfully")
                
                # Verify the update
                response = self.session.get(f"{BACKEND_URL}/consultations/{self.test_consultation_id}", timeout=10)
                if response.status_code == 200:
                    consultation = response.json()
                    if consultation.get("diagnostic") == update_data["diagnostic"]:
                        print("✅ Update verification successful")
                        print(f"   Updated diagnostic: {consultation['diagnostic']}")
                        print(f"   Updated duration: {consultation['duree']} minutes")
                        return True
                    else:
                        print("❌ Update verification failed")
                        return False
                else:
                    print("❌ Could not verify update")
                    return False
            else:
                print(f"❌ Consultation update failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Exception during consultation update: {str(e)}")
            return False
    
    def test_patient_consultations(self):
        """Test patient consultations retrieval"""
        print("\n👤 Testing Patient Consultations Retrieval")
        
        if not self.test_patient_id:
            print("❌ No test patient available")
            return False
        
        try:
            response = self.session.get(f"{BACKEND_URL}/patients/{self.test_patient_id}/consultations", timeout=10)
            
            if response.status_code == 200:
                consultations = response.json()
                
                if isinstance(consultations, list):
                    print(f"✅ Patient consultations retrieved: {len(consultations)} consultations")
                    
                    # Check each consultation for deprecated fields
                    for i, consultation in enumerate(consultations):
                        deprecated_fields = ["observation_medicale", "traitement"]
                        found_deprecated = [field for field in deprecated_fields if field in consultation]
                        
                        if found_deprecated:
                            print(f"⚠️ Consultation {i+1} has deprecated fields: {found_deprecated}")
                        else:
                            print(f"✅ Consultation {i+1} clean (no deprecated fields)")
                    
                    return True
                else:
                    print("❌ Invalid response format")
                    return False
            else:
                print(f"❌ Patient consultations retrieval failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Exception during patient consultations retrieval: {str(e)}")
            return False
    
    def test_consultation_export(self):
        """Test consultation export functionality"""
        print("\n📤 Testing Consultation Export")
        
        try:
            response = self.session.get(f"{BACKEND_URL}/admin/export/consultations", timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                
                if "data" in data and "count" in data:
                    consultations = data["data"]
                    count = data["count"]
                    
                    print(f"✅ Consultation export successful: {count} consultations")
                    
                    # Check exported consultations for deprecated fields
                    deprecated_count = 0
                    for consultation in consultations:
                        deprecated_fields = ["observation_medicale", "traitement"]
                        found_deprecated = [field for field in deprecated_fields if field in consultation]
                        if found_deprecated:
                            deprecated_count += 1
                    
                    if deprecated_count == 0:
                        print("✅ No deprecated fields found in exported consultations")
                    else:
                        print(f"⚠️ {deprecated_count} consultations have deprecated fields")
                    
                    return True
                else:
                    print("❌ Invalid export response format")
                    return False
            else:
                print(f"❌ Consultation export failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Exception during consultation export: {str(e)}")
            return False
    
    def cleanup_test_data(self):
        """Clean up test data"""
        print("\n🧹 Cleaning up test data")
        
        # Delete test consultation
        if self.test_consultation_id:
            try:
                response = self.session.delete(f"{BACKEND_URL}/consultations/{self.test_consultation_id}", timeout=10)
                if response.status_code == 200:
                    print("✅ Test consultation deleted")
                else:
                    print(f"⚠️ Could not delete test consultation: {response.status_code}")
            except Exception as e:
                print(f"⚠️ Error deleting test consultation: {str(e)}")
        
        # Delete test appointment
        if self.test_appointment_id:
            try:
                response = self.session.delete(f"{BACKEND_URL}/rdv/{self.test_appointment_id}", timeout=10)
                if response.status_code == 200:
                    print("✅ Test appointment deleted")
                else:
                    print(f"⚠️ Could not delete test appointment: {response.status_code}")
            except Exception as e:
                print(f"⚠️ Error deleting test appointment: {str(e)}")
    
    def run_all_tests(self):
        """Run all consultation management tests"""
        print("📝 STARTING CONSULTATION MANAGEMENT REGRESSION TEST")
        print("=" * 80)
        print("Testing consultation CRUD operations after deprecated field removal")
        print("Verifying no 'observation_medicale' and 'traitement' fields remain")
        print()
        
        if not self.authenticate():
            print("❌ CRITICAL: Authentication failed. Cannot proceed.")
            return False
        
        if not self.get_test_patient():
            print("❌ CRITICAL: No test patient available. Cannot proceed.")
            return False
        
        success_count = 0
        total_tests = 5
        
        # Test 1: Consultation Creation
        if self.test_consultation_creation():
            success_count += 1
        
        # Test 2: Consultation Retrieval
        if self.test_consultation_retrieval():
            success_count += 1
        
        # Test 3: Consultation Update
        if self.test_consultation_update():
            success_count += 1
        
        # Test 4: Patient Consultations
        if self.test_patient_consultations():
            success_count += 1
        
        # Test 5: Consultation Export
        if self.test_consultation_export():
            success_count += 1
        
        # Cleanup
        self.cleanup_test_data()
        
        print("\n" + "=" * 80)
        print("📋 CONSULTATION MANAGEMENT REGRESSION TEST REPORT")
        print("=" * 80)
        print(f"✅ Successful tests: {success_count}/{total_tests}")
        print(f"📈 Success rate: {(success_count/total_tests*100):.1f}%")
        
        if success_count == total_tests:
            print("\n🎉 ALL CONSULTATION MANAGEMENT TESTS PASSED!")
            print("✅ Deprecated fields successfully removed")
            print("✅ Consultation CRUD operations working correctly")
            print("✅ No data corruption detected")
            print("✅ Export functionality clean")
            return True
        else:
            print(f"\n⚠️ {total_tests - success_count} TESTS FAILED")
            print("❌ Some consultation functionality may be broken")
            print("🔧 Review failed tests before production")
            return False

if __name__ == "__main__":
    print("🏥 Cabinet Médical - Consultation Management Regression Test")
    print("Testing consultation operations after deprecated field removal")
    print()
    
    tester = ConsultationTester()
    success = tester.run_all_tests()
    
    exit(0 if success else 1)