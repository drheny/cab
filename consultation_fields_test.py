#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime

class ConsultationFieldsTest:
    def __init__(self, base_url="https://3389e576-bdbc-485e-bdc3-00374f489362.preview.emergentagent.com"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.patient_id = None
        self.appointment_id = None
        self.consultation_id = None

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        if headers is None:
            headers = {'Content-Type': 'application/json'}

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        if data:
            print(f"   Data: {json.dumps(data, indent=2)}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    print(f"   Response: {json.dumps(response_data, indent=2)}")
                    return True, response_data
                except:
                    return True, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {json.dumps(error_data, indent=2)}")
                except:
                    print(f"   Error: {response.text}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def setup_test_data(self):
        """Setup test data"""
        print("🔧 Setting up test data...")
        
        # Initialize demo data
        success, _ = self.run_test("Initialize Demo Data", "GET", "api/init-demo", 200)
        if not success:
            return False
        
        # Get patients
        success, response = self.run_test("Get Patients", "GET", "api/patients", 200)
        if success and response.get('patients'):
            self.patient_id = response['patients'][0]['id']
            print(f"   Selected patient ID: {self.patient_id}")
        else:
            return False
        
        # Get today's appointments
        today = datetime.now().strftime("%Y-%m-%d")
        success, response = self.run_test("Get Today's Appointments", "GET", f"api/rdv/jour/{today}", 200)
        if success and response:
            for apt in response:
                if apt.get('patient_id') == self.patient_id:
                    self.appointment_id = apt['id']
                    break
            if not self.appointment_id and response:
                self.appointment_id = response[0]['id']
                self.patient_id = response[0]['patient_id']
            print(f"   Selected appointment ID: {self.appointment_id}")
            print(f"   Patient ID: {self.patient_id}")
        else:
            return False
        
        return True

    def test_consultation_payload_complete(self):
        """Test 1: Validation du payload complet"""
        print("\n📋 TEST 1: VALIDATION DU PAYLOAD COMPLET")
        print("=" * 50)
        
        consultation_data = {
            "patient_id": self.patient_id,
            "appointment_id": self.appointment_id,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "duree": 25,
            "poids": 17.2,
            "taille": 96.0,
            "pc": 50.0,
            "observations": "Test consultation avec toutes les mesures",
            "traitement": "Test traitement",
            "bilan": "Test bilan",
            "relance_date": ""
        }

        print(f"\n📤 PAYLOAD ENVOYÉ (JSON.stringify équivalent):")
        print(json.dumps(consultation_data, indent=2))

        success, response = self.run_test(
            "Create Consultation with All Fields",
            "POST",
            "api/consultations",
            200,
            consultation_data
        )
        
        if success and response.get('consultation_id'):
            self.consultation_id = response['consultation_id']
            print(f"✅ Consultation créée avec ID: {self.consultation_id}")
        
        return success

    def test_database_verification(self):
        """Test 2: Vérification base de données"""
        print("\n📊 TEST 2: VÉRIFICATION BASE DE DONNÉES")
        print("=" * 50)
        
        if not self.consultation_id:
            print("❌ Pas d'ID de consultation pour vérifier la base")
            return False

        success, response = self.run_test(
            "Get Consultation from Database",
            "GET",
            f"api/consultations/{self.consultation_id}",
            200
        )

        if success:
            print(f"\n📊 DONNÉES RÉCUPÉRÉES DE LA BASE:")
            print(f"   Poids: {response.get('poids')} kg")
            print(f"   Taille: {response.get('taille')} cm") 
            print(f"   PC: {response.get('pc')} cm")
            
            # Verify all three fields are present and not null/zero
            poids_ok = response.get('poids') is not None and response.get('poids') > 0
            taille_ok = response.get('taille') is not None and response.get('taille') > 0
            pc_ok = response.get('pc') is not None and response.get('pc') > 0
            
            if poids_ok and taille_ok and pc_ok:
                print("✅ Tous les champs (poids, taille, pc) sont présents et valides")
                print("✅ Les valeurs ne sont plus 'Non mesuré'")
            else:
                print("❌ Certains champs manquent ou sont invalides:")
                print(f"   - Poids valide: {poids_ok}")
                print(f"   - Taille valide: {taille_ok}")
                print(f"   - PC valide: {pc_ok}")
                return False

        return success

    def test_decimal_values(self):
        """Test 3: Test avec valeurs décimales"""
        print("\n🔢 TEST 3: TEST AVEC VALEURS DÉCIMALES")
        print("=" * 50)
        
        consultation_data = {
            "patient_id": self.patient_id,
            "appointment_id": self.appointment_id,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "duree": 20,
            "poids": 16.5,
            "taille": 95.7,
            "pc": 49.3,
            "observations": "Test avec valeurs décimales",
            "traitement": "Test traitement décimal",
            "bilan": "Test bilan décimal",
            "relance_date": ""
        }

        print(f"\n📤 PAYLOAD AVEC DÉCIMALES:")
        print(json.dumps(consultation_data, indent=2))

        success, response = self.run_test(
            "Create Consultation with Decimal Values",
            "POST",
            "api/consultations",
            200,
            consultation_data
        )

        if success and response.get('consultation_id'):
            decimal_consultation_id = response['consultation_id']
            
            # Verify decimal values are preserved
            success2, response2 = self.run_test(
                "Verify Decimal Values in Database",
                "GET",
                f"api/consultations/{decimal_consultation_id}",
                200
            )
            
            if success2:
                print(f"\n📊 VÉRIFICATION DES DÉCIMALES:")
                print(f"   Poids: {response2.get('poids')} (attendu: 16.5)")
                print(f"   Taille: {response2.get('taille')} (attendu: 95.7)")
                print(f"   PC: {response2.get('pc')} (attendu: 49.3)")
                
                # Check if decimal values are preserved
                poids_decimal = abs(response2.get('poids', 0) - 16.5) < 0.01
                taille_decimal = abs(response2.get('taille', 0) - 95.7) < 0.01
                pc_decimal = abs(response2.get('pc', 0) - 49.3) < 0.01
                
                if poids_decimal and taille_decimal and pc_decimal:
                    print("✅ Les valeurs décimales sont préservées")
                else:
                    print("❌ Les valeurs décimales ne sont pas préservées correctement")
                    return False
        
        return success

    def test_history_display(self):
        """Test historique des consultations"""
        print("\n📚 TEST 4: AFFICHAGE DANS L'HISTORIQUE")
        print("=" * 50)
        
        success, response = self.run_test(
            "Get Patient Consultation History",
            "GET",
            f"api/patients/{self.patient_id}/consultations",
            200
        )

        if success and response:
            print(f"\n📚 HISTORIQUE DES CONSULTATIONS:")
            for consultation in response:
                print(f"   Date: {consultation.get('date')}")
                print(f"   Type: {consultation.get('type')}")
                print(f"   Durée: {consultation.get('duree')} min")
                
            print("✅ L'historique est accessible (les mesures détaillées sont dans les consultations individuelles)")
        
        return success

def main():
    print("🏥 TESTS DE VALIDATION DES CORRECTIONS POIDS/TAILLE/PC")
    print("=" * 70)
    print("CONTEXTE: Vérification que les 3 champs sont maintenant sauvegardés")
    print("=" * 70)
    
    tester = ConsultationFieldsTest()
    
    # Setup test data
    if not tester.setup_test_data():
        print("❌ Échec de la configuration des données de test")
        return 1
    
    # Run specific tests
    tests = [
        tester.test_consultation_payload_complete,
        tester.test_database_verification,
        tester.test_decimal_values,
        tester.test_history_display
    ]
    
    for test in tests:
        try:
            test()
        except Exception as e:
            print(f"❌ Test failed with exception: {str(e)}")
    
    # Print final results
    print(f"\n📊 RÉSULTATS FINAUX:")
    print("=" * 50)
    print(f"   Tests exécutés: {tester.tests_run}")
    print(f"   Tests réussis: {tester.tests_passed}")
    print(f"   Taux de réussite: {(tester.tests_passed/tester.tests_run*100):.1f}%")
    
    if tester.tests_passed == tester.tests_run:
        print("\n🎉 TOUS LES TESTS SONT PASSÉS!")
        print("✅ Les corrections pour les champs poids/taille/pc fonctionnent")
        print("✅ Le payload complet est maintenant envoyé")
        print("✅ Les 3 champs sont sauvegardés en base de données")
        print("✅ Les valeurs décimales sont préservées")
        return 0
    else:
        print(f"\n⚠️  {tester.tests_run - tester.tests_passed} test(s) ont échoué")
        print("❌ Des problèmes persistent avec les champs poids/taille/pc")
        return 1

if __name__ == "__main__":
    sys.exit(main())