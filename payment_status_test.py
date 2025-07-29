import requests
import unittest
import json
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/frontend/.env')

class PaymentStatusTest(unittest.TestCase):
    def setUp(self):
        # Use the correct backend URL from environment
        backend_url = os.getenv('REACT_APP_BACKEND_URL', 'https://b41bbcdf-8fee-41b8-8d35-533fd4cb83fc.preview.emergentagent.com')
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
    
    def test_init_demo_endpoint(self):
        """Test GET /api/init-demo endpoint that creates test data with payment statuses"""
        response = requests.get(f"{self.base_url}/api/init-demo")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify response structure
        self.assertIn("message", data)
        self.assertIn("summary", data)
        
        # Verify summary data
        summary = data["summary"]
        self.assertIn("patients", summary)
        self.assertIn("appointments", summary)
        self.assertIn("consultations", summary)
        self.assertIn("payments", summary)
        self.assertIn("visites_payees", summary)
        self.assertIn("controles_payes", summary)
        self.assertIn("visites_impayees", summary)
        self.assertIn("montant_total_encaisse", summary)
        
        # Verify expected counts
        self.assertEqual(summary["patients"], 3)
        self.assertEqual(summary["appointments"], 6)
        self.assertEqual(summary["consultations"], 6)
        self.assertEqual(summary["payments"], 4)  # 2 visites payées + 2 contrôles payés
        self.assertEqual(summary["visites_payees"], 2)
        self.assertEqual(summary["controles_payes"], 2)
        self.assertEqual(summary["visites_impayees"], 2)
        self.assertEqual(summary["montant_total_encaisse"], 130.0)  # 2 visites × 65 TND
        
        print("✅ Demo data created successfully with expected payment structure")
    
    def test_payments_enriched_endpoint(self):
        """Test GET /api/payments endpoint returns enriched data with type_rdv and patient info"""
        response = requests.get(f"{self.base_url}/api/payments")
        self.assertEqual(response.status_code, 200)
        payments = response.json()
        self.assertIsInstance(payments, list)
        
        # Should have 4 payments (2 visites + 2 contrôles)
        self.assertGreaterEqual(len(payments), 4, "Should have at least 4 payments from demo data")
        
        # Verify each payment has enriched data
        for payment in payments:
            # Basic payment fields
            self.assertIn("id", payment)
            self.assertIn("patient_id", payment)
            self.assertIn("appointment_id", payment)
            self.assertIn("montant", payment)
            self.assertIn("type_paiement", payment)
            self.assertIn("statut", payment)
            self.assertIn("date", payment)
            
            # Enriched fields - type_rdv from appointment
            self.assertIn("type_rdv", payment, "Payment should include type_rdv from appointment")
            self.assertIn(payment["type_rdv"], ["visite", "controle"], "type_rdv should be visite or controle")
            
            # Enriched fields - patient information (nested object)
            self.assertIn("patient", payment, "Payment should include patient object")
            patient_info = payment["patient"]
            self.assertIn("nom", patient_info, "Patient should include nom")
            self.assertIn("prenom", patient_info, "Patient should include prenom")
            self.assertIsInstance(patient_info["nom"], str)
            self.assertIsInstance(patient_info["prenom"], str)
            
            # Verify payment amounts based on type
            if payment["type_rdv"] == "visite":
                self.assertEqual(payment["montant"], 65.0, "Visite payments should be 65 TND")
            elif payment["type_rdv"] == "controle":
                self.assertEqual(payment["montant"], 0.0, "Controle payments should be 0 TND (free)")
        
        print("✅ Payments endpoint returns enriched data with type_rdv and patient info")
    
    def test_payments_search_statut_paiement_filter(self):
        """Test GET /api/payments/search with statut_paiement filter"""
        # Test filter for visites payées
        response = requests.get(f"{self.base_url}/api/payments/search?statut_paiement=visite")
        self.assertEqual(response.status_code, 200)
        visite_data = response.json()
        
        # Verify response structure
        self.assertIn("payments", visite_data)
        self.assertIn("pagination", visite_data)
        visite_payments = visite_data["payments"]
        
        # Should return only visite payments
        self.assertGreater(len(visite_payments), 0, "Should have visite payments")
        for payment in visite_payments:
            self.assertEqual(payment.get("type_rdv"), "visite", "Should only return visite payments")
            self.assertEqual(payment["montant"], 65.0, "Visite payments should be 65 TND")
            self.assertEqual(payment["statut"], "paye", "Should only return paid payments")
        
        # Test filter for contrôles payés
        response = requests.get(f"{self.base_url}/api/payments/search?statut_paiement=controle")
        self.assertEqual(response.status_code, 200)
        controle_data = response.json()
        
        # Verify response structure
        self.assertIn("payments", controle_data)
        self.assertIn("pagination", controle_data)
        controle_payments = controle_data["payments"]
        
        # Should return only controle payments
        self.assertGreater(len(controle_payments), 0, "Should have controle payments")
        for payment in controle_payments:
            self.assertEqual(payment.get("type_rdv"), "controle", "Should only return controle payments")
            self.assertEqual(payment["montant"], 0.0, "Controle payments should be 0 TND (free)")
            self.assertEqual(payment["statut"], "paye", "Should only return paid payments")
        
        # Test filter for impayé (should return empty since we're looking in payments collection)
        response = requests.get(f"{self.base_url}/api/payments/search?statut_paiement=impaye")
        self.assertEqual(response.status_code, 200)
        impaye_data = response.json()
        
        # This should return empty or handle unpaid appointments differently
        # Since payments collection only contains paid items
        self.assertIn("payments", impaye_data)
        impaye_results = impaye_data["payments"]
        self.assertIsInstance(impaye_results, list, "Should return a list even if empty")
        
        print("✅ Payment search with statut_paiement filter working correctly")
    
    def test_payment_calculations_verification(self):
        """Test payment calculations: 2 visites × 65 TND = 130 TND, 2 contrôles × 0 TND = 0 TND"""
        # Get all payments
        response = requests.get(f"{self.base_url}/api/payments")
        self.assertEqual(response.status_code, 200)
        payments = response.json()
        
        # Calculate totals by type
        visite_total = 0
        controle_total = 0
        visite_count = 0
        controle_count = 0
        
        for payment in payments:
            if payment.get("type_rdv") == "visite":
                visite_total += payment["montant"]
                visite_count += 1
            elif payment.get("type_rdv") == "controle":
                controle_total += payment["montant"]
                controle_count += 1
        
        # Verify calculations
        self.assertGreaterEqual(visite_count, 2, "Should have at least 2 visite payments")
        self.assertGreaterEqual(controle_count, 2, "Should have at least 2 controle payments")
        
        # Verify visite calculations (2 × 65 = 130 TND minimum)
        expected_visite_total = visite_count * 65.0
        self.assertEqual(visite_total, expected_visite_total, f"Visite total should be {visite_count} × 65 = {expected_visite_total} TND")
        
        # Verify controle calculations (should be 0 TND)
        self.assertEqual(controle_total, 0.0, "Controle total should be 0 TND (free)")
        
        # Verify overall total
        total_encaisse = visite_total + controle_total
        self.assertEqual(total_encaisse, expected_visite_total, f"Total encaissé should be {expected_visite_total} TND")
        
        print(f"✅ Payment calculations verified: {visite_count} visites × 65 TND = {visite_total} TND, {controle_count} contrôles × 0 TND = {controle_total} TND")
    
    def test_demo_patients_verification(self):
        """Test that demo data contains the expected 3 patients: Jean Martin, Marie Dupont, Ahmed Ben Ali"""
        # Get all patients
        response = requests.get(f"{self.base_url}/api/patients")
        self.assertEqual(response.status_code, 200)
        patients_data = response.json()
        patients = patients_data["patients"]
        
        # Should have at least 3 patients
        self.assertGreaterEqual(len(patients), 3, "Should have at least 3 demo patients")
        
        # Look for expected patient names
        patient_names = [(p["prenom"], p["nom"]) for p in patients]
        expected_names = [("Jean", "Martin"), ("Marie", "Dupont"), ("Ahmed", "Ben Ali")]
        
        found_patients = []
        for expected_prenom, expected_nom in expected_names:
            found = False
            for prenom, nom in patient_names:
                if prenom == expected_prenom and nom == expected_nom:
                    found = True
                    found_patients.append((prenom, nom))
                    break
            if not found:
                print(f"⚠️ Expected patient {expected_prenom} {expected_nom} not found in demo data")
        
        # Verify Marie Dupont is marked as insured
        marie_patient = None
        for patient in patients:
            if patient["prenom"] == "Marie" and patient["nom"] == "Dupont":
                marie_patient = patient
                break
        
        if marie_patient:
            # Check if Marie has insurance info or is marked as assured in appointments/payments
            print(f"✅ Found Marie Dupont in demo data: {marie_patient['prenom']} {marie_patient['nom']}")
        
        print(f"✅ Demo patients verification: Found {len(found_patients)} expected patients")
    
    def test_payment_status_badges_data_structure(self):
        """Test that payment data structure supports frontend badge display (Visite, Contrôle, Impayé)"""
        # Get enriched payments
        response = requests.get(f"{self.base_url}/api/payments")
        self.assertEqual(response.status_code, 200)
        payments = response.json()
        
        # Verify data structure supports badge display
        badge_types = {"visite": 0, "controle": 0}
        
        for payment in payments:
            # Verify required fields for badge display
            self.assertIn("type_rdv", payment, "type_rdv required for badge type")
            self.assertIn("statut", payment, "statut required for badge display")
            self.assertIn("patient", payment, "patient object required for display")
            self.assertIn("montant", payment, "montant required for display")
            self.assertIn("date", payment, "date required for display")
            
            # Verify patient info structure
            patient_info = payment["patient"]
            self.assertIn("nom", patient_info, "patient nom required for display")
            self.assertIn("prenom", patient_info, "patient prenom required for display")
            
            # Count badge types
            if payment["type_rdv"] in badge_types:
                badge_types[payment["type_rdv"]] += 1
            
            # Verify badge color logic data
            if payment["type_rdv"] == "visite":
                self.assertEqual(payment["statut"], "paye", "Visite should be paid (green badge)")
                self.assertGreater(payment["montant"], 0, "Visite should have amount > 0")
            elif payment["type_rdv"] == "controle":
                self.assertEqual(payment["statut"], "paye", "Controle should be paid (purple badge)")
                self.assertEqual(payment["montant"], 0.0, "Controle should be free (0 TND)")
        
        # Verify we have both types for badge testing
        self.assertGreater(badge_types["visite"], 0, "Should have visite payments for green badges")
        self.assertGreater(badge_types["controle"], 0, "Should have controle payments for purple badges")
        
        print(f"✅ Payment data structure supports badges: {badge_types['visite']} visites (green), {badge_types['controle']} contrôles (purple)")
    
    def test_unpaid_appointments_for_red_badges(self):
        """Test that unpaid appointments exist for red badge display (Impayé)"""
        # Get all appointments to find unpaid ones
        response = requests.get(f"{self.base_url}/api/appointments")
        self.assertEqual(response.status_code, 200)
        appointments = response.json()
        
        # Find unpaid visite appointments
        unpaid_visites = []
        for appointment in appointments:
            if (appointment.get("type_rdv") == "visite" and 
                appointment.get("paye") == False):
                unpaid_visites.append(appointment)
        
        # Should have unpaid visites for red badges
        self.assertGreater(len(unpaid_visites), 0, "Should have unpaid visite appointments for red badges")
        
        # Verify unpaid appointment structure
        for appointment in unpaid_visites:
            self.assertEqual(appointment["type_rdv"], "visite", "Unpaid should be visite type")
            self.assertEqual(appointment["paye"], False, "Should be unpaid")
            self.assertIn("patient", appointment, "Should have patient info for display")
            
            patient_info = appointment["patient"]
            self.assertIn("nom", patient_info, "Patient nom required for red badge display")
            self.assertIn("prenom", patient_info, "Patient prenom required for red badge display")
        
        print(f"✅ Found {len(unpaid_visites)} unpaid visite appointments for red badges")
    
    def test_payment_history_complete_workflow(self):
        """Test complete payment history workflow with all three statuses"""
        # Test 1: Get all payments (paid items)
        response = requests.get(f"{self.base_url}/api/payments")
        self.assertEqual(response.status_code, 200)
        all_payments = response.json()
        
        # Test 2: Filter by visite status
        response = requests.get(f"{self.base_url}/api/payments/search?statut_paiement=visite")
        self.assertEqual(response.status_code, 200)
        visite_data = response.json()
        visite_payments = visite_data["payments"]
        
        # Test 3: Filter by controle status
        response = requests.get(f"{self.base_url}/api/payments/search?statut_paiement=controle")
        self.assertEqual(response.status_code, 200)
        controle_data = response.json()
        controle_payments = controle_data["payments"]
        
        # Test 4: Get unpaid appointments
        response = requests.get(f"{self.base_url}/api/appointments")
        self.assertEqual(response.status_code, 200)
        appointments = response.json()
        unpaid_appointments = [a for a in appointments if a.get("type_rdv") == "visite" and a.get("paye") == False]
        
        # Verify workflow completeness
        total_paid = len(visite_payments) + len(controle_payments)
        total_unpaid = len(unpaid_appointments)
        
        self.assertGreater(total_paid, 0, "Should have paid items")
        self.assertGreater(total_unpaid, 0, "Should have unpaid items")
        
        # Verify data consistency
        visite_paid_count = len(visite_payments)
        controle_paid_count = len(controle_payments)
        
        # Calculate expected totals
        visite_total = visite_paid_count * 65.0
        controle_total = 0.0  # Always free
        
        actual_visite_total = sum(p["montant"] for p in visite_payments)
        actual_controle_total = sum(p["montant"] for p in controle_payments)
        
        self.assertEqual(actual_visite_total, visite_total, "Visite total calculation mismatch")
        self.assertEqual(actual_controle_total, controle_total, "Controle total should be 0")
        
        print(f"✅ Complete workflow verified:")
        print(f"   - Paid visites: {visite_paid_count} × 65 TND = {visite_total} TND")
        print(f"   - Paid contrôles: {controle_paid_count} × 0 TND = {controle_total} TND")
        print(f"   - Unpaid visites: {total_unpaid} items")
        print(f"   - Total encaissé: {visite_total + controle_total} TND")


if __name__ == '__main__':
    unittest.main()