import requests
import unittest
import json
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/frontend/.env')

class PhoneRemindersTest(unittest.TestCase):
    def setUp(self):
        # Use the correct backend URL from environment
        backend_url = os.getenv('REACT_APP_BACKEND_URL', 'https://21013378-6a50-4f8f-b666-859400c9b99f.preview.emergentagent.com')
        self.base_url = backend_url
        print(f"Testing backend at: {self.base_url}")
        # Initialize demo data before running tests
        self.init_demo_data()
    
    def init_demo_data(self):
        """Initialize demo data for testing"""
        try:
            response = requests.get(f"{self.base_url}/api/init-demo")
            self.assertEqual(response.status_code, 200)
            print("Demo data initialized successfully")
        except Exception as e:
            print(f"Error initializing demo data: {e}")

    # ========== PHONE REMINDERS FUNCTIONALITY TESTS ==========
    
    def test_phone_reminders_endpoint_basic(self):
        """Test GET /api/dashboard/phone-reminders - Basic functionality"""
        response = requests.get(f"{self.base_url}/api/dashboard/phone-reminders")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify response structure
        self.assertIn("reminders", data)
        self.assertIsInstance(data["reminders"], list)
        
        print(f"✅ Phone reminders endpoint accessible - found {len(data['reminders'])} reminders")
    
    def test_phone_reminders_relance_data_structure(self):
        """Test phone reminders response includes all required fields"""
        response = requests.get(f"{self.base_url}/api/dashboard/phone-reminders")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        reminders = data["reminders"]
        
        if len(reminders) > 0:
            # Test first reminder structure
            reminder = reminders[0]
            
            # Verify required fields from review request
            required_fields = [
                "id", "patient_id", "patient_nom", "patient_prenom", 
                "numero_whatsapp", "date_rdv", "heure_rdv", "motif",
                "consultation_id", "relance_date", "observations", "traitement"
            ]
            
            for field in required_fields:
                self.assertIn(field, reminder, f"Missing required field: {field}")
            
            # Verify data types
            self.assertIsInstance(reminder["patient_nom"], str)
            self.assertIsInstance(reminder["patient_prenom"], str)
            self.assertIsInstance(reminder["numero_whatsapp"], str)
            self.assertIsInstance(reminder["observations"], str)
            self.assertIsInstance(reminder["traitement"], str)
            
            print(f"✅ Reminder data structure validated - all required fields present")
        else:
            print("⚠️ No reminders found for today - cannot validate structure")
    
    def test_phone_reminders_today_filter(self):
        """Test that phone reminders only returns relances for today"""
        today_str = datetime.now().strftime("%Y-%m-%d")
        
        response = requests.get(f"{self.base_url}/api/dashboard/phone-reminders")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        reminders = data["reminders"]
        
        # Verify all reminders have relance_date = today
        for reminder in reminders:
            self.assertEqual(reminder["relance_date"], today_str, 
                           f"Reminder has wrong relance_date: {reminder['relance_date']} (expected: {today_str})")
        
        print(f"✅ All {len(reminders)} reminders are for today ({today_str})")
    
    def test_phone_reminders_demo_data_patients(self):
        """Test that demo data includes relances for patient1 and patient2"""
        response = requests.get(f"{self.base_url}/api/dashboard/phone-reminders")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        reminders = data["reminders"]
        
        # Look for patient1 (Yassine Ben Ahmed) and patient2 (Lina Alami)
        patient1_found = False
        patient2_found = False
        
        for reminder in reminders:
            if reminder["patient_id"] == "patient1":
                self.assertEqual(reminder["patient_nom"], "Ben Ahmed")
                self.assertEqual(reminder["patient_prenom"], "Yassine")
                patient1_found = True
                print(f"✅ Found patient1 (Yassine Ben Ahmed) relance")
            
            elif reminder["patient_id"] == "patient2":
                self.assertEqual(reminder["patient_nom"], "Alami")
                self.assertEqual(reminder["patient_prenom"], "Lina")
                patient2_found = True
                print(f"✅ Found patient2 (Lina Alami) relance")
        
        # Verify both demo patients have relances for today
        self.assertTrue(patient1_found, "patient1 (Yassine Ben Ahmed) relance not found for today")
        self.assertTrue(patient2_found, "patient2 (Lina Alami) relance not found for today")
        
        print(f"✅ Both demo patients have relances for today")
    
    def test_phone_reminders_patient_information_linkage(self):
        """Test that patient information is correctly linked to consultation relances"""
        response = requests.get(f"{self.base_url}/api/dashboard/phone-reminders")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        reminders = data["reminders"]
        
        for reminder in reminders:
            patient_id = reminder["patient_id"]
            
            # Get patient data directly to verify linkage
            patient_response = requests.get(f"{self.base_url}/api/patients/{patient_id}")
            self.assertEqual(patient_response.status_code, 200)
            patient_data = patient_response.json()
            
            # Verify patient information matches
            self.assertEqual(reminder["patient_nom"], patient_data["nom"])
            self.assertEqual(reminder["patient_prenom"], patient_data["prenom"])
            self.assertEqual(reminder["numero_whatsapp"], patient_data.get("numero_whatsapp", ""))
            
            print(f"✅ Patient linkage verified for {reminder['patient_prenom']} {reminder['patient_nom']}")
    
    def test_phone_reminders_consultation_context(self):
        """Test that reminders include consultation-specific context"""
        response = requests.get(f"{self.base_url}/api/dashboard/phone-reminders")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        reminders = data["reminders"]
        
        for reminder in reminders:
            consultation_id = reminder["consultation_id"]
            
            # Get consultation data to verify context
            consultation_response = requests.get(f"{self.base_url}/api/consultations/{consultation_id}")
            self.assertEqual(consultation_response.status_code, 200)
            consultation_data = consultation_response.json()
            
            # Verify consultation context is included
            self.assertEqual(reminder["observations"], consultation_data.get("observations", ""))
            self.assertEqual(reminder["traitement"], consultation_data.get("traitement", ""))
            
            # Verify relance_date matches
            today_str = datetime.now().strftime("%Y-%m-%d")
            self.assertEqual(consultation_data.get("relance_date", ""), today_str)
            
            print(f"✅ Consultation context verified for consultation {consultation_id}")
    
    def test_phone_reminders_dashboard_integration(self):
        """Test that phone reminders endpoint returns proper format for Dashboard consumption"""
        response = requests.get(f"{self.base_url}/api/dashboard/phone-reminders")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify top-level structure matches Dashboard expectations
        self.assertIn("reminders", data)
        self.assertIsInstance(data["reminders"], list)
        
        reminders = data["reminders"]
        
        # Verify each reminder has all fields needed by Dashboard
        dashboard_required_fields = [
            "id", "patient_nom", "patient_prenom", "numero_whatsapp",
            "date_rdv", "heure_rdv", "motif", "raison_relance", "time"
        ]
        
        for reminder in reminders:
            for field in dashboard_required_fields:
                self.assertIn(field, reminder, f"Dashboard field missing: {field}")
            
            # Verify specific Dashboard field values
            self.assertEqual(reminder["raison_relance"], "Relance téléphonique programmée")
            self.assertEqual(reminder["time"], "10:00")  # Default reminder time
        
        print(f"✅ Dashboard integration format verified for {len(reminders)} reminders")
    
    def test_phone_reminders_vs_old_appointments_logic(self):
        """Test that new logic retrieves from consultations, not appointments with suivi_requis"""
        # This test verifies the fix mentioned in the review request
        response = requests.get(f"{self.base_url}/api/dashboard/phone-reminders")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        reminders = data["reminders"]
        
        # Verify that all reminders come from consultations with relance_date
        for reminder in reminders:
            consultation_id = reminder["consultation_id"]
            
            # Verify consultation exists and has relance_date for today
            consultation_response = requests.get(f"{self.base_url}/api/consultations/{consultation_id}")
            self.assertEqual(consultation_response.status_code, 200)
            consultation_data = consultation_response.json()
            
            today_str = datetime.now().strftime("%Y-%m-%d")
            self.assertEqual(consultation_data.get("relance_date", ""), today_str)
            
            print(f"✅ Reminder sourced from consultation {consultation_id} with relance_date={today_str}")
        
        print(f"✅ All {len(reminders)} reminders correctly sourced from consultations, not appointments")
    
    def test_phone_reminders_comprehensive_workflow(self):
        """Test complete phone reminders workflow end-to-end"""
        print("\n=== COMPREHENSIVE PHONE REMINDERS WORKFLOW TEST ===")
        
        # Step 1: Get phone reminders
        response = requests.get(f"{self.base_url}/api/dashboard/phone-reminders")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        reminders = data["reminders"]
        print(f"Step 1: Retrieved {len(reminders)} phone reminders ✅")
        
        # Step 2: Verify each reminder has complete data
        for i, reminder in enumerate(reminders):
            print(f"\nStep 2.{i+1}: Validating reminder for {reminder['patient_prenom']} {reminder['patient_nom']}")
            
            # Verify patient data
            self.assertNotEqual(reminder["patient_nom"], "")
            self.assertNotEqual(reminder["patient_prenom"], "")
            print(f"  - Patient info: {reminder['patient_prenom']} {reminder['patient_nom']} ✅")
            
            # Verify contact info
            if reminder["numero_whatsapp"]:
                print(f"  - WhatsApp: {reminder['numero_whatsapp']} ✅")
            
            # Verify consultation context
            self.assertNotEqual(reminder["observations"], "")
            self.assertNotEqual(reminder["traitement"], "")
            print(f"  - Consultation context: observations and treatment present ✅")
            
            # Verify relance date is today
            today_str = datetime.now().strftime("%Y-%m-%d")
            self.assertEqual(reminder["relance_date"], today_str)
            print(f"  - Relance date: {reminder['relance_date']} (today) ✅")
        
        # Step 3: Verify success criteria from review request
        print(f"\n=== SUCCESS CRITERIA VERIFICATION ===")
        
        # ✅ Phone reminders endpoint returns relances from consultations
        self.assertGreater(len(reminders), 0, "No reminders returned")
        print(f"✅ Phone reminders endpoint returns {len(reminders)} relances from consultations")
        
        # ✅ Demo data includes relances for today that appear in response
        patient_ids = [r["patient_id"] for r in reminders]
        self.assertIn("patient1", patient_ids, "patient1 relance missing")
        self.assertIn("patient2", patient_ids, "patient2 relance missing")
        print(f"✅ Demo data includes relances for today (patient1 and patient2 found)")
        
        # ✅ Patient information is correctly linked to consultation relances
        for reminder in reminders:
            self.assertNotEqual(reminder["patient_nom"], "")
            self.assertNotEqual(reminder["patient_prenom"], "")
        print(f"✅ Patient information correctly linked to consultation relances")
        
        # ✅ Response structure includes all necessary fields for Dashboard display
        required_fields = ["id", "patient_nom", "patient_prenom", "numero_whatsapp", 
                          "date_rdv", "heure_rdv", "motif", "consultation_id", 
                          "observations", "traitement", "relance_date"]
        for reminder in reminders:
            for field in required_fields:
                self.assertIn(field, reminder)
        print(f"✅ Response structure includes all necessary fields for Dashboard display")
        
        # ✅ Relances created with relance_date = today are retrieved correctly
        today_str = datetime.now().strftime("%Y-%m-%d")
        for reminder in reminders:
            self.assertEqual(reminder["relance_date"], today_str)
        print(f"✅ Relances with relance_date = today retrieved correctly")
        
        print(f"\n🎉 ALL SUCCESS CRITERIA MET - Phone reminders functionality working correctly!")


if __name__ == "__main__":
    unittest.main()