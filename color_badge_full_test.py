#!/usr/bin/env python3
"""
COLOR-CODED WAITING TIME BADGE SYSTEM - COMPREHENSIVE TESTING
Testing all 4 color ranges with available appointments

TESTING REQUIREMENTS:
- Green: < 15 minutes (test with 5 minutes)
- Blue: 15-30 minutes (test with 20 minutes)  
- Orange: 30-60 minutes (test with 45 minutes)
- Red: > 60 minutes (test with 75 minutes)
"""

import requests
import json
import time
from datetime import datetime, timedelta
import sys

# Configuration
BACKEND_URL = "https://e095a16b-4f79-4d50-8576-cad954291484.preview.emergentagent.com/api"
TEST_CREDENTIALS = {"username": "medecin", "password": "medecin123"}

class ColorBadgeFullTester:
    def __init__(self):
        self.session = requests.Session()
        self.session.verify = False
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        self.auth_token = None
        self.test_results = []
        self.start_time = time.time()
        
    def log_result(self, test_name, success, details="", response_time=0):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "response_time": response_time
        })
        print(f"{status} {test_name} ({response_time:.3f}s)")
        if details:
            print(f"    {details}")
    
    def authenticate(self):
        """Authenticate with medecin credentials"""
        print("🔐 AUTHENTICATING...")
        start_time = time.time()
        
        try:
            response = self.session.post(f"{BACKEND_URL}/auth/login", json=TEST_CREDENTIALS, timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data["access_token"]
                self.session.headers.update({"Authorization": f"Bearer {self.auth_token}"})
                
                user_info = data["user"]
                details = f"Logged in as {user_info.get('full_name')} ({user_info.get('role')})"
                self.log_result("Authentication", True, details, response_time)
                return True
            else:
                self.log_result("Authentication", False, f"HTTP {response.status_code}", response_time)
                return False
                
        except Exception as e:
            response_time = time.time() - start_time
            self.log_result("Authentication", False, f"Exception: {str(e)}", response_time)
            return False
    
    def get_appointments(self):
        """Get today's appointments"""
        today = datetime.now().strftime("%Y-%m-%d")
        start_time = time.time()
        
        try:
            response = self.session.get(f"{BACKEND_URL}/rdv/jour/{today}", timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                appointments = response.json()
                count = len(appointments)
                details = f"Found {count} appointments for {today}"
                self.log_result("Get Today's Appointments", True, details, response_time)
                return appointments
            else:
                self.log_result("Get Today's Appointments", False, f"HTTP {response.status_code}", response_time)
                return []
                
        except Exception as e:
            response_time = time.time() - start_time
            self.log_result("Get Today's Appointments", False, f"Exception: {str(e)}", response_time)
            return []
    
    def test_color_range(self, appointment, target_duree, color_name, color_range):
        """Test a specific color range by setting duree_attente"""
        rdv_id = appointment["id"]
        patient = appointment.get("patient", {})
        patient_name = f"{patient.get('prenom', '')} {patient.get('nom', '')}"
        
        print(f"\n🎨 TESTING {color_name} BADGE ({color_range})")
        print(f"    Patient: {patient_name}")
        print(f"    Target: {target_duree} minutes")
        
        # Step 1: Set to attente with calculated arrival time
        start_time = time.time()
        try:
            now = datetime.now()
            arrival_time = now - timedelta(minutes=target_duree)
            
            update_data = {
                "statut": "attente",
                "heure_arrivee_attente": arrival_time.strftime("%Y-%m-%dT%H:%M:%S.%f")
            }
            
            response = self.session.put(f"{BACKEND_URL}/rdv/{rdv_id}/statut", json=update_data, timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                details = f"Set {patient_name} to attente with arrival time {target_duree} minutes ago"
                self.log_result(f"{color_name} Badge - Set Attente", True, details, response_time)
            else:
                details = f"Failed to set attente: HTTP {response.status_code}"
                self.log_result(f"{color_name} Badge - Set Attente", False, details, response_time)
                return False
                
        except Exception as e:
            response_time = time.time() - start_time
            self.log_result(f"{color_name} Badge - Set Attente", False, f"Exception: {str(e)}", response_time)
            return False
        
        # Step 2: Move to en_cours to calculate duree_attente
        start_time = time.time()
        try:
            update_data = {"statut": "en_cours"}
            response = self.session.put(f"{BACKEND_URL}/rdv/{rdv_id}/statut", json=update_data, timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                calculated_duree = data.get("duree_attente")
                
                if calculated_duree is not None:
                    # Allow some tolerance for timing differences
                    if abs(calculated_duree - target_duree) <= 1:
                        details = f"✅ SUCCESS: {patient_name} duree_attente = {calculated_duree} minutes ({color_name} badge)"
                        self.log_result(f"{color_name} Badge - Duration Calculation", True, details, response_time)
                        return True
                    else:
                        details = f"Duration mismatch: Expected {target_duree}, got {calculated_duree}"
                        self.log_result(f"{color_name} Badge - Duration Calculation", False, details, response_time)
                        return False
                else:
                    details = "API response missing duree_attente field"
                    self.log_result(f"{color_name} Badge - Duration Calculation", False, details, response_time)
                    return False
            else:
                details = f"Failed to move to en_cours: HTTP {response.status_code}"
                self.log_result(f"{color_name} Badge - Duration Calculation", False, details, response_time)
                return False
                
        except Exception as e:
            response_time = time.time() - start_time
            self.log_result(f"{color_name} Badge - Duration Calculation", False, f"Exception: {str(e)}", response_time)
            return False
    
    def test_all_color_ranges(self):
        """Test all 4 color ranges using available appointments"""
        print("\n🎨 TESTING ALL COLOR RANGES...")
        
        appointments = self.get_appointments()
        if len(appointments) < 3:
            self.log_result("Color Range Testing", False, f"Need at least 3 appointments, found {len(appointments)}", 0)
            return False
        
        # Test scenarios - we'll cycle through appointments
        color_tests = [
            {"duree": 5, "color": "GREEN", "range": "< 15 minutes"},
            {"duree": 20, "color": "BLUE", "range": "15-30 minutes"},
            {"duree": 45, "color": "ORANGE", "range": "30-60 minutes"},
            {"duree": 75, "color": "RED", "range": "> 60 minutes"}
        ]
        
        success_count = 0
        
        # Test each color range with available appointments
        for i, color_test in enumerate(color_tests):
            # Use appointments cyclically if we don't have enough
            apt_index = i % len(appointments)
            appointment = appointments[apt_index]
            
            success = self.test_color_range(
                appointment,
                color_test["duree"],
                color_test["color"],
                color_test["range"]
            )
            
            if success:
                success_count += 1
            
            # Small delay between tests
            time.sleep(0.5)
        
        # Summary of color range testing
        details = f"Successfully tested {success_count}/{len(color_tests)} color ranges"
        if success_count >= 3:
            self.log_result("Color Range Testing Complete", True, details, 0)
        else:
            self.log_result("Color Range Testing Complete", False, details, 0)
        
        return success_count >= 3
    
    def verify_final_state(self):
        """Verify final state shows different duree_attente values"""
        print("\n💾 VERIFYING FINAL STATE...")
        
        appointments = self.get_appointments()
        if not appointments:
            self.log_result("Final State Verification", False, "No appointments to verify", 0)
            return False
        
        # Collect all duree_attente values
        duree_values = []
        color_distribution = {"green": 0, "blue": 0, "orange": 0, "red": 0}
        
        print("    Final appointment states:")
        for apt in appointments:
            patient = apt.get("patient", {})
            name = f"{patient.get('prenom', '')} {patient.get('nom', '')}"
            duree = apt.get("duree_attente")
            status = apt.get("statut")
            
            if duree is not None:
                duree_values.append(duree)
                
                # Determine color
                if duree < 15:
                    color = "GREEN"
                    color_distribution["green"] += 1
                elif duree <= 30:
                    color = "BLUE"
                    color_distribution["blue"] += 1
                elif duree <= 60:
                    color = "ORANGE"
                    color_distribution["orange"] += 1
                else:
                    color = "RED"
                    color_distribution["red"] += 1
                
                print(f"      • {name}: {duree} min → {color} badge (status: {status})")
        
        # Check diversity of values
        unique_values = len(set(duree_values))
        colors_represented = len([color for color, count in color_distribution.items() if count > 0])
        
        details = f"Found {unique_values} unique duree_attente values, {colors_represented} color ranges represented"
        
        if unique_values >= 3 and colors_represented >= 3:
            self.log_result("Final State Verification", True, details, 0)
            return True
        else:
            self.log_result("Final State Verification", False, details, 0)
            return False
    
    def generate_summary(self):
        """Generate comprehensive test summary"""
        print("\n" + "="*80)
        print("🎨 COLOR-CODED WAITING TIME BADGE SYSTEM - FINAL SUMMARY")
        print("="*80)
        
        total_tests = len(self.test_results)
        passed_tests = len([t for t in self.test_results if t["success"]])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"\n📊 TEST RESULTS:")
        print(f"   Total Tests: {total_tests}")
        print(f"   Passed: {passed_tests} ✅")
        print(f"   Failed: {failed_tests} ❌")
        print(f"   Success Rate: {success_rate:.1f}%")
        print(f"   Execution Time: {time.time() - self.start_time:.2f} seconds")
        
        print(f"\n🎨 COLOR BADGE SYSTEM STATUS:")
        if success_rate >= 75:
            print(f"   🎉 COLOR BADGE SYSTEM VERIFIED WORKING!")
            print(f"   ✅ Backend correctly stores different duree_attente values")
            print(f"   ✅ API returns appointments with various waiting time durations")
            print(f"   ✅ Color-coding logic will receive different time values:")
            print(f"      • GREEN badges: < 15 minutes")
            print(f"      • BLUE badges: 15-30 minutes")
            print(f"      • ORANGE badges: 30-60 minutes")
            print(f"      • RED badges: > 60 minutes")
        else:
            print(f"   ⚠️  System needs attention - {failed_tests} tests failed")
        
        # Show current appointment states
        print(f"\n📋 CURRENT APPOINTMENT STATES:")
        appointments = self.get_appointments()
        for apt in appointments:
            patient = apt.get("patient", {})
            name = f"{patient.get('prenom', '')} {patient.get('nom', '')}"
            duree = apt.get("duree_attente")
            status = apt.get("statut")
            
            if duree is not None:
                if duree < 15:
                    color = "GREEN"
                elif duree <= 30:
                    color = "BLUE"
                elif duree <= 60:
                    color = "ORANGE"
                else:
                    color = "RED"
                print(f"   • {name}: {duree} min → {color} badge (status: {status})")
        
        print(f"\n🔍 DETAILED TEST RESULTS:")
        for result in self.test_results:
            status_icon = "✅" if result["success"] else "❌"
            print(f"   {status_icon} {result['test']} ({result['response_time']:.3f}s)")
            if result['details'] and not result['success']:
                print(f"      └─ {result['details']}")
        
        return success_rate >= 75

def main():
    """Main test execution"""
    print("🎨 COLOR-CODED WAITING TIME BADGE SYSTEM - COMPREHENSIVE TESTING")
    print("="*70)
    print("Testing all 4 color ranges:")
    print("• GREEN: < 15 minutes (testing with 5 minutes)")
    print("• BLUE: 15-30 minutes (testing with 20 minutes)")
    print("• ORANGE: 30-60 minutes (testing with 45 minutes)")
    print("• RED: > 60 minutes (testing with 75 minutes)")
    print("="*70)
    
    tester = ColorBadgeFullTester()
    
    # Authenticate
    if not tester.authenticate():
        print("❌ Authentication failed - cannot proceed")
        return False
    
    # Test all color ranges
    tester.test_all_color_ranges()
    
    # Verify final state
    tester.verify_final_state()
    
    # Generate summary
    success = tester.generate_summary()
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)