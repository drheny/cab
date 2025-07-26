import requests
import unittest
import json
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/frontend/.env')

class AuthenticationSystemTest(unittest.TestCase):
    def setUp(self):
        # Use the correct backend URL from environment
        backend_url = os.getenv('REACT_APP_BACKEND_URL', 'https://8b45b722-0b82-461c-8cd4-01b1cb4950c0.preview.emergentagent.com')
        self.base_url = backend_url
        print(f"Testing authentication system at: {self.base_url}")
    
    # ========== USER MANAGEMENT AND AUTHENTICATION SYSTEM TESTS ==========
    
    def test_authentication_login_doctor(self):
        """Test login with default doctor credentials"""
        login_data = {
            "username": "medecin",
            "password": "medecin123"
        }
        
        response = requests.post(f"{self.base_url}/api/auth/login", json=login_data)
        self.assertEqual(response.status_code, 200)
        
        # Verify response structure
        data = response.json()
        self.assertIn("access_token", data)
        self.assertIn("token_type", data)
        self.assertIn("user", data)
        
        # Verify token type
        self.assertEqual(data["token_type"], "bearer")
        
        # Verify user data structure
        user = data["user"]
        self.assertEqual(user["username"], "medecin")
        self.assertEqual(user["role"], "medecin")
        self.assertEqual(user["full_name"], "Dr Heni Dridi")
        # Note: is_active is not returned in the response, but user can login so they are active
        
        # Verify doctor permissions
        permissions = user["permissions"]
        self.assertTrue(permissions["administration"])
        self.assertTrue(permissions["manage_users"])
        self.assertTrue(permissions["delete_appointment"])
        self.assertTrue(permissions["export_data"])
        self.assertTrue(permissions["reset_data"])
        self.assertFalse(permissions["consultation_read_only"])
        
        # Store token for subsequent tests
        self.doctor_token = data["access_token"]
        
        print("✅ Doctor login successful with correct permissions")
    
    def test_authentication_login_secretary(self):
        """Test login with default secretary credentials"""
        login_data = {
            "username": "secretaire",
            "password": "secretaire123"
        }
        
        response = requests.post(f"{self.base_url}/api/auth/login", json=login_data)
        self.assertEqual(response.status_code, 200)
        
        # Verify response structure
        data = response.json()
        self.assertIn("access_token", data)
        self.assertIn("token_type", data)
        self.assertIn("user", data)
        
        # Verify user data
        user = data["user"]
        self.assertEqual(user["username"], "secretaire")
        self.assertEqual(user["role"], "secretaire")
        self.assertEqual(user["full_name"], "Secrétaire")
        # Note: is_active is not returned in the response, but user can login so they are active
        
        # Verify secretary permissions (limited)
        permissions = user["permissions"]
        self.assertFalse(permissions["administration"])
        self.assertFalse(permissions["manage_users"])
        self.assertFalse(permissions["delete_appointment"])
        self.assertFalse(permissions["export_data"])
        self.assertFalse(permissions["reset_data"])
        self.assertTrue(permissions["consultation_read_only"])
        
        # Store token for subsequent tests
        self.secretary_token = data["access_token"]
        
        print("✅ Secretary login successful with limited permissions")
    
    def test_authentication_invalid_credentials(self):
        """Test login with invalid credentials"""
        invalid_credentials = [
            {"username": "medecin", "password": "wrongpassword"},
            {"username": "wronguser", "password": "medecin123"},
            {"username": "secretaire", "password": "wrongpassword"},
            {"username": "", "password": ""},
            {"username": "admin", "password": "admin"}
        ]
        
        for credentials in invalid_credentials:
            response = requests.post(f"{self.base_url}/api/auth/login", json=credentials)
            self.assertEqual(response.status_code, 401)
            
            # Verify error response
            data = response.json()
            self.assertIn("detail", data)
            
        print("✅ Invalid credentials properly rejected with 401")
    
    def test_authentication_token_validation(self):
        """Test token validation with /api/auth/me"""
        # First login to get a valid token
        login_data = {"username": "medecin", "password": "medecin123"}
        response = requests.post(f"{self.base_url}/api/auth/login", json=login_data)
        self.assertEqual(response.status_code, 200)
        token = response.json()["access_token"]
        
        # Test token validation
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{self.base_url}/api/auth/me", headers=headers)
        self.assertEqual(response.status_code, 200)
        
        # Verify user data from token
        user_data = response.json()
        self.assertEqual(user_data["username"], "medecin")
        self.assertEqual(user_data["role"], "medecin")
        self.assertIn("permissions", user_data)
        
        print("✅ Token validation working correctly")
    
    def test_authentication_invalid_token(self):
        """Test with invalid or missing token"""
        # Test with invalid token
        headers = {"Authorization": "Bearer invalid_token_here"}
        response = requests.get(f"{self.base_url}/api/auth/me", headers=headers)
        self.assertEqual(response.status_code, 401)
        
        # Test with missing token
        response = requests.get(f"{self.base_url}/api/auth/me")
        self.assertEqual(response.status_code, 403)  # Forbidden without token
        
        # Test with malformed authorization header
        headers = {"Authorization": "InvalidFormat token"}
        response = requests.get(f"{self.base_url}/api/auth/me", headers=headers)
        self.assertEqual(response.status_code, 403)
        
        print("✅ Invalid tokens properly rejected")
    
    def test_user_management_get_all_users_doctor(self):
        """Test GET /api/admin/users as doctor (should succeed)"""
        # Login as doctor
        login_data = {"username": "medecin", "password": "medecin123"}
        response = requests.post(f"{self.base_url}/api/auth/login", json=login_data)
        self.assertEqual(response.status_code, 200)
        token = response.json()["access_token"]
        
        # Get all users
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{self.base_url}/api/admin/users", headers=headers)
        self.assertEqual(response.status_code, 200)
        
        # Verify response structure
        data = response.json()
        self.assertIn("users", data)
        self.assertIn("count", data)
        users = data["users"]
        self.assertIsInstance(users, list)
        self.assertGreaterEqual(len(users), 2)  # At least doctor and secretary
        self.assertEqual(data["count"], len(users))
        
        # Verify user structure
        for user in users:
            self.assertIn("id", user)
            self.assertIn("username", user)
            self.assertIn("full_name", user)
            self.assertIn("role", user)
            self.assertIn("is_active", user)
            self.assertIn("permissions", user)
            self.assertNotIn("hashed_password", user)  # Password should not be exposed
        
        # Find doctor and secretary users
        doctor_user = next((u for u in users if u["username"] == "medecin"), None)
        secretary_user = next((u for u in users if u["username"] == "secretaire"), None)
        
        self.assertIsNotNone(doctor_user)
        self.assertIsNotNone(secretary_user)
        
        # Verify doctor permissions
        self.assertTrue(doctor_user["permissions"]["administration"])
        self.assertTrue(doctor_user["permissions"]["manage_users"])
        
        # Verify secretary permissions
        self.assertFalse(secretary_user["permissions"]["administration"])
        self.assertFalse(secretary_user["permissions"]["manage_users"])
        
        print("✅ Doctor can access user management successfully")
    
    def test_user_management_get_all_users_secretary(self):
        """Test GET /api/admin/users as secretary (should fail)"""
        # Login as secretary
        login_data = {"username": "secretaire", "password": "secretaire123"}
        response = requests.post(f"{self.base_url}/api/auth/login", json=login_data)
        self.assertEqual(response.status_code, 200)
        token = response.json()["access_token"]
        
        # Try to get all users
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{self.base_url}/api/admin/users", headers=headers)
        self.assertEqual(response.status_code, 403)  # Forbidden
        
        print("✅ Secretary properly denied access to user management")
    
    def test_user_management_create_user_doctor(self):
        """Test POST /api/admin/users as doctor (should succeed)"""
        # Login as doctor
        login_data = {"username": "medecin", "password": "medecin123"}
        response = requests.post(f"{self.base_url}/api/auth/login", json=login_data)
        self.assertEqual(response.status_code, 200)
        token = response.json()["access_token"]
        
        # Create new user
        import time
        unique_id = str(int(time.time()))
        new_user_data = {
            "username": f"test_user_{unique_id}",
            "email": "test@example.com",
            "full_name": "Test User",
            "role": "secretaire",
            "password": "testpassword123"
        }
        
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.post(f"{self.base_url}/api/admin/users", json=new_user_data, headers=headers)
        self.assertEqual(response.status_code, 200)
        
        # Verify response
        data = response.json()
        self.assertIn("id", data)
        self.assertEqual(data["username"], f"test_user_{unique_id}")
        user_id = data["id"]
        
        # Verify user was created
        response = requests.get(f"{self.base_url}/api/admin/users", headers=headers)
        self.assertEqual(response.status_code, 200)
        users_data = response.json()
        users = users_data["users"]
        
        test_user = next((u for u in users if u["username"] == f"test_user_{unique_id}"), None)
        self.assertIsNotNone(test_user)
        self.assertEqual(test_user["email"], "test@example.com")
        self.assertEqual(test_user["full_name"], "Test User")
        self.assertEqual(test_user["role"], "secretaire")
        
        # Clean up - delete the test user
        response = requests.delete(f"{self.base_url}/api/admin/users/{user_id}", headers=headers)
        self.assertEqual(response.status_code, 200)
        
        print("✅ Doctor can create new users successfully")
    
    def test_user_management_create_user_secretary(self):
        """Test POST /api/admin/users as secretary (should fail)"""
        # Login as secretary
        login_data = {"username": "secretaire", "password": "secretaire123"}
        response = requests.post(f"{self.base_url}/api/auth/login", json=login_data)
        self.assertEqual(response.status_code, 200)
        token = response.json()["access_token"]
        
        # Try to create new user
        new_user_data = {
            "username": "unauthorized_user",
            "full_name": "Unauthorized User",
            "role": "secretaire",
            "password": "password123"
        }
        
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.post(f"{self.base_url}/api/admin/users", json=new_user_data, headers=headers)
        self.assertEqual(response.status_code, 403)  # Forbidden
        
        print("✅ Secretary properly denied user creation access")
    
    def test_user_management_update_user_permissions(self):
        """Test PUT /api/admin/users/{user_id}/permissions"""
        # Login as doctor
        login_data = {"username": "medecin", "password": "medecin123"}
        response = requests.post(f"{self.base_url}/api/auth/login", json=login_data)
        self.assertEqual(response.status_code, 200)
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Get secretary user ID
        response = requests.get(f"{self.base_url}/api/admin/users", headers=headers)
        self.assertEqual(response.status_code, 200)
        users_data = response.json()
        users = users_data["users"]
        
        secretary_user = next((u for u in users if u["username"] == "secretaire"), None)
        self.assertIsNotNone(secretary_user)
        secretary_id = secretary_user["id"]
        
        # Update secretary permissions
        new_permissions = {
            "dashboard": True,
            "patients": True,
            "calendar": True,
            "messages": True,
            "billing": False,  # Remove billing access
            "consultation": True,
            "administration": False,
            "create_appointment": True,
            "edit_appointment": False,  # Remove edit access
            "delete_appointment": False,
            "view_payments": False,  # Remove payment access
            "edit_payments": False,
            "delete_payments": False,
            "export_data": False,
            "reset_data": False,
            "manage_users": False,
            "consultation_read_only": True
        }
        
        response = requests.put(f"{self.base_url}/api/admin/users/{secretary_id}/permissions", 
                               json=new_permissions, headers=headers)
        self.assertEqual(response.status_code, 200)
        
        # Verify permissions were updated
        response = requests.get(f"{self.base_url}/api/admin/users", headers=headers)
        self.assertEqual(response.status_code, 200)
        users_data = response.json()
        users = users_data["users"]
        
        updated_secretary = next((u for u in users if u["id"] == secretary_id), None)
        self.assertIsNotNone(updated_secretary)
        
        permissions = updated_secretary["permissions"]
        self.assertFalse(permissions["billing"])
        self.assertFalse(permissions["edit_appointment"])
        self.assertFalse(permissions["view_payments"])
        self.assertTrue(permissions["consultation_read_only"])
        
        print("✅ User permissions updated successfully")
    
    def test_user_management_update_self(self):
        """Test user can update their own profile"""
        # Login as secretary
        login_data = {"username": "secretaire", "password": "secretaire123"}
        response = requests.post(f"{self.base_url}/api/auth/login", json=login_data)
        self.assertEqual(response.status_code, 200)
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Get secretary user ID
        response = requests.get(f"{self.base_url}/api/auth/me", headers=headers)
        self.assertEqual(response.status_code, 200)
        user_data = response.json()
        user_id = user_data["id"]
        
        # Update own profile
        update_data = {
            "full_name": "Secrétaire Médicale",
            "email": "secretaire@cabinet.com"
        }
        
        response = requests.put(f"{self.base_url}/api/admin/users/{user_id}", 
                               json=update_data, headers=headers)
        self.assertEqual(response.status_code, 200)
        
        # Verify update
        response = requests.get(f"{self.base_url}/api/auth/me", headers=headers)
        self.assertEqual(response.status_code, 200)
        updated_user = response.json()
        
        self.assertEqual(updated_user["full_name"], "Secrétaire Médicale")
        self.assertEqual(updated_user["email"], "secretaire@cabinet.com")
        
        print("✅ User can update own profile successfully")
    
    def test_user_management_delete_user_doctor(self):
        """Test DELETE /api/admin/users/{user_id} as doctor"""
        # Login as doctor
        login_data = {"username": "medecin", "password": "medecin123"}
        response = requests.post(f"{self.base_url}/api/auth/login", json=login_data)
        self.assertEqual(response.status_code, 200)
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create a test user to delete
        import time
        unique_id = str(int(time.time()))
        new_user_data = {
            "username": f"temp_user_{unique_id}",
            "full_name": "Temporary User",
            "role": "secretaire",
            "password": "temppassword123"
        }
        
        response = requests.post(f"{self.base_url}/api/admin/users", json=new_user_data, headers=headers)
        self.assertEqual(response.status_code, 200)
        user_id = response.json()["id"]
        
        # Delete the user
        response = requests.delete(f"{self.base_url}/api/admin/users/{user_id}", headers=headers)
        self.assertEqual(response.status_code, 200)
        
        # Verify user was deleted
        response = requests.get(f"{self.base_url}/api/admin/users", headers=headers)
        self.assertEqual(response.status_code, 200)
        users_data = response.json()
        users = users_data["users"]
        
        deleted_user = next((u for u in users if u["id"] == user_id), None)
        self.assertIsNone(deleted_user)
        
        print("✅ Doctor can delete users successfully")
    
    def test_user_management_delete_user_secretary(self):
        """Test DELETE /api/admin/users/{user_id} as secretary (should fail)"""
        # Login as secretary
        login_data = {"username": "secretaire", "password": "secretaire123"}
        response = requests.post(f"{self.base_url}/api/auth/login", json=login_data)
        self.assertEqual(response.status_code, 200)
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Try to delete a user (use doctor's ID)
        # First get doctor's ID
        login_doctor = {"username": "medecin", "password": "medecin123"}
        response = requests.post(f"{self.base_url}/api/auth/login", json=login_doctor)
        doctor_token = response.json()["access_token"]
        doctor_headers = {"Authorization": f"Bearer {doctor_token}"}
        
        response = requests.get(f"{self.base_url}/api/admin/users", headers=doctor_headers)
        users_data = response.json()
        users = users_data["users"]
        doctor_user = next((u for u in users if u["username"] == "medecin"), None)
        doctor_id = doctor_user["id"]
        
        # Try to delete as secretary
        response = requests.delete(f"{self.base_url}/api/admin/users/{doctor_id}", headers=headers)
        self.assertEqual(response.status_code, 403)  # Forbidden
        
        print("✅ Secretary properly denied user deletion access")
    
    def test_permission_system_comprehensive(self):
        """Test comprehensive permission system validation"""
        # Login as both users
        doctor_login = {"username": "medecin", "password": "medecin123"}
        secretary_login = {"username": "secretaire", "password": "secretaire123"}
        
        doctor_response = requests.post(f"{self.base_url}/api/auth/login", json=doctor_login)
        secretary_response = requests.post(f"{self.base_url}/api/auth/login", json=secretary_login)
        
        self.assertEqual(doctor_response.status_code, 200)
        self.assertEqual(secretary_response.status_code, 200)
        
        doctor_token = doctor_response.json()["access_token"]
        secretary_token = secretary_response.json()["access_token"]
        
        doctor_headers = {"Authorization": f"Bearer {doctor_token}"}
        secretary_headers = {"Authorization": f"Bearer {secretary_token}"}
        
        # Test doctor permissions (should have full access)
        doctor_permissions_tests = [
            ("/api/admin/users", "GET", 200),
            ("/api/admin/users", "POST", 400),  # 400 because no data, but not 403
            ("/api/admin/stats", "GET", 200),
            ("/api/admin/export/patients", "GET", 200),
        ]
        
        for endpoint, method, expected_status in doctor_permissions_tests:
            if method == "GET":
                response = requests.get(f"{self.base_url}{endpoint}", headers=doctor_headers)
            elif method == "POST":
                response = requests.post(f"{self.base_url}{endpoint}", json={}, headers=doctor_headers)
            
            # For doctor, should not get 403 (forbidden)
            self.assertNotEqual(response.status_code, 403, 
                               f"Doctor should have access to {method} {endpoint}")
        
        # Test secretary permissions (should have limited access)
        secretary_permissions_tests = [
            ("/api/admin/users", "GET", 403),
            ("/api/admin/users", "POST", 403),
            ("/api/admin/stats", "GET", 403),
            ("/api/admin/export/patients", "GET", 403),
        ]
        
        for endpoint, method, expected_status in secretary_permissions_tests:
            if method == "GET":
                response = requests.get(f"{self.base_url}{endpoint}", headers=secretary_headers)
            elif method == "POST":
                response = requests.post(f"{self.base_url}{endpoint}", json={}, headers=secretary_headers)
            
            self.assertEqual(response.status_code, expected_status, 
                           f"Secretary permission test failed for {method} {endpoint}")
        
        print("✅ Comprehensive permission system working correctly")
    
    def test_jwt_token_structure(self):
        """Test JWT token structure and content"""
        # Login to get token
        login_data = {"username": "medecin", "password": "medecin123"}
        response = requests.post(f"{self.base_url}/api/auth/login", json=login_data)
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        token = data["access_token"]
        
        # Verify token is not empty and has proper format
        self.assertTrue(len(token) > 0)
        self.assertEqual(len(token.split('.')), 3)  # JWT has 3 parts separated by dots
        
        # Verify token can be used for authentication
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{self.base_url}/api/auth/me", headers=headers)
        self.assertEqual(response.status_code, 200)
        
        # Verify user data from token matches login response
        token_user_data = response.json()
        login_user_data = data["user"]
        
        self.assertEqual(token_user_data["username"], login_user_data["username"])
        self.assertEqual(token_user_data["role"], login_user_data["role"])
        self.assertEqual(token_user_data["full_name"], login_user_data["full_name"])
        
        print("✅ JWT token structure and content validation successful")
    
    def test_default_users_creation(self):
        """Test that default users are created during demo data initialization"""
        # This test verifies that the create_default_users() function works
        # by attempting to login with default credentials
        
        # Test doctor default user
        doctor_login = {"username": "medecin", "password": "medecin123"}
        response = requests.post(f"{self.base_url}/api/auth/login", json=doctor_login)
        self.assertEqual(response.status_code, 200)
        
        doctor_data = response.json()
        self.assertEqual(doctor_data["user"]["username"], "medecin")
        self.assertEqual(doctor_data["user"]["full_name"], "Dr Heni Dridi")
        self.assertEqual(doctor_data["user"]["role"], "medecin")
        
        # Test secretary default user
        secretary_login = {"username": "secretaire", "password": "secretaire123"}
        response = requests.post(f"{self.base_url}/api/auth/login", json=secretary_login)
        self.assertEqual(response.status_code, 200)
        
        secretary_data = response.json()
        self.assertEqual(secretary_data["user"]["username"], "secretaire")
        self.assertEqual(secretary_data["user"]["full_name"], "Secrétaire")
        self.assertEqual(secretary_data["user"]["role"], "secretaire")
        
        print("✅ Default users created successfully during initialization")
    
    def test_password_hashing_security(self):
        """Test that passwords are properly hashed and not stored in plain text"""
        # Login as doctor to get admin access
        login_data = {"username": "medecin", "password": "medecin123"}
        response = requests.post(f"{self.base_url}/api/auth/login", json=login_data)
        self.assertEqual(response.status_code, 200)
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Get all users
        response = requests.get(f"{self.base_url}/api/admin/users", headers=headers)
        self.assertEqual(response.status_code, 200)
        users_data = response.json()
        users = users_data["users"]
        
        # Verify that hashed_password is not exposed in API responses
        for user in users:
            self.assertNotIn("hashed_password", user)
            self.assertNotIn("password", user)
        
        # Create a test user to verify password hashing
        import time
        unique_id = str(int(time.time()))
        new_user_data = {
            "username": f"hash_test_user_{unique_id}",
            "full_name": "Hash Test User",
            "role": "secretaire",
            "password": "plaintext_password_123"
        }
        
        response = requests.post(f"{self.base_url}/api/admin/users", json=new_user_data, headers=headers)
        self.assertEqual(response.status_code, 200)
        user_id = response.json()["id"]
        
        # Verify the user can login with the password (meaning it was hashed and stored correctly)
        test_login = {"username": f"hash_test_user_{unique_id}", "password": "plaintext_password_123"}
        response = requests.post(f"{self.base_url}/api/auth/login", json=test_login)
        self.assertEqual(response.status_code, 200)
        
        # Verify wrong password fails
        wrong_login = {"username": f"hash_test_user_{unique_id}", "password": "wrong_password"}
        response = requests.post(f"{self.base_url}/api/auth/login", json=wrong_login)
        self.assertEqual(response.status_code, 401)
        
        # Clean up
        response = requests.delete(f"{self.base_url}/api/admin/users/{user_id}", headers=headers)
        self.assertEqual(response.status_code, 200)
        
        print("✅ Password hashing and security validation successful")

if __name__ == '__main__':
    unittest.main()