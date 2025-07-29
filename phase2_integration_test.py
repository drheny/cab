import requests
import unittest
import json
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/frontend/.env')

class Phase2IntegrationTest(unittest.TestCase):
    """
    Phase 2 Integration Tests - Testing complete backend-frontend integration
    focusing on enhanced patient model and Tunisia-specific features
    """
    
    def setUp(self):
        backend_url = os.getenv('REACT_APP_BACKEND_URL', 'https://b41bbcdf-8fee-41b8-8d35-533fd4cb83fc.preview.emergentagent.com')
        self.base_url = backend_url
        print(f"Testing Phase 2 integration at: {self.base_url}")
        # Initialize demo data
        self.init_demo_data()
    
    def init_demo_data(self):
        """Initialize demo data for testing"""
        try:
            response = requests.get(f"{self.base_url}/api/init-demo")
            self.assertEqual(response.status_code, 200)
            print("Demo data initialized for Phase 2 testing")
        except Exception as e:
            print(f"Error initializing demo data: {e}")
    
    def test_pagination_with_10_patients_per_page(self):
        """Test pagination specifically with 10 patients per page as required"""
        response = requests.get(f"{self.base_url}/api/patients?page=1&limit=10")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify pagination structure
        self.assertIn("patients", data)
        self.assertIn("total_count", data)
        self.assertIn("page", data)
        self.assertIn("limit", data)
        self.assertIn("total_pages", data)
        
        # Verify 10 patients per page limit
        self.assertEqual(data["limit"], 10)
        self.assertEqual(data["page"], 1)
        self.assertLessEqual(len(data["patients"]), 10)
        
        # Verify total_pages calculation
        expected_total_pages = (data["total_count"] + 9) // 10  # Ceiling division
        self.assertEqual(data["total_pages"], expected_total_pages)
        
        print(f"✅ Pagination test passed: {data['total_count']} patients, {data['total_pages']} pages")
    
    def test_search_functionality_comprehensive(self):
        """Test search by nom, prénom, and date_naissance as specified"""
        # Test search by nom (case-insensitive)
        response = requests.get(f"{self.base_url}/api/patients?search=ben ahmed")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        for patient in data["patients"]:
            found = ("ben ahmed" in patient.get("nom", "").lower() or 
                    "ben ahmed" in patient.get("prenom", "").lower() or
                    "ben ahmed" in patient.get("date_naissance", "").lower())
            self.assertTrue(found, f"Search by nom failed for: {patient}")
        
        # Test search by prénom
        response = requests.get(f"{self.base_url}/api/patients?search=yassine")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Test search by date_naissance
        response = requests.get(f"{self.base_url}/api/patients?search=2020")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Test partial matches
        response = requests.get(f"{self.base_url}/api/patients?search=Ben")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        print("✅ Comprehensive search functionality test passed")
    
    def test_patient_count_endpoint_accuracy(self):
        """Test that patient count endpoint returns correct total"""
        # Get count from dedicated endpoint
        response = requests.get(f"{self.base_url}/api/patients/count")
        self.assertEqual(response.status_code, 200)
        count_data = response.json()
        count_from_endpoint = count_data["count"]
        
        # Get count from pagination endpoint
        response = requests.get(f"{self.base_url}/api/patients?page=1&limit=1")
        self.assertEqual(response.status_code, 200)
        pagination_data = response.json()
        count_from_pagination = pagination_data["total_count"]
        
        # Verify both endpoints return same count
        self.assertEqual(count_from_endpoint, count_from_pagination)
        
        print(f"✅ Patient count accuracy test passed: {count_from_endpoint} patients")
    
    def test_patient_creation_with_new_model_structure(self):
        """Test patient creation with complete new model structure"""
        new_patient = {
            "nom": "Testeur Phase2",
            "prenom": "Integration",
            "date_naissance": "2019-03-15",
            "adresse": "456 Avenue Bourguiba, Tunis, Tunisie",
            "pere": {
                "nom": "Ahmed Testeur Phase2",
                "telephone": "21650111222",
                "fonction": "Architecte"
            },
            "mere": {
                "nom": "Amina Testeur Phase2",
                "telephone": "21650111223",
                "fonction": "Pharmacienne"
            },
            "numero_whatsapp": "21650111222",
            "notes": "Patient créé pour test d'intégration Phase 2",
            "antecedents": "Allergie aux arachides",
            "consultations": [
                {
                    "date": "2024-01-10",
                    "type": "visite",
                    "id_consultation": "phase2_cons_1"
                },
                {
                    "date": "2024-06-15",
                    "type": "controle",
                    "id_consultation": "phase2_cons_2"
                }
            ]
        }
        
        # Create patient
        response = requests.post(f"{self.base_url}/api/patients", json=new_patient)
        self.assertEqual(response.status_code, 200)
        create_data = response.json()
        patient_id = create_data["patient_id"]
        
        # Retrieve and verify all fields
        response = requests.get(f"{self.base_url}/api/patients/{patient_id}")
        self.assertEqual(response.status_code, 200)
        patient_data = response.json()
        
        # Verify basic fields
        self.assertEqual(patient_data["nom"], "Testeur Phase2")
        self.assertEqual(patient_data["prenom"], "Integration")
        self.assertEqual(patient_data["date_naissance"], "2019-03-15")
        self.assertEqual(patient_data["adresse"], "456 Avenue Bourguiba, Tunis, Tunisie")
        
        # Verify parent information
        self.assertEqual(patient_data["pere"]["nom"], "Ahmed Testeur Phase2")
        self.assertEqual(patient_data["pere"]["telephone"], "21650111222")
        self.assertEqual(patient_data["pere"]["fonction"], "Architecte")
        self.assertEqual(patient_data["mere"]["nom"], "Amina Testeur Phase2")
        self.assertEqual(patient_data["mere"]["telephone"], "21650111223")
        self.assertEqual(patient_data["mere"]["fonction"], "Pharmacienne")
        
        # Verify notes and antecedents
        self.assertEqual(patient_data["notes"], "Patient créé pour test d'intégration Phase 2")
        self.assertEqual(patient_data["antecedents"], "Allergie aux arachides")
        
        # Verify consultations
        self.assertEqual(len(patient_data["consultations"]), 2)
        self.assertEqual(patient_data["consultations"][0]["date"], "2024-01-10")
        self.assertEqual(patient_data["consultations"][1]["type"], "controle")
        
        # Clean up
        requests.delete(f"{self.base_url}/api/patients/{patient_id}")
        
        print("✅ Patient creation with new model structure test passed")
    
    def test_age_calculation_formatting(self):
        """Test age calculation in 'X ans, Y mois, Z jours' format"""
        test_cases = [
            {
                "date_naissance": "2020-01-01",
                "name": "TestAge2020"
            },
            {
                "date_naissance": "2023-06-15",
                "name": "TestAge2023"
            },
            {
                "date_naissance": "2024-12-01",
                "name": "TestAge2024"
            }
        ]
        
        created_patients = []
        
        for test_case in test_cases:
            # Create patient
            patient = {
                "nom": test_case["name"],
                "prenom": "AgeTest",
                "date_naissance": test_case["date_naissance"]
            }
            
            response = requests.post(f"{self.base_url}/api/patients", json=patient)
            self.assertEqual(response.status_code, 200)
            patient_id = response.json()["patient_id"]
            created_patients.append(patient_id)
            
            # Get patient and verify age format
            response = requests.get(f"{self.base_url}/api/patients/{patient_id}")
            self.assertEqual(response.status_code, 200)
            patient_data = response.json()
            
            age = patient_data["age"]
            print(f"Patient born {test_case['date_naissance']}: Age = '{age}'")
            
            # Verify age format contains expected patterns
            age_patterns = ["an", "mois", "jour"]
            has_valid_pattern = any(pattern in age for pattern in age_patterns)
            self.assertTrue(has_valid_pattern, f"Age format invalid: '{age}'")
            
            # Verify age is not empty for valid birth dates
            if test_case["date_naissance"]:
                self.assertNotEqual(age, "", f"Age should not be empty for birth date {test_case['date_naissance']}")
        
        # Clean up
        for patient_id in created_patients:
            requests.delete(f"{self.base_url}/api/patients/{patient_id}")
        
        print("✅ Age calculation formatting test passed")
    
    def test_tunisia_whatsapp_link_generation(self):
        """Test WhatsApp link generation for Tunisia format (216xxxxxxxx)"""
        test_cases = [
            {
                "numero": "21650123456",
                "expected_link": "https://wa.me/21650123456",
                "should_generate": True
            },
            {
                "numero": "21654321098",
                "expected_link": "https://wa.me/21654321098",
                "should_generate": True
            },
            {
                "numero": "0612345678",  # Invalid format
                "expected_link": "",
                "should_generate": False
            },
            {
                "numero": "216123",  # Too short
                "expected_link": "",
                "should_generate": False
            },
            {
                "numero": "33612345678",  # Wrong country code
                "expected_link": "",
                "should_generate": False
            }
        ]
        
        created_patients = []
        
        for i, test_case in enumerate(test_cases):
            # Create patient with WhatsApp number
            patient = {
                "nom": f"WhatsAppTest{i}",
                "prenom": "Tunisia",
                "numero_whatsapp": test_case["numero"]
            }
            
            response = requests.post(f"{self.base_url}/api/patients", json=patient)
            self.assertEqual(response.status_code, 200)
            patient_id = response.json()["patient_id"]
            created_patients.append(patient_id)
            
            # Get patient and verify WhatsApp link
            response = requests.get(f"{self.base_url}/api/patients/{patient_id}")
            self.assertEqual(response.status_code, 200)
            patient_data = response.json()
            
            actual_link = patient_data["lien_whatsapp"]
            print(f"Number: {test_case['numero']} -> Link: '{actual_link}'")
            
            if test_case["should_generate"]:
                self.assertEqual(actual_link, test_case["expected_link"])
            else:
                self.assertEqual(actual_link, "")
        
        # Clean up
        for patient_id in created_patients:
            requests.delete(f"{self.base_url}/api/patients/{patient_id}")
        
        print("✅ Tunisia WhatsApp link generation test passed")
    
    def test_consultation_dates_calculation(self):
        """Test first and last consultation date calculations"""
        # Create patient with multiple consultations
        patient = {
            "nom": "ConsultationTest",
            "prenom": "Dates",
            "consultations": [
                {
                    "date": "2024-03-15",
                    "type": "visite",
                    "id_consultation": "cons_1"
                },
                {
                    "date": "2024-01-10",
                    "type": "controle",
                    "id_consultation": "cons_2"
                },
                {
                    "date": "2024-06-20",
                    "type": "visite",
                    "id_consultation": "cons_3"
                }
            ]
        }
        
        response = requests.post(f"{self.base_url}/api/patients", json=patient)
        self.assertEqual(response.status_code, 200)
        patient_id = response.json()["patient_id"]
        
        # Get patient and verify consultation dates
        response = requests.get(f"{self.base_url}/api/patients/{patient_id}")
        self.assertEqual(response.status_code, 200)
        patient_data = response.json()
        
        # Verify first and last consultation dates
        self.assertEqual(patient_data["date_premiere_consultation"], "2024-01-10")
        self.assertEqual(patient_data["date_derniere_consultation"], "2024-06-20")
        
        # Clean up
        requests.delete(f"{self.base_url}/api/patients/{patient_id}")
        
        print("✅ Consultation dates calculation test passed")
    
    def test_patient_updates_with_computed_fields(self):
        """Test that patient updates recalculate computed fields"""
        # Create patient
        patient = {
            "nom": "UpdateTest",
            "prenom": "Computed",
            "date_naissance": "2020-01-01",
            "numero_whatsapp": "21650999888",
            "consultations": [
                {
                    "date": "2024-01-01",
                    "type": "visite",
                    "id_consultation": "update_cons_1"
                }
            ]
        }
        
        response = requests.post(f"{self.base_url}/api/patients", json=patient)
        self.assertEqual(response.status_code, 200)
        patient_id = response.json()["patient_id"]
        
        # Get initial state
        response = requests.get(f"{self.base_url}/api/patients/{patient_id}")
        self.assertEqual(response.status_code, 200)
        initial_data = response.json()
        
        # Update patient with new consultation and birth date
        updated_patient = initial_data.copy()
        updated_patient["date_naissance"] = "2021-01-01"  # Change birth date
        updated_patient["numero_whatsapp"] = "21650777666"  # Change WhatsApp
        updated_patient["consultations"].append({
            "date": "2024-12-01",
            "type": "controle",
            "id_consultation": "update_cons_2"
        })
        
        response = requests.put(f"{self.base_url}/api/patients/{patient_id}", json=updated_patient)
        self.assertEqual(response.status_code, 200)
        
        # Get updated state and verify computed fields were recalculated
        response = requests.get(f"{self.base_url}/api/patients/{patient_id}")
        self.assertEqual(response.status_code, 200)
        updated_data = response.json()
        
        # Verify age was recalculated (should be different)
        self.assertNotEqual(initial_data["age"], updated_data["age"])
        
        # Verify WhatsApp link was recalculated
        self.assertEqual(updated_data["lien_whatsapp"], "https://wa.me/21650777666")
        
        # Verify consultation dates were recalculated
        self.assertEqual(updated_data["date_premiere_consultation"], "2024-01-01")
        self.assertEqual(updated_data["date_derniere_consultation"], "2024-12-01")
        
        # Clean up
        requests.delete(f"{self.base_url}/api/patients/{patient_id}")
        
        print("✅ Patient updates with computed fields test passed")
    
    def test_edge_cases(self):
        """Test various edge cases"""
        # Test empty search results
        response = requests.get(f"{self.base_url}/api/patients?search=NonExistentPatientName12345")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data["patients"]), 0)
        self.assertEqual(data["total_count"], 0)
        
        # Test invalid pagination parameters (should handle gracefully)
        response = requests.get(f"{self.base_url}/api/patients?page=0&limit=0")
        # Should either return error or handle gracefully
        self.assertIn(response.status_code, [200, 400, 422])
        
        # Test very large page number
        response = requests.get(f"{self.base_url}/api/patients?page=9999&limit=10")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data["patients"]), 0)
        
        # Test patient with no consultations
        patient = {
            "nom": "NoConsultations",
            "prenom": "Test",
            "consultations": []
        }
        
        response = requests.post(f"{self.base_url}/api/patients", json=patient)
        self.assertEqual(response.status_code, 200)
        patient_id = response.json()["patient_id"]
        
        response = requests.get(f"{self.base_url}/api/patients/{patient_id}")
        self.assertEqual(response.status_code, 200)
        patient_data = response.json()
        
        # Should have empty consultation dates
        self.assertEqual(patient_data["date_premiere_consultation"], "")
        self.assertEqual(patient_data["date_derniere_consultation"], "")
        
        # Clean up
        requests.delete(f"{self.base_url}/api/patients/{patient_id}")
        
        print("✅ Edge cases test passed")
    
    def test_performance_basic(self):
        """Basic performance test for search and pagination"""
        import time
        
        # Test search performance
        start_time = time.time()
        response = requests.get(f"{self.base_url}/api/patients?search=Ben")
        search_time = time.time() - start_time
        
        self.assertEqual(response.status_code, 200)
        self.assertLess(search_time, 2.0, f"Search took too long: {search_time:.2f}s")
        
        # Test pagination performance
        start_time = time.time()
        response = requests.get(f"{self.base_url}/api/patients?page=1&limit=10")
        pagination_time = time.time() - start_time
        
        self.assertEqual(response.status_code, 200)
        self.assertLess(pagination_time, 2.0, f"Pagination took too long: {pagination_time:.2f}s")
        
        print(f"✅ Performance test passed - Search: {search_time:.2f}s, Pagination: {pagination_time:.2f}s")

if __name__ == "__main__":
    unittest.main()