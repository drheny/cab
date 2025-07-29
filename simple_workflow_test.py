#!/usr/bin/env python3

import requests
import json
from datetime import datetime

def test_workflow():
    base_url = "https://cf4f91e9-01e0-4eb2-abf0-57caf9e2fae7.preview.emergentagent.com"
    
    print("🔍 TESTING CONSULTATION WORKFLOW")
    print("=" * 50)
    
    # Initialize demo data
    print("Initializing demo data...")
    try:
        response = requests.get(f"{base_url}/api/init-demo")
        print(f"Demo data: {response.status_code}")
    except:
        pass
    
    # Get existing patients to avoid creation issues
    print("\nGetting existing patients...")
    response = requests.get(f"{base_url}/api/patients")
    if response.status_code == 200:
        patients_data = response.json()
        patients = patients_data["patients"]
        if len(patients) > 0:
            patient = patients[0]
            patient_id = patient["id"]
            print(f"✅ Using existing patient: {patient['nom']} {patient['prenom']} (ID: {patient_id})")
        else:
            print("❌ No patients found")
            return
    else:
        print(f"❌ Failed to get patients: {response.status_code}")
        return
    
    # Create appointment
    print("\n1. Creating appointment...")
    today = datetime.now().strftime("%Y-%m-%d")
    appointment_data = {
        "patient_id": patient_id,
        "date": today,
        "heure": "14:00",
        "type_rdv": "visite",
        "motif": "Test workflow consultation"
    }
    
    response = requests.post(f"{base_url}/api/appointments", json=appointment_data)
    if response.status_code == 200:
        appointment_id = response.json()["appointment_id"]
        print(f"✅ Appointment created: {appointment_id}")
    else:
        print(f"❌ Appointment creation failed: {response.status_code}")
        return
    
    # Create payment via appointment endpoint
    print("\n2. Creating payment...")
    payment_data = {
        "paye": True,
        "montant": 65.0,
        "type_paiement": "espece",
        "assure": False,
        "notes": "Test payment"
    }
    
    response = requests.put(f"{base_url}/api/rdv/{appointment_id}/paiement", json=payment_data)
    if response.status_code == 200:
        print("✅ Payment created via appointment endpoint")
    else:
        print(f"❌ Payment creation failed: {response.status_code}")
    
    # Create consultation
    print("\n3. Creating consultation...")
    consultation_data = {
        "patient_id": patient_id,
        "appointment_id": appointment_id,
        "date": today,
        "type_rdv": "visite",
        "duree": 30,
        "diagnostic": "Test consultation workflow",
        "observation_clinique": "Normal examination for workflow test"
    }
    
    response = requests.post(f"{base_url}/api/consultations", json=consultation_data)
    if response.status_code == 200:
        consultation_id = response.json()["consultation_id"]
        print(f"✅ Consultation created: {consultation_id}")
    else:
        print(f"❌ Consultation creation failed: {response.status_code}")
        return
    
    print("\n" + "=" * 50)
    print("🔍 TESTING KEY WORKFLOW ISSUES")
    print("=" * 50)
    
    # Test 1: Check if appointment status was updated to "termine"
    print("\n🔍 Test 1: Appointment Status Update")
    response = requests.get(f"{base_url}/api/rdv/jour/{today}")
    if response.status_code == 200:
        appointments = response.json()
        our_appointment = next((apt for apt in appointments if apt["id"] == appointment_id), None)
        
        if our_appointment:
            status = our_appointment["statut"]
            print(f"   Appointment status: {status}")
            
            if status == "termine":
                print("   ✅ SUCCESS: POST /api/consultations correctly updates appointment status to 'termine'")
            else:
                print("   ❌ ISSUE: Appointment status not updated to 'termine'")
        else:
            print("   ❌ ERROR: Appointment not found")
    else:
        print(f"   ❌ ERROR: Calendar endpoint failed: {response.status_code}")
    
    # Test 2: Check if payment appears in payments list
    print("\n🔍 Test 2: Payment Integration")
    response = requests.get(f"{base_url}/api/payments")
    if response.status_code == 200:
        payments = response.json()
        our_payment = next((pay for pay in payments if pay["appointment_id"] == appointment_id), None)
        
        if our_payment:
            print("   ✅ SUCCESS: PUT /api/rdv/{rdv_id}/paiement correctly creates payment in payments collection")
            print(f"   Payment details: {our_payment['montant']} TND, status: {our_payment['statut']}")
        else:
            print("   ❌ ISSUE: Payment not found in payments collection")
    else:
        print(f"   ❌ ERROR: Payments endpoint failed: {response.status_code}")
    
    # Test 3: Check calendar integration
    print("\n🔍 Test 3: Calendar Integration")
    response = requests.get(f"{base_url}/api/rdv/jour/{today}")
    if response.status_code == 200:
        appointments = response.json()
        termine_appointments = [apt for apt in appointments if apt["statut"] == "termine"]
        
        print(f"   Total appointments today: {len(appointments)}")
        print(f"   Appointments with 'termine' status: {len(termine_appointments)}")
        
        our_appointment = next((apt for apt in appointments if apt["id"] == appointment_id), None)
        if our_appointment:
            if "patient" in our_appointment:
                patient_info = our_appointment["patient"]
                print(f"   ✅ SUCCESS: Calendar includes patient data: {patient_info.get('nom', 'N/A')} {patient_info.get('prenom', 'N/A')}")
            else:
                print("   ❌ ISSUE: Calendar appointment missing patient data")
        
        if len(termine_appointments) > 0:
            print("   ✅ SUCCESS: Calendar shows appointments with 'termine' status")
        else:
            print("   ⚠️  WARNING: No appointments with 'termine' status found")
    else:
        print(f"   ❌ ERROR: Calendar endpoint failed: {response.status_code}")
    
    # Test 4: Check billing integration
    print("\n🔍 Test 4: Billing Integration")
    response = requests.get(f"{base_url}/api/payments")
    if response.status_code == 200:
        payments = response.json()
        print(f"   Total payments in system: {len(payments)}")
        
        our_payment = next((pay for pay in payments if pay["appointment_id"] == appointment_id), None)
        if our_payment:
            # Check required fields
            required_fields = ["id", "patient_id", "appointment_id", "montant", "type_paiement", "statut", "date"]
            missing_fields = [field for field in required_fields if field not in our_payment]
            
            if not missing_fields:
                print("   ✅ SUCCESS: Payment has all required fields for billing")
            else:
                print(f"   ❌ ISSUE: Payment missing fields: {missing_fields}")
            
            print(f"   Payment structure: {list(our_payment.keys())}")
        else:
            print("   ❌ ISSUE: Our payment not found in billing")
    else:
        print(f"   ❌ ERROR: Billing endpoint failed: {response.status_code}")
    
    print("\n" + "=" * 50)
    print("🎯 WORKFLOW TEST SUMMARY")
    print("=" * 50)
    print(f"Patient ID: {patient_id}")
    print(f"Appointment ID: {appointment_id}")
    print(f"Consultation ID: {consultation_id}")
    print(f"Test Date: {today}")
    
    print("\nBased on the backend code analysis:")
    print("✅ POST /api/consultations SHOULD update appointment status to 'termine'")
    print("✅ PUT /api/rdv/{rdv_id}/paiement SHOULD create payment in payments collection")
    print("✅ GET /api/rdv/jour/{date} SHOULD include patient data")
    print("✅ GET /api/payments SHOULD show all payments for billing")

if __name__ == "__main__":
    test_workflow()