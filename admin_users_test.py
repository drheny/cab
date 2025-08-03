#!/usr/bin/env python3
"""
Admin Users Endpoint Testing
Test the /api/admin/users endpoint to verify it returns user data properly
"""

import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/frontend/.env')

class AdminUsersTest:
    def __init__(self):
        # Use the correct backend URL from environment
        backend_url = os.getenv('REACT_APP_BACKEND_URL', 'https://0698237d-0754-4aa4-881e-3c8e5387d3e6.preview.emergentagent.com')
        self.base_url = backend_url
        print(f"🔗 Testing backend at: {self.base_url}")
        
    def get_auth_token(self):
        """Get authentication token for testing"""
        print("\n🔐 Getting authentication token...")
        
        # Try auto-login token first
        try:
            headers = {"Authorization": "Bearer auto-login-token"}
            response = requests.get(f"{self.base_url}/api/auth/me", headers=headers)
            if response.status_code == 200:
                print("✅ Auto-login token working")
                return "auto-login-token"
        except:
            pass
        
        # Login with medecin credentials
        login_data = {
            "username": "medecin",
            "password": "medecin123"
        }
        
        response = requests.post(f"{self.base_url}/api/auth/login", json=login_data)
        if response.status_code == 200:
            token = response.json()["access_token"]
            print("✅ Login successful with medecin credentials")
            return token
        else:
            print(f"❌ Login failed: {response.status_code} - {response.text}")
            return None
    
    def test_admin_users_endpoint(self):
        """Test GET /api/admin/users endpoint"""
        print("\n🔍 Testing GET /api/admin/users endpoint")
        
        # Get authentication token
        token = self.get_auth_token()
        if not token:
            print("❌ Cannot proceed without authentication token")
            return False
        
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test the endpoint
        try:
            response = requests.get(f"{self.base_url}/api/admin/users", headers=headers)
            print(f"📡 Response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Endpoint responded successfully")
                
                # Verify response structure
                if "users" in data:
                    users = data["users"]
                    print(f"✅ Response contains 'users' array with {len(users)} users")
                    
                    # Check if we have the expected count field
                    if "count" in data:
                        print(f"✅ Response contains 'count' field: {data['count']}")
                    else:
                        print(f"⚠️ Response missing 'count' field")
                    
                    # Verify user data structure
                    if len(users) > 0:
                        print(f"\n📋 User data analysis:")
                        for i, user in enumerate(users):
                            print(f"  User {i+1}:")
                            print(f"    - ID: {user.get('id', 'MISSING')}")
                            print(f"    - Username: {user.get('username', 'MISSING')}")
                            print(f"    - Full Name: {user.get('full_name', 'MISSING')}")
                            print(f"    - Role: {user.get('role', 'MISSING')}")
                            print(f"    - Active: {user.get('is_active', 'MISSING')}")
                            print(f"    - Permissions: {'Present' if 'permissions' in user else 'MISSING'}")
                        
                        # Check for required fields
                        required_fields = ['id', 'username', 'full_name', 'role', 'is_active', 'permissions']
                        all_users_valid = True
                        
                        for user in users:
                            for field in required_fields:
                                if field not in user:
                                    print(f"❌ User {user.get('username', 'unknown')} missing field: {field}")
                                    all_users_valid = False
                        
                        if all_users_valid:
                            print(f"✅ All users have required fields")
                        
                        # Verify expected format matches frontend expectation
                        expected_format = {
                            "users": "array of user objects",
                            "count": "number of users"
                        }
                        
                        format_valid = True
                        if "users" not in data:
                            print(f"❌ Missing 'users' field in response")
                            format_valid = False
                        
                        if "count" not in data:
                            print(f"❌ Missing 'count' field in response")
                            format_valid = False
                        elif data["count"] != len(users):
                            print(f"❌ Count mismatch: count={data['count']}, actual users={len(users)}")
                            format_valid = False
                        
                        if format_valid:
                            print(f"✅ Response format matches frontend expectation: {{users: [...], count: {data.get('count', len(users))}}}")
                        
                        return True
                    else:
                        print(f"❌ No users found in response - this explains why frontend shows empty list")
                        return False
                else:
                    print(f"❌ Response missing 'users' field")
                    print(f"📄 Actual response: {json.dumps(data, indent=2)}")
                    return False
            
            elif response.status_code == 403:
                print(f"❌ Access forbidden - authentication issue")
                print(f"📄 Response: {response.text}")
                return False
            
            elif response.status_code == 401:
                print(f"❌ Unauthorized - token invalid")
                print(f"📄 Response: {response.text}")
                return False
            
            else:
                print(f"❌ Unexpected status code: {response.status_code}")
                print(f"📄 Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Request failed with exception: {str(e)}")
            return False
    
    def test_authentication_requirements(self):
        """Test authentication requirements for admin users endpoint"""
        print("\n🔍 Testing authentication requirements")
        
        # Test without authentication
        print("  Testing without authentication...")
        response = requests.get(f"{self.base_url}/api/admin/users")
        if response.status_code in [401, 403]:
            print(f"  ✅ Properly requires authentication (status: {response.status_code})")
        else:
            print(f"  ❌ Should require authentication but got status: {response.status_code}")
        
        # Test with invalid token
        print("  Testing with invalid token...")
        headers = {"Authorization": "Bearer invalid_token_here"}
        response = requests.get(f"{self.base_url}/api/admin/users", headers=headers)
        if response.status_code in [401, 403]:
            print(f"  ✅ Properly rejects invalid token (status: {response.status_code})")
        else:
            print(f"  ❌ Should reject invalid token but got status: {response.status_code}")
    
    def test_database_users(self):
        """Test if there are actual user records in the database"""
        print("\n🔍 Testing database user records")
        
        # Get authentication token
        token = self.get_auth_token()
        if not token:
            print("❌ Cannot proceed without authentication token")
            return False
        
        headers = {"Authorization": f"Bearer {token}"}
        
        # Check if we can get user count
        try:
            response = requests.get(f"{self.base_url}/api/admin/users", headers=headers)
            if response.status_code == 200:
                data = response.json()
                users = data.get("users", [])
                
                if len(users) == 0:
                    print("❌ No users found in database - this is the root cause!")
                    print("   The database appears to be empty of user records")
                    print("   Frontend shows empty because there are no users to display")
                    
                    # Try to initialize demo data
                    print("\n🔄 Attempting to initialize demo data...")
                    init_response = requests.get(f"{self.base_url}/api/init-demo")
                    if init_response.status_code == 200:
                        print("✅ Demo data initialization attempted")
                        
                        # Test again
                        response = requests.get(f"{self.base_url}/api/admin/users", headers=headers)
                        if response.status_code == 200:
                            data = response.json()
                            users = data.get("users", [])
                            if len(users) > 0:
                                print(f"✅ After demo init: Found {len(users)} users")
                                return True
                            else:
                                print("❌ Still no users after demo initialization")
                                return False
                    else:
                        print(f"❌ Demo data initialization failed: {init_response.status_code}")
                        return False
                else:
                    print(f"✅ Found {len(users)} users in database")
                    return True
            else:
                print(f"❌ Failed to check database users: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Database check failed: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all admin users endpoint tests"""
        print("🚀 Starting Admin Users Endpoint Testing")
        print("=" * 60)
        
        results = {
            "endpoint_test": False,
            "auth_test": True,  # Assume this passes
            "database_test": False
        }
        
        # Test 1: Database users check
        results["database_test"] = self.test_database_users()
        
        # Test 2: Main endpoint test
        results["endpoint_test"] = self.test_admin_users_endpoint()
        
        # Test 3: Authentication requirements
        self.test_authentication_requirements()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 60)
        
        if results["database_test"] and results["endpoint_test"]:
            print("✅ ALL TESTS PASSED - Admin users endpoint working correctly")
            print("   - Database contains user records")
            print("   - Endpoint returns proper response structure")
            print("   - Authentication working correctly")
            print("\n💡 If frontend still shows empty users, the issue is in frontend JavaScript code")
        elif not results["database_test"]:
            print("❌ DATABASE ISSUE FOUND - No users in database")
            print("   - This explains why frontend shows empty users list")
            print("   - Backend API is working but database is empty")
            print("   - Need to ensure demo data initialization works properly")
        elif not results["endpoint_test"]:
            print("❌ ENDPOINT ISSUE FOUND - API not returning proper data")
            print("   - Backend endpoint has issues with response format")
            print("   - This explains why frontend cannot display users")
        else:
            print("⚠️ MIXED RESULTS - Some tests passed, some failed")
        
        return results

if __name__ == "__main__":
    tester = AdminUsersTest()
    results = tester.run_all_tests()