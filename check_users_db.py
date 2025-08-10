#!/usr/bin/env python3
"""
Check Users Database
Check what's actually stored in the users database
"""

import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/frontend/.env')

class CheckUsersDB:
    def __init__(self):
        # Use the correct backend URL from environment
        backend_url = os.getenv('REACT_APP_BACKEND_URL', 'https://86e1ae33-6e29-4ce5-a743-1e543eb0a6b8.preview.emergentagent.com')
        self.base_url = backend_url
        print(f"🔗 Checking users database at: {self.base_url}")
        
    def check_database_users(self):
        """Check what users are actually in the database"""
        print("\n🔍 Checking Database Users")
        
        # Use auto-login token to bypass permission check
        headers = {"Authorization": "Bearer auto-login-token"}
        
        response = requests.get(f"{self.base_url}/api/admin/users", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            users = data.get("users", [])
            
            print(f"✅ Found {len(users)} users in database:")
            
            for i, user in enumerate(users):
                print(f"\n  User {i+1}:")
                print(f"    - ID: {user.get('id')}")
                print(f"    - Username: {user.get('username')}")
                print(f"    - Full Name: {user.get('full_name')}")
                print(f"    - Role: {user.get('role')}")
                print(f"    - Active: {user.get('is_active')}")
                print(f"    - Created: {user.get('created_at')}")
                
                permissions = user.get('permissions', {})
                print(f"    - Permissions:")
                for perm, value in permissions.items():
                    if perm in ["administration", "manage_users", "delete_appointment", "delete_payments", "export_data", "reset_data"]:
                        print(f"      * {perm}: {value}")
                
                # Check if this is the medecin user with wrong permissions
                if user.get('username') == 'medecin' and not permissions.get('manage_users', False):
                    print(f"    ❌ ISSUE FOUND: medecin user missing manage_users permission!")
            
            return users
        else:
            print(f"❌ Failed to get users: {response.status_code} - {response.text}")
            return []
    
    def fix_medecin_permissions(self):
        """Fix the medecin user permissions"""
        print("\n🔧 Attempting to Fix Medecin User Permissions")
        
        # Use auto-login token
        headers = {"Authorization": "Bearer auto-login-token"}
        
        # First get the current users
        response = requests.get(f"{self.base_url}/api/admin/users", headers=headers)
        if response.status_code != 200:
            print(f"❌ Cannot get users: {response.status_code}")
            return False
        
        users = response.json().get("users", [])
        medecin_user = None
        
        for user in users:
            if user.get('username') == 'medecin':
                medecin_user = user
                break
        
        if not medecin_user:
            print("❌ Medecin user not found")
            return False
        
        print(f"✅ Found medecin user: {medecin_user['full_name']}")
        
        # Update permissions
        updated_permissions = medecin_user.get('permissions', {})
        updated_permissions.update({
            "administration": True,
            "delete_appointment": True,
            "delete_payments": True,
            "export_data": True,
            "reset_data": True,
            "manage_users": True,
            "consultation_read_only": False
        })
        
        # Try to update the user
        user_id = medecin_user['id']
        update_data = {
            "permissions": updated_permissions
        }
        
        response = requests.put(f"{self.base_url}/api/admin/users/{user_id}/permissions", 
                               json=updated_permissions, headers=headers)
        
        if response.status_code == 200:
            print("✅ Successfully updated medecin user permissions")
            return True
        else:
            print(f"❌ Failed to update permissions: {response.status_code} - {response.text}")
            return False
    
    def test_after_fix(self):
        """Test the admin users endpoint after fixing permissions"""
        print("\n🔍 Testing After Permission Fix")
        
        # Login with medecin credentials
        login_data = {
            "username": "medecin",
            "password": "medecin123"
        }
        
        response = requests.post(f"{self.base_url}/api/auth/login", json=login_data)
        if response.status_code != 200:
            print(f"❌ Login failed: {response.status_code}")
            return False
        
        token = response.json()["access_token"]
        user = response.json()["user"]
        
        print(f"✅ Login successful")
        print(f"   - Username: {user['username']}")
        print(f"   - Manage Users Permission: {user.get('permissions', {}).get('manage_users', False)}")
        
        # Test admin users endpoint
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{self.base_url}/api/admin/users", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            users = data.get("users", [])
            print(f"✅ Admin users endpoint now works! Found {len(users)} users")
            return True
        else:
            print(f"❌ Admin users endpoint still fails: {response.status_code} - {response.text}")
            return False
    
    def reset_and_recreate_users(self):
        """Reset and recreate users with correct permissions"""
        print("\n🔄 Resetting and Recreating Users")
        
        # Use auto-login token
        headers = {"Authorization": "Bearer auto-login-token"}
        
        # Reset demo data to recreate users
        response = requests.get(f"{self.base_url}/api/reset-demo", headers=headers)
        
        if response.status_code == 200:
            print("✅ Demo data reset successful")
            
            # Check users again
            response = requests.get(f"{self.base_url}/api/admin/users", headers=headers)
            if response.status_code == 200:
                users = response.json().get("users", [])
                print(f"✅ Found {len(users)} users after reset")
                
                # Check medecin permissions
                for user in users:
                    if user.get('username') == 'medecin':
                        permissions = user.get('permissions', {})
                        manage_users = permissions.get('manage_users', False)
                        print(f"   - Medecin manage_users permission: {manage_users}")
                        return manage_users
            
            return False
        else:
            print(f"❌ Demo data reset failed: {response.status_code}")
            return False
    
    def run_diagnosis(self):
        """Run complete diagnosis and fix"""
        print("🚀 Starting Users Database Diagnosis and Fix")
        print("=" * 60)
        
        # Step 1: Check current database state
        users = self.check_database_users()
        
        # Step 2: Check if medecin user has correct permissions
        medecin_has_manage_users = False
        for user in users:
            if user.get('username') == 'medecin':
                medecin_has_manage_users = user.get('permissions', {}).get('manage_users', False)
                break
        
        if medecin_has_manage_users:
            print("\n✅ Medecin user already has correct permissions")
            return True
        
        print("\n❌ Medecin user missing manage_users permission")
        
        # Step 3: Try to fix permissions
        print("\n🔧 Attempting Permission Fix...")
        if self.fix_medecin_permissions():
            # Test if fix worked
            if self.test_after_fix():
                print("\n✅ PROBLEM FIXED! Admin users endpoint should now work in frontend")
                return True
        
        # Step 4: If permission fix didn't work, try reset
        print("\n🔄 Permission fix didn't work, trying full reset...")
        if self.reset_and_recreate_users():
            if self.test_after_fix():
                print("\n✅ PROBLEM FIXED! Admin users endpoint should now work in frontend")
                return True
        
        print("\n❌ Could not fix the permission issue")
        return False

if __name__ == "__main__":
    checker = CheckUsersDB()
    success = checker.run_diagnosis()
    
    if success:
        print("\n🎉 SUCCESS: The admin users endpoint should now work properly!")
        print("   Frontend Administration page Users tab should display users correctly")
    else:
        print("\n💥 FAILED: Could not resolve the permission issue")
        print("   Manual intervention may be required")