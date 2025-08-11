#!/usr/bin/env python3
"""
LONGER WAITING TIME TEST
Testing with 65+ seconds to see if calculation works for longer periods
"""

import requests
import json
import time
from datetime import datetime, timedelta
import sys
import os

# Configuration
BACKEND_URL = "https://a657b56d-56f9-415b-a575-b3b503d7e7a0.preview.emergentagent.com/api"
TEST_CREDENTIALS = {
    "username": "medecin",
    "password": "medecin123"
}

def authenticate():
    """Login with medecin/medecin123"""
    session = requests.Session()
    session.verify = False
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    try:
        response = session.post(
            f"{BACKEND_URL}/auth/login",
            json=TEST_CREDENTIALS,
            timeout=30,
            verify=False
        )
        
        if response.status_code == 200:
            data = response.json()
            if "access_token" in data:
                session.headers.update({
                    "Authorization": f"Bearer {data['access_token']}"
                })
                print("✅ Authentication successful")
                return session
        
        print(f"❌ Authentication failed: HTTP {response.status_code}")
        return None
        
    except Exception as e:
        print(f"❌ Authentication error: {str(e)}")
        return None

def test_longer_waiting_time():
    """Test with 65+ seconds waiting time"""
    print("🚨 LONGER WAITING TIME TEST (65+ seconds)")
    print("=" * 60)
    
    # Step 1: Login
    session = authenticate()
    if not session:
        return False
    
    # Step 2: Get today's appointments
    today = datetime.now().strftime("%Y-%m-%d")
    
    try:
        response = session.get(f"{BACKEND_URL}/rdv/jour/{today}", timeout=10)
        if response.status_code != 200:
            print(f"❌ Failed to get appointments: HTTP {response.status_code}")
            return False
        
        appointments = response.json()
        if not appointments:
            print("❌ No appointments found for testing")
            return False
        
        # Find a test patient
        test_appointment = appointments[0]
        rdv_id = test_appointment.get("id")
        patient_info = test_appointment.get("patient", {})
        patient_name = f"{patient_info.get('prenom', '')} {patient_info.get('nom', '')}"
        
        print(f"📋 Test Patient: {patient_name}")
        print(f"📋 Initial Status: {test_appointment.get('statut')}")
        print(f"📋 Initial duree_attente: {test_appointment.get('duree_attente')}")
        
        # Step 3: Move to attente
        print("\n🏥 Moving to 'attente' status...")
        attente_start_time = datetime.now()
        
        update_data = {"statut": "attente"}
        response = session.put(f"{BACKEND_URL}/rdv/{rdv_id}/statut", json=update_data, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            heure_arrivee = data.get("heure_arrivee_attente", "NOT_PROVIDED")
            print(f"✅ Moved to attente at {attente_start_time.strftime('%H:%M:%S')}")
            print(f"   API Response - heure_arrivee_attente: {heure_arrivee}")
        else:
            print(f"❌ Failed to move to attente: HTTP {response.status_code}")
            return False
        
        # Step 4: Wait 65 seconds (just over 1 minute)
        wait_seconds = 65
        print(f"\n⏰ Waiting {wait_seconds} seconds (just over 1 minute)...")
        time.sleep(wait_seconds)
        
        # Step 5: Move to en_cours
        print("\n🩺 Moving to 'en_cours' status...")
        en_cours_start_time = datetime.now()
        
        update_data = {"statut": "en_cours"}
        response = session.put(f"{BACKEND_URL}/rdv/{rdv_id}/statut", json=update_data, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            calculated_duree = data.get("duree_attente", "NOT_PROVIDED")
            
            # Calculate expected waiting time
            time_diff = en_cours_start_time - attente_start_time
            expected_minutes = max(1, int(time_diff.total_seconds() / 60))
            actual_seconds = time_diff.total_seconds()
            
            print(f"✅ Moved to en_cours at {en_cours_start_time.strftime('%H:%M:%S')}")
            print(f"   Actual waiting time: {actual_seconds:.1f} seconds ({expected_minutes} minutes)")
            print(f"   API Response - duree_attente: {calculated_duree}")
            
            # Analyze the result
            if calculated_duree == "NOT_PROVIDED":
                print("🚨 BUG: duree_attente not provided in API response")
            elif calculated_duree == 1 and expected_minutes > 1:
                print(f"🚨 POTENTIAL BUG: duree_attente forced to 1 minute instead of real {expected_minutes} minutes")
            elif calculated_duree == expected_minutes:
                print("✅ Calculation appears correct")
            else:
                print(f"ℹ️ Unexpected result: got {calculated_duree}, expected {expected_minutes}")
        else:
            print(f"❌ Failed to move to en_cours: HTTP {response.status_code}")
            return False
        
        # Step 6: Check database storage
        print("\n💾 Checking database storage...")
        response = session.get(f"{BACKEND_URL}/rdv/jour/{today}", timeout=10)
        
        if response.status_code == 200:
            updated_appointments = response.json()
            updated_appointment = next((apt for apt in updated_appointments if apt.get("id") == rdv_id), None)
            
            if updated_appointment:
                stored_duree = updated_appointment.get("duree_attente")
                stored_heure_arrivee = updated_appointment.get("heure_arrivee_attente")
                current_status = updated_appointment.get("statut")
                
                print(f"✅ Database check complete")
                print(f"   Status: {current_status}")
                print(f"   Stored duree_attente: {stored_duree}")
                print(f"   Stored heure_arrivee_attente: {stored_heure_arrivee}")
        
        print("\n" + "=" * 60)
        print("🔍 SUMMARY - LONGER WAIT TEST")
        print("=" * 60)
        print("✅ Test completed successfully")
        print("Key findings:")
        print(f"- Patient: {patient_name}")
        print(f"- Waiting time: {wait_seconds} seconds ({actual_seconds:.1f} actual)")
        print(f"- Expected duration: {expected_minutes} minutes")
        print(f"- Calculated duration: {calculated_duree} minutes")
        
        # Determine if there's a bug
        if calculated_duree == 1 and expected_minutes > 1:
            print("🚨 CONFIRMED BUG: Duration forced to 1 minute regardless of actual time")
        elif calculated_duree == "NOT_PROVIDED":
            print("🚨 CONFIRMED BUG: duree_attente not calculated or returned")
        elif calculated_duree == expected_minutes:
            print("✅ No bug detected - calculation appears correct")
        else:
            print("❓ Unexpected behavior - needs further investigation")
        
        return True
        
    except Exception as e:
        print(f"❌ Exception during testing: {str(e)}")
        return False

def main():
    """Main function"""
    try:
        success = test_longer_waiting_time()
        if success:
            print("\n✅ Longer waiting time test completed")
        else:
            print("\n❌ Longer waiting time test failed")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()