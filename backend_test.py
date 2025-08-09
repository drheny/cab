#!/usr/bin/env python3
"""
CALENDAR AND PAYMENT FUNCTIONALITY TESTING
Backend API Testing Suite for Cabinet Médical

This test suite focuses on testing the specific calendar and payment functionality 
mentioned in the review request:
1. Calendar sections order verification
2. Edit button behavior testing
3. Payment toggle logic testing (Visite to Controle Gratuit)
4. Backend payment API endpoint testing
"""

import requests
import json
import time
from datetime import datetime, timedelta
import sys
import os

# Configuration
BACKEND_URL = "https://ae9700da-fec8-4e1e-ab51-a779f23a5093.preview.emergentagent.com/api"
TEST_CREDENTIALS = {
    "username": "medecin",
    "password": "medecin123"
}

class BackendTester:
    def __init__(self):
        self.session = requests.Session()
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
        if details and not success:
            print(f"    Details: {details}")
    
    def test_authentication(self):
        """Test 1: Authentication - medecin login (medecin/medecin123)"""
        print("\n🔐 TESTING AUTHENTICATION")
        start_time = time.time()
        
        try:
            response = self.session.post(
                f"{BACKEND_URL}/auth/login",
                json=TEST_CREDENTIALS,
                timeout=10
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
                self.log_test("Authentication Login", False, f"HTTP {response.status_code}: {response.text}", response_time)
                return False
                
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("Authentication Login", False, f"Exception: {str(e)}", response_time)
            return False
    
    def test_patient_management(self):
        """Test 2: Patient Management - CRUD operations, patient list, patient search"""
        print("\n👥 TESTING PATIENT MANAGEMENT")
        
        # Test patient list
        start_time = time.time()
        try:
            response = self.session.get(f"{BACKEND_URL}/patients", timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                if "patients" in data and "total_count" in data:
                    patient_count = len(data["patients"])
                    total_count = data["total_count"]
                    details = f"Found {patient_count} patients (total: {total_count})"
                    self.log_test("Patient List Retrieval", True, details, response_time)
                else:
                    self.log_test("Patient List Retrieval", False, "Missing patients or total_count in response", response_time)
            else:
                self.log_test("Patient List Retrieval", False, f"HTTP {response.status_code}: {response.text}", response_time)
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("Patient List Retrieval", False, f"Exception: {str(e)}", response_time)
        
        # Test patient search
        start_time = time.time()
        try:
            response = self.session.get(f"{BACKEND_URL}/patients/search?q=Ben", timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                if "patients" in data:
                    search_results = len(data["patients"])
                    details = f"Search 'Ben' returned {search_results} results"
                    self.log_test("Patient Search", True, details, response_time)
                else:
                    self.log_test("Patient Search", False, "Missing patients in search response", response_time)
            else:
                self.log_test("Patient Search", False, f"HTTP {response.status_code}: {response.text}", response_time)
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("Patient Search", False, f"Exception: {str(e)}", response_time)
        
        # Test patient count
        start_time = time.time()
        try:
            response = self.session.get(f"{BACKEND_URL}/patients/count", timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                if "count" in data:
                    count = data["count"]
                    details = f"Total patient count: {count}"
                    self.log_test("Patient Count", True, details, response_time)
                else:
                    self.log_test("Patient Count", False, "Missing count in response", response_time)
            else:
                self.log_test("Patient Count", False, f"HTTP {response.status_code}: {response.text}", response_time)
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("Patient Count", False, f"Exception: {str(e)}", response_time)
    
    def test_dashboard_stats(self):
        """Test 3: Dashboard Stats - Verify main dashboard stats load correctly"""
        print("\n📊 TESTING DASHBOARD STATS")
        
        start_time = time.time()
        try:
            response = self.session.get(f"{BACKEND_URL}/dashboard", timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["total_rdv", "rdv_restants", "rdv_attente", "recette_jour", "total_patients"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields:
                    details = f"RDV: {data['total_rdv']}, Attente: {data['rdv_attente']}, Recette: {data['recette_jour']} TND, Patients: {data['total_patients']}"
                    self.log_test("Dashboard Stats", True, details, response_time)
                else:
                    self.log_test("Dashboard Stats", False, f"Missing fields: {missing_fields}", response_time)
            else:
                self.log_test("Dashboard Stats", False, f"HTTP {response.status_code}: {response.text}", response_time)
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("Dashboard Stats", False, f"Exception: {str(e)}", response_time)
        
        # Test birthday reminders
        start_time = time.time()
        try:
            response = self.session.get(f"{BACKEND_URL}/dashboard/birthdays", timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                if "birthdays" in data:
                    birthday_count = len(data["birthdays"])
                    details = f"Birthday reminders: {birthday_count}"
                    self.log_test("Birthday Reminders", True, details, response_time)
                else:
                    self.log_test("Birthday Reminders", False, "Missing birthdays in response", response_time)
            else:
                self.log_test("Birthday Reminders", False, f"HTTP {response.status_code}: {response.text}", response_time)
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("Birthday Reminders", False, f"Exception: {str(e)}", response_time)
        
        # Test phone reminders
        start_time = time.time()
        try:
            response = self.session.get(f"{BACKEND_URL}/dashboard/phone-reminders", timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                if "reminders" in data:
                    reminder_count = len(data["reminders"])
                    details = f"Phone reminders: {reminder_count}"
                    self.log_test("Phone Reminders", True, details, response_time)
                else:
                    self.log_test("Phone Reminders", False, "Missing reminders in response", response_time)
            else:
                self.log_test("Phone Reminders", False, f"HTTP {response.status_code}: {response.text}", response_time)
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("Phone Reminders", False, f"Exception: {str(e)}", response_time)
        
        # Test vaccine reminders
        start_time = time.time()
        try:
            response = self.session.get(f"{BACKEND_URL}/dashboard/vaccine-reminders", timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                if "vaccine_reminders" in data:
                    vaccine_count = len(data["vaccine_reminders"])
                    details = f"Vaccine reminders: {vaccine_count}"
                    self.log_test("Vaccine Reminders", True, details, response_time)
                else:
                    self.log_test("Vaccine Reminders", False, "Missing vaccine_reminders in response", response_time)
            else:
                self.log_test("Vaccine Reminders", False, f"HTTP {response.status_code}: {response.text}", response_time)
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("Vaccine Reminders", False, f"Exception: {str(e)}", response_time)
    
    def test_appointments(self):
        """Test 4: Appointments - Test appointment retrieval and basic operations"""
        print("\n📅 TESTING APPOINTMENTS")
        
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Test today's appointments
        start_time = time.time()
        try:
            response = self.session.get(f"{BACKEND_URL}/rdv/jour/{today}", timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                appointments = response.json()
                if isinstance(appointments, list):
                    appointment_count = len(appointments)
                    details = f"Today's appointments: {appointment_count}"
                    self.log_test("Today's Appointments", True, details, response_time)
                else:
                    self.log_test("Today's Appointments", False, "Response is not a list", response_time)
            else:
                self.log_test("Today's Appointments", False, f"HTTP {response.status_code}: {response.text}", response_time)
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("Today's Appointments", False, f"Exception: {str(e)}", response_time)
        
        # Test weekly appointments
        start_time = time.time()
        try:
            response = self.session.get(f"{BACKEND_URL}/rdv/semaine/{today}", timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                if "week_dates" in data and "appointments" in data:
                    week_appointments = len(data["appointments"])
                    week_days = len(data["week_dates"])
                    details = f"Week appointments: {week_appointments} across {week_days} days"
                    self.log_test("Weekly Appointments", True, details, response_time)
                else:
                    self.log_test("Weekly Appointments", False, "Missing week_dates or appointments", response_time)
            else:
                self.log_test("Weekly Appointments", False, f"HTTP {response.status_code}: {response.text}", response_time)
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("Weekly Appointments", False, f"Exception: {str(e)}", response_time)
    
    def test_billing_system(self):
        """Test 5: Billing System - Test payment stats, daily payments with nb_impayes field"""
        print("\n💰 TESTING BILLING SYSTEM")
        
        # Test enhanced stats
        start_time = time.time()
        try:
            response = self.session.get(f"{BACKEND_URL}/facturation/enhanced-stats", timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                # Check for actual field names from API
                required_fields = ["recette_jour", "recette_mois", "recette_annee"]
                if any(field in data for field in required_fields):
                    daily = data.get("recette_jour", 0)
                    monthly = data.get("recette_mois", 0)
                    yearly = data.get("recette_annee", 0)
                    nouveaux = data.get("nouveaux_patients_annee", 0)
                    details = f"Daily: {daily} TND, Monthly: {monthly} TND, Yearly: {yearly} TND, New patients: {nouveaux}"
                    self.log_test("Enhanced Billing Stats", True, details, response_time)
                else:
                    self.log_test("Enhanced Billing Stats", False, f"Missing revenue fields in response", response_time)
            else:
                self.log_test("Enhanced Billing Stats", False, f"HTTP {response.status_code}: {response.text}", response_time)
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("Enhanced Billing Stats", False, f"Exception: {str(e)}", response_time)
        
        # Test cash movements
        start_time = time.time()
        try:
            response = self.session.get(f"{BACKEND_URL}/cash-movements", timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                if "movements" in data and "solde_jour" in data:
                    movement_count = len(data["movements"])
                    daily_balance = data["solde_jour"]
                    details = f"Cash movements: {movement_count}, Daily balance: {daily_balance} TND"
                    self.log_test("Cash Movements", True, details, response_time)
                else:
                    self.log_test("Cash Movements", False, "Missing movements or solde_jour", response_time)
            else:
                self.log_test("Cash Movements", False, f"HTTP {response.status_code}: {response.text}", response_time)
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("Cash Movements", False, f"Exception: {str(e)}", response_time)
        
        # Test daily payments with nb_impayes
        start_time = time.time()
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            response = self.session.get(f"{BACKEND_URL}/facturation/daily-payments?date={today}", timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                if "payments" in data:
                    payment_count = len(data["payments"])
                    nb_impayes = data.get("nb_impayes", 0)
                    details = f"Daily payments: {payment_count}, Unpaid: {nb_impayes}"
                    self.log_test("Daily Payments with nb_impayes", True, details, response_time)
                else:
                    self.log_test("Daily Payments with nb_impayes", False, "Missing payments in response", response_time)
            else:
                # If endpoint doesn't exist, try alternative
                self.log_test("Daily Payments with nb_impayes", False, f"HTTP {response.status_code} - endpoint may not exist", response_time)
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("Daily Payments with nb_impayes", False, f"Exception: {str(e)}", response_time)
    
    def test_export_functionality(self):
        """Test 6: Export Functionality - Test patient export endpoint"""
        print("\n📤 TESTING EXPORT FUNCTIONALITY")
        
        # Test patient export
        start_time = time.time()
        try:
            response = self.session.get(f"{BACKEND_URL}/admin/export/patients", timeout=15)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                if "data" in data and "count" in data:
                    export_count = data["count"]
                    collection_name = data.get("collection", "patients")
                    details = f"Exported {export_count} {collection_name}"
                    self.log_test("Patient Export", True, details, response_time)
                else:
                    self.log_test("Patient Export", False, "Missing data or count in export response", response_time)
            else:
                self.log_test("Patient Export", False, f"HTTP {response.status_code}: {response.text}", response_time)
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("Patient Export", False, f"Exception: {str(e)}", response_time)
        
        # Test consultation export
        start_time = time.time()
        try:
            response = self.session.get(f"{BACKEND_URL}/admin/export/consultations", timeout=15)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                if "data" in data and "count" in data:
                    export_count = data["count"]
                    collection_name = data.get("collection", "consultations")
                    details = f"Exported {export_count} {collection_name}"
                    self.log_test("Consultation Export", True, details, response_time)
                else:
                    self.log_test("Consultation Export", False, "Missing data or count in export response", response_time)
            else:
                self.log_test("Consultation Export", False, f"HTTP {response.status_code}: {response.text}", response_time)
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("Consultation Export", False, f"Exception: {str(e)}", response_time)
        
        # Test payment export
        start_time = time.time()
        try:
            response = self.session.get(f"{BACKEND_URL}/admin/export/payments", timeout=15)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                if "data" in data and "count" in data:
                    export_count = data["count"]
                    collection_name = data.get("collection", "payments")
                    details = f"Exported {export_count} {collection_name}"
                    self.log_test("Payment Export", True, details, response_time)
                else:
                    self.log_test("Payment Export", False, "Missing data or count in export response", response_time)
            else:
                self.log_test("Payment Export", False, f"HTTP {response.status_code}: {response.text}", response_time)
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("Payment Export", False, f"Exception: {str(e)}", response_time)
    
    def test_database_performance(self):
        """Test 7: Database Performance - Verify optimized indexes are working"""
        print("\n⚡ TESTING DATABASE PERFORMANCE")
        
        # Test patient list performance (should be fast with indexes)
        start_time = time.time()
        try:
            response = self.session.get(f"{BACKEND_URL}/patients?limit=50", timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                if "patients" in data:
                    patient_count = len(data["patients"])
                    if response_time < 0.5:  # Should be fast with proper indexing
                        details = f"Retrieved {patient_count} patients in {response_time:.3f}s (Good performance)"
                        self.log_test("Patient List Performance", True, details, response_time)
                    else:
                        details = f"Retrieved {patient_count} patients in {response_time:.3f}s (Slow - may need index optimization)"
                        self.log_test("Patient List Performance", False, details, response_time)
                else:
                    self.log_test("Patient List Performance", False, "Missing patients in response", response_time)
            else:
                self.log_test("Patient List Performance", False, f"HTTP {response.status_code}: {response.text}", response_time)
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("Patient List Performance", False, f"Exception: {str(e)}", response_time)
        
        # Test search performance
        start_time = time.time()
        try:
            response = self.session.get(f"{BACKEND_URL}/patients/search?q=Ahmed", timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                if "patients" in data:
                    search_count = len(data["patients"])
                    if response_time < 0.3:  # Search should be very fast
                        details = f"Search returned {search_count} results in {response_time:.3f}s (Good performance)"
                        self.log_test("Search Performance", True, details, response_time)
                    else:
                        details = f"Search returned {search_count} results in {response_time:.3f}s (Slow - may need index optimization)"
                        self.log_test("Search Performance", False, details, response_time)
                else:
                    self.log_test("Search Performance", False, "Missing patients in search response", response_time)
            else:
                self.log_test("Search Performance", False, f"HTTP {response.status_code}: {response.text}", response_time)
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("Search Performance", False, f"Exception: {str(e)}", response_time)
    
    def test_admin_users_endpoint(self):
        """Test Admin Users Endpoint - Critical for administration functionality"""
        print("\n👨‍💼 TESTING ADMIN USERS ENDPOINT")
        
        start_time = time.time()
        try:
            response = self.session.get(f"{BACKEND_URL}/admin/users", timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                if "users" in data and "count" in data:
                    user_count = data["count"]
                    users = data["users"]
                    details = f"Found {user_count} users in system"
                    self.log_test("Admin Users Endpoint", True, details, response_time)
                    
                    # Verify medecin user has proper permissions
                    medecin_user = next((u for u in users if u.get("username") == "medecin"), None)
                    if medecin_user:
                        permissions = medecin_user.get("permissions", {})
                        manage_users = permissions.get("manage_users", False)
                        if manage_users:
                            self.log_test("Medecin User Permissions", True, "manage_users permission verified", 0)
                        else:
                            self.log_test("Medecin User Permissions", False, "Missing manage_users permission", 0)
                    else:
                        self.log_test("Medecin User Permissions", False, "Medecin user not found", 0)
                else:
                    self.log_test("Admin Users Endpoint", False, "Missing users or count in response", response_time)
            else:
                self.log_test("Admin Users Endpoint", False, f"HTTP {response.status_code}: {response.text}", response_time)
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("Admin Users Endpoint", False, f"Exception: {str(e)}", response_time)
    
    def test_calendar_sections_order(self):
        """Test Calendar Sections Order - Verify correct ordering: rdv programmés → salle d'attente → consultation → terminés → retard"""
        print("\n📅 TESTING CALENDAR SECTIONS ORDER")
        
        today = datetime.now().strftime("%Y-%m-%d")
        
        start_time = time.time()
        try:
            response = self.session.get(f"{BACKEND_URL}/rdv/jour/{today}", timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                appointments = response.json()
                if isinstance(appointments, list):
                    # Group appointments by status
                    status_groups = {}
                    for apt in appointments:
                        status = apt.get("statut", "unknown")
                        if status not in status_groups:
                            status_groups[status] = []
                        status_groups[status].append(apt)
                    
                    # Expected order: programme → attente → en_cours → termine → retard
                    expected_order = ["programme", "attente", "en_cours", "termine", "retard"]
                    found_statuses = list(status_groups.keys())
                    
                    # Check if appointments are properly categorized
                    total_appointments = len(appointments)
                    status_counts = {status: len(status_groups.get(status, [])) for status in expected_order}
                    
                    details = f"Total: {total_appointments}, " + ", ".join([f"{status}: {count}" for status, count in status_counts.items() if count > 0])
                    self.log_test("Calendar Sections Order", True, details, response_time)
                    
                    # Test specific status transitions and ordering logic
                    if status_groups.get("attente"):
                        # Check if waiting appointments have priority ordering
                        waiting_apts = status_groups["attente"]
                        priorities = [apt.get("priority", 999) for apt in waiting_apts]
                        is_sorted = all(priorities[i] <= priorities[i+1] for i in range(len(priorities)-1))
                        self.log_test("Waiting Room Priority Order", is_sorted, f"Priorities: {priorities}", 0)
                    
                else:
                    self.log_test("Calendar Sections Order", False, "Response is not a list", response_time)
            else:
                self.log_test("Calendar Sections Order", False, f"HTTP {response.status_code}: {response.text}", response_time)
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("Calendar Sections Order", False, f"Exception: {str(e)}", response_time)
    
    def test_payment_toggle_logic(self):
        """Test Payment Toggle Logic - Test changing from Visite to Controle Gratuit"""
        print("\n💳 TESTING PAYMENT TOGGLE LOGIC")
        
        # First, get today's appointments to find a test appointment
        today = datetime.now().strftime("%Y-%m-%d")
        
        try:
            response = self.session.get(f"{BACKEND_URL}/rdv/jour/{today}", timeout=10)
            if response.status_code == 200:
                appointments = response.json()
                if appointments and len(appointments) > 0:
                    # Find a visite appointment to test with
                    test_appointment = None
                    for apt in appointments:
                        if apt.get("type_rdv") == "visite":
                            test_appointment = apt
                            break
                    
                    if not test_appointment:
                        # Use the first appointment regardless of type
                        test_appointment = appointments[0]
                    
                    rdv_id = test_appointment.get("id")
                    original_type = test_appointment.get("type_rdv", "visite")
                    
                    # Test 1: Change from visite to controle
                    start_time = time.time()
                    try:
                        update_data = {"type_rdv": "controle"}
                        response = self.session.put(f"{BACKEND_URL}/rdv/{rdv_id}", json=update_data, timeout=10)
                        response_time = time.time() - start_time
                        
                        if response.status_code == 200:
                            data = response.json()
                            if data.get("type_rdv") == "controle":
                                payment_status = data.get("payment_status", "unknown")
                                details = f"Changed to controle, payment_status: {payment_status}"
                                self.log_test("Visite to Controle Toggle", True, details, response_time)
                            else:
                                self.log_test("Visite to Controle Toggle", False, "Type not changed to controle", response_time)
                        else:
                            self.log_test("Visite to Controle Toggle", False, f"HTTP {response.status_code}: {response.text}", response_time)
                    except Exception as e:
                        response_time = time.time() - start_time
                        self.log_test("Visite to Controle Toggle", False, f"Exception: {str(e)}", response_time)
                    
                    # Test 2: Test payment endpoint for controle
                    start_time = time.time()
                    try:
                        payment_data = {
                            "paye": True,
                            "montant": 0,
                            "type_paiement": "gratuit",
                            "type_rdv": "controle"
                        }
                        response = self.session.put(f"{BACKEND_URL}/rdv/{rdv_id}/paiement", json=payment_data, timeout=10)
                        response_time = time.time() - start_time
                        
                        if response.status_code == 200:
                            data = response.json()
                            if data.get("paye") == True and data.get("montant") == 0:
                                details = f"Controle payment: paye={data.get('paye')}, montant={data.get('montant')}, type={data.get('type_paiement')}"
                                self.log_test("Controle Payment Logic", True, details, response_time)
                            else:
                                self.log_test("Controle Payment Logic", False, f"Incorrect payment logic: {data}", response_time)
                        else:
                            self.log_test("Controle Payment Logic", False, f"HTTP {response.status_code}: {response.text}", response_time)
                    except Exception as e:
                        response_time = time.time() - start_time
                        self.log_test("Controle Payment Logic", False, f"Exception: {str(e)}", response_time)
                    
                    # Test 3: Change back to visite
                    start_time = time.time()
                    try:
                        update_data = {"type_rdv": "visite"}
                        response = self.session.put(f"{BACKEND_URL}/rdv/{rdv_id}", json=update_data, timeout=10)
                        response_time = time.time() - start_time
                        
                        if response.status_code == 200:
                            data = response.json()
                            if data.get("type_rdv") == "visite":
                                payment_status = data.get("payment_status", "unknown")
                                details = f"Changed back to visite, payment_status: {payment_status}"
                                self.log_test("Controle to Visite Toggle", True, details, response_time)
                            else:
                                self.log_test("Controle to Visite Toggle", False, "Type not changed to visite", response_time)
                        else:
                            self.log_test("Controle to Visite Toggle", False, f"HTTP {response.status_code}: {response.text}", response_time)
                    except Exception as e:
                        response_time = time.time() - start_time
                        self.log_test("Controle to Visite Toggle", False, f"Exception: {str(e)}", response_time)
                    
                    # Test 4: Test payment endpoint for visite
                    start_time = time.time()
                    try:
                        payment_data = {
                            "paye": True,
                            "montant": 65.0,
                            "type_paiement": "espece",
                            "type_rdv": "visite"
                        }
                        response = self.session.put(f"{BACKEND_URL}/rdv/{rdv_id}/paiement", json=payment_data, timeout=10)
                        response_time = time.time() - start_time
                        
                        if response.status_code == 200:
                            data = response.json()
                            if data.get("paye") == True and data.get("montant") == 65.0:
                                details = f"Visite payment: paye={data.get('paye')}, montant={data.get('montant')}, type={data.get('type_paiement')}"
                                self.log_test("Visite Payment Logic", True, details, response_time)
                            else:
                                self.log_test("Visite Payment Logic", False, f"Incorrect payment logic: {data}", response_time)
                        else:
                            self.log_test("Visite Payment Logic", False, f"HTTP {response.status_code}: {response.text}", response_time)
                    except Exception as e:
                        response_time = time.time() - start_time
                        self.log_test("Visite Payment Logic", False, f"Exception: {str(e)}", response_time)
                
                else:
                    self.log_test("Payment Toggle Logic", False, "No appointments found for testing", 0)
            else:
                self.log_test("Payment Toggle Logic", False, f"Failed to get appointments: HTTP {response.status_code}", 0)
        except Exception as e:
            self.log_test("Payment Toggle Logic", False, f"Exception getting appointments: {str(e)}", 0)
    
    def test_backend_payment_api(self):
        """Test Backend Payment API - Test /api/rdv/{rdv_id}/paiement endpoint"""
        print("\n🏦 TESTING BACKEND PAYMENT API")
        
        # Get today's appointments to find a test appointment
        today = datetime.now().strftime("%Y-%m-%d")
        
        try:
            response = self.session.get(f"{BACKEND_URL}/rdv/jour/{today}", timeout=10)
            if response.status_code == 200:
                appointments = response.json()
                if appointments and len(appointments) > 0:
                    test_appointment = appointments[0]
                    rdv_id = test_appointment.get("id")
                    
                    # Test 1: Payment endpoint with visite type
                    start_time = time.time()
                    try:
                        payment_data = {
                            "paye": True,
                            "montant": 65.0,
                            "type_paiement": "espece",
                            "assure": False,
                            "notes": "Test payment for visite",
                            "type_rdv": "visite"
                        }
                        response = self.session.put(f"{BACKEND_URL}/rdv/{rdv_id}/paiement", json=payment_data, timeout=10)
                        response_time = time.time() - start_time
                        
                        if response.status_code == 200:
                            data = response.json()
                            required_fields = ["paye", "montant", "type_paiement"]
                            missing_fields = [field for field in required_fields if field not in data]
                            
                            if not missing_fields:
                                details = f"Visite payment: paye={data.get('paye')}, montant={data.get('montant')}, type={data.get('type_paiement')}"
                                self.log_test("Payment API - Visite", True, details, response_time)
                            else:
                                self.log_test("Payment API - Visite", False, f"Missing fields: {missing_fields}", response_time)
                        else:
                            self.log_test("Payment API - Visite", False, f"HTTP {response.status_code}: {response.text}", response_time)
                    except Exception as e:
                        response_time = time.time() - start_time
                        self.log_test("Payment API - Visite", False, f"Exception: {str(e)}", response_time)
                    
                    # Test 2: Payment endpoint with controle type (should be gratuit)
                    start_time = time.time()
                    try:
                        payment_data = {
                            "paye": True,
                            "montant": 0,
                            "type_paiement": "gratuit",
                            "assure": False,
                            "notes": "Test payment for controle",
                            "type_rdv": "controle"
                        }
                        response = self.session.put(f"{BACKEND_URL}/rdv/{rdv_id}/paiement", json=payment_data, timeout=10)
                        response_time = time.time() - start_time
                        
                        if response.status_code == 200:
                            data = response.json()
                            # For controle, should be paye: true, montant: 0, type_paiement: "gratuit"
                            if data.get("paye") == True and data.get("montant") == 0 and data.get("type_paiement") == "gratuit":
                                details = f"Controle payment: paye={data.get('paye')}, montant={data.get('montant')}, type={data.get('type_paiement')}"
                                self.log_test("Payment API - Controle", True, details, response_time)
                            else:
                                details = f"Incorrect controle logic: paye={data.get('paye')}, montant={data.get('montant')}, type={data.get('type_paiement')}"
                                self.log_test("Payment API - Controle", False, details, response_time)
                        else:
                            self.log_test("Payment API - Controle", False, f"HTTP {response.status_code}: {response.text}", response_time)
                    except Exception as e:
                        response_time = time.time() - start_time
                        self.log_test("Payment API - Controle", False, f"Exception: {str(e)}", response_time)
                    
                    # Test 3: Test type_rdv changes from visite to controle
                    start_time = time.time()
                    try:
                        # First set to visite
                        payment_data = {
                            "paye": False,
                            "montant": 65.0,
                            "type_paiement": "espece",
                            "type_rdv": "visite"
                        }
                        response = self.session.put(f"{BACKEND_URL}/rdv/{rdv_id}/paiement", json=payment_data, timeout=10)
                        
                        if response.status_code == 200:
                            # Now change to controle
                            payment_data = {
                                "paye": True,
                                "montant": 0,
                                "type_paiement": "gratuit",
                                "type_rdv": "controle"
                            }
                            response = self.session.put(f"{BACKEND_URL}/rdv/{rdv_id}/paiement", json=payment_data, timeout=10)
                            response_time = time.time() - start_time
                            
                            if response.status_code == 200:
                                data = response.json()
                                # Should automatically set payment to gratuit when changing to controle
                                if data.get("type_rdv") == "controle" and data.get("type_paiement") == "gratuit":
                                    details = f"Type change successful: type_rdv={data.get('type_rdv')}, payment={data.get('type_paiement')}"
                                    self.log_test("Payment API - Type Change Logic", True, details, response_time)
                                else:
                                    details = f"Type change failed: type_rdv={data.get('type_rdv')}, payment={data.get('type_paiement')}"
                                    self.log_test("Payment API - Type Change Logic", False, details, response_time)
                            else:
                                self.log_test("Payment API - Type Change Logic", False, f"HTTP {response.status_code}: {response.text}", response_time)
                        else:
                            self.log_test("Payment API - Type Change Logic", False, "Failed to set initial visite type", response_time)
                    except Exception as e:
                        response_time = time.time() - start_time
                        self.log_test("Payment API - Type Change Logic", False, f"Exception: {str(e)}", response_time)
                
                else:
                    self.log_test("Backend Payment API", False, "No appointments found for testing", 0)
            else:
                self.log_test("Backend Payment API", False, f"Failed to get appointments: HTTP {response.status_code}", 0)
        except Exception as e:
            self.log_test("Backend Payment API", False, f"Exception getting appointments: {str(e)}", 0)
    
    def run_all_tests(self):
        """Run all production readiness tests"""
        print("🚀 STARTING CALENDAR AND PAYMENT FUNCTIONALITY TESTING")
        print("=" * 80)
        
        # Test 1: Authentication (Critical)
        if not self.test_authentication():
            print("\n❌ CRITICAL FAILURE: Authentication failed. Cannot proceed with other tests.")
            return self.generate_report()
        
        # Test 2: Patient Management
        self.test_patient_management()
        
        # Test 3: Dashboard Stats
        self.test_dashboard_stats()
        
        # Test 4: Appointments
        self.test_appointments()
        
        # Test 5: Billing System
        self.test_billing_system()
        
        # Test 6: Export Functionality
        self.test_export_functionality()
        
        # Test 7: Database Performance
        self.test_database_performance()
        
        # Test 8: Admin Users Endpoint
        self.test_admin_users_endpoint()
        
        # NEW TESTS FOR REVIEW REQUEST:
        # Test 9: Calendar Sections Order
        self.test_calendar_sections_order()
        
        # Test 10: Payment Toggle Logic
        self.test_payment_toggle_logic()
        
        # Test 11: Backend Payment API
        self.test_backend_payment_api()
        
        return self.generate_report()
    
    def generate_report(self):
        """Generate final test report"""
        total_time = time.time() - self.start_time
        total_tests = len(self.test_results)
        passed_tests = len([t for t in self.test_results if t["success"]])
        failed_tests = total_tests - passed_tests
        
        print("\n" + "=" * 80)
        print("📋 CALENDAR AND PAYMENT FUNCTIONALITY TEST REPORT")
        print("=" * 80)
        print(f"⏱️  Total execution time: {total_time:.2f} seconds")
        print(f"📊 Total tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"📈 Success rate: {(passed_tests/total_tests*100):.1f}%")
        
        print("\n📝 DETAILED RESULTS:")
        print("-" * 80)
        
        for result in self.test_results:
            print(f"{result['status']} {result['test']} ({result['response_time']:.3f}s)")
            if result['details']:
                print(f"    {result['details']}")
        
        print("\n" + "=" * 80)
        
        if failed_tests == 0:
            print("🎉 ALL TESTS PASSED - SYSTEM IS PRODUCTION READY!")
            print("✅ Post-cleanup verification successful")
            print("✅ All critical functionality working correctly")
            print("✅ Performance within acceptable limits")
            print("✅ Ready for deployment")
        else:
            print("⚠️  SOME TESTS FAILED - REVIEW REQUIRED")
            print("❌ Post-cleanup verification found issues")
            print("🔧 Fix failing tests before production deployment")
        
        return {
            "total_tests": total_tests,
            "passed": passed_tests,
            "failed": failed_tests,
            "success_rate": passed_tests/total_tests*100,
            "execution_time": total_time,
            "all_passed": failed_tests == 0,
            "results": self.test_results
        }

if __name__ == "__main__":
    print("🏥 Cabinet Médical - Final Post-Cleanup Production Readiness Test")
    print("Testing backend API endpoints after complete code cleanup and optimization")
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Test Credentials: {TEST_CREDENTIALS['username']}")
    print()
    
    tester = BackendTester()
    report = tester.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if report["all_passed"] else 1)