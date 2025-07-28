#!/usr/bin/env python3
"""
Backend API Testing Script for Review Request
Testing specific endpoints after frontend UI changes (pastel theme and WhatsApp button modifications)

Focus Areas:
1. Basic Dashboard API: Test GET /api/dashboard endpoint
2. Messaging APIs: Test messaging endpoints (/api/messages GET and POST)  
3. Patient Lists: Test GET /api/patients endpoint
4. Authentication: Test login functionality
"""

import requests
import json
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/frontend/.env')

class ReviewBackendTest:
    def __init__(self):
        self.base_url = os.getenv('REACT_APP_BACKEND_URL', 'https://0f556255-778a-43ef-b1e4-2e04fe02d592.preview.emergentagent.com')
        self.test_results = []
        print(f"🔧 Testing backend at: {self.base_url}")
        print(f"📅 Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
    
    def log_result(self, test_name, status, details=""):
        """Log test result"""
        result = {
            "test": test_name,
            "status": status,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status_icon = "✅" if status == "PASS" else "❌"
        print(f"{status_icon} {test_name}: {status}")
        if details:
            print(f"   Details: {details}")
    
    def test_dashboard_api(self):
        """Test GET /api/dashboard endpoint"""
        print("\n🔍 Testing Dashboard API")
        try:
            response = requests.get(f"{self.base_url}/api/dashboard")
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify required fields
                required_fields = [
                    "total_rdv", "rdv_restants", "rdv_attente", "rdv_en_cours", 
                    "rdv_termines", "recette_jour", "total_patients", "duree_attente_moyenne"
                ]
                
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields:
                    self.log_result("Dashboard API", "PASS", 
                                  f"All required fields present. Total RDV: {data.get('total_rdv', 0)}, "
                                  f"Total Patients: {data.get('total_patients', 0)}, "
                                  f"Recette: {data.get('recette_jour', 0)} TND")
                else:
                    self.log_result("Dashboard API", "FAIL", f"Missing fields: {missing_fields}")
            else:
                self.log_result("Dashboard API", "FAIL", f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_result("Dashboard API", "FAIL", f"Exception: {str(e)}")
    
    def test_messaging_apis(self):
        """Test messaging endpoints (/api/messages GET and POST)"""
        print("\n🔍 Testing Messaging APIs")
        
        # Test GET /api/messages
        try:
            response = requests.get(f"{self.base_url}/api/messages")
            
            if response.status_code == 200:
                data = response.json()
                
                if "messages" in data and isinstance(data["messages"], list):
                    message_count = len(data["messages"])
                    self.log_result("Messages GET", "PASS", f"Retrieved {message_count} messages")
                    
                    # Verify message structure if messages exist
                    if message_count > 0:
                        sample_message = data["messages"][0]
                        required_msg_fields = ["id", "sender_type", "sender_name", "content", "timestamp"]
                        missing_msg_fields = [field for field in required_msg_fields if field not in sample_message]
                        
                        if not missing_msg_fields:
                            self.log_result("Messages Structure", "PASS", "Message structure is correct")
                        else:
                            self.log_result("Messages Structure", "FAIL", f"Missing fields: {missing_msg_fields}")
                else:
                    self.log_result("Messages GET", "FAIL", "Invalid response structure")
            else:
                self.log_result("Messages GET", "FAIL", f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_result("Messages GET", "FAIL", f"Exception: {str(e)}")
        
        # Test POST /api/messages
        try:
            test_message = {
                "content": f"Backend test message - {datetime.now().strftime('%H:%M:%S')}"
            }
            
            response = requests.post(
                f"{self.base_url}/api/messages?sender_type=medecin&sender_name=Backend%20Test",
                json=test_message
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if "message" in data and "id" in data:
                    self.log_result("Messages POST", "PASS", f"Message created with ID: {data['id']}")
                else:
                    self.log_result("Messages POST", "FAIL", "Invalid response structure")
            else:
                self.log_result("Messages POST", "FAIL", f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_result("Messages POST", "FAIL", f"Exception: {str(e)}")
    
    def test_patients_api(self):
        """Test GET /api/patients endpoint"""
        print("\n🔍 Testing Patients API")
        
        try:
            # Test basic patients endpoint
            response = requests.get(f"{self.base_url}/api/patients")
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify pagination structure
                required_fields = ["patients", "total_count", "page", "limit", "total_pages"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields:
                    patient_count = len(data["patients"])
                    total_count = data["total_count"]
                    
                    self.log_result("Patients API", "PASS", 
                                  f"Retrieved {patient_count} patients (total: {total_count})")
                    
                    # Test patient structure if patients exist
                    if patient_count > 0:
                        sample_patient = data["patients"][0]
                        required_patient_fields = ["id", "nom", "prenom"]
                        missing_patient_fields = [field for field in required_patient_fields 
                                                if field not in sample_patient]
                        
                        if not missing_patient_fields:
                            self.log_result("Patient Structure", "PASS", 
                                          f"Sample patient: {sample_patient.get('prenom', '')} "
                                          f"{sample_patient.get('nom', '')}")
                        else:
                            self.log_result("Patient Structure", "FAIL", 
                                          f"Missing fields: {missing_patient_fields}")
                    
                    # Test search functionality
                    search_response = requests.get(f"{self.base_url}/api/patients?search=Ben")
                    if search_response.status_code == 200:
                        search_data = search_response.json()
                        search_count = len(search_data["patients"])
                        self.log_result("Patients Search", "PASS", f"Search returned {search_count} results")
                    else:
                        self.log_result("Patients Search", "FAIL", 
                                      f"HTTP {search_response.status_code}")
                        
                else:
                    self.log_result("Patients API", "FAIL", f"Missing fields: {missing_fields}")
            else:
                self.log_result("Patients API", "FAIL", f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_result("Patients API", "FAIL", f"Exception: {str(e)}")
    
    def test_authentication(self):
        """Test login functionality"""
        print("\n🔍 Testing Authentication")
        
        # Test valid medecin login
        try:
            login_data = {
                "username": "medecin",
                "password": "medecin123"
            }
            
            response = requests.post(f"{self.base_url}/api/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify response structure
                required_fields = ["access_token", "token_type", "user"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields:
                    user = data["user"]
                    self.log_result("Medecin Login", "PASS", 
                                  f"User: {user.get('full_name', 'Unknown')} "
                                  f"({user.get('role', 'Unknown')})")
                    
                    # Test token validity with /api/auth/me
                    token = data["access_token"]
                    headers = {"Authorization": f"Bearer {token}"}
                    me_response = requests.get(f"{self.base_url}/api/auth/me", headers=headers)
                    
                    if me_response.status_code == 200:
                        me_data = me_response.json()
                        self.log_result("Token Validation", "PASS", 
                                      f"Token valid for user: {me_data.get('username', 'Unknown')}")
                    else:
                        self.log_result("Token Validation", "FAIL", 
                                      f"HTTP {me_response.status_code}")
                        
                else:
                    self.log_result("Medecin Login", "FAIL", f"Missing fields: {missing_fields}")
            else:
                self.log_result("Medecin Login", "FAIL", f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_result("Medecin Login", "FAIL", f"Exception: {str(e)}")
        
        # Test invalid login
        try:
            invalid_login_data = {
                "username": "invalid_user",
                "password": "wrong_password"
            }
            
            response = requests.post(f"{self.base_url}/api/auth/login", json=invalid_login_data)
            
            if response.status_code == 401:
                self.log_result("Invalid Login Rejection", "PASS", "Invalid credentials properly rejected")
            else:
                self.log_result("Invalid Login Rejection", "FAIL", 
                              f"Expected 401, got {response.status_code}")
                
        except Exception as e:
            self.log_result("Invalid Login Rejection", "FAIL", f"Exception: {str(e)}")
    
    def test_whatsapp_integration(self):
        """Test WhatsApp-related functionality (mentioned in review request)"""
        print("\n🔍 Testing WhatsApp Integration")
        
        try:
            # Get patients to check WhatsApp data
            response = requests.get(f"{self.base_url}/api/patients")
            
            if response.status_code == 200:
                data = response.json()
                patients = data["patients"]
                
                whatsapp_patients = [p for p in patients if p.get("numero_whatsapp")]
                
                if whatsapp_patients:
                    sample_patient = whatsapp_patients[0]
                    whatsapp_number = sample_patient.get("numero_whatsapp", "")
                    whatsapp_link = sample_patient.get("lien_whatsapp", "")
                    
                    # Verify WhatsApp link generation
                    if whatsapp_link and "wa.me" in whatsapp_link:
                        self.log_result("WhatsApp Links", "PASS", 
                                      f"WhatsApp links properly generated. Sample: {whatsapp_link}")
                    else:
                        self.log_result("WhatsApp Links", "FAIL", 
                                      "WhatsApp links not properly generated")
                    
                    self.log_result("WhatsApp Data", "PASS", 
                                  f"{len(whatsapp_patients)} patients have WhatsApp numbers")
                else:
                    self.log_result("WhatsApp Data", "FAIL", "No patients with WhatsApp numbers found")
            else:
                self.log_result("WhatsApp Integration", "FAIL", 
                              f"Could not retrieve patients: HTTP {response.status_code}")
                
        except Exception as e:
            self.log_result("WhatsApp Integration", "FAIL", f"Exception: {str(e)}")
    
    def run_all_tests(self):
        """Run all tests"""
        print("🚀 Starting Backend API Tests for Review Request")
        print("Focus: Dashboard, Messaging, Patients, Authentication after UI changes")
        
        self.test_dashboard_api()
        self.test_messaging_apis()
        self.test_patients_api()
        self.test_authentication()
        self.test_whatsapp_integration()
        
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 80)
        print("📊 TEST SUMMARY")
        print("=" * 80)
        
        passed_tests = [r for r in self.test_results if r["status"] == "PASS"]
        failed_tests = [r for r in self.test_results if r["status"] == "FAIL"]
        
        print(f"✅ PASSED: {len(passed_tests)}")
        print(f"❌ FAILED: {len(failed_tests)}")
        print(f"📈 SUCCESS RATE: {len(passed_tests)}/{len(self.test_results)} ({len(passed_tests)/len(self.test_results)*100:.1f}%)")
        
        if failed_tests:
            print("\n❌ FAILED TESTS:")
            for test in failed_tests:
                print(f"   - {test['test']}: {test['details']}")
        
        print(f"\n🕐 Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Determine overall status
        if len(failed_tests) == 0:
            print("\n🎉 ALL TESTS PASSED - Backend APIs working correctly after UI changes")
            return True
        else:
            print(f"\n⚠️  {len(failed_tests)} TESTS FAILED - Issues detected in backend APIs")
            return False

if __name__ == "__main__":
    tester = ReviewBackendTest()
    success = tester.run_all_tests()
    
    # Exit with appropriate code
    exit(0 if success else 1)