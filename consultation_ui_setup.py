#!/usr/bin/env python3

import requests
import sys
from datetime import datetime, timedelta
import json

class ConsultationUITester:
    def __init__(self, base_url="https://1fb31e4b-51b3-4865-9aeb-aafab30b5994.preview.emergentagent.com"):
        self.base_url = base_url
        self.today = datetime.now().strftime("%Y-%m-%d")

    def setup_en_cours_appointments(self):
        """Setup appointments with en_cours status and future times to avoid delay detection"""
        print("🔧 Setting up appointments for consultation testing...")
        
        # Initialize demo data
        response = requests.get(f"{self.base_url}/api/init-demo")
        if response.status_code != 200:
            print("❌ Failed to initialize demo data")
            return False
        
        # Get current appointments
        response = requests.get(f"{self.base_url}/api/rdv/jour/{self.today}")
        if response.status_code != 200:
            print("❌ Failed to get appointments")
            return False
            
        appointments = response.json()
        print(f"   Found {len(appointments)} appointments")
        
        # Update first two appointments to en_cours with future times
        future_time = (datetime.now() + timedelta(hours=1)).strftime("%H:%M")
        
        for i, apt in enumerate(appointments[:2]):
            apt_id = apt.get('id')
            if apt_id:
                # First update the time to future to avoid delay detection
                update_data = {
                    **apt,
                    "heure": future_time,
                    "statut": "en_cours",
                    "salle": "salle1" if i == 0 else "salle2"
                }
                
                # Update the appointment
                response = requests.put(f"{self.base_url}/api/appointments/{apt_id}", json=update_data)
                if response.status_code == 200:
                    print(f"   ✅ Updated appointment {apt_id} to en_cours with future time")
                else:
                    print(f"   ❌ Failed to update appointment {apt_id}")
        
        # Verify the updates
        response = requests.get(f"{self.base_url}/api/rdv/jour/{self.today}")
        if response.status_code == 200:
            updated_appointments = response.json()
            en_cours_count = len([a for a in updated_appointments if a.get('statut') == 'en_cours'])
            print(f"   📊 Successfully set {en_cours_count} appointments to 'en_cours' status")
            return en_cours_count >= 2
        
        return False

def main():
    print("🏥 Cabinet Médical - Consultation UI Setup")
    print("=" * 50)
    
    tester = ConsultationUITester()
    
    if tester.setup_en_cours_appointments():
        print("✅ Setup completed successfully!")
        print("🔄 Now test the UI immediately...")
        return 0
    else:
        print("❌ Setup failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())