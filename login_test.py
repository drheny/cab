#!/usr/bin/env python3
"""
URGENT LOGIN FUNCTIONALITY TEST
Testing medecin user login functionality as requested in review.
"""

import requests
import json
import os
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv('/app/frontend/.env')

class LoginTest:
    def __init__(self):
        # Use the correct backend URL from environment
        backend_url = os.getenv('REACT_APP_BACKEND_URL', 'https://0698237d-0754-4aa4-881e-3c8e5387d3e6.preview.emergentagent.com')
        self.base_url = backend_url
        print(f"🔗 Testing backend at: {self.base_url}")
    
    def test_database_users(self):
        """Check what users exist in the database with their current credentials"""
        print("\n" + "="*60)
        print("🔍 STEP 1: CHECKING DATABASE USERS")
        print("="*60)
        
        try:
            # Use auto-login token to access admin endpoint
            headers = {"Authorization": "Bearer auto-login-token"}
            response = requests.get(f"{self.base_url}/api/admin/users", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                users = data.get("users", [])
                print(f"✅ Found {len(users)} users in database:")
                
                for user in users:
                    print(f"  👤 Username: {user.get('username')}")
                    print(f"     Full Name: {user.get('full_name')}")
                    print(f"     Role: {user.get('role')}")
                    print(f"     Active: {user.get('is_active')}")
                    print(f"     Permissions: manage_users = {user.get('permissions', {}).get('manage_users', False)}")
                    print(f"     Last Login: {user.get('last_login', 'Never')}")
                    print()
                
                return users
            else:
                print(f"❌ Failed to fetch users: {response.status_code}")
                print(f"Response: {response.text}")
                return []
                
        except Exception as e:
            print(f"❌ Error checking database users: {str(e)}")
            return []
    
    def test_login_credentials(self, username, password):
        """Test login with specific credentials"""
        print(f"\n🔐 Testing login: {username} / {password}")
        
        login_data = {
            "username": username,
            "password": password
        }
        
        try:
            response = requests.post(f"{self.base_url}/api/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                user = data.get("user", {})
                print(f"✅ LOGIN SUCCESS!")
                print(f"   Token Type: {data.get('token_type')}")
                print(f"   User: {user.get('full_name')} ({user.get('username')})")
                print(f"   Role: {user.get('role')}")
                print(f"   Active: {user.get('is_active')}")
                print(f"   Permissions: {json.dumps(user.get('permissions', {}), indent=6)}")
                return True, data
            else:
                print(f"❌ LOGIN FAILED: {response.status_code}")
                print(f"   Error: {response.text}")
                return False, response.text
                
        except Exception as e:
            print(f"❌ LOGIN ERROR: {str(e)}")
            return False, str(e)
    
    def test_login_endpoint_availability(self):
        """Test if the login endpoint is available and working"""
        print("\n" + "="*60)
        print("🌐 STEP 2: TESTING LOGIN ENDPOINT AVAILABILITY")
        print("="*60)
        
        try:
            # Test with invalid credentials to see if endpoint responds
            response = requests.post(f"{self.base_url}/api/auth/login", json={"username": "test", "password": "test"})
            
            if response.status_code in [401, 422]:
                print("✅ Login endpoint is available and responding")
                print(f"   Status: {response.status_code}")
                print(f"   Response: {response.text}")
                return True
            else:
                print(f"⚠️ Unexpected response from login endpoint: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Login endpoint not accessible: {str(e)}")
            return False
    
    def test_medecin_login_variations(self):
        """Test various medecin login combinations"""
        print("\n" + "="*60)
        print("🔐 STEP 3: TESTING MEDECIN LOGIN VARIATIONS")
        print("="*60)
        
        # Common medecin credential combinations
        credentials_to_test = [
            ("medecin", "medecin123"),
            ("medecin", "medecin"),
            ("doctor", "doctor123"),
            ("doctor", "doctor"),
            ("admin", "admin123"),
            ("admin", "admin"),
            ("heni", "heni123"),
            ("dr_heni", "dridi123"),
        ]
        
        successful_logins = []
        
        for username, password in credentials_to_test:
            success, result = self.test_login_credentials(username, password)
            if success:
                successful_logins.append((username, password, result))
        
        return successful_logins
    
    def test_demo_data_initialization_impact(self):
        """Check if demo data initialization affected user credentials"""
        print("\n" + "="*60)
        print("🔄 STEP 4: CHECKING DEMO DATA INITIALIZATION IMPACT")
        print("="*60)
        
        try:
            # Check demo data status
            headers = {"Authorization": "Bearer auto-login-token"}
            response = requests.get(f"{self.base_url}/api/init-demo", headers=headers)
            
            print(f"Demo data status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"Demo data response: {json.dumps(data, indent=2)}")
            else:
                print(f"Demo data response: {response.text}")
                
        except Exception as e:
            print(f"❌ Error checking demo data: {str(e)}")
    
    def check_password_hashing(self):
        """Check if passwords are properly hashed in database"""
        print("\n" + "="*60)
        print("🔒 STEP 5: CHECKING PASSWORD HASHING")
        print("="*60)
        
        # This would require direct database access, but we can infer from login attempts
        print("Password hashing verification through login attempts...")
        
        # Test if plaintext passwords work (they shouldn't)
        plaintext_tests = [
            ("medecin", "medecin123"),  # This should work if properly hashed
            ("secretaire", "secretaire123"),  # This should work if properly hashed
        ]
        
        for username, password in plaintext_tests:
            success, result = self.test_login_credentials(username, password)
            if success:
                print(f"✅ {username} login working with expected password")
            else:
                print(f"❌ {username} login failed with expected password")
    
    def run_comprehensive_login_test(self):
        """Run comprehensive login functionality test"""
        print("🚨 URGENT LOGIN FUNCTIONALITY TEST STARTED")
        print("=" * 80)
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Backend URL: {self.base_url}")
        print("=" * 80)
        
        # Step 1: Check database users
        users = self.test_database_users()
        
        # Step 2: Test login endpoint availability
        endpoint_available = self.test_login_endpoint_availability()
        
        # Step 3: Test medecin login variations
        successful_logins = self.test_medecin_login_variations()
        
        # Step 4: Check demo data impact
        self.test_demo_data_initialization_impact()
        
        # Step 5: Check password hashing
        self.check_password_hashing()
        
        # Summary
        print("\n" + "="*80)
        print("📋 COMPREHENSIVE LOGIN TEST SUMMARY")
        print("="*80)
        
        print(f"🔍 Database Users Found: {len(users)}")
        for user in users:
            print(f"   - {user.get('username')} ({user.get('role')}) - Active: {user.get('is_active')}")
        
        print(f"\n🌐 Login Endpoint Available: {'✅ YES' if endpoint_available else '❌ NO'}")
        
        print(f"\n🔐 Successful Login Combinations: {len(successful_logins)}")
        for username, password, result in successful_logins:
            user_info = result.get('user', {})
            print(f"   ✅ {username} / {password} -> {user_info.get('full_name')} ({user_info.get('role')})")
        
        if len(successful_logins) == 0:
            print("   ❌ NO SUCCESSFUL LOGINS FOUND!")
            print("   🔧 RECOMMENDED ACTIONS:")
            print("      1. Check if users exist in database")
            print("      2. Verify password hashing is working correctly")
            print("      3. Check if demo data initialization corrupted user accounts")
            print("      4. Verify login endpoint is functioning properly")
        
        # Critical findings
        print(f"\n🚨 CRITICAL FINDINGS:")
        medecin_user = next((u for u in users if u.get('username') == 'medecin'), None)
        if medecin_user:
            print(f"   ✅ Medecin user exists in database")
            print(f"   - Full Name: {medecin_user.get('full_name')}")
            print(f"   - Active: {medecin_user.get('is_active')}")
            print(f"   - Role: {medecin_user.get('role')}")
            print(f"   - Manage Users Permission: {medecin_user.get('permissions', {}).get('manage_users', False)}")
        else:
            print(f"   ❌ Medecin user NOT FOUND in database!")
        
        # Check if medecin login worked
        medecin_login_success = any(username == 'medecin' for username, _, _ in successful_logins)
        if medecin_login_success:
            print(f"   ✅ Medecin login is WORKING")
        else:
            print(f"   ❌ Medecin login is FAILING")
            print(f"   🔧 IMMEDIATE ACTION REQUIRED:")
            print(f"      - Reset medecin password to 'medecin123'")
            print(f"      - Verify password hashing function")
            print(f"      - Check user account status")
        
        return {
            'users_found': len(users),
            'endpoint_available': endpoint_available,
            'successful_logins': successful_logins,
            'medecin_exists': medecin_user is not None,
            'medecin_login_works': medecin_login_success
        }

if __name__ == "__main__":
    test = LoginTest()
    results = test.run_comprehensive_login_test()
    
    # Exit with appropriate code
    if results['medecin_login_works']:
        print(f"\n🎉 SUCCESS: Medecin login is working!")
        exit(0)
    else:
        print(f"\n💥 FAILURE: Medecin login is NOT working!")
        exit(1)