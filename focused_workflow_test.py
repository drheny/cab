import requests
import json
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/frontend/.env')

def test_consultation_workflow():
    """
    Focused test for the consultation workflow issues mentioned in the review request
    """
    base_url = os.getenv('REACT_APP_BACKEND_URL', 'https://4b217b17-873e-4b0f-ae18-7cc0e70848d9.preview.emergentagent.com')
    print(f"Testing backend at: {base_url}")
    
    # Initialize demo data
    try:
        response = requests.get(f"{base_url}/api/init-demo")
        if response.status_code == 200:
            print("✅ Demo data initialized")
    except Exception as e:
        print(f"Warning: Demo data init failed: {e}")
    
    print("\n🔍 TESTING CONSULTATION WORKFLOW ISSUES")
    print("=" * 60)
    
    # Step 1: Create a simple patient
    print("\n1. Creating test patient...")
    patient_data = {
        "nom": "TestWorkflow",
        "prenom": "Patient"
    }
    
    try:
        response = requests.post(f"{base_url}/api/patients", json=patient_data)
        if response.status_code == 200:
            patient_id = response.json()["patient_id"]
            print(f"✅ Patient created: {patient_id}")
        else:
            print(f"❌ Patient creation failed: {response.status_code} - {response.text}")
            return
    except Exception as e:
        print(f"❌ Patient creation error: {e}")
        return
    
    # Step 2: Create appointment
    print("\n2. Creating appointment...")
    today = datetime.now().strftime("%Y-%m-%d")
    appointment_data = {
        "patient_id": patient_id,
        "date": today,
        "heure": "10:00",
        "type_rdv": "visite",
        "motif": "Test consultation workflow"
    }
    
    try:
        response = requests.post(f"{base_url}/api/appointments", json=appointment_data)
        if response.status_code == 200:
            appointment_id = response.json()["appointment_id"]
            print(f"✅ Appointment created: {appointment_id}")
        else:
            print(f"❌ Appointment creation failed: {response.status_code} - {response.text}")
            return
    except Exception as e:
        print(f"❌ Appointment creation error: {e}")
        return
    
    # Step 3: Create payment via PUT /api/rdv/{rdv_id}/paiement
    print("\n3. Creating payment via appointment endpoint...")
    payment_data = {
        "paye": True,
        "montant": 65.0,
        "type_paiement": "espece",
        "assure": False
    }
    
    try:
        response = requests.put(f"{base_url}/api/rdv/{appointment_id}/paiement", json=payment_data)
        if response.status_code == 200:
            print("✅ Payment created via appointment endpoint")
        else:
            print(f"❌ Payment creation failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Payment creation error: {e}")
    
    # Step 4: Create consultation
    print("\n4. Creating consultation...")
    consultation_data = {
        "patient_id": patient_id,
        "appointment_id": appointment_id,
        "date": today,
        "type_rdv": "visite",
        "duree": 30,
        "diagnostic": "Test consultation",
        "observation_clinique": "Normal examination"
    }
    
    try:
        response = requests.post(f"{base_url}/api/consultations", json=consultation_data)
        if response.status_code == 200:
            consultation_id = response.json()["consultation_id"]
            print(f"✅ Consultation created: {consultation_id}")
        else:
            print(f"❌ Consultation creation failed: {response.status_code} - {response.text}")
            return
    except Exception as e:
        print(f"❌ Consultation creation error: {e}")
        return
    
    print("\n" + "=" * 60)
    print("🔍 TESTING KEY ISSUES FROM REVIEW REQUEST")
    print("=" * 60)
    
    # Issue 1: Does POST /api/consultations update appointment status to "termine"?
    print("\n🔍 Issue 1: Consultation → Appointment Status Update")
    try:
        response = requests.get(f"{base_url}/api/rdv/jour/{today}")
        if response.status_code == 200:
            appointments = response.json()
            our_appointment = next((apt for apt in appointments if apt["id"] == appointment_id), None)
            
            if our_appointment:
                status = our_appointment["statut"]
                print(f"   Appointment status after consultation: {status}")
                
                if status == "termine":
                    print("   ✅ SUCCESS: Appointment status updated to 'termine'")
                else:
                    print("   ❌ ISSUE: Appointment status NOT updated to 'termine'")
                    print("   🚨 ROOT CAUSE: POST /api/consultations does NOT update appointment status")
            else:
                print("   ❌ ERROR: Appointment not found in calendar")
        else:
            print(f"   ❌ ERROR: Calendar endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
    
    # Issue 2: Do payments appear in GET /api/payments?
    print("\n🔍 Issue 2: Payment Integration")
    try:
        response = requests.get(f"{base_url}/api/payments")
        if response.status_code == 200:
            payments = response.json()
            our_payment = next((pay for pay in payments if pay["appointment_id"] == appointment_id), None)
            
            if our_payment:
                print("   ✅ SUCCESS: Payment appears in GET /api/payments")
                print(f"   Payment details: {our_payment['montant']} TND, {our_payment['statut']}")
            else:
                print("   ❌ ISSUE: Payment NOT found in GET /api/payments")
                print("   🚨 ROOT CAUSE: PUT /api/rdv/{rdv_id}/paiement doesn't update payments collection")
        else:
            print(f"   ❌ ERROR: Payments endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
    
    # Issue 3: Does calendar show appointments with "termine" status?
    print("\n🔍 Issue 3: Calendar Integration")
    try:
        # First, manually set appointment to "termine" to test calendar display
        status_update = {"statut": "termine"}
        response = requests.put(f"{base_url}/api/rdv/{appointment_id}/statut", json=status_update)
        
        if response.status_code == 200:
            print("   ✅ Manually set appointment status to 'termine'")
            
            # Now check calendar
            response = requests.get(f"{base_url}/api/rdv/jour/{today}")
            if response.status_code == 200:
                appointments = response.json()
                termine_appointments = [apt for apt in appointments if apt["statut"] == "termine"]
                our_appointment = next((apt for apt in appointments if apt["id"] == appointment_id), None)
                
                if our_appointment and our_appointment["statut"] == "termine":
                    print("   ✅ SUCCESS: Calendar shows appointment with 'termine' status")
                    
                    # Check patient data inclusion
                    if "patient" in our_appointment:
                        patient_info = our_appointment["patient"]
                        print(f"   ✅ SUCCESS: Calendar includes patient data: {patient_info.get('nom', 'N/A')} {patient_info.get('prenom', 'N/A')}")
                    else:
                        print("   ❌ ISSUE: Calendar appointment missing patient data")
                else:
                    print("   ❌ ISSUE: Calendar doesn't show appointment with 'termine' status")
            else:
                print(f"   ❌ ERROR: Calendar endpoint failed: {response.status_code}")
        else:
            print(f"   ❌ ERROR: Status update failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
    
    # Issue 4: Are payments enriched with patient/appointment data?
    print("\n🔍 Issue 4: Billing Integration")
    try:
        response = requests.get(f"{base_url}/api/payments")
        if response.status_code == 200:
            payments = response.json()
            our_payment = next((pay for pay in payments if pay["appointment_id"] == appointment_id), None)
            
            if our_payment:
                print("   ✅ Payment found in billing")
                
                # Check required fields for billing
                required_fields = ["id", "patient_id", "appointment_id", "montant", "type_paiement", "statut", "date"]
                missing_fields = [field for field in required_fields if field not in our_payment]
                
                if not missing_fields:
                    print("   ✅ SUCCESS: Payment has all required fields for billing")
                else:
                    print(f"   ❌ ISSUE: Payment missing fields: {missing_fields}")
                
                # Check if enriched with patient data
                if "patient_nom" in our_payment or "patient_prenom" in our_payment:
                    print("   ✅ SUCCESS: Payment enriched with patient data")
                else:
                    print("   ⚠️  WARNING: Payment may need client-side enrichment with patient data")
            else:
                print("   ❌ ISSUE: Payment not found in billing")
        else:
            print(f"   ❌ ERROR: Billing endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
    
    # Issue 5: Test appointment_id linkage
    print("\n🔍 Issue 5: Data Linkage Verification")
    try:
        # Get all related records and verify linkage
        print("   Verifying appointment_id linkage across all records...")
        
        # Get consultation
        response = requests.get(f"{base_url}/api/consultations/patient/{patient_id}")
        if response.status_code == 200:
            consultations = response.json()
            our_consultation = next((cons for cons in consultations if cons["id"] == consultation_id), None)
            
            if our_consultation and our_consultation["appointment_id"] == appointment_id:
                print("   ✅ SUCCESS: Consultation properly linked to appointment")
            else:
                print("   ❌ ISSUE: Consultation not properly linked to appointment")
        
        # Get payment
        response = requests.get(f"{base_url}/api/payments")
        if response.status_code == 200:
            payments = response.json()
            our_payment = next((pay for pay in payments if pay["appointment_id"] == appointment_id), None)
            
            if our_payment and our_payment["patient_id"] == patient_id:
                print("   ✅ SUCCESS: Payment properly linked to patient and appointment")
            else:
                print("   ❌ ISSUE: Payment not properly linked")
        
        print("   ✅ Data linkage verification completed")
        
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
    
    print("\n" + "=" * 60)
    print("🎯 SUMMARY OF FINDINGS")
    print("=" * 60)
    print("Based on this test, the main issues are likely:")
    print("1. POST /api/consultations may not update appointment status to 'termine'")
    print("2. PUT /api/rdv/{rdv_id}/paiement may not update the payments collection")
    print("3. Calendar integration depends on proper appointment status updates")
    print("4. Billing integration depends on payments appearing in GET /api/payments")
    print("5. All records should be properly linked by appointment_id")
    
    print(f"\nTest completed with patient_id: {patient_id}, appointment_id: {appointment_id}")

if __name__ == '__main__':
    test_consultation_workflow()