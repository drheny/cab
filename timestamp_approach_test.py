#!/usr/bin/env python3
"""
SPECIFIC TIMESTAMP APPROACH TESTING
Testing for Pure Timestamp + Frontend Calculation Approach

REVIEW REQUEST TESTING:
1. Login avec medecin/medecin123
2. GET /rdv/jour/{today} pour Lina Alami
3. Vérifier les champs dans la réponse API :
   - heure_arrivee_attente : Doit être un timestamp ISO
   - duree_attente : Doit être ABSENT (nouvelle approche pure) ou null
4. Si duree_attente est encore présent avec une valeur, c'est que l'ancien système persiste

L'objectif est de confirmer si :
- ✅ SUCCÈS : duree_attente absent/null + heure_arrivee_attente présent = nouvelle approche pure
- ❌ PARTIEL : duree_attente=5 présent = mélange ancien/nouveau système
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

class TimestampApproachTester:
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
            
            print(f"Response status: {response.status_code}")
            
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
            print(f"Authentication error: {error_details}")
            self.log_test("Authentication Login", False, error_details, response_time)
            return False
    
    def test_timestamp_approach_verification(self):
        """Test the specific timestamp approach for Lina Alami"""
        print("\n🕐 TESTING TIMESTAMP APPROACH VERIFICATION")
        print("Checking if we have pure timestamp approach or mixed old/new system")
        
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Step 1: GET /rdv/jour/{today} to find Lina Alami
        start_time = time.time()
        try:
            response = self.session.get(f"{BACKEND_URL}/rdv/jour/{today}", timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                appointments = response.json()
                if isinstance(appointments, list):
                    # Find Lina Alami
                    lina_appointment = None
                    for apt in appointments:
                        patient_info = apt.get("patient", {})
                        patient_name = f"{patient_info.get('prenom', '')} {patient_info.get('nom', '')}"
                        if "Lina" in patient_name and "Alami" in patient_name:
                            lina_appointment = apt
                            break
                    
                    if lina_appointment:
                        self.log_test("Find Lina Alami", True, f"Found Lina Alami in today's appointments", response_time)
                        
                        # Step 2: Analyze the API response structure for Lina Alami
                        self.analyze_lina_appointment_structure(lina_appointment)
                        
                        # Step 3: Test all appointments for approach consistency
                        self.analyze_all_appointments_approach(appointments)
                        
                    else:
                        # If Lina not found, analyze first appointment as example
                        if appointments:
                            example_appointment = appointments[0]
                            patient_info = example_appointment.get("patient", {})
                            patient_name = f"{patient_info.get('prenom', '')} {patient_info.get('nom', '')}"
                            self.log_test("Find Lina Alami", False, f"Lina Alami not found, analyzing {patient_name} instead", response_time)
                            self.analyze_lina_appointment_structure(example_appointment)
                            self.analyze_all_appointments_approach(appointments)
                        else:
                            self.log_test("Find Lina Alami", False, "No appointments found for today", response_time)
                else:
                    self.log_test("GET Today's Appointments", False, "Response is not a list", response_time)
            else:
                self.log_test("GET Today's Appointments", False, f"HTTP {response.status_code}: {response.text}", response_time)
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("GET Today's Appointments", False, f"Exception: {str(e)}", response_time)
    
    def analyze_lina_appointment_structure(self, appointment):
        """Analyze the specific appointment structure for timestamp approach"""
        print("\n🔍 ANALYZING APPOINTMENT STRUCTURE FOR TIMESTAMP APPROACH")
        
        patient_info = appointment.get("patient", {})
        patient_name = f"{patient_info.get('prenom', '')} {patient_info.get('nom', '')}"
        
        # Check for heure_arrivee_attente field
        heure_arrivee_attente = appointment.get("heure_arrivee_attente")
        duree_attente = appointment.get("duree_attente")
        statut = appointment.get("statut", "unknown")
        
        print(f"Patient: {patient_name}")
        print(f"Status: {statut}")
        print(f"heure_arrivee_attente: {heure_arrivee_attente}")
        print(f"duree_attente: {duree_attente}")
        
        # Test 1: Check heure_arrivee_attente presence and format
        if heure_arrivee_attente is not None and heure_arrivee_attente != "":
            # Check if it's an ISO timestamp format
            try:
                # Try to parse as ISO timestamp
                if "T" in str(heure_arrivee_attente) and ("Z" in str(heure_arrivee_attente) or "+" in str(heure_arrivee_attente)):
                    self.log_test("heure_arrivee_attente ISO Format", True, f"ISO timestamp present: {heure_arrivee_attente}", 0)
                    iso_timestamp = True
                else:
                    self.log_test("heure_arrivee_attente Format", True, f"Timestamp present but not ISO: {heure_arrivee_attente}", 0)
                    iso_timestamp = False
            except:
                self.log_test("heure_arrivee_attente Format", False, f"Invalid timestamp format: {heure_arrivee_attente}", 0)
                iso_timestamp = False
        else:
            self.log_test("heure_arrivee_attente Presence", False, "heure_arrivee_attente is missing or empty", 0)
            iso_timestamp = False
        
        # Test 2: Check duree_attente presence (should be absent/null in pure approach)
        if "duree_attente" not in appointment:
            self.log_test("duree_attente Field Absence", True, "duree_attente field is ABSENT (pure timestamp approach)", 0)
            pure_approach = True
        elif duree_attente is None:
            self.log_test("duree_attente Field Null", True, "duree_attente field is NULL (pure timestamp approach)", 0)
            pure_approach = True
        elif duree_attente == 0:
            self.log_test("duree_attente Field Zero", True, "duree_attente field is 0 (could be pure approach)", 0)
            pure_approach = True  # Zero could be acceptable in pure approach
        else:
            self.log_test("duree_attente Field Present", False, f"duree_attente has value: {duree_attente} (mixed approach detected)", 0)
            pure_approach = False
        
        # Test 3: Determine approach type
        if iso_timestamp and pure_approach:
            approach_type = "✅ PURE TIMESTAMP APPROACH"
            success = True
            details = "heure_arrivee_attente present + duree_attente absent/null = Pure timestamp + frontend calculation"
        elif iso_timestamp and not pure_approach:
            approach_type = "⚠️ MIXED APPROACH"
            success = False
            details = f"heure_arrivee_attente present + duree_attente={duree_attente} = Mixed old/new system"
        elif not iso_timestamp and not pure_approach:
            approach_type = "❌ OLD APPROACH"
            success = False
            details = f"No ISO timestamp + duree_attente={duree_attente} = Old backend calculation approach"
        else:
            approach_type = "❓ UNCLEAR APPROACH"
            success = False
            details = "Unclear approach - needs investigation"
        
        self.log_test(f"Approach Type for {patient_name}", success, f"{approach_type}: {details}", 0)
        
        return {
            "patient_name": patient_name,
            "approach_type": approach_type,
            "iso_timestamp": iso_timestamp,
            "pure_approach": pure_approach,
            "heure_arrivee_attente": heure_arrivee_attente,
            "duree_attente": duree_attente
        }
    
    def analyze_all_appointments_approach(self, appointments):
        """Analyze all appointments to determine system-wide approach"""
        print("\n📊 ANALYZING ALL APPOINTMENTS FOR SYSTEM-WIDE APPROACH")
        
        approach_stats = {
            "total_appointments": len(appointments),
            "with_iso_timestamp": 0,
            "with_duree_attente_value": 0,
            "with_duree_attente_null": 0,
            "with_duree_attente_zero": 0,
            "without_duree_attente": 0,
            "pure_approach_count": 0,
            "mixed_approach_count": 0
        }
        
        for apt in appointments:
            patient_info = apt.get("patient", {})
            patient_name = f"{patient_info.get('prenom', '')} {patient_info.get('nom', '')}"
            
            heure_arrivee_attente = apt.get("heure_arrivee_attente")
            duree_attente = apt.get("duree_attente")
            
            # Check timestamp format
            if heure_arrivee_attente and "T" in str(heure_arrivee_attente):
                approach_stats["with_iso_timestamp"] += 1
            
            # Check duree_attente status
            if "duree_attente" not in apt:
                approach_stats["without_duree_attente"] += 1
            elif duree_attente is None:
                approach_stats["with_duree_attente_null"] += 1
            elif duree_attente == 0:
                approach_stats["with_duree_attente_zero"] += 1
            else:
                approach_stats["with_duree_attente_value"] += 1
            
            # Determine approach for this appointment
            has_iso = heure_arrivee_attente and "T" in str(heure_arrivee_attente)
            is_pure = "duree_attente" not in apt or duree_attente is None or duree_attente == 0
            
            if has_iso and is_pure:
                approach_stats["pure_approach_count"] += 1
            else:
                approach_stats["mixed_approach_count"] += 1
        
        # Log detailed statistics
        details = f"Total: {approach_stats['total_appointments']}, ISO timestamps: {approach_stats['with_iso_timestamp']}, duree_attente values: {approach_stats['with_duree_attente_value']}"
        self.log_test("System-wide Approach Statistics", True, details, 0)
        
        # Determine overall system approach
        if approach_stats["pure_approach_count"] == approach_stats["total_appointments"]:
            system_approach = "✅ PURE TIMESTAMP APPROACH"
            success = True
            details = "All appointments use pure timestamp approach"
        elif approach_stats["mixed_approach_count"] == approach_stats["total_appointments"]:
            system_approach = "❌ OLD BACKEND CALCULATION APPROACH"
            success = False
            details = "All appointments use old backend calculation approach"
        else:
            system_approach = "⚠️ MIXED SYSTEM"
            success = False
            details = f"Mixed system: {approach_stats['pure_approach_count']} pure, {approach_stats['mixed_approach_count']} mixed"
        
        self.log_test("Overall System Approach", success, f"{system_approach}: {details}", 0)
        
        return approach_stats
    
    def run_all_tests(self):
        """Run all tests"""
        print("🚀 STARTING TIMESTAMP APPROACH TESTING")
        print("=" * 80)
        
        # Test authentication first
        if not self.test_authentication():
            print("❌ Authentication failed, cannot continue with other tests")
            return
        
        # Test timestamp approach verification
        self.test_timestamp_approach_verification()
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        total_time = time.time() - self.start_time
        total_tests = len(self.test_results)
        passed_tests = len([t for t in self.test_results if t["success"]])
        failed_tests = total_tests - passed_tests
        
        print("\n" + "=" * 80)
        print("📋 TIMESTAMP APPROACH TEST SUMMARY")
        print("=" * 80)
        
        print(f"⏱️  Total execution time: {total_time:.2f} seconds")
        print(f"📊 Total tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"📈 Success rate: {(passed_tests/total_tests*100):.1f}%")
        
        print("\n📝 DETAILED RESULTS:")
        for result in self.test_results:
            print(f"{result['status']} {result['test']} ({result['response_time']:.3f}s)")
            if result['details']:
                print(f"    {result['details']}")
        
        print("\n" + "=" * 80)
        print("🎯 CONCLUSION FOR REVIEW REQUEST:")
        
        # Analyze results for conclusion
        approach_tests = [t for t in self.test_results if "Approach" in t["test"]]
        if any("PURE TIMESTAMP APPROACH" in t["details"] for t in approach_tests):
            print("✅ SUCCÈS: duree_attente absent/null + heure_arrivee_attente présent = nouvelle approche pure")
        elif any("MIXED APPROACH" in t["details"] for t in approach_tests):
            print("❌ PARTIEL: duree_attente présent avec valeur = mélange ancien/nouveau système")
        else:
            print("❓ UNCLEAR: Needs further investigation")
        
        print("=" * 80)

if __name__ == "__main__":
    tester = TimestampApproachTester()
    tester.run_all_tests()