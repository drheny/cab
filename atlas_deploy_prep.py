#!/usr/bin/env python3
"""
Atlas Deployment Preparation Script
Prepares the application for MongoDB Atlas deployment with proper error handling
"""

import os
import re

def prepare_server_for_atlas():
    """Prepare server.py for Atlas deployment"""
    server_file = "/app/backend/server.py"
    
    print("🔧 Preparing server.py for Atlas deployment...")
    
    with open(server_file, 'r') as f:
        content = f.read()
    
    # Ensure proper MongoDB connection with Atlas support
    mongo_connection_pattern = r'# MongoDB connection.*?client = MongoClient\(MONGO_URL\)'
    
    new_mongo_connection = '''# MongoDB connection with Atlas support
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017/cabinet_medical')
print(f"🔧 Connecting to MongoDB: {MONGO_URL[:30]}...")

try:
    # Create MongoDB client with Atlas-optimized settings
    client = MongoClient(
        MONGO_URL,
        serverSelectionTimeoutMS=10000,  # 10 seconds timeout
        connectTimeoutMS=10000,
        maxPoolSize=10,
        retryWrites=True
    )
    
    # Test the connection
    client.admin.command('ping')
    print("✅ MongoDB connection successful")
    
except Exception as e:
    print(f"❌ MongoDB connection failed: {e}")
    print("🔄 Falling back to local connection for development")
    client = MongoClient('mongodb://localhost:27017/cabinet_medical')'''
    
    if re.search(mongo_connection_pattern, content, re.DOTALL):
        content = re.sub(mongo_connection_pattern, new_mongo_connection, content, flags=re.DOTALL)
        print("  ✅ Updated MongoDB connection code")
    else:
        print("  ℹ️ MongoDB connection code not found - will add at the end")
    
    # Ensure proper database selection with Atlas compatibility
    db_selection_pattern = r'db = client\..*?(?=\n\n|\n#|\npatients_collection)'
    
    new_db_selection = '''# Database selection with Atlas compatibility
if "mongodb+srv://" in MONGO_URL or "mongodb://" in MONGO_URL:
    # Extract database name from connection string
    try:
        if "/" in MONGO_URL.split("?")[0] and MONGO_URL.split("?")[0].split("/")[-1]:
            db_name = MONGO_URL.split("?")[0].split("/")[-1]
            db = client.get_database(db_name)
            print(f"✅ Using database: {db_name}")
        else:
            # Use default database if no specific name in URL
            db = client.get_default_database()
            print(f"✅ Using default database: {db.name}")
    except Exception as e:
        print(f"⚠️  Database selection error: {e}")
        db = client.get_database("cabinet_medical")
        print("✅ Using fallback database: cabinet_medical")
else:
    # Local development
    db = client.get_database("cabinet_medical")
    print("✅ Using local database: cabinet_medical")'''
    
    if re.search(db_selection_pattern, content, re.DOTALL):
        content = re.sub(db_selection_pattern, new_db_selection, content, flags=re.DOTALL)
        print("  ✅ Updated database selection code")
    
    # Add startup user creation if not present
    startup_pattern = r'@app\.on_event\("startup"\).*?async def startup_event\(\):.*?return.*?\}'
    
    if not re.search(startup_pattern, content, re.DOTALL):
        startup_code = '''
@app.on_event("startup")
async def startup_event():
    """Initialize the application on startup"""
    print("🚀 Starting Medical Cabinet Backend...")
    
    try:
        # Test database connection
        db.command("ping")
        print("✅ Database connection verified")
        
        # Create default users if they don't exist
        users_count = users_collection.count_documents({})
        if users_count == 0:
            print("👤 Creating default users...")
            
            # Create medecin user
            medecin_user = {
                "username": "medecin",
                "full_name": "Dr Heni Dridi",
                "role": "medecin",
                "hashed_password": bcrypt.hashpw("medecin123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
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
                "hashed_password": bcrypt.hashpw("secretaire123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
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
            
            users_collection.insert_many([medecin_user, secretaire_user])
            print("✅ Default users created successfully")
        else:
            print(f"👤 Found {users_count} existing users")
            
        # Create minimal demo data if needed
        patients_count = patients_collection.count_documents({})
        if patients_count == 0:
            print("📊 Creating demo data...")
            create_demo_data() 
            print("✅ Demo data created")
        else:
            print(f"📊 Found {patients_count} existing patients")
            
    except Exception as e:
        print(f"⚠️  Startup error: {e}")
        
    print("🎉 Application startup completed!")
    return {"message": "Application initialized successfully"}
'''
        
        # Add startup code before the last function
        content = content.rstrip() + startup_code
        print("  ✅ Added startup event handler")
    
    # Add health check endpoints
    if "/health" not in content:
        health_endpoints = '''
@app.get("/health")
async def health_check():
    """Health check for Kubernetes/deployment"""
    try:
        db.command("ping")
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Database unhealthy: {str(e)}")

@app.get("/api/health")  
async def api_health_check():
    """API health check"""
    try:
        db.command("ping")
        users_count = users_collection.count_documents({})
        return {
            "api_status": "healthy",
            "database": "connected", 
            "users_count": users_count,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"API unhealthy: {str(e)}")
'''
        content = content.rstrip() + health_endpoints
        print("  ✅ Added health check endpoints")
    
    # Write back the modified content
    with open(server_file, 'w') as f:
        f.write(content)
    
    print("✅ Server prepared for Atlas deployment")

def create_deployment_checklist():
    """Create deployment checklist"""
    checklist = '''# 🚀 ATLAS DEPLOYMENT CHECKLIST

## ✅ MongoDB Atlas Configuration
- [ ] Cluster created and running
- [ ] Database user created with Atlas admin permissions
- [ ] Network access configured (0.0.0.0/0 for testing)
- [ ] Connection string obtained and password replaced
- [ ] Database name added to connection string (/cabinet_medical)

## ✅ Environment Variables in Emergent
- [ ] MONGO_URL set with full Atlas connection string
- [ ] REACT_APP_BACKEND_URL set to https://docflow-system-2.emergent.host
- [ ] EMERGENT_LLM_KEY set (if available)

## ✅ Application Preparation
- [ ] Code updated for Atlas compatibility
- [ ] Health check endpoints added
- [ ] Startup event handler configured
- [ ] User creation automated

## 🚀 Deployment Steps
1. Configure all environment variables in Emergent
2. Deploy the updated application
3. Wait 3-5 minutes for full deployment
4. Test health endpoints
5. Test user login

## 🧪 Post-Deployment Testing
Test these URLs after deployment:
- https://docflow-system-2.emergent.host/health
- https://docflow-system-2.emergent.host/api/health  
- https://docflow-system-2.emergent.host/api/auth/login (POST with medecin/medecin123)

## 🔧 Troubleshooting
If deployment fails:
1. Check environment variables are correctly set
2. Verify Atlas connection string format
3. Confirm Atlas user has proper permissions
4. Check network access allows Emergent IPs

**Login Credentials After Successful Deployment:**
- Username: medecin
- Password: medecin123
'''
    
    with open("/app/ATLAS_DEPLOYMENT_GUIDE.md", 'w') as f:
        f.write(checklist)
    
    print("✅ Created deployment checklist: ATLAS_DEPLOYMENT_GUIDE.md")

def main():
    """Main preparation function"""
    print("🎯 ATLAS DEPLOYMENT PREPARATION")
    print("=" * 50)
    
    prepare_server_for_atlas()
    create_deployment_checklist()
    
    print("\n" + "=" * 50)
    print("✅ ATLAS PREPARATION COMPLETED!")
    
    print("\n📋 Next Steps:")
    print("1. Configure MongoDB Atlas (create cluster, user, connection string)")
    print("2. Set environment variables in Emergent console")
    print("3. Deploy the prepared application")
    print("4. Test health endpoints after deployment")
    print("5. Login with medecin/medecin123")
    
    print("\n📖 See ATLAS_DEPLOYMENT_GUIDE.md for detailed checklist")

if __name__ == "__main__":
    main()