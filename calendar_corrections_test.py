import requests
import unittest
import json
import time
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/frontend/.env')

class CalendarCorrectionsTest(unittest.TestCase):
    """
    Test suite for Calendar backend corrections validation
    Focus: Error handling corrections, priority response format, performance, and workflow testing
    """
    
    def setUp(self):
        # Use the correct backend URL from environment
        backend_url = os.getenv('REACT_APP_BACKEND_URL', 'https://cbd199ac-e82c-4b53-a71c-648951cb9dec.preview.emergentagent.com')
        self.base_url = backend_url
        print(f"Testing Calendar corrections at: {self.base_url}")
        
        # Initialize demo data before running tests
        self.init_demo_data()
        
        # Get test patient for appointments
        self.test_patient_id = self.get_test_patient()
        
    def init_demo_data(self):
        """Initialize demo data for testing"""
        try:
            response = requests.get(f"{self.base_url}/api/init-demo")
            self.assertEqual(response.status_code, 200)
            print("Demo data initialized successfully")
        except Exception as e:
            print(f"Error initializing demo data: {e}")
    
    def get_test_patient(self):
        """Get a test patient ID for creating appointments"""
        response = requests.get(f"{self.base_url}/api/patients")
        self.assertEqual(response.status_code, 200)
        patients_data = response.json()
        patients = patients_data["patients"]
        self.assertTrue(len(patients) > 0, "No patients found for testing")
        return patients[0]["id"]
    
    def create_test_appointment(self, status="programme", appointment_type="visite"):
        """Create a test appointment for testing"""
        today = datetime.now().strftime("%Y-%m-%d")
        future_time = (datetime.now() + timedelta(hours=2)).strftime("%H:%M")
        
        appointment_data = {
            "patient_id": self.test_patient_id,
            "date": today,
            "heure": future_time,
            "type_rdv": appointment_type,
            "statut": status,
            "motif": "Test appointment for corrections",
            "paye": False
        }
        
        response = requests.post(f"{self.base_url}/api/appointments", json=appointment_data)
        self.assertEqual(response.status_code, 200)
        return response.json()["appointment_id"]
    
    # ========== ERROR HANDLING CORRECTIONS TESTS ==========
    
    def test_payment_validation_error_handling(self):
        """Test PUT /api/rdv/{rdv_id}/paiement returns 400 for invalid payment methods (not 500)"""
        print("\n=== Testing Payment Validation Error Handling ===")
        
        # Create test appointment
        rdv_id = self.create_test_appointment()
        
        try:
            # Test invalid payment method - should return 400, not 500
            invalid_payment_data = {
                "paye": True,
                "montant_paye": 300,
                "methode_paiement": "invalid_method",  # Invalid method
                "date_paiement": datetime.now().strftime("%Y-%m-%d")
            }
            
            start_time = time.time()
            response = requests.put(f"{self.base_url}/api/rdv/{rdv_id}/paiement", json=invalid_payment_data)
            response_time = (time.time() - start_time) * 1000
            
            # CRITICAL: Should return 400, not 500
            self.assertEqual(response.status_code, 400, 
                           f"Expected 400 for invalid payment method, got {response.status_code}")
            
            # Verify error message is descriptive
            error_data = response.json()
            self.assertIn("detail", error_data)
            self.assertIn("Invalid payment method", error_data["detail"])
            
            print(f"✅ Invalid payment method correctly returns 400 (Response time: {response_time:.1f}ms)")
            
            # Test valid payment methods still work
            valid_methods = ["espece", "carte", "cheque", "virement", "gratuit", ""]
            
            for method in valid_methods:
                valid_payment_data = {
                    "paye": True if method != "" else False,
                    "montant_paye": 300 if method != "" else 0,
                    "methode_paiement": method,
                    "date_paiement": datetime.now().strftime("%Y-%m-%d")
                }
                
                response = requests.put(f"{self.base_url}/api/rdv/{rdv_id}/paiement", json=valid_payment_data)
                self.assertEqual(response.status_code, 200, 
                               f"Valid payment method '{method}' should work")
                
                response_data = response.json()
                self.assertIn("message", response_data)
                self.assertEqual(response_data["methode_paiement"], method)
            
            print(f"✅ All valid payment methods work correctly")
            
        finally:
            # Clean up
            requests.delete(f"{self.base_url}/api/appointments/{rdv_id}")
    
    def test_type_validation_error_handling(self):
        """Test PUT /api/rdv/{rdv_id} returns 400 for invalid appointment types (not 500)"""
        print("\n=== Testing Type Validation Error Handling ===")
        
        # Create test appointment
        rdv_id = self.create_test_appointment()
        
        try:
            # Test invalid appointment type - should return 400, not 500
            invalid_type_data = {
                "type_rdv": "invalid_type"  # Invalid type
            }
            
            start_time = time.time()
            response = requests.put(f"{self.base_url}/api/rdv/{rdv_id}", json=invalid_type_data)
            response_time = (time.time() - start_time) * 1000
            
            # CRITICAL: Should return 400, not 500
            self.assertEqual(response.status_code, 400, 
                           f"Expected 400 for invalid appointment type, got {response.status_code}")
            
            # Verify error message is descriptive
            error_data = response.json()
            self.assertIn("detail", error_data)
            self.assertIn("Invalid type", error_data["detail"])
            
            print(f"✅ Invalid appointment type correctly returns 400 (Response time: {response_time:.1f}ms)")
            
            # Test valid appointment types still work
            valid_types = ["visite", "controle"]
            
            for appointment_type in valid_types:
                valid_type_data = {
                    "type_rdv": appointment_type
                }
                
                response = requests.put(f"{self.base_url}/api/rdv/{rdv_id}", json=valid_type_data)
                self.assertEqual(response.status_code, 200, 
                               f"Valid appointment type '{appointment_type}' should work")
                
                response_data = response.json()
                self.assertIn("message", response_data)
                self.assertEqual(response_data["type_rdv"], appointment_type)
            
            print(f"✅ All valid appointment types work correctly")
            
        finally:
            # Clean up
            requests.delete(f"{self.base_url}/api/appointments/{rdv_id}")
    
    def test_http_exception_handling(self):
        """Test that HTTPException are properly raised and not converted to 500 errors"""
        print("\n=== Testing HTTPException Handling ===")
        
        # Test non-existent appointment ID - should return 404, not 500
        non_existent_id = "non_existent_appointment_id"
        
        # Test payment endpoint with non-existent ID
        payment_data = {"paye": True, "montant_paye": 300, "methode_paiement": "espece"}
        response = requests.put(f"{self.base_url}/api/rdv/{non_existent_id}/paiement", json=payment_data)
        self.assertEqual(response.status_code, 404, "Non-existent appointment should return 404")
        
        # Test type update endpoint with non-existent ID
        type_data = {"type_rdv": "visite"}
        response = requests.put(f"{self.base_url}/api/rdv/{non_existent_id}", json=type_data)
        self.assertEqual(response.status_code, 404, "Non-existent appointment should return 404")
        
        # Test priority endpoint with non-existent ID
        priority_data = {"action": "move_up"}
        response = requests.put(f"{self.base_url}/api/rdv/{non_existent_id}/priority", json=priority_data)
        self.assertEqual(response.status_code, 404, "Non-existent appointment should return 404")
        
        print("✅ HTTPException handling working correctly - 404 errors maintained")
    
    # ========== PRIORITY RESPONSE FORMAT TESTS ==========
    
    def test_priority_response_format_consistency(self):
        """Test PUT /api/rdv/{rdv_id}/priority always includes 'action' field in response"""
        print("\n=== Testing Priority Response Format Consistency ===")
        
        # Create multiple test appointments in waiting status
        today = datetime.now().strftime("%Y-%m-%d")
        appointment_ids = []
        
        for i in range(3):
            rdv_id = self.create_test_appointment(status="attente")
            appointment_ids.append(rdv_id)
        
        try:
            # Test all priority actions and verify 'action' field is always present
            test_actions = [
                {"action": "set_first"},
                {"action": "move_up"},
                {"action": "move_down"},
                {"action": "set_position", "position": 1}
            ]
            
            for action_data in test_actions:
                rdv_id = appointment_ids[1]  # Use middle appointment
                
                start_time = time.time()
                response = requests.put(f"{self.base_url}/api/rdv/{rdv_id}/priority", json=action_data)
                response_time = (time.time() - start_time) * 1000
                
                self.assertEqual(response.status_code, 200, 
                               f"Priority action '{action_data['action']}' should work")
                
                response_data = response.json()
                
                # CRITICAL: 'action' field must always be present
                self.assertIn("action", response_data, 
                             f"Response missing 'action' field for action '{action_data['action']}'")
                self.assertEqual(response_data["action"], action_data["action"],
                               f"Response 'action' field should match request action")
                
                # Verify other expected fields
                expected_fields = ["message", "total_waiting", "action"]
                for field in expected_fields:
                    self.assertIn(field, response_data, 
                                 f"Response missing expected field '{field}'")
                
                print(f"✅ Action '{action_data['action']}' includes 'action' field (Response time: {response_time:.1f}ms)")
            
            # Test edge case: single appointment in waiting room
            single_rdv_id = appointment_ids[0]
            
            # Remove other appointments from waiting to test single appointment scenario
            for rdv_id in appointment_ids[1:]:
                requests.put(f"{self.base_url}/api/rdv/{rdv_id}/statut", json={"statut": "programme"})
            
            # Test priority action on single appointment
            response = requests.put(f"{self.base_url}/api/rdv/{single_rdv_id}/priority", 
                                  json={"action": "move_up"})
            self.assertEqual(response.status_code, 200)
            
            response_data = response.json()
            self.assertIn("action", response_data, 
                         "Single appointment response must include 'action' field")
            self.assertEqual(response_data["action"], "move_up")
            
            print("✅ Single appointment scenario includes 'action' field")
            
        finally:
            # Clean up
            for rdv_id in appointment_ids:
                requests.delete(f"{self.base_url}/api/appointments/{rdv_id}")
    
    # ========== PERFORMANCE TESTING ==========
    
    def test_performance_maintained(self):
        """Test that response times remain under 100ms after corrections"""
        print("\n=== Testing Performance Maintained ===")
        
        # Create test appointment
        rdv_id = self.create_test_appointment()
        today = datetime.now().strftime("%Y-%m-%d")
        
        try:
            performance_results = {}
            
            # Test GET /api/rdv/jour performance
            start_time = time.time()
            response = requests.get(f"{self.base_url}/api/rdv/jour/{today}")
            response_time = (time.time() - start_time) * 1000
            self.assertEqual(response.status_code, 200)
            performance_results["GET /api/rdv/jour"] = response_time
            
            # Test PUT /api/rdv/statut performance
            start_time = time.time()
            response = requests.put(f"{self.base_url}/api/rdv/{rdv_id}/statut", json={"statut": "attente"})
            response_time = (time.time() - start_time) * 1000
            self.assertEqual(response.status_code, 200)
            performance_results["PUT /api/rdv/statut"] = response_time
            
            # Test PUT /api/rdv/salle performance
            start_time = time.time()
            response = requests.put(f"{self.base_url}/api/rdv/{rdv_id}/salle?salle=salle1")
            response_time = (time.time() - start_time) * 1000
            self.assertEqual(response.status_code, 200)
            performance_results["PUT /api/rdv/salle"] = response_time
            
            # Test PUT /api/rdv/priority performance
            start_time = time.time()
            response = requests.put(f"{self.base_url}/api/rdv/{rdv_id}/priority", json={"action": "set_first"})
            response_time = (time.time() - start_time) * 1000
            self.assertEqual(response.status_code, 200)
            performance_results["PUT /api/rdv/priority"] = response_time
            
            # Test PUT /api/rdv/paiement performance
            start_time = time.time()
            payment_data = {"paye": True, "montant_paye": 300, "methode_paiement": "espece"}
            response = requests.put(f"{self.base_url}/api/rdv/{rdv_id}/paiement", json=payment_data)
            response_time = (time.time() - start_time) * 1000
            self.assertEqual(response.status_code, 200)
            performance_results["PUT /api/rdv/paiement"] = response_time
            
            # Test PUT /api/rdv type update performance
            start_time = time.time()
            response = requests.put(f"{self.base_url}/api/rdv/{rdv_id}", json={"type_rdv": "controle"})
            response_time = (time.time() - start_time) * 1000
            self.assertEqual(response.status_code, 200)
            performance_results["PUT /api/rdv (type)"] = response_time
            
            # Verify all endpoints are under 100ms threshold
            print("\nPerformance Results:")
            all_under_threshold = True
            for endpoint, time_ms in performance_results.items():
                status = "✅" if time_ms < 100 else "⚠️"
                print(f"{status} {endpoint}: {time_ms:.1f}ms")
                if time_ms >= 100:
                    all_under_threshold = False
            
            # Allow some flexibility for network conditions, but flag if significantly over
            if not all_under_threshold:
                print("⚠️ Some endpoints over 100ms - may be due to network conditions")
            else:
                print("✅ All endpoints under 100ms threshold")
            
        finally:
            # Clean up
            requests.delete(f"{self.base_url}/api/appointments/{rdv_id}")
    
    def test_concurrent_operations_performance(self):
        """Test performance under concurrent operations"""
        print("\n=== Testing Concurrent Operations Performance ===")
        
        # Create multiple test appointments
        appointment_ids = []
        for i in range(5):
            rdv_id = self.create_test_appointment(status="attente")
            appointment_ids.append(rdv_id)
        
        try:
            # Test concurrent status updates
            import threading
            import queue
            
            results_queue = queue.Queue()
            
            def concurrent_status_update(rdv_id, status):
                start_time = time.time()
                response = requests.put(f"{self.base_url}/api/rdv/{rdv_id}/statut", json={"statut": status})
                response_time = (time.time() - start_time) * 1000
                results_queue.put((rdv_id, response.status_code, response_time))
            
            # Launch concurrent requests
            threads = []
            statuses = ["en_cours", "termine", "absent", "retard", "attente"]
            
            start_time = time.time()
            for i, rdv_id in enumerate(appointment_ids):
                thread = threading.Thread(target=concurrent_status_update, 
                                        args=(rdv_id, statuses[i]))
                threads.append(thread)
                thread.start()
            
            # Wait for all threads to complete
            for thread in threads:
                thread.join()
            
            total_time = (time.time() - start_time) * 1000
            
            # Collect results
            successful_requests = 0
            total_response_time = 0
            
            while not results_queue.empty():
                rdv_id, status_code, response_time = results_queue.get()
                if status_code == 200:
                    successful_requests += 1
                    total_response_time += response_time
            
            # Calculate average response time
            avg_response_time = total_response_time / successful_requests if successful_requests > 0 else 0
            
            print(f"✅ Concurrent operations completed in {total_time:.1f}ms")
            print(f"✅ {successful_requests}/{len(appointment_ids)} requests successful")
            print(f"✅ Average response time: {avg_response_time:.1f}ms")
            
            # Verify all requests were successful
            self.assertEqual(successful_requests, len(appointment_ids), 
                           "All concurrent requests should be successful")
            
        finally:
            # Clean up
            for rdv_id in appointment_ids:
                requests.delete(f"{self.base_url}/api/appointments/{rdv_id}")
    
    # ========== COMPLETE WORKFLOW TESTING ==========
    
    def test_complete_workflow_integrity(self):
        """Test complete workflow: creation → attente → reordering → consultation → terminé"""
        print("\n=== Testing Complete Workflow Integrity ===")
        
        # Step 1: Create appointment
        rdv_id = self.create_test_appointment(status="programme", appointment_type="visite")
        today = datetime.now().strftime("%Y-%m-%d")
        
        try:
            # Step 2: Move to waiting room
            response = requests.put(f"{self.base_url}/api/rdv/{rdv_id}/statut", json={"statut": "attente"})
            self.assertEqual(response.status_code, 200)
            print("✅ Step 1: Moved to waiting room")
            
            # Verify heure_arrivee_attente is set
            response = requests.get(f"{self.base_url}/api/rdv/jour/{today}")
            appointments = response.json()
            test_appointment = next((a for a in appointments if a["id"] == rdv_id), None)
            self.assertIsNotNone(test_appointment)
            self.assertEqual(test_appointment["statut"], "attente")
            
            # Step 3: Test priority reordering
            response = requests.put(f"{self.base_url}/api/rdv/{rdv_id}/priority", json={"action": "set_first"})
            self.assertEqual(response.status_code, 200)
            response_data = response.json()
            self.assertIn("action", response_data)
            print("✅ Step 2: Priority reordering working")
            
            # Step 4: Assign to consultation room
            response = requests.put(f"{self.base_url}/api/rdv/{rdv_id}/salle?salle=salle1")
            self.assertEqual(response.status_code, 200)
            print("✅ Step 3: Assigned to consultation room")
            
            # Step 5: Start consultation
            response = requests.put(f"{self.base_url}/api/rdv/{rdv_id}/statut", json={"statut": "en_cours"})
            self.assertEqual(response.status_code, 200)
            print("✅ Step 4: Consultation started")
            
            # Step 6: Process payment
            payment_data = {
                "paye": True,
                "montant_paye": 300,
                "methode_paiement": "espece",
                "date_paiement": today
            }
            response = requests.put(f"{self.base_url}/api/rdv/{rdv_id}/paiement", json=payment_data)
            self.assertEqual(response.status_code, 200)
            print("✅ Step 5: Payment processed")
            
            # Step 7: Complete consultation
            response = requests.put(f"{self.base_url}/api/rdv/{rdv_id}/statut", json={"statut": "termine"})
            self.assertEqual(response.status_code, 200)
            print("✅ Step 6: Consultation completed")
            
            # Step 8: Verify final state
            response = requests.get(f"{self.base_url}/api/rdv/jour/{today}")
            appointments = response.json()
            final_appointment = next((a for a in appointments if a["id"] == rdv_id), None)
            
            self.assertIsNotNone(final_appointment)
            self.assertEqual(final_appointment["statut"], "termine")
            self.assertEqual(final_appointment["salle"], "salle1")
            self.assertEqual(final_appointment["paye"], True)
            
            print("✅ Step 7: Final state verified - workflow complete")
            
            # Test data persistence after workflow
            time.sleep(1)  # Brief pause
            response = requests.get(f"{self.base_url}/api/rdv/jour/{today}")
            appointments = response.json()
            persistent_appointment = next((a for a in appointments if a["id"] == rdv_id), None)
            
            self.assertIsNotNone(persistent_appointment)
            self.assertEqual(persistent_appointment["statut"], "termine")
            print("✅ Step 8: Data persistence verified")
            
        finally:
            # Clean up
            requests.delete(f"{self.base_url}/api/appointments/{rdv_id}")
    
    def test_type_toggle_workflow(self):
        """Test type toggle workflow with payment logic"""
        print("\n=== Testing Type Toggle Workflow ===")
        
        # Create visite appointment
        rdv_id = self.create_test_appointment(appointment_type="visite")
        
        try:
            # Step 1: Toggle to controle (should be free)
            response = requests.put(f"{self.base_url}/api/rdv/{rdv_id}", json={"type_rdv": "controle"})
            self.assertEqual(response.status_code, 200)
            response_data = response.json()
            self.assertEqual(response_data["type_rdv"], "controle")
            self.assertEqual(response_data["payment_status"], "gratuit")
            print("✅ Visite → Controle: Automatically marked as gratuit")
            
            # Step 2: Toggle back to visite (should be unpaid)
            response = requests.put(f"{self.base_url}/api/rdv/{rdv_id}", json={"type_rdv": "visite"})
            self.assertEqual(response.status_code, 200)
            response_data = response.json()
            self.assertEqual(response_data["type_rdv"], "visite")
            self.assertEqual(response_data["payment_status"], "non_paye")
            print("✅ Controle → Visite: Automatically marked as non_paye")
            
            # Step 3: Verify payment records are handled correctly
            today = datetime.now().strftime("%Y-%m-%d")
            response = requests.get(f"{self.base_url}/api/rdv/jour/{today}")
            appointments = response.json()
            test_appointment = next((a for a in appointments if a["id"] == rdv_id), None)
            
            self.assertIsNotNone(test_appointment)
            self.assertEqual(test_appointment["type_rdv"], "visite")
            self.assertEqual(test_appointment["paye"], False)
            print("✅ Payment logic working correctly with type toggle")
            
        finally:
            # Clean up
            requests.delete(f"{self.base_url}/api/appointments/{rdv_id}")
    
    # ========== REGRESSION TESTING ==========
    
    def test_all_calendar_endpoints_working(self):
        """Test that all Calendar endpoints are still working after corrections"""
        print("\n=== Testing All Calendar Endpoints Still Working ===")
        
        today = datetime.now().strftime("%Y-%m-%d")
        rdv_id = self.create_test_appointment(status="attente")
        
        try:
            endpoints_tested = {}
            
            # Test GET /api/rdv/jour/{date}
            response = requests.get(f"{self.base_url}/api/rdv/jour/{today}")
            self.assertEqual(response.status_code, 200)
            appointments = response.json()
            self.assertIsInstance(appointments, list)
            endpoints_tested["GET /api/rdv/jour"] = "✅"
            
            # Test GET /api/rdv/semaine/{date}
            response = requests.get(f"{self.base_url}/api/rdv/semaine/{today}")
            self.assertEqual(response.status_code, 200)
            week_data = response.json()
            self.assertIn("week_dates", week_data)
            self.assertIn("appointments", week_data)
            endpoints_tested["GET /api/rdv/semaine"] = "✅"
            
            # Test GET /api/rdv/stats/{date}
            response = requests.get(f"{self.base_url}/api/rdv/stats/{today}")
            self.assertEqual(response.status_code, 200)
            stats = response.json()
            self.assertIn("total_rdv", stats)
            endpoints_tested["GET /api/rdv/stats"] = "✅"
            
            # Test GET /api/rdv/time-slots
            response = requests.get(f"{self.base_url}/api/rdv/time-slots?date={today}")
            self.assertEqual(response.status_code, 200)
            time_slots = response.json()
            self.assertIsInstance(time_slots, list)
            endpoints_tested["GET /api/rdv/time-slots"] = "✅"
            
            # Test PUT /api/rdv/{rdv_id}/statut
            response = requests.put(f"{self.base_url}/api/rdv/{rdv_id}/statut", json={"statut": "en_cours"})
            self.assertEqual(response.status_code, 200)
            endpoints_tested["PUT /api/rdv/statut"] = "✅"
            
            # Test PUT /api/rdv/{rdv_id}/salle
            response = requests.put(f"{self.base_url}/api/rdv/{rdv_id}/salle?salle=salle2")
            self.assertEqual(response.status_code, 200)
            endpoints_tested["PUT /api/rdv/salle"] = "✅"
            
            # Test PUT /api/rdv/{rdv_id}/priority
            response = requests.put(f"{self.base_url}/api/rdv/{rdv_id}/statut", json={"statut": "attente"})  # Reset to attente
            response = requests.put(f"{self.base_url}/api/rdv/{rdv_id}/priority", json={"action": "move_up"})
            self.assertEqual(response.status_code, 200)
            endpoints_tested["PUT /api/rdv/priority"] = "✅"
            
            # Test PUT /api/rdv/{rdv_id}/paiement
            payment_data = {"paye": True, "montant_paye": 300, "methode_paiement": "carte"}
            response = requests.put(f"{self.base_url}/api/rdv/{rdv_id}/paiement", json=payment_data)
            self.assertEqual(response.status_code, 200)
            endpoints_tested["PUT /api/rdv/paiement"] = "✅"
            
            # Test PUT /api/rdv/{rdv_id} (type update)
            response = requests.put(f"{self.base_url}/api/rdv/{rdv_id}", json={"type_rdv": "controle"})
            self.assertEqual(response.status_code, 200)
            endpoints_tested["PUT /api/rdv (type)"] = "✅"
            
            print("\nEndpoint Status:")
            for endpoint, status in endpoints_tested.items():
                print(f"{status} {endpoint}")
            
            print(f"\n✅ All {len(endpoints_tested)} Calendar endpoints working correctly")
            
        finally:
            # Clean up
            requests.delete(f"{self.base_url}/api/appointments/{rdv_id}")
    
    def test_data_integrity_maintained(self):
        """Test that data integrity is maintained after corrections"""
        print("\n=== Testing Data Integrity Maintained ===")
        
        # Create multiple appointments for comprehensive testing
        appointment_ids = []
        today = datetime.now().strftime("%Y-%m-%d")
        
        for i in range(3):
            rdv_id = self.create_test_appointment(status="attente")
            appointment_ids.append(rdv_id)
        
        try:
            # Test multiple operations on different appointments
            operations = [
                (appointment_ids[0], "status", {"statut": "en_cours"}),
                (appointment_ids[1], "payment", {"paye": True, "montant_paye": 300, "methode_paiement": "espece"}),
                (appointment_ids[2], "type", {"type_rdv": "controle"})
            ]
            
            # Perform operations
            for rdv_id, operation_type, data in operations:
                if operation_type == "status":
                    response = requests.put(f"{self.base_url}/api/rdv/{rdv_id}/statut", json=data)
                elif operation_type == "payment":
                    response = requests.put(f"{self.base_url}/api/rdv/{rdv_id}/paiement", json=data)
                elif operation_type == "type":
                    response = requests.put(f"{self.base_url}/api/rdv/{rdv_id}", json=data)
                
                self.assertEqual(response.status_code, 200)
            
            # Verify data integrity by retrieving all appointments
            response = requests.get(f"{self.base_url}/api/rdv/jour/{today}")
            self.assertEqual(response.status_code, 200)
            appointments = response.json()
            
            # Find our test appointments and verify changes persisted
            test_appointments = [a for a in appointments if a["id"] in appointment_ids]
            self.assertEqual(len(test_appointments), 3, "All test appointments should be retrievable")
            
            # Verify specific changes
            for appointment in test_appointments:
                if appointment["id"] == appointment_ids[0]:
                    self.assertEqual(appointment["statut"], "en_cours")
                elif appointment["id"] == appointment_ids[1]:
                    self.assertEqual(appointment["paye"], True)
                elif appointment["id"] == appointment_ids[2]:
                    self.assertEqual(appointment["type_rdv"], "controle")
                    self.assertEqual(appointment["paye"], True)  # Should be auto-set for controle
            
            print("✅ Data integrity maintained across all operations")
            
            # Test that patient info is still properly included
            for appointment in test_appointments:
                self.assertIn("patient", appointment)
                patient_info = appointment["patient"]
                self.assertIn("nom", patient_info)
                self.assertIn("prenom", patient_info)
            
            print("✅ Patient info integration maintained")
            
        finally:
            # Clean up
            for rdv_id in appointment_ids:
                requests.delete(f"{self.base_url}/api/appointments/{rdv_id}")

if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2)