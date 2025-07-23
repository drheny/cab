#!/usr/bin/env python3
"""
Test script for the corrected 'Impayé' filter functionality
Priority test from review request - testing the fix for unpaid consultations
"""

import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/frontend/.env')

def test_impaye_filter_correction():
    """Test the corrected 'Impayé' filter functionality - Priority Test from Review Request"""
    
    # Get backend URL from environment
    backend_url = os.getenv('REACT_APP_BACKEND_URL', 'https://98ea2688-e431-4ee4-a33d-1c7cb0edbedd.preview.emergentagent.com')
    base_url = backend_url
    
    print(f"\n🔍 TESTING IMPAYÉ FILTER CORRECTION - Priority Test")
    print(f"Backend URL: {base_url}")
    
    try:
        # Step 1: Initialize test data with unpaid consultations
        print("\nStep 1: Initializing test data...")
        response = requests.get(f"{base_url}/api/init-test-data")
        
        if response.status_code != 200:
            print(f"❌ Failed to initialize test data: {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
        init_data = response.json()
        print(f"✅ Test data initialized: {init_data.get('summary', {})}")
        
        # Verify expected data structure
        summary = init_data.get('summary', {})
        expected_checks = [
            ('patients', 3, "Should have 3 test patients"),
            ('appointments', 6, "Should have 6 appointments"),
            ('consultations', 6, "Should have 6 consultations"),
            ('payments', 4, "Should have 4 payment records"),
            ('visites_payees', 2, "Should have 2 paid visits"),
            ('controles_payes', 2, "Should have 2 paid controls"),
            ('visites_impayees', 2, "Should have 2 unpaid visits")
        ]
        
        for key, expected_value, description in expected_checks:
            actual_value = summary.get(key)
            if actual_value != expected_value:
                print(f"❌ {description}: expected {expected_value}, got {actual_value}")
                return False
            print(f"✅ {description}: {actual_value}")
        
        # Step 2: Test Visite filter (paid visits)
        print("\nStep 2: Testing Visite filter...")
        response = requests.get(f"{base_url}/api/payments/search?statut_paiement=visite")
        
        if response.status_code != 200:
            print(f"❌ Visite filter request failed: {response.status_code}")
            return False
        
        visite_data = response.json()
        if 'payments' not in visite_data:
            print("❌ Response should contain 'payments' array")
            return False
        
        visite_payments = visite_data['payments']
        print(f"✅ Visite filter returned {len(visite_payments)} payments")
        
        if len(visite_payments) != 2:
            print(f"❌ Should return 2 paid visite appointments, got {len(visite_payments)}")
            return False
        
        # Verify visite payment structure
        for payment in visite_payments:
            if payment.get('type_rdv') != 'visite':
                print(f"❌ Payment should be visite type, got {payment.get('type_rdv')}")
                return False
            if payment.get('statut') != 'paye':
                print(f"❌ Payment should be paid status, got {payment.get('statut')}")
                return False
            if payment.get('montant') != 65.0:
                print(f"❌ Payment should be 65 TND, got {payment.get('montant')}")
                return False
            if 'patient' not in payment:
                print("❌ Payment should include patient information")
                return False
        
        print("✅ Visite payments structure validated")
        
        # Step 3: Test Contrôle filter (paid controls)
        print("\nStep 3: Testing Contrôle filter...")
        response = requests.get(f"{base_url}/api/payments/search?statut_paiement=controle")
        
        if response.status_code != 200:
            print(f"❌ Contrôle filter request failed: {response.status_code}")
            return False
        
        controle_data = response.json()
        if 'payments' not in controle_data:
            print("❌ Response should contain 'payments' array")
            return False
        
        controle_payments = controle_data['payments']
        print(f"✅ Contrôle filter returned {len(controle_payments)} payments")
        
        if len(controle_payments) != 2:
            print(f"❌ Should return 2 paid contrôle appointments, got {len(controle_payments)}")
            return False
        
        # Verify contrôle payment structure
        for payment in controle_payments:
            if payment.get('type_rdv') != 'controle':
                print(f"❌ Payment should be controle type, got {payment.get('type_rdv')}")
                return False
            if payment.get('statut') != 'paye':
                print(f"❌ Payment should be paid status, got {payment.get('statut')}")
                return False
            if payment.get('montant') != 0.0:
                print(f"❌ Payment should be 0 TND (gratuit), got {payment.get('montant')}")
                return False
        
        print("✅ Contrôle payments structure validated")
        
        # Step 4: Test Impayé filter (THE MAIN TEST - corrected functionality)
        print("\nStep 4: Testing Impayé filter (CORRECTED FUNCTIONALITY)...")
        response = requests.get(f"{base_url}/api/payments/search?statut_paiement=impaye")
        
        if response.status_code != 200:
            print(f"❌ Impayé filter request failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
        impaye_data = response.json()
        if 'payments' not in impaye_data:
            print("❌ Response should contain 'payments' array")
            return False
        
        impaye_payments = impaye_data['payments']
        print(f"✅ Impayé filter returned {len(impaye_payments)} unpaid consultations")
        
        if len(impaye_payments) != 2:
            print(f"❌ Should return 2 unpaid visite appointments, got {len(impaye_payments)}")
            return False
        
        # Verify impayé payment structure (these come from appointments, not payments collection)
        for payment in impaye_payments:
            if payment.get('type_rdv') != 'visite':
                print(f"❌ Unpaid should only be visite type, got {payment.get('type_rdv')}")
                return False
            if payment.get('statut') != 'impaye':
                print(f"❌ Should have impaye status, got {payment.get('statut')}")
                return False
            if payment.get('montant') != 65.0:
                print(f"❌ Should be 65 TND, got {payment.get('montant')}")
                return False
            if 'patient' not in payment:
                print("❌ Should include patient information")
                return False
            
            # Verify patient info is complete
            patient = payment['patient']
            if 'nom' not in patient or 'prenom' not in patient:
                print("❌ Patient should have nom and prenom")
                return False
            if not patient['nom'] or not patient['prenom']:
                print("❌ Patient name should not be empty")
                return False
        
        print("✅ Impayé payments structure validated")
        
        # Step 5: Verify patient names in unpaid consultations
        print("\nStep 5: Verifying patient information in unpaid consultations...")
        patient_names = [(p['patient']['prenom'], p['patient']['nom']) for p in impaye_payments]
        print(f"✅ Unpaid consultations for patients: {patient_names}")
        
        # Should include Marie Dupont and Ahmed Ben Ali based on test data
        expected_patients = [('Marie', 'Dupont'), ('Ahmed', 'Ben Ali')]
        for expected_patient in expected_patients:
            found = any(p[0] == expected_patient[0] and p[1] == expected_patient[1] for p in patient_names)
            if not found:
                print(f"❌ Expected patient {expected_patient} not found in unpaid consultations")
                return False
        
        print("✅ Expected patients found in unpaid consultations")
        
        # Step 6: Verify pagination and response structure
        print("\nStep 6: Verifying response structure and pagination...")
        if 'pagination' not in impaye_data:
            print("❌ Response should include pagination object")
            return False
        
        pagination = impaye_data['pagination']
        required_pagination_fields = ['current_page', 'total_pages', 'total_count', 'limit']
        for field in required_pagination_fields:
            if field not in pagination:
                print(f"❌ Pagination should include {field}")
                return False
            if not isinstance(pagination[field], int):
                print(f"❌ {field} should be integer")
                return False
        
        print(f"✅ Pagination: total_count={pagination['total_count']}, current_page={pagination['current_page']}, limit={pagination['limit']}")
        
        # Step 7: Test that unpaid consultations are NOT in payments collection
        print("\nStep 7: Verifying unpaid consultations are NOT in payments collection...")
        response = requests.get(f"{base_url}/api/payments")
        
        if response.status_code != 200:
            print(f"❌ Failed to get all payments: {response.status_code}")
            return False
        
        all_payments = response.json()
        payment_appointment_ids = [p.get('appointment_id') for p in all_payments if p.get('appointment_id')]
        
        # Verify that unpaid appointment IDs are NOT in payments collection
        for unpaid_payment in impaye_payments:
            unpaid_appointment_id = unpaid_payment.get('appointment_id')
            if unpaid_appointment_id in payment_appointment_ids:
                print(f"❌ Unpaid appointment {unpaid_appointment_id} should NOT be in payments collection")
                return False
        
        print("✅ Confirmed: Unpaid consultations are correctly NOT in payments collection")
        
        # Step 8: Verify total amounts calculation
        print("\nStep 8: Verifying amount calculations...")
        total_paid_visites = sum(p.get('montant', 0) for p in visite_payments)
        total_paid_controles = sum(p.get('montant', 0) for p in controle_payments)
        total_unpaid_amount = sum(p.get('montant', 0) for p in impaye_payments)
        
        print(f"✅ Total paid visites: {total_paid_visites} TND (2 × 65 = 130 TND)")
        print(f"✅ Total paid contrôles: {total_paid_controles} TND (2 × 0 = 0 TND)")
        print(f"✅ Total unpaid amount: {total_unpaid_amount} TND (2 × 65 = 130 TND)")
        
        if total_paid_visites != 130.0:
            print(f"❌ Paid visites should total 130 TND, got {total_paid_visites}")
            return False
        if total_paid_controles != 0.0:
            print(f"❌ Paid contrôles should total 0 TND, got {total_paid_controles}")
            return False
        if total_unpaid_amount != 130.0:
            print(f"❌ Unpaid amount should total 130 TND, got {total_unpaid_amount}")
            return False
        
        print("\n🎉 IMPAYÉ FILTER CORRECTION TEST COMPLETED SUCCESSFULLY!")
        print("✅ All success criteria met:")
        print("  - Impayé filter returns unpaid consultations from appointments (not payments)")
        print("  - Unpaid consultations have complete patient information")
        print("  - Only visite appointments appear as unpaid (contrôles are free)")
        print("  - Correct amounts and statuses for all filter types")
        print("  - Proper pagination and data structure")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed with exception: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_impaye_filter_correction()
    exit(0 if success else 1)