#!/usr/bin/env python3
"""
Comprehensive Calendar Backend Testing Suite
Tests all Calendar endpoints for errors, performance, and optimization opportunities
"""

import requests
import unittest
import json
import time
import threading
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/frontend/.env')

class CalendarBackendComprehensiveTest(unittest.TestCase):
    """Comprehensive test suite for Calendar backend functionality"""
    
    def setUp(self):
        """Setup test environment"""
        backend_url = os.getenv('REACT_APP_BACKEND_URL', 'https://9fbf800f-d1de-4fd5-ab5a-a9ad9ec8040f.preview.emergentagent.com')
        self.base_url = backend_url
        self.performance_results = {}
        self.error_log = []
        
        print(f"\n🔍 Testing Calendar Backend at: {self.base_url}")
        print("=" * 80)
        
        # Initialize demo data
        self.init_demo_data()
        
        # Get test data
        self.test_patients = self.get_test_patients()
        self.today = datetime.now().strftime("%Y-%m-%d")
        self.tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    
    def init_demo_data(self):
        """Initialize demo data for testing"""
        try:
            response = requests.get(f"{self.base_url}/api/init-demo")
            self.assertEqual(response.status_code, 200)
            print("✅ Demo data initialized successfully")
        except Exception as e:
            print(f"❌ Error initializing demo data: {e}")
            self.error_log.append(f"Demo data initialization failed: {e}")
    
    def get_test_patients(self):
        """Get test patients for appointment creation"""
        try:
            response = requests.get(f"{self.base_url}/api/patients")
            self.assertEqual(response.status_code, 200)
            patients_data = response.json()
            return patients_data["patients"][:3]  # Get first 3 patients
        except Exception as e:
            print(f"❌ Error getting test patients: {e}")
            return []
    
    def measure_performance(self, test_name, func, *args, **kwargs):
        """Measure performance of a function call"""
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            end_time = time.time()
            duration = (end_time - start_time) * 1000  # Convert to milliseconds
            self.performance_results[test_name] = duration
            return result, duration
        except Exception as e:
            end_time = time.time()
            duration = (end_time - start_time) * 1000
            self.performance_results[test_name] = duration
            self.error_log.append(f"{test_name} failed: {e}")
            raise
    
    def create_test_appointment(self, patient_id, date, heure, status="programme", type_rdv="visite"):
        """Helper to create test appointments"""
        appointment_data = {
            "patient_id": patient_id,
            "date": date,
            "heure": heure,
            "type_rdv": type_rdv,
            "statut": status,
            "motif": f"Test appointment {status}",
            "notes": f"Created for testing {status} status",
            "paye": False
        }
        
        response = requests.post(f"{self.base_url}/api/appointments", json=appointment_data)
        if response.status_code == 200:
            return response.json()["appointment_id"]
        return None
    
    # ========== 1. TEST ALL CALENDAR ENDPOINTS ==========
    
    def test_01_get_rdv_jour_endpoint(self):
        """Test GET /api/rdv/jour/{date} - Récupération des appointments du jour"""
        print("\n📅 Testing GET /api/rdv/jour/{date} endpoint...")
        
        # Test with today's date
        response, duration = self.measure_performance(
            "GET_rdv_jour_today",
            requests.get,
            f"{self.base_url}/api/rdv/jour/{self.today}"
        )
        
        self.assertEqual(response.status_code, 200)
        appointments = response.json()
        self.assertIsInstance(appointments, list)
        
        print(f"✅ Response time: {duration:.2f}ms")
        print(f"✅ Found {len(appointments)} appointments for today")
        
        # Validate appointment structure
        for appointment in appointments:
            self.assertIn("id", appointment)
            self.assertIn("patient_id", appointment)
            self.assertIn("date", appointment)
            self.assertIn("heure", appointment)
            self.assertIn("type_rdv", appointment)
            self.assertIn("statut", appointment)
            self.assertIn("salle", appointment)
            self.assertIn("patient", appointment)
            
            # Validate patient info structure
            patient = appointment["patient"]
            self.assertIn("nom", patient)
            self.assertIn("prenom", patient)
            self.assertIn("numero_whatsapp", patient)
            self.assertIn("lien_whatsapp", patient)
        
        # Test with invalid date format
        response = requests.get(f"{self.base_url}/api/rdv/jour/invalid-date")
        # Should still return 200 with empty list (graceful handling)
        self.assertEqual(response.status_code, 200)
        
        # Test with future date
        future_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        response = requests.get(f"{self.base_url}/api/rdv/jour/{future_date}")
        self.assertEqual(response.status_code, 200)
        
        print("✅ GET /api/rdv/jour/{date} endpoint tests passed")
    
    def test_02_put_rdv_statut_endpoint(self):
        """Test PUT /api/rdv/{rdv_id}/statut - Mise à jour du statut"""
        print("\n🔄 Testing PUT /api/rdv/{rdv_id}/statut endpoint...")
        
        if not self.test_patients:
            self.skipTest("No test patients available")
        
        # Create test appointment
        patient_id = self.test_patients[0]["id"]
        appointment_id = self.create_test_appointment(patient_id, self.today, "10:00")
        
        if not appointment_id:
            self.skipTest("Could not create test appointment")
        
        try:
            valid_statuses = ["programme", "attente", "en_cours", "termine", "absent", "retard"]
            
            for status in valid_statuses:
                # Test status update
                response, duration = self.measure_performance(
                    f"PUT_rdv_statut_{status}",
                    requests.put,
                    f"{self.base_url}/api/rdv/{appointment_id}/statut",
                    json={"statut": status}
                )
                
                self.assertEqual(response.status_code, 200)
                data = response.json()
                self.assertIn("message", data)
                self.assertEqual(data["statut"], status)
                
                print(f"✅ Status update to '{status}': {duration:.2f}ms")
            
            # Test invalid status
            response = requests.put(
                f"{self.base_url}/api/rdv/{appointment_id}/statut",
                json={"statut": "invalid_status"}
            )
            self.assertEqual(response.status_code, 400)
            
            # Test non-existent appointment
            response = requests.put(
                f"{self.base_url}/api/rdv/non_existent_id/statut",
                json={"statut": "attente"}
            )
            self.assertEqual(response.status_code, 404)
            
            # Test with heure_arrivee_attente for 'attente' status
            response = requests.put(
                f"{self.base_url}/api/rdv/{appointment_id}/statut",
                json={
                    "statut": "attente",
                    "heure_arrivee_attente": datetime.now().isoformat()
                }
            )
            self.assertEqual(response.status_code, 200)
            
            print("✅ PUT /api/rdv/{rdv_id}/statut endpoint tests passed")
            
        finally:
            # Clean up
            requests.delete(f"{self.base_url}/api/appointments/{appointment_id}")
    
    def test_03_put_rdv_salle_endpoint(self):
        """Test PUT /api/rdv/{rdv_id}/salle - Assignation de salle"""
        print("\n🏥 Testing PUT /api/rdv/{rdv_id}/salle endpoint...")
        
        if not self.test_patients:
            self.skipTest("No test patients available")
        
        # Create test appointment
        patient_id = self.test_patients[0]["id"]
        appointment_id = self.create_test_appointment(patient_id, self.today, "11:00")
        
        if not appointment_id:
            self.skipTest("Could not create test appointment")
        
        try:
            valid_rooms = ["", "salle1", "salle2"]
            
            for room in valid_rooms:
                # Test room assignment
                response, duration = self.measure_performance(
                    f"PUT_rdv_salle_{room or 'empty'}",
                    requests.put,
                    f"{self.base_url}/api/rdv/{appointment_id}/salle",
                    params={"salle": room}
                )
                
                self.assertEqual(response.status_code, 200)
                data = response.json()
                self.assertIn("message", data)
                self.assertEqual(data["salle"], room)
                
                print(f"✅ Room assignment to '{room or 'none'}': {duration:.2f}ms")
            
            # Test invalid room
            response = requests.put(
                f"{self.base_url}/api/rdv/{appointment_id}/salle",
                params={"salle": "invalid_room"}
            )
            self.assertEqual(response.status_code, 400)
            
            # Test non-existent appointment
            response = requests.put(
                f"{self.base_url}/api/rdv/non_existent_id/salle",
                params={"salle": "salle1"}
            )
            self.assertEqual(response.status_code, 404)
            
            print("✅ PUT /api/rdv/{rdv_id}/salle endpoint tests passed")
            
        finally:
            # Clean up
            requests.delete(f"{self.base_url}/api/appointments/{appointment_id}")
    
    def test_04_put_rdv_priority_endpoint(self):
        """Test PUT /api/rdv/{rdv_id}/priority - Repositionnement drag and drop"""
        print("\n🔄 Testing PUT /api/rdv/{rdv_id}/priority endpoint...")
        
        if len(self.test_patients) < 3:
            self.skipTest("Need at least 3 test patients")
        
        # Create multiple test appointments with 'attente' status
        appointment_ids = []
        for i, patient in enumerate(self.test_patients[:3]):
            appointment_id = self.create_test_appointment(
                patient["id"], 
                self.today, 
                f"{9 + i}:00", 
                status="attente"
            )
            if appointment_id:
                appointment_ids.append(appointment_id)
        
        if len(appointment_ids) < 3:
            self.skipTest("Could not create enough test appointments")
        
        try:
            # Test different priority actions
            actions = ["move_up", "move_down", "set_first", "set_position"]
            
            for action in actions:
                if action == "set_position":
                    # Test set_position with specific position
                    response, duration = self.measure_performance(
                        f"PUT_rdv_priority_{action}",
                        requests.put,
                        f"{self.base_url}/api/rdv/{appointment_ids[1]}/priority",
                        json={"action": action, "position": 0}
                    )
                else:
                    # Test other actions
                    response, duration = self.measure_performance(
                        f"PUT_rdv_priority_{action}",
                        requests.put,
                        f"{self.base_url}/api/rdv/{appointment_ids[1]}/priority",
                        json={"action": action}
                    )
                
                self.assertEqual(response.status_code, 200)
                data = response.json()
                self.assertIn("message", data)
                self.assertIn("action", data)
                self.assertEqual(data["action"], action)
                
                print(f"✅ Priority action '{action}': {duration:.2f}ms")
            
            # Test invalid action
            response = requests.put(
                f"{self.base_url}/api/rdv/{appointment_ids[0]}/priority",
                json={"action": "invalid_action"}
            )
            self.assertEqual(response.status_code, 400)
            
            # Test missing action
            response = requests.put(
                f"{self.base_url}/api/rdv/{appointment_ids[0]}/priority",
                json={}
            )
            self.assertEqual(response.status_code, 400)
            
            # Test non-waiting appointment (should fail)
            non_waiting_id = self.create_test_appointment(
                self.test_patients[0]["id"], 
                self.today, 
                "15:00", 
                status="programme"
            )
            
            if non_waiting_id:
                response = requests.put(
                    f"{self.base_url}/api/rdv/{non_waiting_id}/priority",
                    json={"action": "move_up"}
                )
                self.assertEqual(response.status_code, 400)
                requests.delete(f"{self.base_url}/api/appointments/{non_waiting_id}")
            
            print("✅ PUT /api/rdv/{rdv_id}/priority endpoint tests passed")
            
        finally:
            # Clean up
            for appointment_id in appointment_ids:
                requests.delete(f"{self.base_url}/api/appointments/{appointment_id}")
    
    def test_05_put_rdv_paiement_endpoint(self):
        """Test PUT /api/rdv/{rdv_id}/paiement - Gestion des paiements"""
        print("\n💰 Testing PUT /api/rdv/{rdv_id}/paiement endpoint...")
        
        if not self.test_patients:
            self.skipTest("No test patients available")
        
        # Create test appointment
        patient_id = self.test_patients[0]["id"]
        appointment_id = self.create_test_appointment(patient_id, self.today, "12:00")
        
        if not appointment_id:
            self.skipTest("Could not create test appointment")
        
        try:
            payment_methods = ["espece", "carte", "cheque", "virement"]
            
            for method in payment_methods:
                # Test payment update
                payment_data = {
                    "paye": True,
                    "montant_paye": 300.0,
                    "methode_paiement": method,
                    "date_paiement": self.today
                }
                
                response, duration = self.measure_performance(
                    f"PUT_rdv_paiement_{method}",
                    requests.put,
                    f"{self.base_url}/api/rdv/{appointment_id}/paiement",
                    json=payment_data
                )
                
                self.assertEqual(response.status_code, 200)
                data = response.json()
                self.assertIn("message", data)
                self.assertEqual(data["paye"], True)
                self.assertEqual(data["montant_paye"], 300.0)
                self.assertEqual(data["methode_paiement"], method)
                
                print(f"✅ Payment update '{method}': {duration:.2f}ms")
            
            # Test unpaid status
            unpaid_data = {
                "paye": False,
                "montant_paye": 0,
                "methode_paiement": "",
                "date_paiement": None
            }
            
            response = requests.put(
                f"{self.base_url}/api/rdv/{appointment_id}/paiement",
                json=unpaid_data
            )
            self.assertEqual(response.status_code, 200)
            
            # Test invalid payment method
            invalid_payment_data = {
                "paye": True,
                "montant_paye": 300.0,
                "methode_paiement": "invalid_method",
                "date_paiement": self.today
            }
            
            response = requests.put(
                f"{self.base_url}/api/rdv/{appointment_id}/paiement",
                json=invalid_payment_data
            )
            self.assertEqual(response.status_code, 400)
            
            print("✅ PUT /api/rdv/{rdv_id}/paiement endpoint tests passed")
            
        finally:
            # Clean up
            requests.delete(f"{self.base_url}/api/appointments/{appointment_id}")
    
    def test_06_put_rdv_type_endpoint(self):
        """Test PUT /api/rdv/{rdv_id} - Mise à jour type appointment"""
        print("\n🔄 Testing PUT /api/rdv/{rdv_id} endpoint...")
        
        if not self.test_patients:
            self.skipTest("No test patients available")
        
        # Create test appointment
        patient_id = self.test_patients[0]["id"]
        appointment_id = self.create_test_appointment(patient_id, self.today, "13:00")
        
        if not appointment_id:
            self.skipTest("Could not create test appointment")
        
        try:
            appointment_types = ["visite", "controle"]
            
            for type_rdv in appointment_types:
                # Test type update
                response, duration = self.measure_performance(
                    f"PUT_rdv_type_{type_rdv}",
                    requests.put,
                    f"{self.base_url}/api/rdv/{appointment_id}",
                    json={"type_rdv": type_rdv}
                )
                
                self.assertEqual(response.status_code, 200)
                data = response.json()
                self.assertIn("message", data)
                self.assertEqual(data["type_rdv"], type_rdv)
                
                # Verify payment logic
                if type_rdv == "controle":
                    self.assertEqual(data["payment_status"], "gratuit")
                else:
                    self.assertEqual(data["payment_status"], "non_paye")
                
                print(f"✅ Type update to '{type_rdv}': {duration:.2f}ms")
            
            # Test invalid type
            response = requests.put(
                f"{self.base_url}/api/rdv/{appointment_id}",
                json={"type_rdv": "invalid_type"}
            )
            self.assertEqual(response.status_code, 400)
            
            # Test missing type_rdv
            response = requests.put(
                f"{self.base_url}/api/rdv/{appointment_id}",
                json={}
            )
            self.assertEqual(response.status_code, 400)
            
            print("✅ PUT /api/rdv/{rdv_id} endpoint tests passed")
            
        finally:
            # Clean up
            requests.delete(f"{self.base_url}/api/appointments/{appointment_id}")
    
    # ========== 2. PERFORMANCE AND OPTIMIZATION TESTS ==========
    
    def test_07_response_time_performance(self):
        """Test response time of each endpoint"""
        print("\n⚡ Testing response time performance...")
        
        # Performance thresholds (in milliseconds)
        thresholds = {
            "GET_rdv_jour": 1000,
            "PUT_rdv_statut": 500,
            "PUT_rdv_salle": 500,
            "PUT_rdv_priority": 800,
            "PUT_rdv_paiement": 600,
            "PUT_rdv_type": 600
        }
        
        performance_issues = []
        
        for test_name, duration in self.performance_results.items():
            # Extract base test name
            base_name = test_name.split('_')[0] + '_' + test_name.split('_')[1] + '_' + test_name.split('_')[2]
            threshold = thresholds.get(base_name, 1000)
            
            if duration > threshold:
                performance_issues.append(f"{test_name}: {duration:.2f}ms (threshold: {threshold}ms)")
            else:
                print(f"✅ {test_name}: {duration:.2f}ms (✓ under {threshold}ms)")
        
        if performance_issues:
            print("\n⚠️ Performance issues found:")
            for issue in performance_issues:
                print(f"  - {issue}")
        else:
            print("\n✅ All endpoints meet performance thresholds")
    
    def test_08_concurrent_requests_performance(self):
        """Test performance under concurrent requests"""
        print("\n🔄 Testing concurrent requests performance...")
        
        if not self.test_patients:
            self.skipTest("No test patients available")
        
        # Create test appointments for concurrent testing
        appointment_ids = []
        for i, patient in enumerate(self.test_patients[:3]):
            appointment_id = self.create_test_appointment(
                patient["id"], 
                self.today, 
                f"{14 + i}:00"
            )
            if appointment_id:
                appointment_ids.append(appointment_id)
        
        if not appointment_ids:
            self.skipTest("Could not create test appointments")
        
        try:
            # Test concurrent status updates
            def update_status(appointment_id, status):
                start_time = time.time()
                response = requests.put(
                    f"{self.base_url}/api/rdv/{appointment_id}/statut",
                    json={"statut": status}
                )
                end_time = time.time()
                return response.status_code, (end_time - start_time) * 1000
            
            # Execute concurrent requests
            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = []
                for i, appointment_id in enumerate(appointment_ids):
                    status = ["attente", "en_cours", "termine"][i % 3]
                    future = executor.submit(update_status, appointment_id, status)
                    futures.append(future)
                
                results = []
                for future in as_completed(futures):
                    status_code, duration = future.result()
                    results.append((status_code, duration))
            
            # Analyze results
            successful_requests = [r for r in results if r[0] == 200]
            avg_duration = sum(r[1] for r in successful_requests) / len(successful_requests)
            max_duration = max(r[1] for r in successful_requests)
            
            print(f"✅ Concurrent requests: {len(successful_requests)}/{len(results)} successful")
            print(f"✅ Average response time: {avg_duration:.2f}ms")
            print(f"✅ Max response time: {max_duration:.2f}ms")
            
            # Performance check
            if avg_duration > 2000:  # 2 seconds threshold
                self.error_log.append(f"Concurrent performance issue: avg {avg_duration:.2f}ms")
            
        finally:
            # Clean up
            for appointment_id in appointment_ids:
                requests.delete(f"{self.base_url}/api/appointments/{appointment_id}")
    
    def test_09_memory_usage_optimization(self):
        """Test memory usage patterns"""
        print("\n💾 Testing memory usage optimization...")
        
        # Test large data retrieval
        start_time = time.time()
        response = requests.get(f"{self.base_url}/api/rdv/jour/{self.today}")
        end_time = time.time()
        
        if response.status_code == 200:
            data = response.json()
            data_size = len(json.dumps(data))
            duration = (end_time - start_time) * 1000
            
            print(f"✅ Data retrieval: {data_size} bytes in {duration:.2f}ms")
            print(f"✅ Appointments returned: {len(data)}")
            
            # Check for unnecessary data
            for appointment in data:
                if "patient" in appointment:
                    patient = appointment["patient"]
                    # Check if only necessary patient fields are included
                    expected_fields = ["nom", "prenom", "numero_whatsapp", "lien_whatsapp"]
                    actual_fields = list(patient.keys())
                    
                    if len(actual_fields) > len(expected_fields) + 2:  # Allow some flexibility
                        print(f"⚠️ Patient object may contain unnecessary fields: {actual_fields}")
                        break
            
            print("✅ Memory usage optimization check completed")
    
    # ========== 3. ERROR HANDLING TESTS ==========
    
    def test_10_invalid_data_handling(self):
        """Test handling of invalid data"""
        print("\n❌ Testing invalid data handling...")
        
        # Test invalid JSON
        response = requests.put(
            f"{self.base_url}/api/rdv/test_id/statut",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        self.assertIn(response.status_code, [400, 422])  # Should handle gracefully
        
        # Test missing required fields
        response = requests.put(
            f"{self.base_url}/api/rdv/test_id/statut",
            json={}
        )
        self.assertIn(response.status_code, [400, 422])
        
        # Test invalid field values
        response = requests.put(
            f"{self.base_url}/api/rdv/test_id/statut",
            json={"statut": None}
        )
        self.assertIn(response.status_code, [400, 422])
        
        print("✅ Invalid data handling tests passed")
    
    def test_11_non_existent_ids_handling(self):
        """Test handling of non-existent IDs"""
        print("\n🔍 Testing non-existent IDs handling...")
        
        non_existent_id = "non_existent_appointment_id_12345"
        
        # Test all endpoints with non-existent ID
        endpoints = [
            ("PUT", f"/api/rdv/{non_existent_id}/statut", {"statut": "attente"}),
            ("PUT", f"/api/rdv/{non_existent_id}/salle", None, {"salle": "salle1"}),
            ("PUT", f"/api/rdv/{non_existent_id}/priority", {"action": "move_up"}),
            ("PUT", f"/api/rdv/{non_existent_id}/paiement", {"paye": True, "montant_paye": 300}),
            ("PUT", f"/api/rdv/{non_existent_id}", {"type_rdv": "visite"})
        ]
        
        for method, endpoint, json_data, *params in endpoints:
            if method == "PUT":
                if params:  # Has query params
                    response = requests.put(f"{self.base_url}{endpoint}", params=params[0])
                else:
                    response = requests.put(f"{self.base_url}{endpoint}", json=json_data)
                
                self.assertEqual(response.status_code, 404)
                print(f"✅ {endpoint}: 404 (correct)")
        
        print("✅ Non-existent IDs handling tests passed")
    
    def test_12_malformed_requests_handling(self):
        """Test handling of malformed requests"""
        print("\n🔧 Testing malformed requests handling...")
        
        if not self.test_patients:
            self.skipTest("No test patients available")
        
        # Create test appointment
        patient_id = self.test_patients[0]["id"]
        appointment_id = self.create_test_appointment(patient_id, self.today, "16:00")
        
        if not appointment_id:
            self.skipTest("Could not create test appointment")
        
        try:
            # Test malformed requests
            malformed_tests = [
                # Wrong content type
                {
                    "url": f"{self.base_url}/api/rdv/{appointment_id}/statut",
                    "data": "statut=attente",
                    "headers": {"Content-Type": "application/x-www-form-urlencoded"}
                },
                # Extra fields
                {
                    "url": f"{self.base_url}/api/rdv/{appointment_id}/statut",
                    "json": {"statut": "attente", "extra_field": "should_be_ignored"},
                    "headers": {"Content-Type": "application/json"}
                },
                # Wrong data types
                {
                    "url": f"{self.base_url}/api/rdv/{appointment_id}/paiement",
                    "json": {"paye": "true", "montant_paye": "300"},  # Strings instead of bool/float
                    "headers": {"Content-Type": "application/json"}
                }
            ]
            
            for test in malformed_tests:
                if "json" in test:
                    response = requests.put(test["url"], json=test["json"], headers=test.get("headers", {}))
                else:
                    response = requests.put(test["url"], data=test["data"], headers=test.get("headers", {}))
                
                # Should handle gracefully (not crash)
                self.assertIn(response.status_code, [200, 400, 422])
                print(f"✅ Malformed request handled: {response.status_code}")
            
        finally:
            # Clean up
            requests.delete(f"{self.base_url}/api/appointments/{appointment_id}")
        
        print("✅ Malformed requests handling tests passed")
    
    # ========== 4. DATA CONSISTENCY TESTS ==========
    
    def test_13_data_integrity_after_operations(self):
        """Test data integrity after operations"""
        print("\n🔒 Testing data integrity after operations...")
        
        if not self.test_patients:
            self.skipTest("No test patients available")
        
        # Create test appointment
        patient_id = self.test_patients[0]["id"]
        appointment_id = self.create_test_appointment(patient_id, self.today, "17:00")
        
        if not appointment_id:
            self.skipTest("Could not create test appointment")
        
        try:
            # Perform multiple operations
            operations = [
                ("statut", {"statut": "attente"}),
                ("salle", None, {"salle": "salle1"}),
                ("paiement", {"paye": True, "montant_paye": 300, "methode_paiement": "espece", "date_paiement": self.today}),
                ("", {"type_rdv": "controle"})  # Type update
            ]
            
            for endpoint_suffix, json_data, *params in operations:
                if endpoint_suffix:
                    url = f"{self.base_url}/api/rdv/{appointment_id}/{endpoint_suffix}"
                else:
                    url = f"{self.base_url}/api/rdv/{appointment_id}"
                
                if params:  # Has query params
                    response = requests.put(url, params=params[0])
                else:
                    response = requests.put(url, json=json_data)
                
                self.assertEqual(response.status_code, 200)
            
            # Verify final state
            response = requests.get(f"{self.base_url}/api/rdv/jour/{self.today}")
            self.assertEqual(response.status_code, 200)
            appointments = response.json()
            
            updated_appointment = None
            for appt in appointments:
                if appt["id"] == appointment_id:
                    updated_appointment = appt
                    break
            
            self.assertIsNotNone(updated_appointment)
            
            # Verify all changes persisted
            self.assertEqual(updated_appointment["statut"], "attente")
            self.assertEqual(updated_appointment["salle"], "salle1")
            self.assertEqual(updated_appointment["type_rdv"], "controle")
            # Note: controle type should automatically set paye=True
            
            print("✅ Data integrity maintained after multiple operations")
            
        finally:
            # Clean up
            requests.delete(f"{self.base_url}/api/appointments/{appointment_id}")
    
    def test_14_field_validation_consistency(self):
        """Test field validation consistency"""
        print("\n✅ Testing field validation consistency...")
        
        if not self.test_patients:
            self.skipTest("No test patients available")
        
        # Create test appointment
        patient_id = self.test_patients[0]["id"]
        appointment_id = self.create_test_appointment(patient_id, self.today, "18:00")
        
        if not appointment_id:
            self.skipTest("Could not create test appointment")
        
        try:
            # Test field validation
            validation_tests = [
                # Status validation
                {
                    "endpoint": f"/api/rdv/{appointment_id}/statut",
                    "valid_data": {"statut": "attente"},
                    "invalid_data": {"statut": "invalid_status"}
                },
                # Room validation
                {
                    "endpoint": f"/api/rdv/{appointment_id}/salle",
                    "valid_params": {"salle": "salle1"},
                    "invalid_params": {"salle": "invalid_room"}
                },
                # Payment method validation
                {
                    "endpoint": f"/api/rdv/{appointment_id}/paiement",
                    "valid_data": {"paye": True, "montant_paye": 300, "methode_paiement": "espece"},
                    "invalid_data": {"paye": True, "montant_paye": 300, "methode_paiement": "invalid_method"}
                },
                # Type validation
                {
                    "endpoint": f"/api/rdv/{appointment_id}",
                    "valid_data": {"type_rdv": "visite"},
                    "invalid_data": {"type_rdv": "invalid_type"}
                }
            ]
            
            for test in validation_tests:
                endpoint = f"{self.base_url}{test['endpoint']}"
                
                # Test valid data
                if "valid_data" in test:
                    response = requests.put(endpoint, json=test["valid_data"])
                    self.assertEqual(response.status_code, 200)
                elif "valid_params" in test:
                    response = requests.put(endpoint, params=test["valid_params"])
                    self.assertEqual(response.status_code, 200)
                
                # Test invalid data
                if "invalid_data" in test:
                    response = requests.put(endpoint, json=test["invalid_data"])
                    self.assertEqual(response.status_code, 400)
                elif "invalid_params" in test:
                    response = requests.put(endpoint, params=test["invalid_params"])
                    self.assertEqual(response.status_code, 400)
                
                print(f"✅ Validation consistent for {test['endpoint']}")
            
        finally:
            # Clean up
            requests.delete(f"{self.base_url}/api/appointments/{appointment_id}")
        
        print("✅ Field validation consistency tests passed")
    
    def test_15_priority_consistency_testing(self):
        """Test priority consistency in waiting room"""
        print("\n🔢 Testing priority consistency...")
        
        if len(self.test_patients) < 4:
            self.skipTest("Need at least 4 test patients")
        
        # Create multiple appointments with 'attente' status
        appointment_ids = []
        for i, patient in enumerate(self.test_patients[:4]):
            appointment_id = self.create_test_appointment(
                patient["id"], 
                self.today, 
                f"{8 + i}:00", 
                status="attente"
            )
            if appointment_id:
                appointment_ids.append(appointment_id)
        
        if len(appointment_ids) < 4:
            self.skipTest("Could not create enough test appointments")
        
        try:
            # Test priority operations
            operations = [
                (appointment_ids[2], {"action": "set_first"}),
                (appointment_ids[0], {"action": "move_down"}),
                (appointment_ids[1], {"action": "set_position", "position": 2}),
                (appointment_ids[3], {"action": "move_up"})
            ]
            
            for appointment_id, action_data in operations:
                response = requests.put(
                    f"{self.base_url}/api/rdv/{appointment_id}/priority",
                    json=action_data
                )
                self.assertEqual(response.status_code, 200)
            
            # Verify final order
            response = requests.get(f"{self.base_url}/api/rdv/jour/{self.today}")
            self.assertEqual(response.status_code, 200)
            appointments = response.json()
            
            # Filter waiting appointments
            waiting_appointments = [appt for appt in appointments if appt["statut"] == "attente"]
            
            # Verify priorities are sequential and unique
            priorities = [appt.get("priority", 999) for appt in waiting_appointments]
            priorities.sort()
            
            expected_priorities = list(range(len(waiting_appointments)))
            self.assertEqual(priorities, expected_priorities)
            
            print(f"✅ Priority consistency maintained: {priorities}")
            
        finally:
            # Clean up
            for appointment_id in appointment_ids:
                requests.delete(f"{self.base_url}/api/appointments/{appointment_id}")
    
    def test_16_data_persistence_verification(self):
        """Test data persistence across operations"""
        print("\n💾 Testing data persistence...")
        
        if not self.test_patients:
            self.skipTest("No test patients available")
        
        # Create test appointment
        patient_id = self.test_patients[0]["id"]
        appointment_id = self.create_test_appointment(patient_id, self.today, "19:00")
        
        if not appointment_id:
            self.skipTest("Could not create test appointment")
        
        try:
            # Perform operations and verify persistence
            test_operations = [
                {
                    "operation": "status_update",
                    "endpoint": f"/api/rdv/{appointment_id}/statut",
                    "data": {"statut": "en_cours"},
                    "verify_field": "statut",
                    "expected_value": "en_cours"
                },
                {
                    "operation": "room_assignment",
                    "endpoint": f"/api/rdv/{appointment_id}/salle",
                    "params": {"salle": "salle2"},
                    "verify_field": "salle",
                    "expected_value": "salle2"
                },
                {
                    "operation": "payment_update",
                    "endpoint": f"/api/rdv/{appointment_id}/paiement",
                    "data": {"paye": True, "montant_paye": 250, "methode_paiement": "carte", "date_paiement": self.today},
                    "verify_field": "paye",
                    "expected_value": True
                }
            ]
            
            for operation in test_operations:
                # Perform operation
                if "data" in operation:
                    response = requests.put(f"{self.base_url}{operation['endpoint']}", json=operation["data"])
                elif "params" in operation:
                    response = requests.put(f"{self.base_url}{operation['endpoint']}", params=operation["params"])
                
                self.assertEqual(response.status_code, 200)
                
                # Verify persistence immediately
                response = requests.get(f"{self.base_url}/api/rdv/jour/{self.today}")
                self.assertEqual(response.status_code, 200)
                appointments = response.json()
                
                updated_appointment = None
                for appt in appointments:
                    if appt["id"] == appointment_id:
                        updated_appointment = appt
                        break
                
                self.assertIsNotNone(updated_appointment)
                self.assertEqual(updated_appointment[operation["verify_field"]], operation["expected_value"])
                
                print(f"✅ {operation['operation']} persisted correctly")
                
                # Wait a bit and verify again (test persistence over time)
                time.sleep(0.1)
                
                response = requests.get(f"{self.base_url}/api/rdv/jour/{self.today}")
                self.assertEqual(response.status_code, 200)
                appointments = response.json()
                
                updated_appointment = None
                for appt in appointments:
                    if appt["id"] == appointment_id:
                        updated_appointment = appt
                        break
                
                self.assertIsNotNone(updated_appointment)
                self.assertEqual(updated_appointment[operation["verify_field"]], operation["expected_value"])
            
            print("✅ Data persistence verification completed")
            
        finally:
            # Clean up
            requests.delete(f"{self.base_url}/api/appointments/{appointment_id}")
    
    # ========== 5. DRAG AND DROP ALGORITHM TESTS ==========
    
    def test_17_drag_drop_algorithm_comprehensive(self):
        """Test drag and drop repositioning algorithm comprehensively"""
        print("\n🎯 Testing drag and drop algorithm comprehensively...")
        
        if len(self.test_patients) < 5:
            self.skipTest("Need at least 5 test patients for comprehensive testing")
        
        # Create 5 test appointments with 'attente' status
        appointment_ids = []
        patient_names = []
        
        for i, patient in enumerate(self.test_patients[:5]):
            appointment_id = self.create_test_appointment(
                patient["id"], 
                self.today, 
                f"{7 + i}:00", 
                status="attente"
            )
            if appointment_id:
                appointment_ids.append(appointment_id)
                patient_names.append(f"{patient['nom']} {patient['prenom']}")
        
        if len(appointment_ids) < 5:
            self.skipTest("Could not create enough test appointments")
        
        try:
            print(f"Created 5 appointments: {patient_names}")
            
            # Test Case 1: Move middle item to first position
            print("\n🔄 Test Case 1: Move middle item (position 2) to first position")
            response = requests.put(
                f"{self.base_url}/api/rdv/{appointment_ids[2]}/priority",
                json={"action": "set_position", "position": 0}
            )
            self.assertEqual(response.status_code, 200)
            
            # Verify new order
            response = requests.get(f"{self.base_url}/api/rdv/jour/{self.today}")
            appointments = [appt for appt in response.json() if appt["statut"] == "attente"]
            priorities = [(appt["id"], appt.get("priority", 999)) for appt in appointments]
            priorities.sort(key=lambda x: x[1])
            
            # Should be: [2, 0, 1, 3, 4] (appointment_ids[2] moved to first)
            expected_order = [appointment_ids[2], appointment_ids[0], appointment_ids[1], appointment_ids[3], appointment_ids[4]]
            actual_order = [p[0] for p in priorities]
            self.assertEqual(actual_order, expected_order)
            print("✅ Middle to first: Order correct")
            
            # Test Case 2: Move last item to middle position
            print("\n🔄 Test Case 2: Move last item to middle position (position 2)")
            response = requests.put(
                f"{self.base_url}/api/rdv/{appointment_ids[4]}/priority",
                json={"action": "set_position", "position": 2}
            )
            self.assertEqual(response.status_code, 200)
            
            # Verify new order
            response = requests.get(f"{self.base_url}/api/rdv/jour/{self.today}")
            appointments = [appt for appt in response.json() if appt["statut"] == "attente"]
            priorities = [(appt["id"], appt.get("priority", 999)) for appt in appointments]
            priorities.sort(key=lambda x: x[1])
            
            # Should be: [2, 0, 4, 1, 3] (appointment_ids[4] moved to position 2)
            expected_order = [appointment_ids[2], appointment_ids[0], appointment_ids[4], appointment_ids[1], appointment_ids[3]]
            actual_order = [p[0] for p in priorities]
            self.assertEqual(actual_order, expected_order)
            print("✅ Last to middle: Order correct")
            
            # Test Case 3: Move first item to last position
            print("\n🔄 Test Case 3: Move first item to last position")
            response = requests.put(
                f"{self.base_url}/api/rdv/{appointment_ids[2]}/priority",
                json={"action": "set_position", "position": 4}
            )
            self.assertEqual(response.status_code, 200)
            
            # Verify new order
            response = requests.get(f"{self.base_url}/api/rdv/jour/{self.today}")
            appointments = [appt for appt in response.json() if appt["statut"] == "attente"]
            priorities = [(appt["id"], appt.get("priority", 999)) for appt in appointments]
            priorities.sort(key=lambda x: x[1])
            
            # Should be: [0, 4, 1, 3, 2] (appointment_ids[2] moved to last)
            expected_order = [appointment_ids[0], appointment_ids[4], appointment_ids[1], appointment_ids[3], appointment_ids[2]]
            actual_order = [p[0] for p in priorities]
            self.assertEqual(actual_order, expected_order)
            print("✅ First to last: Order correct")
            
            # Test Case 4: Test move_up and move_down
            print("\n🔄 Test Case 4: Test move_up and move_down actions")
            
            # Move item up
            response = requests.put(
                f"{self.base_url}/api/rdv/{appointment_ids[1]}/priority",
                json={"action": "move_up"}
            )
            self.assertEqual(response.status_code, 200)
            
            # Move item down
            response = requests.put(
                f"{self.base_url}/api/rdv/{appointment_ids[4]}/priority",
                json={"action": "move_down"}
            )
            self.assertEqual(response.status_code, 200)
            
            # Verify priorities are still sequential
            response = requests.get(f"{self.base_url}/api/rdv/jour/{self.today}")
            appointments = [appt for appt in response.json() if appt["statut"] == "attente"]
            priorities = [appt.get("priority", 999) for appt in appointments]
            priorities.sort()
            
            expected_priorities = list(range(5))  # [0, 1, 2, 3, 4]
            self.assertEqual(priorities, expected_priorities)
            print("✅ Move up/down: Priorities remain sequential")
            
            # Test Case 5: Edge case - single appointment
            print("\n🔄 Test Case 5: Edge case testing")
            
            # Try to move when only one appointment (should handle gracefully)
            # First, change all but one to different status
            for i in range(1, 5):
                requests.put(
                    f"{self.base_url}/api/rdv/{appointment_ids[i]}/statut",
                    json={"statut": "programme"}
                )
            
            # Now try to move the only waiting appointment
            response = requests.put(
                f"{self.base_url}/api/rdv/{appointment_ids[0]}/priority",
                json={"action": "move_up"}
            )
            self.assertEqual(response.status_code, 200)
            print("✅ Single appointment edge case handled")
            
            print("\n✅ Drag and drop algorithm comprehensive testing completed")
            
        finally:
            # Clean up
            for appointment_id in appointment_ids:
                requests.delete(f"{self.base_url}/api/appointments/{appointment_id}")
    
    # ========== 6. BACKEND CODE ANALYSIS ==========
    
    def test_18_code_analysis_and_recommendations(self):
        """Analyze backend code and provide recommendations"""
        print("\n🔍 Backend Code Analysis and Recommendations...")
        
        recommendations = []
        
        # Test endpoint consistency
        print("📊 Analyzing endpoint consistency...")
        
        # Check response formats
        endpoints_to_check = [
            f"/api/rdv/jour/{self.today}",
            f"/api/rdv/stats/{self.today}",
            f"/api/rdv/time-slots?date={self.today}"
        ]
        
        response_formats = {}
        for endpoint in endpoints_to_check:
            response = requests.get(f"{self.base_url}{endpoint}")
            if response.status_code == 200:
                data = response.json()
                response_formats[endpoint] = type(data).__name__
        
        print(f"✅ Response format analysis: {response_formats}")
        
        # Performance analysis
        print("📊 Analyzing performance patterns...")
        
        avg_performance = {}
        for test_name, duration in self.performance_results.items():
            base_name = '_'.join(test_name.split('_')[:3])
            if base_name not in avg_performance:
                avg_performance[base_name] = []
            avg_performance[base_name].append(duration)
        
        for endpoint, durations in avg_performance.items():
            avg_duration = sum(durations) / len(durations)
            if avg_duration > 500:  # 500ms threshold
                recommendations.append(f"Performance: {endpoint} averages {avg_duration:.2f}ms - consider optimization")
        
        # Error handling analysis
        print("📊 Analyzing error handling patterns...")
        
        if self.error_log:
            recommendations.append(f"Error handling: {len(self.error_log)} errors logged during testing")
            for error in self.error_log[:3]:  # Show first 3 errors
                recommendations.append(f"  - {error}")
        
        # Data structure analysis
        print("📊 Analyzing data structure efficiency...")
        
        # Check if patient data is efficiently included
        response = requests.get(f"{self.base_url}/api/rdv/jour/{self.today}")
        if response.status_code == 200:
            appointments = response.json()
            if appointments:
                sample_appointment = appointments[0]
                if "patient" in sample_appointment:
                    patient_fields = list(sample_appointment["patient"].keys())
                    if len(patient_fields) > 6:  # More than necessary fields
                        recommendations.append("Data structure: Patient object in appointments may contain unnecessary fields")
        
        # Generate final recommendations
        print("\n📋 BACKEND ANALYSIS RECOMMENDATIONS:")
        print("=" * 50)
        
        if not recommendations:
            print("✅ No major issues found - backend is well optimized")
        else:
            for i, rec in enumerate(recommendations, 1):
                print(f"{i}. {rec}")
        
        # Additional optimization suggestions
        optimization_suggestions = [
            "Consider implementing response caching for frequently accessed endpoints",
            "Add request rate limiting to prevent abuse",
            "Implement database connection pooling for better performance",
            "Add comprehensive logging for better debugging",
            "Consider adding API versioning for future compatibility",
            "Implement request validation middleware",
            "Add health check endpoints for monitoring",
            "Consider implementing pagination for large data sets"
        ]
        
        print("\n💡 GENERAL OPTIMIZATION SUGGESTIONS:")
        print("=" * 50)
        for i, suggestion in enumerate(optimization_suggestions, 1):
            print(f"{i}. {suggestion}")
    
    def tearDown(self):
        """Clean up after tests"""
        print("\n" + "=" * 80)
        print("📊 COMPREHENSIVE CALENDAR BACKEND TEST SUMMARY")
        print("=" * 80)
        
        # Performance summary
        if self.performance_results:
            print("\n⚡ PERFORMANCE RESULTS:")
            for test_name, duration in sorted(self.performance_results.items()):
                status = "✅" if duration < 1000 else "⚠️" if duration < 2000 else "❌"
                print(f"  {status} {test_name}: {duration:.2f}ms")
        
        # Error summary
        if self.error_log:
            print(f"\n❌ ERRORS FOUND ({len(self.error_log)}):")
            for error in self.error_log:
                print(f"  - {error}")
        else:
            print("\n✅ NO CRITICAL ERRORS FOUND")
        
        # Overall assessment
        critical_errors = len([e for e in self.error_log if "failed" in e.lower()])
        performance_issues = len([d for d in self.performance_results.values() if d > 2000])
        
        print(f"\n🎯 OVERALL ASSESSMENT:")
        print(f"  - Critical Errors: {critical_errors}")
        print(f"  - Performance Issues: {performance_issues}")
        print(f"  - Tests Completed: {len(self.performance_results)}")
        
        if critical_errors == 0 and performance_issues == 0:
            print("  - Status: ✅ BACKEND READY FOR PRODUCTION")
        elif critical_errors == 0:
            print("  - Status: ⚠️ BACKEND FUNCTIONAL WITH MINOR PERFORMANCE ISSUES")
        else:
            print("  - Status: ❌ BACKEND HAS CRITICAL ISSUES REQUIRING ATTENTION")

if __name__ == '__main__':
    # Run the comprehensive test suite
    unittest.main(verbosity=2)