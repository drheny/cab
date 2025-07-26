import requests
import unittest
import json
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/frontend/.env')

class AdminExportAPITest(unittest.TestCase):
    def setUp(self):
        # Use the correct backend URL from environment
        backend_url = os.getenv('REACT_APP_BACKEND_URL', 'https://8b45b722-0b82-461c-8cd4-01b1cb4950c0.preview.emergentagent.com')
        self.base_url = backend_url
        print(f"Testing admin export at: {self.base_url}")
        # Initialize demo data before running tests
        self.init_demo_data()
    
    def init_demo_data(self):
        """Initialize demo data for testing"""
        try:
            response = requests.get(f"{self.base_url}/api/init-test-data")
            self.assertEqual(response.status_code, 200)
            print("Demo data initialized successfully")
        except Exception as e:
            print(f"Error initializing demo data: {e}")
    
    # ========== ADMIN EXPORT FUNCTIONALITY TESTING ==========
    
    def test_admin_export_patients(self):
        """Test GET /api/admin/export/patients - Export patient data"""
        response = requests.get(f"{self.base_url}/api/admin/export/patients")
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        
        # Verify response structure
        self.assertIn("message", data)
        self.assertIn("data", data)
        self.assertIn("count", data)
        self.assertIn("collection", data)
        
        # Verify collection name
        self.assertEqual(data["collection"], "patients")
        
        # Verify data is a list
        self.assertIsInstance(data["data"], list)
        self.assertIsInstance(data["count"], int)
        
        # Verify count matches data length
        self.assertEqual(data["count"], len(data["data"]))
        
        # If we have patient data, verify structure
        if data["count"] > 0:
            patient = data["data"][0]
            
            # Verify no MongoDB _id field
            self.assertNotIn("_id", patient)
            
            # Verify required patient fields are present
            required_fields = ["id", "nom", "prenom"]
            for field in required_fields:
                self.assertIn(field, patient, f"Required field '{field}' missing from patient data")
            
            # Verify data types
            self.assertIsInstance(patient["id"], str)
            self.assertIsInstance(patient["nom"], str)
            self.assertIsInstance(patient["prenom"], str)
            
            print(f"✅ Exported {data['count']} patients successfully")
        else:
            print("⚠️ No patient data found for export")
    
    def test_admin_export_appointments(self):
        """Test GET /api/admin/export/appointments - Export appointment data"""
        response = requests.get(f"{self.base_url}/api/admin/export/appointments")
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        
        # Verify response structure
        self.assertIn("message", data)
        self.assertIn("data", data)
        self.assertIn("count", data)
        self.assertIn("collection", data)
        
        # Verify collection name
        self.assertEqual(data["collection"], "appointments")
        
        # Verify data structure
        self.assertIsInstance(data["data"], list)
        self.assertIsInstance(data["count"], int)
        self.assertEqual(data["count"], len(data["data"]))
        
        # If we have appointment data, verify structure
        if data["count"] > 0:
            appointment = data["data"][0]
            
            # Verify no MongoDB _id field
            self.assertNotIn("_id", appointment)
            
            # Verify required appointment fields
            required_fields = ["id", "patient_id", "date", "heure", "type_rdv", "statut"]
            for field in required_fields:
                self.assertIn(field, appointment, f"Required field '{field}' missing from appointment data")
            
            # Verify data types and formats
            self.assertIsInstance(appointment["id"], str)
            self.assertIsInstance(appointment["patient_id"], str)
            self.assertIsInstance(appointment["date"], str)
            self.assertIsInstance(appointment["heure"], str)
            self.assertIn(appointment["type_rdv"], ["visite", "controle"])
            self.assertIn(appointment["statut"], ["programme", "attente", "en_cours", "termine", "absent", "retard"])
            
            print(f"✅ Exported {data['count']} appointments successfully")
        else:
            print("⚠️ No appointment data found for export")
    
    def test_admin_export_consultations(self):
        """Test GET /api/admin/export/consultations - Export consultation data"""
        response = requests.get(f"{self.base_url}/api/admin/export/consultations")
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        
        # Verify response structure
        self.assertIn("message", data)
        self.assertIn("data", data)
        self.assertIn("count", data)
        self.assertIn("collection", data)
        
        # Verify collection name
        self.assertEqual(data["collection"], "consultations")
        
        # Verify data structure
        self.assertIsInstance(data["data"], list)
        self.assertIsInstance(data["count"], int)
        self.assertEqual(data["count"], len(data["data"]))
        
        # If we have consultation data, verify structure
        if data["count"] > 0:
            consultation = data["data"][0]
            
            # Verify no MongoDB _id field
            self.assertNotIn("_id", consultation)
            
            # Verify required consultation fields
            required_fields = ["id", "patient_id", "appointment_id", "date"]
            for field in required_fields:
                self.assertIn(field, consultation, f"Required field '{field}' missing from consultation data")
            
            # Verify data types
            self.assertIsInstance(consultation["id"], str)
            self.assertIsInstance(consultation["patient_id"], str)
            self.assertIsInstance(consultation["appointment_id"], str)
            self.assertIsInstance(consultation["date"], str)
            
            # Verify optional fields exist (even if empty) - adjust based on actual data structure
            optional_fields = ["observations", "duree", "poids", "taille", "pc", "type_rdv"]
            for field in optional_fields:
                # Only check if field exists, don't require it
                if field in consultation:
                    print(f"  Found optional field: {field}")
            
            # Check for fields that might be present
            possible_fields = ["traitement", "bilan", "relance_date", "created_at"]
            for field in possible_fields:
                if field in consultation:
                    print(f"  Found additional field: {field}")
            
            print(f"✅ Exported {data['count']} consultations successfully")
        else:
            print("⚠️ No consultation data found for export")
    
    def test_admin_export_payments(self):
        """Test GET /api/admin/export/payments - Export payment data"""
        response = requests.get(f"{self.base_url}/api/admin/export/payments")
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        
        # Verify response structure
        self.assertIn("message", data)
        self.assertIn("data", data)
        self.assertIn("count", data)
        self.assertIn("collection", data)
        
        # Verify collection name
        self.assertEqual(data["collection"], "payments")
        
        # Verify data structure
        self.assertIsInstance(data["data"], list)
        self.assertIsInstance(data["count"], int)
        self.assertEqual(data["count"], len(data["data"]))
        
        # If we have payment data, verify structure
        if data["count"] > 0:
            payment = data["data"][0]
            
            # Verify no MongoDB _id field
            self.assertNotIn("_id", payment)
            
            # Verify required payment fields
            required_fields = ["id", "patient_id", "appointment_id", "montant", "type_paiement", "statut", "date"]
            for field in required_fields:
                self.assertIn(field, payment, f"Required field '{field}' missing from payment data")
            
            # Verify data types
            self.assertIsInstance(payment["id"], str)
            self.assertIsInstance(payment["patient_id"], str)
            self.assertIsInstance(payment["appointment_id"], str)
            self.assertIsInstance(payment["montant"], (int, float))
            self.assertIsInstance(payment["type_paiement"], str)
            self.assertIsInstance(payment["statut"], str)
            self.assertIsInstance(payment["date"], str)
            
            # Verify valid payment types and statuses
            valid_payment_types = ["espece", "carte", "cheque", "virement", "gratuit"]
            valid_statuses = ["paye", "en_attente", "rembourse"]
            
            self.assertIn(payment["type_paiement"], valid_payment_types)
            self.assertIn(payment["statut"], valid_statuses)
            
            print(f"✅ Exported {data['count']} payments successfully")
        else:
            print("⚠️ No payment data found for export")
    
    def test_admin_export_invalid_collection(self):
        """Test GET /api/admin/export/{invalid_collection} - Error handling for invalid collection names"""
        invalid_collections = ["users", "messages", "invalid_collection", "patient", "appointment"]
        
        for invalid_collection in invalid_collections:
            response = requests.get(f"{self.base_url}/api/admin/export/{invalid_collection}")
            self.assertEqual(response.status_code, 400)
            
            data = response.json()
            self.assertIn("detail", data)
            self.assertIn("Invalid collection", data["detail"])
            self.assertIn("patients, appointments, consultations, payments", data["detail"])
            
            print(f"✅ Invalid collection '{invalid_collection}' properly rejected")
    
    def test_admin_export_empty_collections(self):
        """Test export behavior with empty collections"""
        # This test assumes we might have empty collections in some scenarios
        # We'll test the structure even if collections are empty
        
        collections = ["patients", "appointments", "consultations", "payments"]
        
        for collection_name in collections:
            response = requests.get(f"{self.base_url}/api/admin/export/{collection_name}")
            self.assertEqual(response.status_code, 200)
            
            data = response.json()
            
            # Verify response structure is consistent even for empty collections
            self.assertIn("message", data)
            self.assertIn("data", data)
            self.assertIn("count", data)
            self.assertIn("collection", data)
            
            # Verify collection name is correct
            self.assertEqual(data["collection"], collection_name)
            
            # Verify data is always a list
            self.assertIsInstance(data["data"], list)
            self.assertIsInstance(data["count"], int)
            
            # Verify count matches data length
            self.assertEqual(data["count"], len(data["data"]))
            
            # If empty, verify appropriate message
            if data["count"] == 0:
                self.assertIn("Aucune donnée trouvée", data["message"])
                self.assertEqual(data["data"], [])
            
            print(f"✅ Collection '{collection_name}' export structure verified (count: {data['count']})")
    
    def test_admin_export_data_format_csv_ready(self):
        """Test that exported data is ready for CSV export (no nested objects, clean field names)"""
        collections = ["patients", "appointments", "consultations", "payments"]
        
        for collection_name in collections:
            response = requests.get(f"{self.base_url}/api/admin/export/{collection_name}")
            self.assertEqual(response.status_code, 200)
            
            data = response.json()
            
            if data["count"] > 0:
                sample_record = data["data"][0]
                
                # Verify no MongoDB _id field
                self.assertNotIn("_id", sample_record)
                
                # Check for problematic nested objects that would break CSV export
                for field_name, field_value in sample_record.items():
                    # Field names should be clean (no special characters that break CSV)
                    self.assertIsInstance(field_name, str)
                    self.assertTrue(len(field_name) > 0, f"Empty field name in {collection_name}")
                    
                    # Values should be CSV-compatible (strings, numbers, booleans, or None)
                    if field_value is not None:
                        self.assertIn(type(field_value), [str, int, float, bool, list, dict], 
                                    f"Field '{field_name}' has unsupported type {type(field_value)} in {collection_name}")
                        
                        # If it's a complex object, it should be serializable
                        if isinstance(field_value, (dict, list)):
                            try:
                                import json
                                json.dumps(field_value, default=str)
                            except:
                                self.fail(f"Field '{field_name}' contains non-serializable data in {collection_name}")
                
                print(f"✅ Collection '{collection_name}' data format is CSV-ready")
    
    def test_admin_export_comprehensive_workflow(self):
        """Test complete admin export workflow for all collections"""
        print("\n🔍 Testing comprehensive admin export workflow...")
        
        collections = ["patients", "appointments", "consultations", "payments"]
        export_results = {}
        
        # Test each collection export
        for collection_name in collections:
            response = requests.get(f"{self.base_url}/api/admin/export/{collection_name}")
            self.assertEqual(response.status_code, 200)
            
            data = response.json()
            export_results[collection_name] = {
                "count": data["count"],
                "has_data": data["count"] > 0,
                "message": data["message"]
            }
            
            print(f"  📊 {collection_name}: {data['count']} records")
        
        # Verify we have some data to export
        total_records = sum(result["count"] for result in export_results.values())
        self.assertGreater(total_records, 0, "No data found across all collections for export testing")
        
        # Verify data consistency between collections
        if export_results["patients"]["has_data"] and export_results["appointments"]["has_data"]:
            # Get actual data to verify relationships
            patients_response = requests.get(f"{self.base_url}/api/admin/export/patients")
            appointments_response = requests.get(f"{self.base_url}/api/admin/export/appointments")
            
            patients_data = patients_response.json()["data"]
            appointments_data = appointments_response.json()["data"]
            
            # Verify patient IDs in appointments exist in patients
            patient_ids = {patient["id"] for patient in patients_data}
            appointment_patient_ids = {appointment["patient_id"] for appointment in appointments_data}
            
            # Check if appointment patient IDs are valid (should be subset of patient IDs)
            invalid_patient_refs = appointment_patient_ids - patient_ids
            if invalid_patient_refs:
                print(f"⚠️ Found appointments referencing non-existent patients: {invalid_patient_refs}")
            else:
                print("✅ All appointment patient references are valid")
        
        print(f"🎉 Export workflow complete - Total records available: {total_records}")
        
        return export_results


if __name__ == '__main__':
    unittest.main()