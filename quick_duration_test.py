#!/usr/bin/env python3
"""
QUICK DURATION TEST - Test just one scenario to understand the calculation
"""

import requests
import json
import time
from datetime import datetime, timedelta
import sys

# Configuration
BACKEND_URL = "https://a657b56d-56f9-415b-a575-b3b503d7e7a0.preview.emergentagent.com/api"
TEST_CREDENTIALS = {"username": "medecin", "password": "medecin123"}

def authenticate():
    session = requests.Session()
    session.verify = False
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    response = session.post(f"{BACKEND_URL}/auth/login", json=TEST_CREDENTIALS, timeout=30, verify=False)
    if response.status_code == 200:
        data = response.json()
        session.headers.update({"Authorization": f"Bearer {data['access_token']}"})
        return session
    return None

def main():
    print("🚀 QUICK DURATION TEST")
    
    session = authenticate()
    if not session:
        print("❌ Authentication failed")
        return
    
    today = datetime.now().strftime("%Y-%m-%d")
    
    # Get appointments
    response = session.get(f"{BACKEND_URL}/rdv/jour/{today}", timeout=10)
    if response.status_code != 200:
        print("❌ Failed to get appointments")
        return
    
    appointments = response.json()
    if not appointments:
        print("❌ No appointments found")
        return
    
    # Use first appointment
    test_appointment = appointments[0]
    rdv_id = test_appointment.get("id")
    patient_info = test_appointment.get("patient", {})
    patient_name = f"{patient_info.get('prenom', '')} {patient_info.get('nom', '')}"
    
    print(f"Testing with patient: {patient_name}")
    
    # Reset to programme
    session.put(f"{BACKEND_URL}/rdv/{rdv_id}/statut", json={"statut": "programme"}, timeout=10)
    time.sleep(1)
    
    # Move to attente
    print("Moving to attente...")
    attente_start = datetime.now()
    response = session.put(f"{BACKEND_URL}/rdv/{rdv_id}/statut", json={"statut": "attente"}, timeout=10)
    
    if response.status_code == 200:
        data = response.json()
        heure_arrivee = data.get("heure_arrivee_attente", "NOT_SET")
        print(f"heure_arrivee_attente: {heure_arrivee}")
        
        # Wait 10 seconds (should be 0 minutes)
        print("Waiting 10 seconds...")
        time.sleep(10)
        
        # Move to en_cours
        print("Moving to en_cours...")
        consultation_start = datetime.now()
        response = session.put(f"{BACKEND_URL}/rdv/{rdv_id}/statut", json={"statut": "en_cours"}, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            calculated_duree = data.get("duree_attente", "NOT_CALCULATED")
            
            elapsed_seconds = (consultation_start - attente_start).total_seconds()
            expected_minutes = int(elapsed_seconds / 60)
            
            print(f"Elapsed: {elapsed_seconds:.1f} seconds")
            print(f"Expected: {expected_minutes} minutes")
            print(f"Calculated: {calculated_duree} minutes")
            
            if calculated_duree == 0:
                print("✅ CORRECT: 0 minutes for short wait")
            elif calculated_duree == 1 and expected_minutes == 0:
                print("🚨 BUG FOUND: Forced to 1 minute minimum")
            else:
                print(f"❓ UNEXPECTED: Got {calculated_duree}, expected {expected_minutes}")
        else:
            print(f"❌ Failed to move to en_cours: {response.status_code}")
    else:
        print(f"❌ Failed to move to attente: {response.status_code}")

if __name__ == "__main__":
    main()