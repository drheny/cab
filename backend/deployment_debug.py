#!/usr/bin/env python3
"""
Post-deployment debugging script
Checks database state and creates missing users if needed
"""

import os
import sys
from pymongo import MongoClient
import bcrypt
from datetime import datetime
import json

# MongoDB connection - use environment variable or fallback
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017/cabinet_medical')

def check_database_connection():
    """Check if we can connect to MongoDB"""
    try:
        client = MongoClient(MONGO_URL)
        
        # Extract database name from URL for Atlas compatibility
        if "mongodb+srv://" in MONGO_URL or "mongodb://" in MONGO_URL:
            if "/" in MONGO_URL.split("?")[0]:
                db_name = MONGO_URL.split("?")[0].split("/")[-1]
                if db_name and db_name != "":
                    db = client.get_database(db_name)
                else:
                    db = client.get_database("cabinet_medical")
            else:
                db = client.get_database("cabinet_medical")
        else:
            db = client.get_database("cabinet_medical")
        
        # Test connection
        db.command("ping")
        return True, db, f"Connected to database: {db.name}"
    except Exception as e:
        return False, None, f"Connection failed: {str(e)}"

def check_collections_state(db):
    """Check the state of all collections"""
    collections_info = {}
    
    collection_names = ['users', 'patients', 'appointments', 'consultations', 'payments', 'phone_messages']
    
    for collection_name in collection_names:
        try:
            collection = db[collection_name]
            count = collection.count_documents({})
            collections_info[collection_name] = {
                'count': count,
                'exists': count > 0
            }
            
            # Get sample document for users collection
            if collection_name == 'users' and count > 0:
                sample_user = collection.find_one({}, {'username': 1, 'role': 1, 'full_name': 1})
                collections_info[collection_name]['sample'] = sample_user
                
        except Exception as e:
            collections_info[collection_name] = {
                'count': 0,
                'exists': False,
                'error': str(e)
            }
    
    return collections_info

def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def create_default_users(db):
    """Create default users (medecin and secretaire)"""
    users_collection = db['users']
    
    try:
        # Check if users already exist
        existing_users = users_collection.count_documents({})
        if existing_users > 0:
            return False, f"Users already exist ({existing_users} found)"
        
        # Create medecin user
        medecin_user = {
            "username": "medecin",
            "full_name": "Dr Heni Dridi",
            "role": "medecin", 
            "hashed_password": hash_password("medecin123"),
            "is_active": True,
            "permissions": {
                "administration": True,
                "delete_appointment": True,
                "delete_payments": True,
                "export_data": True,
                "reset_data": True,
                "manage_users": True,
                "consultation_read_only": False
            },
            "created_at": datetime.now(),
            "last_login": None
        }
        
        # Create secretaire user
        secretaire_user = {
            "username": "secretaire",
            "full_name": "Secrétaire Médicale", 
            "role": "secretaire",
            "hashed_password": hash_password("secretaire123"),
            "is_active": True,
            "permissions": {
                "administration": False,
                "delete_appointment": False,
                "delete_payments": False,
                "export_data": False,
                "reset_data": False,
                "manage_users": False,
                "consultation_read_only": True
            },
            "created_at": datetime.now(),
            "last_login": None
        }
        
        # Insert users
        result = users_collection.insert_many([medecin_user, secretaire_user])
        
        return True, f"Created {len(result.inserted_ids)} users successfully"
        
    except Exception as e:
        return False, f"Failed to create users: {str(e)}"

def create_minimal_demo_data(db):
    """Create minimal demo data for the system to function"""
    try:
        patients_collection = db['patients']
        
        # Check if patients already exist
        existing_patients = patients_collection.count_documents({})
        if existing_patients > 0:
            return False, f"Demo data already exists ({existing_patients} patients found)"
        
        # Create minimal demo patient
        demo_patient = {
            "id": "patient_demo_1",
            "nom": "Demo",
            "prenom": "Patient", 
            "date_naissance": "1990-01-01",
            "age": "34 ans",
            "sexe": "M",
            "telephone": "21612345678",
            "adresse": "Adresse Demo, Tunis",
            "numero_whatsapp": "21612345678",
            "lien_whatsapp": "https://wa.me/21612345678",
            "pere": {"nom": "", "telephone": "", "fonction": ""},
            "mere": {"nom": "", "telephone": "", "fonction": ""}, 
            "notes": "Patient de démonstration",
            "antecedents": "Aucun",
            "allergies": "Aucune",
            "consultations": [],
            "date_premiere_consultation": "",
            "date_derniere_consultation": "",
            "photo_url": "",
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        
        result = patients_collection.insert_one(demo_patient)
        return True, f"Created demo patient: {result.inserted_id}"
        
    except Exception as e:
        return False, f"Failed to create demo data: {str(e)}"

def main():
    """Main diagnostic function"""
    print("🔍 POST-DEPLOYMENT DIAGNOSTIC")
    print("=" * 50)
    
    # Check database connection
    connected, db, connection_msg = check_database_connection()
    print(f"📊 Database Connection: {connection_msg}")
    
    if not connected:
        print("❌ Cannot proceed without database connection")
        print("\n💡 Solutions:")
        print("1. Check MONGO_URL environment variable")
        print("2. Verify Atlas cluster is running")
        print("3. Check IP whitelist in Atlas")
        print("4. Verify username/password in connection string")
        return False
    
    print("✅ Database connection successful!")
    
    # Check collections state
    print("\n📋 Collections Status:")
    collections_info = check_collections_state(db)
    
    empty_collections = []
    for collection_name, info in collections_info.items():
        count = info.get('count', 0)
        if count == 0:
            empty_collections.append(collection_name)
        
        status = "✅" if count > 0 else "❌"
        print(f"  {status} {collection_name}: {count} documents")
        
        if collection_name == 'users' and 'sample' in info:
            sample = info['sample']
            print(f"      Sample user: {sample.get('username')} ({sample.get('role')})")
    
    # Check if users collection is empty (main issue)
    users_empty = 'users' in empty_collections
    
    if users_empty:
        print("\n🚨 ISSUE FOUND: No users in database!")
        print("This is why login fails - no medecin user exists.")
        
        # Offer to create users
        print("\n🔧 CREATING DEFAULT USERS...")
        success, message = create_default_users(db)
        if success:
            print(f"✅ {message}")
        else:
            print(f"❌ {message}")
        
        # Also create minimal demo data if needed
        if len(empty_collections) > 1:
            print("\n🔧 CREATING MINIMAL DEMO DATA...")
            success, message = create_minimal_demo_data(db)
            if success:
                print(f"✅ {message}")
            else:
                print(f"❌ {message}")
    
    else:
        print("\n✅ Users collection has data - issue might be elsewhere")
        
        # Check specific medecin user
        users_collection = db['users']
        medecin_user = users_collection.find_one({"username": "medecin"})
        
        if medecin_user:
            print("✅ medecin user exists")
            print(f"   Full name: {medecin_user.get('full_name')}")
            print(f"   Active: {medecin_user.get('is_active')}")
            print(f"   Role: {medecin_user.get('role')}")
        else:
            print("❌ medecin user not found!")
            print("🔧 Creating medecin user...")
            success, message = create_default_users(db)
            print(f"Result: {message}")
    
    print("\n" + "=" * 50)
    print("🎯 DIAGNOSTIC COMPLETE")
    
    if users_empty:
        print("✅ Issue resolved: Default users created")
        print("🔑 You can now login with: medecin/medecin123")
    
    print("\n📋 Next steps:")
    print("1. Try logging in again with medecin/medecin123")
    print("2. If still issues, check frontend REACT_APP_BACKEND_URL")
    print("3. Verify /api/auth/login endpoint is accessible")
    
    return True

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"❌ Diagnostic failed: {str(e)}")
        sys.exit(1)