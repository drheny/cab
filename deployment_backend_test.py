#!/usr/bin/env python3
"""
Comprehensive Backend Testing for Medical Cabinet Management System
Deployment Preparation - Testing all major endpoints and functionality
"""

import requests
import json
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
import time

# Load environment variables
load_dotenv('/app/frontend/.env')

class DeploymentBackendTest:
    def __init__(self):
        self.base_url = os.getenv('REACT_APP_BACKEND_URL', 'https://b41bbcdf-8fee-41b8-8d35-533fd4cb83fc.preview.emergentagent.com')
        self.auth_token = None
        self.test_results = []
        print(f"🚀 DEPLOYMENT BACKEND TESTING")
        print(f"Backend URL: {self.base_url}")
        print("=" * 80)
    
    def log_test(self, test_name, status, details=""):
        """Log test results"""
        result = {
            "test": test_name,
            "status": status,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        status_icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{status_icon} {test_name}: {status}")
        if details:
            print(f"   {details}")
    
    def authenticate(self):
        """Authenticate and get token"""
        try:
            login_data = {"username": "medecin", "password": "medecin123"}
            response = requests.post(f"{self.base_url}/api/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("access_token")
                user = data.get("user", {})
                self.log_test("Authentication - Medecin Login", "PASS", 
                             f"User: {user.get('full_name', 'Unknown')} ({user.get('role', 'Unknown')})")
                return True
            else:
                self.log_test("Authentication - Medecin Login", "FAIL", 
                             f"Status: {response.status_code}, Response: {response.text}")
                return False
        except Exception as e:
            self.log_test("Authentication - Medecin Login", "FAIL", f"Exception: {str(e)}")
            return False
    
    def get_headers(self):
        """Get headers with authentication"""
        if self.auth_token:
            return {"Authorization": f"Bearer {self.auth_token}"}
        return {}
    
    def test_dashboard_endpoints(self):
        """Test dashboard-related endpoints"""
        print("\n📊 TESTING DASHBOARD ENDPOINTS")
        print("-" * 40)
        
        # Test main dashboard
        try:
            response = requests.get(f"{self.base_url}/api/dashboard", headers=self.get_headers())
            if response.status_code == 200:
                data = response.json()
                required_fields = ["total_rdv", "rdv_restants", "rdv_attente", "rdv_en_cours", 
                                 "rdv_termines", "recette_jour", "total_patients"]
                missing_fields = [field for field in required_fields if field not in data]
                if not missing_fields:
                    self.log_test("Dashboard - Main Stats", "PASS", 
                                 f"Total RDV: {data.get('total_rdv')}, Patients: {data.get('total_patients')}")
                else:
                    self.log_test("Dashboard - Main Stats", "FAIL", f"Missing fields: {missing_fields}")
            else:
                self.log_test("Dashboard - Main Stats", "FAIL", f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Dashboard - Main Stats", "FAIL", f"Exception: {str(e)}")
        
        # Test birthday reminders
        try:
            response = requests.get(f"{self.base_url}/api/dashboard/birthdays", headers=self.get_headers())
            if response.status_code == 200:
                data = response.json()
                birthdays = data.get("birthdays", [])
                self.log_test("Dashboard - Birthday Reminders", "PASS", f"Found {len(birthdays)} birthdays today")
            else:
                self.log_test("Dashboard - Birthday Reminders", "FAIL", f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Dashboard - Birthday Reminders", "FAIL", f"Exception: {str(e)}")
        
        # Test phone reminders
        try:
            response = requests.get(f"{self.base_url}/api/dashboard/phone-reminders", headers=self.get_headers())
            if response.status_code == 200:
                data = response.json()
                reminders = data.get("reminders", [])
                self.log_test("Dashboard - Phone Reminders", "PASS", f"Found {len(reminders)} phone reminders")
            else:
                self.log_test("Dashboard - Phone Reminders", "FAIL", f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Dashboard - Phone Reminders", "FAIL", f"Exception: {str(e)}")
        
        # Test vaccine reminders
        try:
            response = requests.get(f"{self.base_url}/api/dashboard/vaccine-reminders", headers=self.get_headers())
            if response.status_code == 200:
                data = response.json()
                vaccine_reminders = data.get("vaccine_reminders", [])
                self.log_test("Dashboard - Vaccine Reminders", "PASS", f"Found {len(vaccine_reminders)} vaccine reminders")
            else:
                self.log_test("Dashboard - Vaccine Reminders", "FAIL", f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Dashboard - Vaccine Reminders", "FAIL", f"Exception: {str(e)}")
    
    def test_patient_management(self):
        """Test patient management endpoints"""
        print("\n👥 TESTING PATIENT MANAGEMENT")
        print("-" * 40)
        
        # Test patient list with pagination
        try:
            response = requests.get(f"{self.base_url}/api/patients?page=1&limit=10", headers=self.get_headers())
            if response.status_code == 200:
                data = response.json()
                required_fields = ["patients", "total_count", "page", "limit", "total_pages"]
                missing_fields = [field for field in required_fields if field not in data]
                if not missing_fields:
                    patients = data.get("patients", [])
                    self.log_test("Patient Management - List with Pagination", "PASS", 
                                 f"Found {len(patients)} patients, Total: {data.get('total_count')}")
                else:
                    self.log_test("Patient Management - List with Pagination", "FAIL", f"Missing fields: {missing_fields}")
            else:
                self.log_test("Patient Management - List with Pagination", "FAIL", f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Patient Management - List with Pagination", "FAIL", f"Exception: {str(e)}")
        
        # Test patient count
        try:
            response = requests.get(f"{self.base_url}/api/patients/count", headers=self.get_headers())
            if response.status_code == 200:
                data = response.json()
                count = data.get("count", 0)
                self.log_test("Patient Management - Count", "PASS", f"Total patients: {count}")
            else:
                self.log_test("Patient Management - Count", "FAIL", f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Patient Management - Count", "FAIL", f"Exception: {str(e)}")
        
        # Test patient search
        try:
            response = requests.get(f"{self.base_url}/api/patients/search?q=Ben", headers=self.get_headers())
            if response.status_code == 200:
                data = response.json()
                patients = data.get("patients", [])
                self.log_test("Patient Management - Search", "PASS", f"Search results: {len(patients)} patients")
            else:
                self.log_test("Patient Management - Search", "FAIL", f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Patient Management - Search", "FAIL", f"Exception: {str(e)}")
    
    def test_appointment_system(self):
        """Test appointment system endpoints"""
        print("\n📅 TESTING APPOINTMENT SYSTEM")
        print("-" * 40)
        
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Test daily appointments
        try:
            response = requests.get(f"{self.base_url}/api/rdv/jour/{today}", headers=self.get_headers())
            if response.status_code == 200:
                appointments = response.json()
                self.log_test("Appointment System - Daily Appointments", "PASS", 
                             f"Found {len(appointments)} appointments for today")
            else:
                self.log_test("Appointment System - Daily Appointments", "FAIL", f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Appointment System - Daily Appointments", "FAIL", f"Exception: {str(e)}")
        
        # Test weekly appointments
        try:
            response = requests.get(f"{self.base_url}/api/rdv/semaine/{today}", headers=self.get_headers())
            if response.status_code == 200:
                data = response.json()
                appointments = data.get("appointments", [])
                week_dates = data.get("week_dates", [])
                self.log_test("Appointment System - Weekly Appointments", "PASS", 
                             f"Found {len(appointments)} appointments for week ({len(week_dates)} days)")
            else:
                self.log_test("Appointment System - Weekly Appointments", "FAIL", f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Appointment System - Weekly Appointments", "FAIL", f"Exception: {str(e)}")
        
        # Test all appointments
        try:
            response = requests.get(f"{self.base_url}/api/appointments", headers=self.get_headers())
            if response.status_code == 200:
                appointments = response.json()
                self.log_test("Appointment System - All Appointments", "PASS", 
                             f"Found {len(appointments)} total appointments")
            else:
                self.log_test("Appointment System - All Appointments", "FAIL", f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Appointment System - All Appointments", "FAIL", f"Exception: {str(e)}")
    
    def test_consultation_system(self):
        """Test consultation system endpoints"""
        print("\n🩺 TESTING CONSULTATION SYSTEM")
        print("-" * 40)
        
        # Test consultations list
        try:
            response = requests.get(f"{self.base_url}/api/consultations", headers=self.get_headers())
            if response.status_code == 200:
                consultations = response.json()
                self.log_test("Consultation System - List Consultations", "PASS", 
                             f"Found {len(consultations)} consultations")
            else:
                self.log_test("Consultation System - List Consultations", "FAIL", f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Consultation System - List Consultations", "FAIL", f"Exception: {str(e)}")
        
        # Test consultation statistics
        try:
            response = requests.get(f"{self.base_url}/api/consultations/stats", headers=self.get_headers())
            if response.status_code == 200:
                stats = response.json()
                self.log_test("Consultation System - Statistics", "PASS", 
                             f"Stats retrieved: {list(stats.keys())}")
            else:
                self.log_test("Consultation System - Statistics", "FAIL", f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Consultation System - Statistics", "FAIL", f"Exception: {str(e)}")
    
    def test_payment_system(self):
        """Test payment system endpoints"""
        print("\n💰 TESTING PAYMENT SYSTEM")
        print("-" * 40)
        
        # Test payments list
        try:
            response = requests.get(f"{self.base_url}/api/payments", headers=self.get_headers())
            if response.status_code == 200:
                payments = response.json()
                self.log_test("Payment System - List Payments", "PASS", 
                             f"Found {len(payments)} payments")
            else:
                self.log_test("Payment System - List Payments", "FAIL", f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Payment System - List Payments", "FAIL", f"Exception: {str(e)}")
        
        # Test payment statistics
        try:
            response = requests.get(f"{self.base_url}/api/payments/stats", headers=self.get_headers())
            if response.status_code == 200:
                stats = response.json()
                self.log_test("Payment System - Statistics", "PASS", 
                             f"Revenue stats: {stats.get('total_revenue', 'N/A')} TND")
            else:
                self.log_test("Payment System - Statistics", "FAIL", f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Payment System - Statistics", "FAIL", f"Exception: {str(e)}")
        
        # Test cash movements
        try:
            response = requests.get(f"{self.base_url}/api/cash-movements", headers=self.get_headers())
            if response.status_code == 200:
                movements = response.json()
                self.log_test("Payment System - Cash Movements", "PASS", 
                             f"Found {len(movements)} cash movements")
            else:
                self.log_test("Payment System - Cash Movements", "FAIL", f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Payment System - Cash Movements", "FAIL", f"Exception: {str(e)}")
    
    def test_messaging_system(self):
        """Test messaging system endpoints"""
        print("\n💬 TESTING MESSAGING SYSTEM")
        print("-" * 40)
        
        # Test internal messages
        try:
            response = requests.get(f"{self.base_url}/api/messages", headers=self.get_headers())
            if response.status_code == 200:
                messages = response.json()
                self.log_test("Messaging System - Internal Messages", "PASS", 
                             f"Found {len(messages)} internal messages")
            else:
                self.log_test("Messaging System - Internal Messages", "FAIL", f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Messaging System - Internal Messages", "FAIL", f"Exception: {str(e)}")
        
        # Test phone messages
        try:
            response = requests.get(f"{self.base_url}/api/phone-messages", headers=self.get_headers())
            if response.status_code == 200:
                messages = response.json()
                self.log_test("Messaging System - Phone Messages", "PASS", 
                             f"Found {len(messages)} phone messages")
            else:
                self.log_test("Messaging System - Phone Messages", "FAIL", f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Messaging System - Phone Messages", "FAIL", f"Exception: {str(e)}")
        
        # Test phone message stats
        try:
            response = requests.get(f"{self.base_url}/api/phone-messages/stats", headers=self.get_headers())
            if response.status_code == 200:
                stats = response.json()
                self.log_test("Messaging System - Phone Message Stats", "PASS", 
                             f"Stats: {stats}")
            else:
                self.log_test("Messaging System - Phone Message Stats", "FAIL", f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Messaging System - Phone Message Stats", "FAIL", f"Exception: {str(e)}")
    
    def test_ai_integration(self):
        """Test AI integration endpoints"""
        print("\n🤖 TESTING AI INTEGRATION")
        print("-" * 40)
        
        # Test AI Room initialization
        try:
            response = requests.post(f"{self.base_url}/api/ai-room/initialize", headers=self.get_headers())
            if response.status_code == 200:
                data = response.json()
                self.log_test("AI Integration - AI Room Initialize", "PASS", 
                             f"Processed {data.get('appointments_processed', 0)} appointments")
            else:
                self.log_test("AI Integration - AI Room Initialize", "FAIL", f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("AI Integration - AI Room Initialize", "FAIL", f"Exception: {str(e)}")
        
        # Test AI Room queue
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            response = requests.get(f"{self.base_url}/api/ai-room/queue?date={today}", headers=self.get_headers())
            if response.status_code == 200:
                data = response.json()
                queue = data.get("queue", [])
                self.log_test("AI Integration - AI Room Queue", "PASS", 
                             f"AI queue has {len(queue)} patients")
            else:
                self.log_test("AI Integration - AI Room Queue", "FAIL", f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("AI Integration - AI Room Queue", "FAIL", f"Exception: {str(e)}")
        
        # Test AI Room doctor analytics
        try:
            response = requests.get(f"{self.base_url}/api/ai-room/doctor-analytics", headers=self.get_headers())
            if response.status_code == 200:
                data = response.json()
                efficiency = data.get("efficiency_score", "N/A")
                self.log_test("AI Integration - Doctor Analytics", "PASS", 
                             f"Doctor efficiency: {efficiency}")
            else:
                self.log_test("AI Integration - Doctor Analytics", "FAIL", f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("AI Integration - Doctor Analytics", "FAIL", f"Exception: {str(e)}")
        
        # Test AI Learning endpoints
        try:
            response = requests.get(f"{self.base_url}/api/ai-learning/doctor-state", headers=self.get_headers())
            if response.status_code == 200:
                data = response.json()
                efficiency = data.get("current_efficiency", "N/A")
                self.log_test("AI Integration - AI Learning Doctor State", "PASS", 
                             f"Current efficiency: {efficiency}")
            else:
                self.log_test("AI Integration - AI Learning Doctor State", "FAIL", f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("AI Integration - AI Learning Doctor State", "FAIL", f"Exception: {str(e)}")
    
    def test_whatsapp_hub(self):
        """Test WhatsApp Hub endpoints"""
        print("\n📱 TESTING WHATSAPP HUB")
        print("-" * 40)
        
        # Test WhatsApp Hub initialization
        try:
            response = requests.post(f"{self.base_url}/api/whatsapp-hub/initialize", headers=self.get_headers())
            if response.status_code == 200:
                data = response.json()
                templates_created = data.get("templates_created", 0)
                self.log_test("WhatsApp Hub - Initialize", "PASS", 
                             f"Created {templates_created} default templates")
            else:
                self.log_test("WhatsApp Hub - Initialize", "FAIL", f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("WhatsApp Hub - Initialize", "FAIL", f"Exception: {str(e)}")
        
        # Test WhatsApp templates
        try:
            response = requests.get(f"{self.base_url}/api/whatsapp-hub/templates", headers=self.get_headers())
            if response.status_code == 200:
                data = response.json()
                total_templates = sum(len(templates) for templates in data.values())
                self.log_test("WhatsApp Hub - Templates", "PASS", 
                             f"Found {total_templates} templates across categories")
            else:
                self.log_test("WhatsApp Hub - Templates", "FAIL", f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("WhatsApp Hub - Templates", "FAIL", f"Exception: {str(e)}")
        
        # Test WhatsApp queue
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            response = requests.get(f"{self.base_url}/api/whatsapp-hub/queue?date={today}", headers=self.get_headers())
            if response.status_code == 200:
                data = response.json()
                queue = data.get("queue", [])
                self.log_test("WhatsApp Hub - Queue", "PASS", 
                             f"WhatsApp queue has {len(queue)} patients")
            else:
                self.log_test("WhatsApp Hub - Queue", "FAIL", f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("WhatsApp Hub - Queue", "FAIL", f"Exception: {str(e)}")
    
    def test_administration(self):
        """Test administration endpoints"""
        print("\n⚙️ TESTING ADMINISTRATION")
        print("-" * 40)
        
        # Test user management
        try:
            response = requests.get(f"{self.base_url}/api/admin/users", headers=self.get_headers())
            if response.status_code == 200:
                users = response.json()
                self.log_test("Administration - User Management", "PASS", 
                             f"Found {len(users)} users in system")
            else:
                self.log_test("Administration - User Management", "FAIL", f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Administration - User Management", "FAIL", f"Exception: {str(e)}")
        
        # Test system stats
        try:
            response = requests.get(f"{self.base_url}/api/admin/stats", headers=self.get_headers())
            if response.status_code == 200:
                stats = response.json()
                self.log_test("Administration - System Stats", "PASS", 
                             f"System stats retrieved: {list(stats.keys())}")
            else:
                self.log_test("Administration - System Stats", "FAIL", f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Administration - System Stats", "FAIL", f"Exception: {str(e)}")
    
    def test_data_initialization(self):
        """Test data initialization endpoints"""
        print("\n🔄 TESTING DATA INITIALIZATION")
        print("-" * 40)
        
        # Test demo data initialization
        try:
            response = requests.get(f"{self.base_url}/api/init-demo", headers=self.get_headers())
            if response.status_code == 200:
                data = response.json()
                self.log_test("Data Initialization - Demo Data", "PASS", 
                             f"Demo data initialized: {data.get('message', 'Success')}")
            else:
                self.log_test("Data Initialization - Demo Data", "FAIL", f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Data Initialization - Demo Data", "FAIL", f"Exception: {str(e)}")
    
    def generate_summary(self):
        """Generate test summary"""
        print("\n" + "=" * 80)
        print("🎯 DEPLOYMENT BACKEND TESTING SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["status"] == "PASS"])
        failed_tests = len([r for r in self.test_results if r["status"] == "FAIL"])
        warning_tests = len([r for r in self.test_results if r["status"] == "WARN"])
        
        print(f"📊 TOTAL TESTS: {total_tests}")
        print(f"✅ PASSED: {passed_tests}")
        print(f"❌ FAILED: {failed_tests}")
        print(f"⚠️ WARNINGS: {warning_tests}")
        print(f"📈 SUCCESS RATE: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print(f"\n❌ FAILED TESTS:")
            for result in self.test_results:
                if result["status"] == "FAIL":
                    print(f"   • {result['test']}: {result['details']}")
        
        if warning_tests > 0:
            print(f"\n⚠️ WARNING TESTS:")
            for result in self.test_results:
                if result["status"] == "WARN":
                    print(f"   • {result['test']}: {result['details']}")
        
        print(f"\n🚀 DEPLOYMENT READINESS:")
        if failed_tests == 0:
            print("✅ BACKEND IS READY FOR PRODUCTION DEPLOYMENT")
        elif failed_tests <= 3:
            print("⚠️ BACKEND HAS MINOR ISSUES - REVIEW BEFORE DEPLOYMENT")
        else:
            print("❌ BACKEND HAS CRITICAL ISSUES - FIX BEFORE DEPLOYMENT")
        
        print("=" * 80)
        
        return {
            "total": total_tests,
            "passed": passed_tests,
            "failed": failed_tests,
            "warnings": warning_tests,
            "success_rate": (passed_tests/total_tests)*100,
            "deployment_ready": failed_tests == 0
        }

def main():
    """Run comprehensive backend testing"""
    tester = DeploymentBackendTest()
    
    # Authenticate first
    if not tester.authenticate():
        print("❌ Authentication failed - cannot proceed with testing")
        return
    
    # Run all test suites
    tester.test_dashboard_endpoints()
    tester.test_patient_management()
    tester.test_appointment_system()
    tester.test_consultation_system()
    tester.test_payment_system()
    tester.test_messaging_system()
    tester.test_ai_integration()
    tester.test_whatsapp_hub()
    tester.test_administration()
    tester.test_data_initialization()
    
    # Generate summary
    summary = tester.generate_summary()
    
    return summary

if __name__ == "__main__":
    main()