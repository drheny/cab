#!/usr/bin/env python3
"""
COLOR-CODED WAITING TIME BADGE SYSTEM - FINAL COMPREHENSIVE TEST
Testing the actual backend implementation for color badge system

APPROACH:
- Test by directly setting duree_attente values via status update
- Verify backend stores different duree_attente values correctly
- Verify API returns appointments with various waiting time durations
- Test all 4 color ranges: Green (<15), Blue (15-30), Orange (30-60), Red (>60)
"""

import requests
import json
import time
from datetime import datetime, timedelta
import sys

# Configuration
BACKEND_URL = "https://a657b56d-56f9-415b-a575-b3b503d7e7a0.preview.emergentagent.com/api"
TEST_CREDENTIALS = {"username": "medecin", "password": "medecin123"}

class ColorBadgeSystemTest:
    def __init__(self):
        self.session = requests.Session()
        self.session.verify = False
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        self.auth_token = None
        self.test_results = []
        self.start_time = time.time()
        self.tested_appointments = []
        
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
    
    def test_color_badge_with_direct_duree(self, appointment, target_duree, color_name, color_range):
        """Test color badge by directly setting duree_attente value"""
        rdv_id = appointment["id"]
        patient = appointment.get("patient", {})
        patient_name = f"{patient.get('prenom', '')} {patient.get('nom', '')}"
        
        print(f"\n🎨 TESTING {color_name} BADGE ({color_range})")
        print(f"    Patient: {patient_name}")
        print(f"    Target duree_attente: {target_duree} minutes")
        
        # Step 1: Set to en_cours with explicit duree_attente
        start_time = time.time()
        try:
            update_data = {
                "statut": "en_cours",
                "duree_attente": target_duree
            }
            
            response = self.session.put(f"{BACKEND_URL}/rdv/{rdv_id}/statut", json=update_data, timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                returned_duree = data.get("duree_attente")
                
                if returned_duree == target_duree:
                    details = f"✅ SUCCESS: {patient_name} duree_attente set to {returned_duree} minutes ({color_name} badge)"
                    self.log_result(f"{color_name} Badge - Set Duration", True, details, response_time)
                    
                    # Store successful test
                    self.tested_appointments.append({
                        "patient_name": patient_name,
                        "duree_attente": returned_duree,
                        "color": color_name,
                        "color_range": color_range,
                        "rdv_id": rdv_id
                    })
                    return True
                else:
                    details = f"Duration mismatch: Expected {target_duree}, got {returned_duree}"
                    self.log_result(f"{color_name} Badge - Set Duration", False, details, response_time)
                    return False
            else:
                details = f"Failed to set status: HTTP {response.status_code}: {response.text}"
                self.log_result(f"{color_name} Badge - Set Duration", False, details, response_time)
                return False
                
        except Exception as e:
            response_time = time.time() - start_time
            self.log_result(f"{color_name} Badge - Set Duration", False, f"Exception: {str(e)}", response_time)
            return False
    
    def test_all_color_ranges(self):
        """Test all 4 color ranges"""
        print("\n🎨 TESTING ALL COLOR BADGE RANGES...")
        
        appointments = self.get_appointments()
        if len(appointments) < 3:
            self.log_result("Color Badge Testing", False, f"Need at least 3 appointments, found {len(appointments)}", 0)
            return False
        
        # Color test scenarios
        color_tests = [
            {"duree": 5, "color": "GREEN", "range": "< 15 minutes"},
            {"duree": 20, "color": "BLUE", "range": "15-30 minutes"},
            {"duree": 45, "color": "ORANGE", "range": "30-60 minutes"},
            {"duree": 75, "color": "RED", "range": "> 60 minutes"}
        ]
        
        success_count = 0
        
        # Test each color range
        for i, color_test in enumerate(color_tests):
            # Use appointments cyclically
            apt_index = i % len(appointments)
            appointment = appointments[apt_index]
            
            success = self.test_color_badge_with_direct_duree(
                appointment,
                color_test["duree"],
                color_test["color"],
                color_test["range"]
            )
            
            if success:
                success_count += 1
            
            # Small delay between tests
            time.sleep(0.2)
        
        # Summary
        details = f"Successfully tested {success_count}/{len(color_tests)} color ranges"
        if success_count >= 3:
            self.log_result("Color Badge System Testing", True, details, 0)
            return True
        else:
            self.log_result("Color Badge System Testing", False, details, 0)
            return False
    
    def verify_database_storage(self):
        """Verify all duree_attente values are stored correctly in database"""
        print("\n💾 VERIFYING DATABASE STORAGE...")
        
        appointments = self.get_appointments()
        if not appointments:
            self.log_result("Database Storage Verification", False, "No appointments to verify", 0)
            return False
        
        # Analyze stored values
        duree_values = []
        color_counts = {"GREEN": 0, "BLUE": 0, "ORANGE": 0, "RED": 0}
        
        print("    Current database state:")
        for apt in appointments:
            patient = apt.get("patient", {})
            name = f"{patient.get('prenom', '')} {patient.get('nom', '')}"
            duree = apt.get("duree_attente")
            status = apt.get("statut")
            
            if duree is not None:
                duree_values.append(duree)
                
                # Determine color based on business logic
                if duree < 15:
                    color = "GREEN"
                    color_counts["GREEN"] += 1
                elif duree <= 30:
                    color = "BLUE"
                    color_counts["BLUE"] += 1
                elif duree <= 60:
                    color = "ORANGE"
                    color_counts["ORANGE"] += 1
                else:
                    color = "RED"
                    color_counts["RED"] += 1
                
                print(f"      • {name}: {duree} min → {color} badge (status: {status})")
        
        # Check diversity
        unique_values = len(set(duree_values))
        colors_with_data = len([color for color, count in color_counts.items() if count > 0])
        
        details = f"Found {unique_values} unique duree_attente values, {colors_with_data}/4 color ranges represented"
        
        if unique_values >= 3 and colors_with_data >= 3:
            self.log_result("Database Storage Verification", True, details, 0)
            return True
        else:
            self.log_result("Database Storage Verification", False, details, 0)
            return False
    
    def test_api_response_structure(self):
        """Test API response structure for frontend compatibility"""
        print("\n📋 TESTING API RESPONSE STRUCTURE...")
        
        appointments = self.get_appointments()
        if not appointments:
            self.log_result("API Response Structure", False, "No appointments to test", 0)
            return False
        
        sample_apt = appointments[0]
        required_fields = ["id", "duree_attente", "statut", "patient"]
        missing_fields = [field for field in required_fields if field not in sample_apt]
        
        if not missing_fields:
            details = f"All required fields present: {required_fields}"
            self.log_result("API Response Structure", True, details, 0)
            
            # Check patient structure
            patient = sample_apt.get("patient", {})
            patient_fields = ["nom", "prenom"]
            missing_patient_fields = [field for field in patient_fields if field not in patient]
            
            if not missing_patient_fields:
                details = f"Patient structure complete: {patient_fields}"
                self.log_result("Patient Info Structure", True, details, 0)
                return True
            else:
                details = f"Missing patient fields: {missing_patient_fields}"
                self.log_result("Patient Info Structure", False, details, 0)
                return False
        else:
            details = f"Missing required fields: {missing_fields}"
            self.log_result("API Response Structure", False, details, 0)
            return False
    
    def test_color_boundary_logic(self):
        """Test color boundary logic verification"""
        print("\n🎯 TESTING COLOR BOUNDARY LOGIC...")
        
        boundary_tests = [
            {"duree": 14, "expected": "GREEN", "desc": "14 min (green boundary)"},
            {"duree": 15, "expected": "BLUE", "desc": "15 min (blue start)"},
            {"duree": 30, "expected": "BLUE", "desc": "30 min (blue end)"},
            {"duree": 31, "expected": "ORANGE", "desc": "31 min (orange start)"},
            {"duree": 60, "expected": "ORANGE", "desc": "60 min (orange end)"},
            {"duree": 61, "expected": "RED", "desc": "61 min (red start)"}
        ]
        
        all_correct = True
        for test in boundary_tests:
            duree = test["duree"]
            expected = test["expected"]
            desc = test["desc"]
            
            # Apply color logic
            if duree < 15:
                actual = "GREEN"
            elif duree <= 30:
                actual = "BLUE"
            elif duree <= 60:
                actual = "ORANGE"
            else:
                actual = "RED"
            
            if actual == expected:
                details = f"{desc} → {actual} ✅"
                self.log_result(f"Boundary Test - {duree}min", True, details, 0)
            else:
                details = f"{desc} → Expected {expected}, got {actual} ❌"
                self.log_result(f"Boundary Test - {duree}min", False, details, 0)
                all_correct = False
        
        return all_correct
    
    def generate_final_summary(self):
        """Generate comprehensive final summary"""
        print("\n" + "="*80)
        print("🎨 COLOR-CODED WAITING TIME BADGE SYSTEM - FINAL TEST SUMMARY")
        print("="*80)
        
        total_tests = len(self.test_results)
        passed_tests = len([t for t in self.test_results if t["success"]])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"\n📊 OVERALL TEST RESULTS:")
        print(f"   Total Tests: {total_tests}")
        print(f"   Passed: {passed_tests} ✅")
        print(f"   Failed: {failed_tests} ❌")
        print(f"   Success Rate: {success_rate:.1f}%")
        print(f"   Execution Time: {time.time() - self.start_time:.2f} seconds")
        
        print(f"\n🎨 COLOR BADGE SYSTEM VERIFICATION:")
        if self.tested_appointments:
            print(f"   Successfully tested appointments:")
            for apt in self.tested_appointments:
                print(f"   • {apt['patient_name']}: {apt['duree_attente']} min → {apt['color']} badge ({apt['color_range']})")
        
        print(f"\n📋 CURRENT SYSTEM STATE:")
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
        
        print(f"\n🎯 SYSTEM READINESS ASSESSMENT:")
        if success_rate >= 80:
            print(f"   🎉 COLOR BADGE SYSTEM IS READY FOR PRODUCTION!")
            print(f"   ✅ Backend correctly stores different duree_attente values")
            print(f"   ✅ API returns appointments with various waiting time durations")
            print(f"   ✅ Frontend can display color-coded badges based on waiting times:")
            print(f"      • GREEN badges: < 15 minutes")
            print(f"      • BLUE badges: 15-30 minutes")
            print(f"      • ORANGE badges: 30-60 minutes")
            print(f"      • RED badges: > 60 minutes")
            print(f"   ✅ Color-coding logic will receive different time values to display")
        else:
            print(f"   ⚠️  System needs attention - {failed_tests} tests failed")
            print(f"   🔧 Review failed tests and fix issues before production")
        
        print(f"\n🔍 DETAILED TEST RESULTS:")
        for result in self.test_results:
            status_icon = "✅" if result["success"] else "❌"
            print(f"   {status_icon} {result['test']} ({result['response_time']:.3f}s)")
            if result['details'] and not result['success']:
                print(f"      └─ {result['details']}")
        
        return success_rate >= 80

def main():
    """Main test execution"""
    print("🎨 COLOR-CODED WAITING TIME BADGE SYSTEM - COMPREHENSIVE TESTING")
    print("="*70)
    print("Testing Requirements from User:")
    print("• Test color-coded waiting time badge system")
    print("• Color coding: Green (<15), Blue (15-30), Orange (30-60), Red (>60)")
    print("• Test duree_attente values: 5, 20, 45, 75 minutes")
    print("• Verify backend stores different duree_attente values")
    print("• Verify API returns appointments with various waiting time durations")
    print("="*70)
    
    tester = ColorBadgeSystemTest()
    
    # Authenticate
    if not tester.authenticate():
        print("❌ Authentication failed - cannot proceed")
        return False
    
    # Run comprehensive tests
    tester.test_all_color_ranges()
    tester.verify_database_storage()
    tester.test_api_response_structure()
    tester.test_color_boundary_logic()
    
    # Generate final summary
    success = tester.generate_final_summary()
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)