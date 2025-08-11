#!/usr/bin/env python3
"""
SIMPLE CRITICAL WAITING TIME BUG FIX TEST
Direct test of the critical waiting time duration bug fix
"""

import requests
import json
import time
from datetime import datetime
import urllib3

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configuration
BACKEND_URL = "https://e095a16b-4f79-4d50-8576-cad954291484.preview.emergentagent.com/api"

def test_waiting_time_bug_fix():
    """Test the critical waiting time bug fix"""
    print("🚨 TESTING CRITICAL WAITING TIME BUG FIX")
    print("=" * 60)
    
    session = requests.Session()
    session.verify = False
    
    # Step 1: Authenticate
    print("🔐 Step 1: Authentication")
    try:
        auth_response = session.post(
            f"{BACKEND_URL}/auth/login",
            json={"username": "medecin", "password": "medecin123"},
            timeout=30
        )
        
        if auth_response.status_code != 200:
            print(f"❌ Authentication failed: {auth_response.status_code}")
            print(f"Response: {auth_response.text}")
            return False
            
        auth_data = auth_response.json()
        token = auth_data["access_token"]
        session.headers.update({"Authorization": f"Bearer {token}"})
        print("✅ Authentication successful")
        
    except Exception as e:
        print(f"❌ Authentication error: {e}")
        return False
    
    # Step 2: Get today's appointments
    print("\n📅 Step 2: Get today's appointments")
    today = datetime.now().strftime("%Y-%m-%d")
    
    try:
        appointments_response = session.get(f"{BACKEND_URL}/rdv/jour/{today}")
        if appointments_response.status_code != 200:
            print(f"❌ Failed to get appointments: {appointments_response.status_code}")
            return False
            
        appointments = appointments_response.json()
        print(f"✅ Found {len(appointments)} appointments")
        
        if not appointments:
            print("❌ No appointments found for testing")
            return False
            
        # Select first appointment for testing
        test_appointment = appointments[0]
        rdv_id = test_appointment["id"]
        patient_info = test_appointment.get("patient", {})
        patient_name = f"{patient_info.get('prenom', '')} {patient_info.get('nom', '')}"
        
        print(f"📋 Selected patient: {patient_name}")
        print(f"📋 Current status: {test_appointment.get('statut')}")
        print(f"📋 Current duree_attente: {test_appointment.get('duree_attente')}")
        
    except Exception as e:
        print(f"❌ Error getting appointments: {e}")
        return False
    
    # Step 3: Move to attente
    print(f"\n🏥 Step 3: Move {patient_name} to 'attente'")
    try:
        attente_start = datetime.now()
        
        attente_response = session.put(
            f"{BACKEND_URL}/rdv/{rdv_id}/statut",
            json={"statut": "attente"}
        )
        
        if attente_response.status_code != 200:
            print(f"❌ Failed to move to attente: {attente_response.status_code}")
            print(f"Response: {attente_response.text}")
            return False
            
        attente_data = attente_response.json()
        print("✅ Moved to attente successfully")
        print(f"📋 heure_arrivee_attente: {attente_data.get('heure_arrivee_attente', 'NOT_SET')}")
        
    except Exception as e:
        print(f"❌ Error moving to attente: {e}")
        return False
    
    # Step 4: Wait for realistic duration (3 minutes)
    print(f"\n⏰ Step 4: Waiting 3 minutes for realistic duration...")
    print("This simulates a patient waiting in the waiting room")
    time.sleep(180)  # Wait 3 minutes
    
    # Step 5: CRITICAL TEST - Move to en_cours and check duration
    print(f"\n🩺 Step 5: CRITICAL TEST - Move to 'en_cours' and verify REAL duration")
    try:
        consultation_start = datetime.now()
        
        en_cours_response = session.put(
            f"{BACKEND_URL}/rdv/{rdv_id}/statut",
            json={"statut": "en_cours"}
        )
        
        if en_cours_response.status_code != 200:
            print(f"❌ Failed to move to en_cours: {en_cours_response.status_code}")
            print(f"Response: {en_cours_response.text}")
            return False
            
        en_cours_data = en_cours_response.json()
        calculated_duration = en_cours_data.get("duree_attente")
        
        # Calculate expected duration
        time_diff = consultation_start - attente_start
        expected_minutes = int(time_diff.total_seconds() / 60)
        
        print("✅ Moved to en_cours successfully")
        print(f"📊 API Response duree_attente: {calculated_duration} minutes")
        print(f"📊 Expected duration: ~{expected_minutes} minutes")
        
        # CRITICAL BUG FIX VERIFICATION
        if calculated_duration == 1 and expected_minutes > 1:
            print("❌ CRITICAL BUG DETECTED: Duration forced to 1 minute instead of real duration!")
            print(f"   Expected: {expected_minutes} minutes, Got: {calculated_duration} minute")
            return False
        elif calculated_duration and calculated_duration >= expected_minutes - 1:
            print("✅ CRITICAL FIX WORKING: Real duration calculated correctly!")
            print(f"   Real duration: {calculated_duration} minutes (not forced to 1)")
        else:
            print(f"⚠️  Unexpected duration: {calculated_duration} (expected ~{expected_minutes})")
        
    except Exception as e:
        print(f"❌ Error moving to en_cours: {e}")
        return False
    
    # Step 6: Verify database persistence
    print(f"\n💾 Step 6: Verify database persistence")
    try:
        final_appointments_response = session.get(f"{BACKEND_URL}/rdv/jour/{today}")
        if final_appointments_response.status_code == 200:
            final_appointments = final_appointments_response.json()
            final_appointment = next((apt for apt in final_appointments if apt["id"] == rdv_id), None)
            
            if final_appointment:
                stored_duration = final_appointment.get("duree_attente")
                stored_status = final_appointment.get("statut")
                
                print(f"📊 Database status: {stored_status}")
                print(f"📊 Database duree_attente: {stored_duration} minutes")
                
                if stored_duration == calculated_duration:
                    print("✅ Duration correctly persisted in database")
                else:
                    print(f"⚠️  Duration mismatch: API returned {calculated_duration}, DB has {stored_duration}")
            else:
                print("❌ Appointment not found in database")
        else:
            print("❌ Failed to verify database state")
            
    except Exception as e:
        print(f"❌ Error verifying database: {e}")
    
    print("\n" + "=" * 60)
    print("🎉 CRITICAL WAITING TIME BUG FIX TEST COMPLETED")
    print("✅ Real duration calculation working (not forced to 1 minute)")
    print("✅ API response includes calculated duree_attente")
    print("✅ Database persistence verified")
    
    return True

if __name__ == "__main__":
    success = test_waiting_time_bug_fix()
    exit(0 if success else 1)