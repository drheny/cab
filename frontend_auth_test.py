#!/usr/bin/env python3
"""
Frontend Authentication Test
Test if the frontend authentication flow is working properly for admin users endpoint
"""

import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/frontend/.env')

class FrontendAuthTest:
    def __init__(self):
        # Use the correct backend URL from environment
        backend_url = os.getenv('REACT_APP_BACKEND_URL', 'https://0698237d-0754-4aa4-881e-3c8e5387d3e6.preview.emergentagent.com')
        self.base_url = backend_url
        print(f"🔗 Testing backend at: {self.base_url}")
        
    def test_login_flow(self):
        """Test the complete login flow that frontend uses"""
        print("\n🔍 Testing Frontend Login Flow")
        
        # Step 1: Login with medecin credentials (same as frontend)
        login_data = {
            "username": "medecin",
            "password": "medecin123"
        }
        
        print("  Step 1: Logging in with medecin credentials...")
        response = requests.post(f"{self.base_url}/api/auth/login", json=login_data)
        
        if response.status_code != 200:
            print(f"  ❌ Login failed: {response.status_code} - {response.text}")
            return None
        
        login_data = response.json()
        token = login_data["access_token"]
        user = login_data["user"]
        
        print(f"  ✅ Login successful")
        print(f"     - Username: {user['username']}")
        print(f"     - Role: {user['role']}")
        print(f"     - Full Name: {user['full_name']}")
        
        # Step 2: Check user permissions
        print("  Step 2: Checking user permissions...")
        permissions = user.get("permissions", {})
        
        print(f"     - Administration: {permissions.get('administration', False)}")
        print(f"     - Manage Users: {permissions.get('manage_users', False)}")
        
        if not permissions.get("manage_users", False):
            print("  ❌ CRITICAL ISSUE: User does not have 'manage_users' permission!")
            print("     This explains why the admin users endpoint returns 403")
            return None
        else:
            print("  ✅ User has required 'manage_users' permission")
        
        return token, user
    
    def test_admin_users_with_real_token(self):
        """Test admin users endpoint with real login token"""
        print("\n🔍 Testing Admin Users Endpoint with Real Login Token")
        
        # Get real login token
        login_result = self.test_login_flow()
        if not login_result:
            print("❌ Cannot proceed without valid login")
            return False
        
        token, user = login_result
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test the admin users endpoint
        print("  Testing /api/admin/users endpoint...")
        response = requests.get(f"{self.base_url}/api/admin/users", headers=headers)
        
        print(f"  Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            users = data.get("users", [])
            count = data.get("count", 0)
            
            print(f"  ✅ Success! Found {count} users")
            print(f"     - Response format: {{users: array({len(users)}), count: {count}}}")
            
            # Show user details
            for i, user_data in enumerate(users):
                print(f"     - User {i+1}: {user_data.get('username')} ({user_data.get('full_name')})")
            
            return True
        
        elif response.status_code == 403:
            print(f"  ❌ Access forbidden: {response.text}")
            print("     This indicates a permission issue with the logged-in user")
            return False
        
        else:
            print(f"  ❌ Unexpected error: {response.status_code} - {response.text}")
            return False
    
    def test_user_creation_issue(self):
        """Test if the issue is with user creation/permissions"""
        print("\n🔍 Testing User Creation and Permissions Issue")
        
        # Check if default users exist and have correct permissions
        print("  Checking default user creation...")
        
        # Try to initialize demo data
        response = requests.get(f"{self.base_url}/api/init-demo")
        print(f"  Demo data init response: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"  Demo data message: {data.get('message', 'No message')}")
        
        # Now test login again
        login_data = {
            "username": "medecin",
            "password": "medecin123"
        }
        
        response = requests.post(f"{self.base_url}/api/auth/login", json=login_data)
        
        if response.status_code == 200:
            user_data = response.json()["user"]
            permissions = user_data.get("permissions", {})
            
            print(f"  User permissions after demo init:")
            for perm, value in permissions.items():
                if perm in ["administration", "manage_users", "delete_appointment", "delete_payments", "export_data", "reset_data"]:
                    print(f"     - {perm}: {value}")
            
            # Check if this is a permission configuration issue
            if not permissions.get("manage_users", False):
                print("  ❌ FOUND THE ISSUE: Default medecin user doesn't have 'manage_users' permission")
                print("     This is a backend configuration problem in create_default_users()")
                return False
            else:
                print("  ✅ Default medecin user has correct permissions")
                return True
        else:
            print(f"  ❌ Login failed after demo init: {response.status_code}")
            return False
    
    def test_frontend_simulation(self):
        """Simulate exactly what the frontend does"""
        print("\n🔍 Simulating Frontend Behavior")
        
        # Step 1: Frontend login
        print("  Step 1: Frontend login simulation...")
        login_data = {
            "username": "medecin",
            "password": "medecin123"
        }
        
        response = requests.post(f"{self.base_url}/api/auth/login", json=login_data)
        if response.status_code != 200:
            print(f"  ❌ Frontend login would fail: {response.status_code}")
            return False
        
        login_response = response.json()
        token = login_response["access_token"]
        user = login_response["user"]
        
        print(f"  ✅ Frontend login would succeed")
        print(f"     - Token received: {token[:20]}...")
        print(f"     - User role: {user['role']}")
        
        # Step 2: Frontend would set axios headers
        print("  Step 2: Setting axios headers (simulated)...")
        headers = {"Authorization": f"Bearer {token}"}
        
        # Step 3: Frontend calls fetchUsers() which calls /api/admin/users
        print("  Step 3: Frontend fetchUsers() call simulation...")
        
        # This is exactly what the frontend Administration.js does:
        # const response = await axios.get(`${API_BASE_URL}/api/admin/users`);
        response = requests.get(f"{self.base_url}/api/admin/users", headers=headers)
        
        print(f"     - Request URL: {self.base_url}/api/admin/users")
        print(f"     - Request headers: Authorization: Bearer {token[:20]}...")
        print(f"     - Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            users = data.get("users", [])
            
            print(f"  ✅ Frontend would receive {len(users)} users")
            print(f"     - setAllUsers() would be called with: {len(users)} users")
            print(f"     - Frontend should display users in the Administration page")
            
            if len(users) == 0:
                print("  ⚠️ Users array is empty - this explains empty frontend display")
            
            return True
        
        elif response.status_code == 403:
            print(f"  ❌ Frontend would get 403 Forbidden")
            print(f"     - Error message: {response.text}")
            print(f"     - This explains why frontend shows empty users")
            print(f"     - Frontend console would show: 'Error fetching users: 403'")
            return False
        
        else:
            print(f"  ❌ Frontend would get unexpected error: {response.status_code}")
            return False
    
    def run_all_tests(self):
        """Run all frontend authentication tests"""
        print("🚀 Starting Frontend Authentication Testing")
        print("=" * 60)
        
        results = {
            "login_flow": False,
            "admin_endpoint": False,
            "user_permissions": False,
            "frontend_simulation": False
        }
        
        # Test 1: User creation and permissions
        results["user_permissions"] = self.test_user_creation_issue()
        
        # Test 2: Login flow
        login_result = self.test_login_flow()
        results["login_flow"] = login_result is not None
        
        # Test 3: Admin endpoint with real token
        results["admin_endpoint"] = self.test_admin_users_with_real_token()
        
        # Test 4: Frontend simulation
        results["frontend_simulation"] = self.test_frontend_simulation()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 FRONTEND AUTHENTICATION TEST RESULTS")
        print("=" * 60)
        
        if all(results.values()):
            print("✅ ALL TESTS PASSED - Frontend authentication should work")
            print("   If users still don't show, check frontend JavaScript console for errors")
        elif not results["user_permissions"]:
            print("❌ USER PERMISSIONS ISSUE FOUND")
            print("   - Default medecin user doesn't have 'manage_users' permission")
            print("   - This is a backend configuration issue")
            print("   - Need to fix create_default_users() function")
        elif not results["login_flow"]:
            print("❌ LOGIN FLOW ISSUE FOUND")
            print("   - Cannot login with medecin credentials")
            print("   - Check user creation and authentication system")
        elif not results["admin_endpoint"]:
            print("❌ ADMIN ENDPOINT ACCESS ISSUE FOUND")
            print("   - User can login but cannot access admin users endpoint")
            print("   - Permission configuration problem")
        elif not results["frontend_simulation"]:
            print("❌ FRONTEND SIMULATION FAILED")
            print("   - The exact frontend flow is not working")
            print("   - Check token handling and API calls")
        
        return results

if __name__ == "__main__":
    tester = FrontendAuthTest()
    results = tester.run_all_tests()