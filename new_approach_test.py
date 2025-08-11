#!/usr/bin/env python3
"""
NEW RADICAL APPROACH TESTING - "0 MIN" BUG FIX
Backend API Testing Suite for Cabinet Médical

TESTING THE NEW RADICAL APPROACH to fix the persistent "0 min" bug:

**MAJOR CHANGE:**
- Backend: NO MORE duree_attente calculation, ONLY stores heure_arrivee_attente timestamp
- Frontend: Real-time calculation based on heure_arrivee_attente in badge display code

**New Approach Eliminates:**
- Faulty preservation logic
- Complex backend calculations  
- API call conflicts
- Integer division giving 0

**Test Workflow:**
1. Login with medecin/medecin123
2. Take a patient and move to "attente" 
3. Verify heure_arrivee_attente is stored (timestamp ISO)
4. Wait 30+ seconds for significant time
5. Move to "en_cours"
6. Verify heure_arrivee_attente is PRESERVED (no duree_attente calculated backend)
7. Check GET API for data format

**Frontend Logic Should Calculate:**
- heureArrivee = new Date(appointment.heure_arrivee_attente)
- maintenant = new Date()
- waitingTime = Math.floor((maintenant - heureArrivee) / 60000)

This should give REAL times instead of "0 min".
"""

import requests
import json
import time
from datetime import datetime, timedelta
import sys
import os

# Configuration
BACKEND_URL = "https://86e1ae33-6e29-4ce5-a743-1e543eb0a6b8.preview.emergentagent.com/api"
TEST_CREDENTIALS = {
    "username": "medecin",
    "password": "medecin123"
}

class NewApproachTester:
    def __init__(self):
        self.session = requests.Session()
        # Disable SSL verification for testing environment
        self.session.verify = False
        # Disable SSL warnings
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        self.auth_token = None
        self.test_results = []
        self.start_time = time.time()
        
    def log_test(self, test_name, success, details="", response_time=0):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "response_time": response_time,
            "status": status
        })
        print(f"{status} {test_name} ({response_time:.3f}s)")
        if details:
            print(f"    Details: {details}")
    
    def test_authentication(self):
        """Test 1: Authentication - medecin login (medecin/medecin123)"""
        print("\n🔐 TESTING AUTHENTICATION")
        start_time = time.time()
        
        try:
            print(f"Attempting to connect to: {BACKEND_URL}/auth/login")
            response = self.session.post(
                f"{BACKEND_URL}/auth/login",
                json=TEST_CREDENTIALS,
                timeout=30,
                verify=False
            )
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                if "access_token" in data and "user" in data:
                    self.auth_token = data["access_token"]
                    self.session.headers.update({
                        "Authorization": f"Bearer {self.auth_token}"
                    })
                    user_info = data["user"]
                    details = f"User: {user_info.get('full_name', 'Unknown')}, Role: {user_info.get('role', 'Unknown')}"
                    self.log_test("Authentication Login", True, details, response_time)
                    return True
                else:
                    self.log_test("Authentication Login", False, "Missing access_token or user in response", response_time)
                    return False
            else:
                response_text = response.text[:200] if response.text else "No response body"
                self.log_test("Authentication Login", False, f"HTTP {response.status_code}: {response_text}", response_time)
                return False
                
        except Exception as e:
            response_time = time.time() - start_time
            error_details = f"Exception: {str(e)[:200]}"
            self.log_test("Authentication Login", False, error_details, response_time)
            return False
    
    def test_new_radical_approach_workflow(self):
        """Test NEW RADICAL APPROACH - Complete workflow testing"""
        print("\n🚀 TESTING NEW RADICAL APPROACH - Complete Workflow")
        print("Testing: Backend stores ONLY heure_arrivee_attente, Frontend calculates in real-time")
        
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Step 1: Get current appointments and select a test patient
        print("\n📋 STEP 1: Find a patient for testing the new approach")
        start_time = time.time()
        try:
            response = self.session.get(f"{BACKEND_URL}/rdv/jour/{today}", timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                appointments = response.json()
                if appointments:
                    # Find a suitable test patient
                    test_appointment = None
                    for apt in appointments:
                        if apt.get("statut") in ["programme", "termine", "en_cours"]:
                            test_appointment = apt
                            break
                    
                    if not test_appointment:
                        test_appointment = appointments[0]
                    
                    patient_info = test_appointment.get("patient", {})
                    test_patient_name = f"{patient_info.get('prenom', '')} {patient_info.get('nom', '')}"
                    rdv_id = test_appointment.get("id")
                    current_status = test_appointment.get("statut")
                    current_duree = test_appointment.get("duree_attente")
                    current_heure_arrivee = test_appointment.get("heure_arrivee_attente")
                    
                    details = f"Selected: '{test_patient_name}' - Status: {current_status}, duree_attente: {current_duree}, heure_arrivee: {current_heure_arrivee}"
                    self.log_test("Patient Selection for New Approach", True, details, response_time)
                    
                    # Step 2: Move patient to "attente" - VERIFY heure_arrivee_attente timestamp is stored
                    print("\n🏥 STEP 2: Move to 'attente' - VERIFY heure_arrivee_attente timestamp stored (ISO format)")
                    start_time = time.time()
                    
                    attente_start_time = datetime.now()
                    
                    update_data = {"statut": "attente"}
                    response = self.session.put(f"{BACKEND_URL}/rdv/{rdv_id}/statut", json=update_data, timeout=10)
                    response_time = time.time() - start_time
                    
                    if response.status_code == 200:
                        data = response.json()
                        heure_arrivee = data.get("heure_arrivee_attente", "NOT_SET")
                        duree_attente_after_attente = data.get("duree_attente", "NOT_PROVIDED")
                        
                        # NEW APPROACH: Check if heure_arrivee_attente is ISO timestamp
                        if heure_arrivee and heure_arrivee != "NOT_SET":
                            try:
                                # Try to parse as ISO timestamp
                                parsed_time = datetime.fromisoformat(heure_arrivee.replace('Z', '+00:00'))
                                details = f"✅ heure_arrivee_attente stored as ISO timestamp: {heure_arrivee}"
                                self.log_test("NEW APPROACH - ISO Timestamp Storage", True, details, response_time)
                            except:
                                # Try to parse as time only (HH:MM)
                                if ":" in heure_arrivee and len(heure_arrivee) <= 5:
                                    details = f"⚠️ heure_arrivee_attente stored as time only: {heure_arrivee} (should be ISO timestamp)"
                                    self.log_test("NEW APPROACH - Time Format (Not ISO)", False, details, response_time)
                                else:
                                    details = f"❌ heure_arrivee_attente format unknown: {heure_arrivee}"
                                    self.log_test("NEW APPROACH - Unknown Time Format", False, details, response_time)
                        else:
                            details = f"❌ heure_arrivee_attente not set: {heure_arrivee}"
                            self.log_test("NEW APPROACH - Timestamp Not Set", False, details, response_time)
                        
                        # NEW APPROACH: Backend should NOT calculate duree_attente
                        if duree_attente_after_attente == "NOT_PROVIDED":
                            details = "✅ Backend correctly does NOT provide duree_attente (new approach)"
                            self.log_test("NEW APPROACH - No Backend Calculation", True, details, 0)
                        else:
                            details = f"⚠️ Backend still provides duree_attente: {duree_attente_after_attente} (old approach)"
                            self.log_test("NEW APPROACH - Backend Still Calculating", False, details, 0)
                        
                        # Step 3: Wait 30+ seconds for significant time accumulation
                        print("\n⏰ STEP 3: Wait 30+ seconds for significant time accumulation")
                        print("Waiting 35 seconds to accumulate significant waiting time...")
                        time.sleep(35)  # Wait 35 seconds for significant time
                        
                        elapsed_time = datetime.now() - attente_start_time
                        elapsed_seconds = elapsed_time.total_seconds()
                        print(f"🔍 DEBUG: Elapsed seconds: {elapsed_seconds:.1f}")
                        
                        # Step 4: Move to "en_cours" - VERIFY heure_arrivee_attente is PRESERVED
                        print("\n🩺 STEP 4: Move to 'en_cours' - VERIFY heure_arrivee_attente PRESERVED (no backend calculation)")
                        start_time = time.time()
                        
                        update_data = {"statut": "en_cours"}
                        response = self.session.put(f"{BACKEND_URL}/rdv/{rdv_id}/statut", json=update_data, timeout=10)
                        response_time = time.time() - start_time
                        
                        if response.status_code == 200:
                            data = response.json()
                            
                            # NEW APPROACH: Check if heure_arrivee_attente is PRESERVED
                            preserved_heure_arrivee = data.get("heure_arrivee_attente", "NOT_PROVIDED")
                            duree_attente_after_en_cours = data.get("duree_attente", "NOT_PROVIDED")
                            
                            if preserved_heure_arrivee == heure_arrivee:
                                details = f"✅ heure_arrivee_attente PRESERVED: {preserved_heure_arrivee}"
                                self.log_test("NEW APPROACH - Timestamp Preserved", True, details, response_time)
                            elif preserved_heure_arrivee != "NOT_PROVIDED":
                                details = f"⚠️ heure_arrivee_attente CHANGED: {heure_arrivee} → {preserved_heure_arrivee}"
                                self.log_test("NEW APPROACH - Timestamp Changed", False, details, response_time)
                            else:
                                details = f"❌ heure_arrivee_attente NOT PROVIDED in response"
                                self.log_test("NEW APPROACH - Timestamp Not Provided", False, details, response_time)
                            
                            # NEW APPROACH: Backend should NOT calculate duree_attente
                            if duree_attente_after_en_cours == "NOT_PROVIDED":
                                details = "✅ Backend correctly does NOT calculate duree_attente (new approach)"
                                self.log_test("NEW APPROACH - No Backend Calculation in en_cours", True, details, 0)
                            else:
                                details = f"⚠️ Backend still calculates duree_attente: {duree_attente_after_en_cours} (old approach)"
                                self.log_test("NEW APPROACH - Backend Still Calculating in en_cours", False, details, 0)
                            
                            # Step 5: Check GET API for data format
                            print("\n💾 STEP 5: Check GET API for data format - VERIFY heure_arrivee_attente available for frontend")
                            start_time = time.time()
                            
                            response = self.session.get(f"{BACKEND_URL}/rdv/jour/{today}", timeout=10)
                            response_time = time.time() - start_time
                            
                            if response.status_code == 200:
                                updated_appointments = response.json()
                                updated_appointment = next((apt for apt in updated_appointments if apt.get("id") == rdv_id), None)
                                
                                if updated_appointment:
                                    final_heure_arrivee = updated_appointment.get("heure_arrivee_attente", "NOT_PROVIDED")
                                    final_duree_attente = updated_appointment.get("duree_attente", "NOT_PROVIDED")
                                    final_status = updated_appointment.get("statut", "UNKNOWN")
                                    
                                    # NEW APPROACH: Verify data format for frontend calculation
                                    if final_heure_arrivee and final_heure_arrivee != "NOT_PROVIDED":
                                        try:
                                            # Test frontend calculation logic
                                            heureArrivee = datetime.fromisoformat(final_heure_arrivee.replace('Z', '+00:00'))
                                            maintenant = datetime.now()
                                            waitingTime = int((maintenant - heureArrivee).total_seconds() / 60)
                                            
                                            details = f"✅ Frontend can calculate: {waitingTime} min from heure_arrivee_attente: {final_heure_arrivee}"
                                            self.log_test("NEW APPROACH - Frontend Calculation Possible", True, details, response_time)
                                            
                                            # Verify this gives REAL time instead of 0
                                            if waitingTime > 0:
                                                details = f"✅ Real waiting time calculated: {waitingTime} min (NOT 0 min!)"
                                                self.log_test("NEW APPROACH - Real Time Calculated", True, details, 0)
                                            else:
                                                details = f"⚠️ Calculated time is 0 min (may be too fast or timestamp issue)"
                                                self.log_test("NEW APPROACH - Zero Time Calculated", False, details, 0)
                                            
                                        except Exception as e:
                                            details = f"❌ Frontend calculation failed: {str(e)}"
                                            self.log_test("NEW APPROACH - Frontend Calculation Failed", False, details, response_time)
                                    else:
                                        details = f"❌ heure_arrivee_attente not available for frontend: {final_heure_arrivee}"
                                        self.log_test("NEW APPROACH - No Timestamp for Frontend", False, details, response_time)
                                    
                                    # NEW APPROACH: Backend should NOT provide duree_attente
                                    if final_duree_attente == "NOT_PROVIDED" or final_duree_attente is None:
                                        details = "✅ Backend correctly does NOT provide duree_attente in GET API (new approach)"
                                        self.log_test("NEW APPROACH - No Backend duree_attente in GET", True, details, 0)
                                    else:
                                        details = f"⚠️ Backend still provides duree_attente in GET API: {final_duree_attente} (old approach)"
                                        self.log_test("NEW APPROACH - Backend Still Provides duree_attente", False, details, 0)
                                    
                                    # Summary of new approach verification
                                    print(f"\n📊 NEW APPROACH SUMMARY:")
                                    print(f"   Patient: {test_patient_name}")
                                    print(f"   Status: {final_status}")
                                    print(f"   heure_arrivee_attente: {final_heure_arrivee}")
                                    print(f"   duree_attente (backend): {final_duree_attente}")
                                    print(f"   Elapsed time: {elapsed_seconds:.1f} seconds")
                                    if final_heure_arrivee and final_heure_arrivee != "NOT_PROVIDED":
                                        try:
                                            heureArrivee = datetime.fromisoformat(final_heure_arrivee.replace('Z', '+00:00'))
                                            maintenant = datetime.now()
                                            waitingTime = int((maintenant - heureArrivee).total_seconds() / 60)
                                            print(f"   Frontend calculation: {waitingTime} min")
                                        except:
                                            print(f"   Frontend calculation: FAILED")
                                
                                else:
                                    self.log_test("NEW APPROACH - Updated Appointment Not Found", False, "Appointment not found in GET response", response_time)
                            else:
                                self.log_test("NEW APPROACH - GET API Failed", False, f"HTTP {response.status_code}: {response.text}", response_time)
                        
                        else:
                            self.log_test("NEW APPROACH - Move to en_cours Failed", False, f"HTTP {response.status_code}: {response.text}", response_time)
                    
                    else:
                        self.log_test("NEW APPROACH - Move to attente Failed", False, f"HTTP {response.status_code}: {response.text}", response_time)
                
                else:
                    self.log_test("NEW APPROACH - No Appointments Found", False, "No appointments available for testing", response_time)
            else:
                self.log_test("NEW APPROACH - Get Appointments Failed", False, f"HTTP {response.status_code}: {response.text}", response_time)
        
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("NEW APPROACH - Exception", False, f"Exception: {str(e)}", response_time)
    
    def test_frontend_calculation_logic(self):
        """Test Frontend Calculation Logic - Verify the new frontend logic works"""
        print("\n🧮 TESTING FRONTEND CALCULATION LOGIC")
        print("Testing: heureArrivee = new Date(appointment.heure_arrivee_attente)")
        print("         maintenant = new Date()")
        print("         waitingTime = Math.floor((maintenant - heureArrivee) / 60000)")
        
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Get current appointments to test frontend logic
        start_time = time.time()
        try:
            response = self.session.get(f"{BACKEND_URL}/rdv/jour/{today}", timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                appointments = response.json()
                if appointments:
                    # Test frontend calculation logic on all appointments
                    for apt in appointments:
                        patient_info = apt.get("patient", {})
                        patient_name = f"{patient_info.get('prenom', '')} {patient_info.get('nom', '')}"
                        heure_arrivee = apt.get("heure_arrivee_attente")
                        status = apt.get("statut", "unknown")
                        backend_duree = apt.get("duree_attente", "not_provided")
                        
                        if heure_arrivee and heure_arrivee != "":
                            try:
                                # Simulate frontend calculation
                                if "T" in heure_arrivee or "Z" in heure_arrivee:
                                    # ISO timestamp format
                                    heureArrivee = datetime.fromisoformat(heure_arrivee.replace('Z', '+00:00'))
                                    maintenant = datetime.now()
                                    waitingTime = int((maintenant - heureArrivee).total_seconds() / 60)
                                    
                                    details = f"Patient '{patient_name}' ({status}) - Frontend calculates: {waitingTime} min, Backend: {backend_duree}"
                                    
                                    if waitingTime >= 0:
                                        self.log_test(f"Frontend Calculation - {patient_name}", True, details, 0)
                                    else:
                                        self.log_test(f"Frontend Calculation - {patient_name}", False, f"Negative time: {details}", 0)
                                
                                else:
                                    # Time only format (HH:MM)
                                    details = f"Patient '{patient_name}' ({status}) - Time format not ISO: {heure_arrivee}"
                                    self.log_test(f"Frontend Calculation - {patient_name}", False, details, 0)
                            
                            except Exception as e:
                                details = f"Patient '{patient_name}' ({status}) - Calculation error: {str(e)}"
                                self.log_test(f"Frontend Calculation - {patient_name}", False, details, 0)
                        
                        else:
                            details = f"Patient '{patient_name}' ({status}) - No heure_arrivee_attente available"
                            self.log_test(f"Frontend Calculation - {patient_name}", False, details, 0)
                
                else:
                    self.log_test("Frontend Calculation Logic", False, "No appointments found for testing", response_time)
            else:
                self.log_test("Frontend Calculation Logic", False, f"HTTP {response.status_code}: {response.text}", response_time)
        
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("Frontend Calculation Logic", False, f"Exception: {str(e)}", response_time)
    
    def run_all_tests(self):
        """Run all tests for the new radical approach"""
        print("🚀 STARTING NEW RADICAL APPROACH TESTING")
        print("=" * 80)
        print("Testing the new approach to fix the persistent '0 min' bug:")
        print("- Backend: ONLY stores heure_arrivee_attente timestamp")
        print("- Frontend: Real-time calculation in badge display")
        print("=" * 80)
        
        # Test authentication first
        if not self.test_authentication():
            print("❌ Authentication failed. Cannot proceed with tests.")
            return
        
        # Test the new radical approach workflow
        self.test_new_radical_approach_workflow()
        
        # Test frontend calculation logic
        self.test_frontend_calculation_logic()
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        total_time = time.time() - self.start_time
        total_tests = len(self.test_results)
        passed_tests = len([t for t in self.test_results if t["success"]])
        failed_tests = total_tests - passed_tests
        
        print("\n" + "=" * 80)
        print("🏁 NEW RADICAL APPROACH TEST SUMMARY")
        print("=" * 80)
        print(f"⏱️  Total execution time: {total_time:.2f} seconds")
        print(f"📊 Total tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"📈 Success rate: {(passed_tests/total_tests*100):.1f}%")
        
        if failed_tests > 0:
            print(f"\n❌ FAILED TESTS:")
            for test in self.test_results:
                if not test["success"]:
                    print(f"   • {test['test']}: {test['details']}")
        
        print("\n🎯 NEW APPROACH VERIFICATION:")
        
        # Check if new approach is working
        new_approach_tests = [t for t in self.test_results if "NEW APPROACH" in t["test"]]
        new_approach_passed = len([t for t in new_approach_tests if t["success"]])
        new_approach_total = len(new_approach_tests)
        
        if new_approach_total > 0:
            print(f"   📊 New Approach Tests: {new_approach_passed}/{new_approach_total} passed")
            
            if new_approach_passed == new_approach_total:
                print("   ✅ NEW RADICAL APPROACH IS WORKING CORRECTLY!")
                print("   🎉 Backend stores only heure_arrivee_attente, Frontend calculates real-time")
            elif new_approach_passed > new_approach_total / 2:
                print("   ⚠️  NEW RADICAL APPROACH PARTIALLY WORKING")
                print("   🔧 Some components need adjustment")
            else:
                print("   ❌ NEW RADICAL APPROACH NOT WORKING")
                print("   🚨 Major issues found - may still be using old approach")
        
        print("=" * 80)

if __name__ == "__main__":
    tester = NewApproachTester()
    tester.run_all_tests()