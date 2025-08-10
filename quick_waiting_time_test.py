#!/usr/bin/env python3
"""
QUICK WAITING TIME BUG TESTING
Testing the specific workflow with shorter wait times
"""

import requests
import json
import time
from datetime import datetime, timedelta
import sys
import os

# Configuration
BACKEND_URL = "https://86e1ae33-6e29-4ce5-a743-1e543eb0a6b8.preview.emergentagent.com/api"
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

def test_waiting_time_workflow():
    """Test the specific waiting time workflow"""
    print("🚨 QUICK WAITING TIME BUG TEST")
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
        print(f"📋 Initial heure_arrivee_attente: {test_appointment.get('heure_arrivee_attente')}")
        
        # Step 3: Move to attente
        print("\n🏥 Moving to 'attente' status...")
        attente_start_time = datetime.now()
        
        update_data = {"statut": "attente"}
        response = session.put(f"{BACKEND_URL}/rdv/{rdv_id}/statut", json=update_data, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            heure_arrivee = data.get("heure_arrivee_attente", "NOT_PROVIDED")
            duree_in_response = data.get("duree_attente", "NOT_PROVIDED")
            print(f"✅ Moved to attente")
            print(f"   API Response - heure_arrivee_attente: {heure_arrivee}")
            print(f"   API Response - duree_attente: {duree_in_response}")
        else:
            print(f"❌ Failed to move to attente: HTTP {response.status_code}")
            return False
        
        # Step 4: Wait 5 seconds
        print("\n⏰ Waiting 5 seconds...")
        time.sleep(5)
        
        # Step 5: Move to en_cours
        print("\n🩺 Moving to 'en_cours' status...")
        en_cours_start_time = datetime.now()
        
        update_data = {"statut": "en_cours"}
        response = session.put(f"{BACKEND_URL}/rdv/{rdv_id}/statut", json=update_data, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            calculated_duree = data.get("duree_attente", "NOT_PROVIDED")
            heure_arrivee = data.get("heure_arrivee_attente", "NOT_PROVIDED")
            
            # Calculate expected waiting time
            time_diff = en_cours_start_time - attente_start_time
            expected_minutes = max(0, int(time_diff.total_seconds() / 60))
            actual_seconds = time_diff.total_seconds()
            
            print(f"✅ Moved to en_cours")
            print(f"   Actual waiting time: {actual_seconds:.1f} seconds ({expected_minutes} minutes)")
            print(f"   API Response - duree_attente: {calculated_duree}")
            print(f"   API Response - heure_arrivee_attente: {heure_arrivee}")
            
            # Check if there's a bug
            if calculated_duree == "NOT_PROVIDED":
                print("🚨 POTENTIAL BUG: duree_attente not provided in API response")
            elif calculated_duree == 1 and expected_minutes == 0:
                print("🚨 POTENTIAL BUG: duree_attente forced to 1 minute for short waits")
            elif calculated_duree == 0 and expected_minutes == 0:
                print("✅ Calculation appears correct for short wait (0 minutes)")
            else:
                print(f"ℹ️ Calculation: {calculated_duree} minutes (expected ~{expected_minutes})")
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
                
                # Check consistency
                if calculated_duree != "NOT_PROVIDED" and stored_duree != calculated_duree:
                    print(f"🚨 INCONSISTENCY: API response ({calculated_duree}) != Database ({stored_duree})")
                else:
                    print("✅ API response and database are consistent")
            else:
                print("❌ Appointment not found in database")
        else:
            print(f"❌ Failed to check database: HTTP {response.status_code}")
        
        # Step 7: Move to termine
        print("\n✅ Moving to 'termine' status...")
        update_data = {"statut": "termine"}
        response = session.put(f"{BACKEND_URL}/rdv/{rdv_id}/statut", json=update_data, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            duree_in_termine_response = data.get("duree_attente", "NOT_PROVIDED")
            print(f"✅ Moved to termine")
            print(f"   API Response - duree_attente: {duree_in_termine_response}")
            
            # Final database check
            response = session.get(f"{BACKEND_URL}/rdv/jour/{today}", timeout=10)
            if response.status_code == 200:
                final_appointments = response.json()
                final_appointment = next((apt for apt in final_appointments if apt.get("id") == rdv_id), None)
                
                if final_appointment:
                    final_duree = final_appointment.get("duree_attente")
                    final_status = final_appointment.get("statut")
                    
                    print(f"✅ Final database check")
                    print(f"   Final status: {final_status}")
                    print(f"   Final duree_attente: {final_duree}")
                    
                    # Check if duree_attente was preserved
                    if stored_duree == final_duree:
                        print("✅ duree_attente preserved across status changes")
                    else:
                        print(f"🚨 POTENTIAL BUG: duree_attente changed from {stored_duree} to {final_duree}")
        else:
            print(f"❌ Failed to move to termine: HTTP {response.status_code}")
        
        print("\n" + "=" * 60)
        print("🔍 SUMMARY")
        print("=" * 60)
        print("✅ Test completed successfully")
        print("Key findings:")
        print(f"- Patient: {patient_name}")
        print(f"- Workflow: attente → en_cours → termine")
        print(f"- Waiting time: ~5 seconds")
        print(f"- Calculated duration: {calculated_duree} minutes")
        print(f"- Duration preserved: {stored_duree == final_duree if 'final_duree' in locals() else 'Unknown'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Exception during testing: {str(e)}")
        return False

def main():
    """Main function"""
    try:
        success = test_waiting_time_workflow()
        if success:
            print("\n✅ Quick waiting time test completed")
        else:
            print("\n❌ Quick waiting time test failed")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()