#!/usr/bin/env python3
"""
Authentication and User Management Backend Testing
Tests the authentication system and user management functionality
"""

import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/frontend/.env')

class AuthenticationBackendTest:
    def __init__(self):
        self.base_url = os.getenv('REACT_APP_BACKEND_URL', 'https://0698237d-0754-4aa4-881e-3c8e5387d3e6.preview.emergentagent.com')
        print(f"🔧 Testing backend at: {self.base_url}")
        
    def test_auth_login_medecin(self):
        """Test POST /api/auth/login with medecin credentials"""
        print("\n🔍 Testing Authentication - Medecin Login")
        
        login_data = {
            "username": "medecin",
            "password": "medecin123"
        }
        
        response = requests.post(f"{self.base_url}/api/auth/login", json=login_data)
        
        if response.status_code != 200:
            print(f"❌ Medecin login failed: {response.status_code} - {response.text}")
            return False
        
        data = response.json()
        
        # Verify response structure
        required_fields = ["access_token", "token_type", "user"]
        for field in required_fields:
            if field not in data:
                print(f"❌ Missing field in response: {field}")
                return False
        
        # Verify token type
        if data["token_type"] != "bearer":
            print(f"❌ Expected token_type 'bearer', got: {data['token_type']}")
            return False
        
        # Verify user data
        user = data["user"]
        expected_user_fields = ["id", "username", "email", "full_name", "role", "permissions"]
        for field in expected_user_fields:
            if field not in user:
                print(f"❌ Missing user field: {field}")
                return False
        
        # Verify medecin specific data
        if user["username"] != "medecin":
            print(f"❌ Expected username 'medecin', got: {user['username']}")
            return False
            
        if user["full_name"] != "Dr Heni Dridi":
            print(f"❌ Expected full_name 'Dr Heni Dridi', got: {user['full_name']}")
            return False
            
        if user["role"] != "medecin":
            print(f"❌ Expected role 'medecin', got: {user['role']}")
            return False
        
        # Verify medecin has full permissions
        permissions = user["permissions"]
        admin_permissions = ["administration", "delete_appointment", "delete_payments", "export_data", "reset_data", "manage_users"]
        
        for perm in admin_permissions:
            if not permissions.get(perm, False):
                print(f"❌ Medecin should have {perm} permission")
                return False
        
        # Verify medecin is NOT read-only for consultations
        if permissions.get("consultation_read_only", True):
            print(f"❌ Medecin should NOT have consultation_read_only=True")
            return False
        
        print(f"✅ Medecin login successful")
        print(f"   - Username: {user['username']}")
        print(f"   - Full name: {user['full_name']}")
        print(f"   - Role: {user['role']}")
        print(f"   - Administration access: {permissions['administration']}")
        print(f"   - Manage users: {permissions['manage_users']}")
        print(f"   - AI Room access (calendar): {permissions['calendar']}")
        
        return data["access_token"]
    
    def test_auth_login_secretaire(self):
        """Test POST /api/auth/login with secretaire credentials"""
        print("\n🔍 Testing Authentication - Secretaire Login")
        
        login_data = {
            "username": "secretaire",
            "password": "secretaire123"
        }
        
        response = requests.post(f"{self.base_url}/api/auth/login", json=login_data)
        
        if response.status_code != 200:
            print(f"❌ Secretaire login failed: {response.status_code} - {response.text}")
            return False
        
        data = response.json()
        user = data["user"]
        
        # Verify secretaire specific data
        if user["username"] != "secretaire":
            print(f"❌ Expected username 'secretaire', got: {user['username']}")
            return False
            
        if user["role"] != "secretaire":
            print(f"❌ Expected role 'secretaire', got: {user['role']}")
            return False
        
        # Verify secretaire has limited permissions
        permissions = user["permissions"]
        restricted_permissions = ["administration", "delete_appointment", "delete_payments", "export_data", "reset_data", "manage_users"]
        
        for perm in restricted_permissions:
            if permissions.get(perm, False):
                print(f"❌ Secretaire should NOT have {perm} permission")
                return False
        
        # Verify secretaire IS read-only for consultations
        if not permissions.get("consultation_read_only", False):
            print(f"❌ Secretaire should have consultation_read_only=True")
            return False
        
        # Verify secretaire has basic access
        basic_permissions = ["dashboard", "patients", "calendar", "messages", "consultation"]
        for perm in basic_permissions:
            if not permissions.get(perm, False):
                print(f"❌ Secretaire should have {perm} permission")
                return False
        
        print(f"✅ Secretaire login successful")
        print(f"   - Username: {user['username']}")
        print(f"   - Full name: {user['full_name']}")
        print(f"   - Role: {user['role']}")
        print(f"   - Administration access: {permissions['administration']}")
        print(f"   - Consultation read-only: {permissions['consultation_read_only']}")
        print(f"   - AI Room access (calendar): {permissions['calendar']}")
        
        return data["access_token"]
    
    def test_auth_login_invalid_credentials(self):
        """Test POST /api/auth/login with invalid credentials"""
        print("\n🔍 Testing Authentication - Invalid Credentials")
        
        invalid_cases = [
            {"username": "medecin", "password": "wrongpassword", "desc": "wrong password"},
            {"username": "wronguser", "password": "medecin123", "desc": "wrong username"},
            {"username": "secretaire", "password": "wrongpassword", "desc": "secretaire wrong password"},
            {"username": "", "password": "medecin123", "desc": "empty username"},
            {"username": "medecin", "password": "", "desc": "empty password"}
        ]
        
        for case in invalid_cases:
            response = requests.post(f"{self.base_url}/api/auth/login", json={
                "username": case["username"],
                "password": case["password"]
            })
            
            if response.status_code != 401:
                print(f"❌ Expected 401 for {case['desc']}, got: {response.status_code}")
                return False
            
            data = response.json()
            if "detail" not in data:
                print(f"❌ Expected error detail for {case['desc']}")
                return False
        
        print(f"✅ All invalid credential cases properly rejected with 401")
        return True
    
    def test_users_list_endpoint(self):
        """Test GET /api/admin/users - List all users"""
        print("\n🔍 Testing User Management - List Users")
        
        # Get admin token
        medecin_token = self.test_auth_login_medecin()
        if not medecin_token:
            print("❌ Cannot test users list without medecin token")
            return False
        
        headers = {"Authorization": f"Bearer {medecin_token}"}
        response = requests.get(f"{self.base_url}/api/admin/users", headers=headers)
        
        if response.status_code != 200:
            print(f"❌ List users failed: {response.status_code} - {response.text}")
            return False
        
        data = response.json()
        
        if "users" not in data:
            print(f"❌ Expected 'users' field in response")
            return False
        
        users = data["users"]
        if not isinstance(users, list):
            print(f"❌ Expected users to be a list")
            return False
        
        if len(users) < 2:
            print(f"❌ Expected at least 2 users (medecin and secretaire), got: {len(users)}")
            return False
        
        # Find default users
        medecin_user = None
        secretaire_user = None
        
        for user in users:
            if user["username"] == "medecin":
                medecin_user = user
            elif user["username"] == "secretaire":
                secretaire_user = user
        
        if not medecin_user:
            print(f"❌ Default medecin user not found in users list")
            return False
        
        if not secretaire_user:
            print(f"❌ Default secretaire user not found in users list")
            return False
        
        # Verify user structure
        required_user_fields = ["id", "username", "email", "full_name", "role", "is_active", "permissions", "created_at"]
        for field in required_user_fields:
            if field not in medecin_user:
                print(f"❌ Missing field in medecin user: {field}")
                return False
            if field not in secretaire_user:
                print(f"❌ Missing field in secretaire user: {field}")
                return False
        
        # Verify medecin user properties
        if not medecin_user["is_active"]:
            print(f"❌ Medecin user should be active")
            return False
        
        if not medecin_user["permissions"]["administration"]:
            print(f"❌ Medecin user should have administration permission")
            return False
        
        # Verify secretaire user properties
        if not secretaire_user["is_active"]:
            print(f"❌ Secretaire user should be active")
            return False
        
        if secretaire_user["permissions"]["administration"]:
            print(f"❌ Secretaire user should NOT have administration permission")
            return False
        
        print(f"✅ Users list retrieved successfully")
        print(f"   - Total users: {len(users)}")
        print(f"   - Medecin user: {medecin_user['username']} ({medecin_user['full_name']})")
        print(f"   - Secretaire user: {secretaire_user['username']} ({secretaire_user['full_name']})")
        
        return users
    
    def test_user_creation(self):
        """Test POST /api/admin/users - Create new user"""
        print("\n🔍 Testing User Management - Create New User")
        
        # Get admin token
        medecin_token = self.test_auth_login_medecin()
        if not medecin_token:
            print("❌ Cannot test user creation without medecin token")
            return False
        
        headers = {"Authorization": f"Bearer {medecin_token}"}
        
        # Create new user data
        new_user_data = {
            "username": "test_auth_user",
            "email": "test.auth@cabinet.com",
            "full_name": "Test Auth User",
            "role": "secretaire",
            "password": "testauth123",
            "permissions": {
                "dashboard": True,
                "patients": True,
                "calendar": True,
                "messages": True,
                "billing": False,
                "consultation": True,
                "administration": False,
                "create_appointment": True,
                "edit_appointment": False,
                "delete_appointment": False,
                "view_payments": False,
                "edit_payments": False,
                "delete_payments": False,
                "export_data": False,
                "reset_data": False,
                "manage_users": False,
                "consultation_read_only": True
            }
        }
        
        response = requests.post(f"{self.base_url}/api/admin/users", json=new_user_data, headers=headers)
        
        if response.status_code != 200:
            print(f"❌ Create user failed: {response.status_code} - {response.text}")
            return False
        
        data = response.json()
        
        # Verify response structure
        required_fields = ["id", "username", "email", "full_name", "role", "is_active", "permissions"]
        for field in required_fields:
            if field not in data:
                print(f"❌ Missing field in create user response: {field}")
                return False
        
        # Verify user data
        if data["username"] != "test_auth_user":
            print(f"❌ Expected username 'test_auth_user', got: {data['username']}")
            return False
        
        if data["role"] != "secretaire":
            print(f"❌ Expected role 'secretaire', got: {data['role']}")
            return False
        
        if not data["is_active"]:
            print(f"❌ New user should be active")
            return False
        
        created_user_id = data["id"]
        
        # Test login with new user
        test_login_data = {"username": "test_auth_user", "password": "testauth123"}
        login_response = requests.post(f"{self.base_url}/api/auth/login", json=test_login_data)
        
        if login_response.status_code != 200:
            print(f"❌ New user cannot login: {login_response.status_code} - {login_response.text}")
            return False
        
        print(f"✅ New user created and can login successfully")
        print(f"   - User ID: {created_user_id}")
        print(f"   - Username: {data['username']}")
        print(f"   - Full name: {data['full_name']}")
        print(f"   - Role: {data['role']}")
        
        # Clean up - delete the test user
        delete_response = requests.delete(f"{self.base_url}/api/admin/users/{created_user_id}", headers=headers)
        if delete_response.status_code == 200:
            print(f"   - Test user cleaned up successfully")
        else:
            print(f"   - Warning: Could not clean up test user")
        
        return True
    
    def test_user_permissions_update(self):
        """Test PUT /api/admin/users/{user_id}/permissions - Update user permissions"""
        print("\n🔍 Testing User Management - Update User Permissions")
        
        # Get admin token
        medecin_token = self.test_auth_login_medecin()
        if not medecin_token:
            print("❌ Cannot test permissions update without medecin token")
            return False
        
        headers = {"Authorization": f"Bearer {medecin_token}"}
        
        # Get users list to find secretaire
        users_response = requests.get(f"{self.base_url}/api/admin/users", headers=headers)
        if users_response.status_code != 200:
            print(f"❌ Cannot get users list for permissions test")
            return False
        
        users = users_response.json()["users"]
        secretaire_user = None
        for user in users:
            if user["username"] == "secretaire":
                secretaire_user = user
                break
        
        if not secretaire_user:
            print(f"❌ Secretaire user not found for permissions test")
            return False
        
        secretaire_user_id = secretaire_user["id"]
        original_permissions = secretaire_user["permissions"].copy()
        
        # Update permissions - give secretaire export_data permission temporarily
        updated_permissions = original_permissions.copy()
        updated_permissions["export_data"] = True  # Changed from False to True
        updated_permissions["consultation_read_only"] = False  # Changed from True to False
        
        response = requests.put(
            f"{self.base_url}/api/admin/users/{secretaire_user_id}/permissions",
            json={"permissions": updated_permissions},
            headers=headers
        )
        
        if response.status_code != 200:
            print(f"❌ Update permissions failed: {response.status_code} - {response.text}")
            return False
        
        data = response.json()
        
        if "message" not in data or "user" not in data:
            print(f"❌ Expected 'message' and 'user' in permissions update response")
            return False
        
        updated_user = data["user"]
        updated_perms = updated_user["permissions"]
        
        # Verify permissions were updated
        if not updated_perms["export_data"]:
            print(f"❌ export_data permission was not updated")
            return False
        
        if updated_perms["consultation_read_only"]:
            print(f"❌ consultation_read_only permission was not updated")
            return False
        
        # Verify updated permissions are reflected in login
        secretaire_login = {"username": "secretaire", "password": "secretaire123"}
        login_response = requests.post(f"{self.base_url}/api/auth/login", json=secretaire_login)
        
        if login_response.status_code != 200:
            print(f"❌ Secretaire cannot login after permissions update")
            return False
        
        login_user = login_response.json()["user"]
        login_perms = login_user["permissions"]
        
        if not login_perms["export_data"]:
            print(f"❌ Updated permissions not reflected in login")
            return False
        
        print(f"✅ User permissions updated successfully")
        print(f"   - User ID: {secretaire_user_id}")
        print(f"   - Export data permission: {updated_perms['export_data']}")
        print(f"   - Consultation read-only: {updated_perms['consultation_read_only']}")
        print(f"   - Login verification: PASSED")
        
        # Restore original permissions
        restore_response = requests.put(
            f"{self.base_url}/api/admin/users/{secretaire_user_id}/permissions",
            json={"permissions": original_permissions},
            headers=headers
        )
        
        if restore_response.status_code == 200:
            print(f"   - Original permissions restored")
        else:
            print(f"   - Warning: Could not restore original permissions")
        
        return True
    
    def test_ai_room_permissions(self):
        """Test that users have AI Room access through calendar permissions"""
        print("\n🔍 Testing AI Room Permissions")
        
        # Test medecin AI Room access
        medecin_token = self.test_auth_login_medecin()
        if not medecin_token:
            print("❌ Cannot test AI Room permissions without medecin token")
            return False
        
        # Test secretaire AI Room access
        secretaire_token = self.test_auth_login_secretaire()
        if not secretaire_token:
            print("❌ Cannot test AI Room permissions without secretaire token")
            return False
        
        # Get user data from login responses
        medecin_login = requests.post(f"{self.base_url}/api/auth/login", json={"username": "medecin", "password": "medecin123"})
        secretaire_login = requests.post(f"{self.base_url}/api/auth/login", json={"username": "secretaire", "password": "secretaire123"})
        
        medecin_user = medecin_login.json()["user"]
        secretaire_user = secretaire_login.json()["user"]
        
        # Check calendar permissions (which enable AI Room access)
        medecin_ai_room_access = medecin_user["permissions"].get("calendar", False)
        secretaire_ai_room_access = secretaire_user["permissions"].get("calendar", False)
        
        if not medecin_ai_room_access:
            print(f"❌ Medecin should have AI Room access via calendar permission")
            return False
        
        if not secretaire_ai_room_access:
            print(f"❌ Secretaire should have AI Room access via calendar permission")
            return False
        
        print(f"✅ AI Room permissions verified")
        print(f"   - Medecin AI Room access (calendar): {medecin_ai_room_access}")
        print(f"   - Secretaire AI Room access (calendar): {secretaire_ai_room_access}")
        print(f"   - Both users can access AI Room functionality")
        
        return True
    
    def run_all_tests(self):
        """Run all authentication and user management tests"""
        print("🚀 Starting Authentication and User Management Backend Tests")
        print("=" * 80)
        
        test_results = []
        
        # Authentication Tests
        print("\n📋 AUTHENTICATION TESTS")
        print("-" * 40)
        
        test_results.append(("Medecin Login", self.test_auth_login_medecin()))
        test_results.append(("Secretaire Login", self.test_auth_login_secretaire()))
        test_results.append(("Invalid Credentials", self.test_auth_login_invalid_credentials()))
        
        # User Management Tests
        print("\n📋 USER MANAGEMENT TESTS")
        print("-" * 40)
        
        test_results.append(("List Users", self.test_users_list_endpoint()))
        test_results.append(("Create User", self.test_user_creation()))
        test_results.append(("Update Permissions", self.test_user_permissions_update()))
        test_results.append(("AI Room Permissions", self.test_ai_room_permissions()))
        
        # Summary
        print("\n" + "=" * 80)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 80)
        
        passed = 0
        failed = 0
        
        for test_name, result in test_results:
            if result:
                print(f"✅ {test_name}: PASSED")
                passed += 1
            else:
                print(f"❌ {test_name}: FAILED")
                failed += 1
        
        print(f"\n📈 FINAL RESULTS:")
        print(f"   - Total tests: {len(test_results)}")
        print(f"   - Passed: {passed}")
        print(f"   - Failed: {failed}")
        print(f"   - Success rate: {(passed/len(test_results)*100):.1f}%")
        
        if failed == 0:
            print(f"\n🎉 ALL AUTHENTICATION AND USER MANAGEMENT TESTS PASSED!")
            print(f"   - Authentication system working correctly")
            print(f"   - Default users (medecin/secretaire) created and accessible")
            print(f"   - User management endpoints functional")
            print(f"   - Permissions system working as expected")
            print(f"   - AI Room access permissions verified")
            return True
        else:
            print(f"\n⚠️ SOME TESTS FAILED - Please review the issues above")
            return False

if __name__ == "__main__":
    tester = AuthenticationBackendTest()
    success = tester.run_all_tests()
    exit(0 if success else 1)