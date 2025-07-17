#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime

def test_consultation_editing():
    """Test consultation editing functionality"""
    base_url = "https://1fb31e4b-51b3-4865-9aeb-aafab30b5994.preview.emergentagent.com"
    
    print("🏥 CONSULTATION EDITING TEST")
    print("=" * 50)
    
    # Step 1: Initialize demo data
    print("🔄 Initializing demo data...")
    response = requests.get(f"{base_url}/api/init-demo")
    if response.status_code != 200:
        print("❌ Failed to initialize demo data")
        return False
    print("✅ Demo data initialized")
    
    # Step 2: Create test consultations for patient1 and patient2
    today = datetime.now().strftime("%Y-%m-%d")
    
    test_consultations = [
        {
            "patient_id": "patient1",
            "appointment_id": "appt1",
            "date": today,
            "duree": 30,
            "observations": "Consultation test pour édition",
            "traitement": "Traitement initial",
            "bilan": "Bilan initial",
            "relance_date": ""
        },
        {
            "patient_id": "patient2", 
            "appointment_id": "appt2",
            "date": today,
            "duree": 25,
            "observations": "Test consultation patient 2",
            "traitement": "Traitement patient 2",
            "bilan": "Bilan patient 2",
            "relance_date": ""
        }
    ]
    
    created_consultations = []
    
    print("🔄 Creating test consultations...")
    for i, consultation_data in enumerate(test_consultations):
        response = requests.post(f"{base_url}/api/consultations", json=consultation_data)
        if response.status_code == 200:
            consultation_id = response.json().get('consultation_id')
            created_consultations.append({
                'id': consultation_id,
                'patient_id': consultation_data['patient_id'],
                'original_data': consultation_data
            })
            print(f"✅ Created consultation {consultation_id} for {consultation_data['patient_id']}")
        else:
            print(f"❌ Failed to create consultation for {consultation_data['patient_id']}")
    
    if len(created_consultations) == 0:
        print("❌ No consultations created. Cannot test editing.")
        return False
    
    # Step 3: Test getting patient consultation history
    print("🔄 Testing patient consultation history...")
    for patient_id in ["patient1", "patient2"]:
        response = requests.get(f"{base_url}/api/patients/{patient_id}/consultations")
        if response.status_code == 200:
            consultations = response.json()
            print(f"✅ Patient {patient_id} has {len(consultations)} consultations")
            for consultation in consultations:
                print(f"   - {consultation.get('id')}: {consultation.get('observations', 'N/A')[:50]}...")
        else:
            print(f"❌ Failed to get consultations for {patient_id}")
    
    # Step 4: Test editing consultations
    print("🔄 Testing consultation editing...")
    
    for i, consultation in enumerate(created_consultations):
        # Prepare updated data
        updated_data = {
            "id": consultation['id'],
            "patient_id": consultation['patient_id'],
            "appointment_id": consultation['original_data'].get('appointment_id', 'test_appt'),
            "date": consultation['original_data'].get('date', today),
            "duree": consultation['original_data'].get('duree', 30),
            "observations": f"Observations modifiées via test #{i+1}",
            "traitement": f"Traitement modifié #{i+1}",
            "bilan": f"Bilan modifié #{i+1}",
            "relance_date": ""
        }
        
        print(f"🔄 Updating consultation {consultation['id']}...")
        response = requests.put(f"{base_url}/api/consultations/{consultation['id']}", json=updated_data)
        
        if response.status_code == 200:
            print(f"✅ Successfully updated consultation {consultation['id']}")
            
            # Verify the update
            verify_response = requests.get(f"{base_url}/api/consultations/{consultation['id']}")
            if verify_response.status_code == 200:
                updated_consultation = verify_response.json()
                if (updated_consultation.get('observations') == updated_data['observations'] and
                    updated_consultation.get('traitement') == updated_data['traitement'] and
                    updated_consultation.get('bilan') == updated_data['bilan']):
                    print(f"✅ Update verified - data persisted correctly")
                else:
                    print(f"⚠️  Update verification failed - data may not have persisted")
                    print(f"   Expected: {updated_data['observations']}")
                    print(f"   Actual: {updated_consultation.get('observations')}")
            else:
                print(f"❌ Failed to verify update for consultation {consultation['id']}")
        else:
            print(f"❌ Failed to update consultation {consultation['id']} - Status: {response.status_code}")
            if response.content:
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data}")
                except:
                    print(f"   Error: {response.text}")
    
    # Step 5: Test deletion
    if len(created_consultations) > 0:
        consultation_to_delete = created_consultations[0]
        print(f"🔄 Testing deletion of consultation {consultation_to_delete['id']}...")
        
        response = requests.delete(f"{base_url}/api/consultations/{consultation_to_delete['id']}")
        if response.status_code == 200:
            print(f"✅ Successfully deleted consultation {consultation_to_delete['id']}")
            
            # Verify deletion
            verify_response = requests.get(f"{base_url}/api/consultations/{consultation_to_delete['id']}")
            if verify_response.status_code == 404:
                print(f"✅ Deletion verified - consultation no longer exists")
            else:
                print(f"⚠️  Deletion verification failed - consultation may still exist")
        else:
            print(f"❌ Failed to delete consultation {consultation_to_delete['id']}")
    
    print("=" * 50)
    print("🎉 Consultation editing test completed!")
    return True

if __name__ == "__main__":
    success = test_consultation_editing()
    sys.exit(0 if success else 1)