#!/usr/bin/env python3

import requests
import json
from datetime import datetime

# Use the public backend URL
BASE_URL = "https://1fb31e4b-51b3-4865-9aeb-aafab30b5994.preview.emergentagent.com"

def test_consultation_setup():
    """Test and setup consultation data for testing"""
    print("🔍 Testing Consultation Setup...")
    
    try:
        # 1. Initialize demo data
        print("📊 Initializing demo data...")
        response = requests.get(f"{BASE_URL}/api/init-demo")
        if response.status_code == 200:
            print("✅ Demo data initialized")
        else:
            print(f"❌ Failed to initialize demo data: {response.status_code}")
            return False
        
        # 2. Get today's appointments
        today = datetime.now().strftime("%Y-%m-%d")
        print(f"📅 Getting appointments for {today}...")
        response = requests.get(f"{BASE_URL}/api/rdv/jour/{today}")
        if response.status_code != 200:
            print(f"❌ Failed to get appointments: {response.status_code}")
            return False
        
        appointments = response.json()
        print(f"📋 Found {len(appointments)} appointments today")
        
        # 3. Check for appointments with "en_cours" status
        en_cours_appointments = [apt for apt in appointments if apt.get('statut') == 'en_cours']
        print(f"🏥 Found {len(en_cours_appointments)} appointments with 'en_cours' status")
        
        # 4. If no "en_cours" appointments, create some by updating existing ones
        if len(en_cours_appointments) < 2:
            print("🔧 Creating test appointments with 'en_cours' status...")
            
            # Get first two appointments and update their status
            for i, apt in enumerate(appointments[:2]):
                apt_id = apt['id']
                salle = f"salle{i+1}"
                
                # Update status to "en_cours" and assign room
                update_data = {
                    "statut": "en_cours",
                    "salle": salle
                }
                
                response = requests.put(f"{BASE_URL}/api/rdv/{apt_id}/statut", json=update_data)
                if response.status_code == 200:
                    print(f"✅ Updated appointment {apt_id} to 'en_cours' in {salle}")
                else:
                    print(f"❌ Failed to update appointment {apt_id}: {response.status_code}")
        
        # 5. Verify we now have "en_cours" appointments
        response = requests.get(f"{BASE_URL}/api/rdv/jour/{today}")
        if response.status_code == 200:
            appointments = response.json()
            en_cours_appointments = [apt for apt in appointments if apt.get('statut') == 'en_cours']
            print(f"✅ Now have {len(en_cours_appointments)} appointments with 'en_cours' status")
            
            for apt in en_cours_appointments:
                patient_name = f"{apt.get('patient', {}).get('prenom', 'N/A')} {apt.get('patient', {}).get('nom', 'N/A')}"
                print(f"   - {patient_name} at {apt.get('heure')} in {apt.get('salle', 'no room')}")
        
        # 6. Test consultation endpoints
        print("🩺 Testing consultation endpoints...")
        
        # Get all consultations
        response = requests.get(f"{BASE_URL}/api/consultations")
        if response.status_code == 200:
            consultations = response.json()
            print(f"✅ Found {len(consultations)} existing consultations")
        else:
            print(f"❌ Failed to get consultations: {response.status_code}")
        
        # Get patients for consultation history
        response = requests.get(f"{BASE_URL}/api/patients")
        if response.status_code == 200:
            patients_data = response.json()
            patients = patients_data.get('patients', [])
            print(f"✅ Found {len(patients)} patients")
            
            # Test patient consultation history for first patient
            if patients:
                patient_id = patients[0]['id']
                response = requests.get(f"{BASE_URL}/api/patients/{patient_id}/consultations")
                if response.status_code == 200:
                    patient_consultations = response.json()
                    print(f"✅ Patient {patients[0].get('nom')} has {len(patient_consultations)} consultations in history")
                else:
                    print(f"❌ Failed to get patient consultations: {response.status_code}")
        
        print("🎉 Consultation setup test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error during consultation setup test: {str(e)}")
        return False

def test_consultation_apis():
    """Test specific consultation-related APIs"""
    print("\n🔍 Testing Consultation APIs...")
    
    try:
        # Test dashboard endpoint
        response = requests.get(f"{BASE_URL}/api/dashboard")
        if response.status_code == 200:
            dashboard = response.json()
            print(f"✅ Dashboard: {dashboard.get('rdv_en_cours', 0)} consultations en cours")
        else:
            print(f"❌ Dashboard failed: {response.status_code}")
        
        # Test today's appointments
        response = requests.get(f"{BASE_URL}/api/appointments/today")
        if response.status_code == 200:
            today_appointments = response.json()
            en_cours = [apt for apt in today_appointments if apt.get('statut') == 'en_cours']
            print(f"✅ Today's appointments: {len(en_cours)} en cours")
        else:
            print(f"❌ Today's appointments failed: {response.status_code}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing consultation APIs: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Starting Consultation Test Suite...")
    
    setup_success = test_consultation_setup()
    api_success = test_consultation_apis()
    
    if setup_success and api_success:
        print("\n✅ All consultation tests passed!")
        exit(0)
    else:
        print("\n❌ Some consultation tests failed!")
        exit(1)