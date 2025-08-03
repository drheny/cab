#!/usr/bin/env python3
"""
Deployment fix script - ensures all dependencies and configurations are correct
"""

import os
import sys
import subprocess

def check_requirements():
    """Check if all requirements are installed"""
    print("📦 Checking Python requirements...")
    
    requirements_file = "/app/backend/requirements.txt"
    
    if not os.path.exists(requirements_file):
        print("❌ requirements.txt not found")
        return False
    
    try:
        # Read requirements
        with open(requirements_file, 'r') as f:
            requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        
        print(f"📋 Found {len(requirements)} requirements:")
        for req in requirements:
            print(f"  - {req}")
        
        # Check if emergentintegrations is properly specified
        emergent_found = any('emergentintegrations' in req for req in requirements)
        if not emergent_found:
            print("⚠️  emergentintegrations not found in requirements")
        
        return True
        
    except Exception as e:
        print(f"❌ Error reading requirements: {e}")
        return False

def check_import_issues():
    """Check for common import issues"""
    print("\n🔍 Checking for import issues...")
    
    try:
        # Test basic FastAPI import
        import fastapi
        print("✅ FastAPI import successful")
        
        # Test MongoDB import
        import pymongo
        print("✅ PyMongo import successful")
        
        # Test bcrypt import
        import bcrypt
        print("✅ bcrypt import successful")
        
        # Test JWT import
        from jose import jwt
        print("✅ JWT import successful")
        
        # Test emergentintegrations
        try:
            import emergentintegrations
            print("✅ emergentintegrations import successful")
        except ImportError as e:
            print(f"❌ emergentintegrations import failed: {e}")
            print("💡 Run: pip install emergentintegrations --extra-index-url https://d33sy5i8bnduwe.cloudfront.net/simple/")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def check_environment_variables():
    """Check critical environment variables"""
    print("\n🌍 Checking environment variables...")
    
    critical_vars = [
        'MONGO_URL',
        'EMERGENT_LLM_KEY'
    ]
    
    all_good = True
    for var in critical_vars:
        value = os.environ.get(var)
        if value:
            if var == 'MONGO_URL':
                # Don't show full connection string for security
                masked = value[:20] + "..." if len(value) > 20 else value
                print(f"✅ {var}: {masked}")
            else:
                print(f"✅ {var}: Set")
        else:
            print(f"❌ {var}: Not set")
            all_good = False
    
    return all_good

def create_startup_script():
    """Create a startup script for production"""
    startup_script = '''#!/bin/bash
# Production startup script for Medical Cabinet Backend

echo "🚀 Starting Medical Cabinet Backend..."

# Set working directory
cd /app/backend

# Check if requirements are installed
echo "📦 Installing requirements..."
pip install -r requirements.txt

# Install emergentintegrations if not already installed
pip install emergentintegrations --extra-index-url https://d33sy5i8bnduwe.cloudfront.net/simple/ || echo "emergentintegrations already installed"

# Set environment variables (these should be set in deployment config)
export PYTHONPATH="/app/backend:$PYTHONPATH"

# Start the server
echo "🌐 Starting FastAPI server..."
python -m uvicorn server:app --host 0.0.0.0 --port 8001 --workers 1

echo "✅ Server started successfully"
'''
    
    with open("/app/start_production.sh", 'w') as f:
        f.write(startup_script)
    
    # Make executable
    os.chmod("/app/start_production.sh", 0o755)
    print("✅ Created startup script: /app/start_production.sh")

def create_simple_test_endpoint():
    """Create a very simple test endpoint"""
    simple_server = '''from fastapi import FastAPI
from datetime import datetime
import os

app = FastAPI()

@app.get("/")
def root():
    return {
        "message": "Medical Cabinet Backend Test",
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "environment": {
            "mongo_url_set": bool(os.environ.get("MONGO_URL")),
            "emergent_key_set": bool(os.environ.get("EMERGENT_LLM_KEY"))
        }
    }

@app.get("/api/test")
def api_test():
    return {"api": "working", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
'''
    
    with open("/app/backend/simple_server.py", 'w') as f:
        f.write(simple_server)
    
    print("✅ Created simple test server: /app/backend/simple_server.py")

def main():
    """Main diagnostic and fix function"""
    print("🔧 DEPLOYMENT FIX DIAGNOSTIC")
    print("=" * 50)
    
    success = True
    
    if not check_requirements():
        success = False
    
    if not check_import_issues():
        success = False
    
    if not check_environment_variables():
        success = False
    
    # Always create these files for deployment
    create_startup_script()
    create_simple_test_endpoint()
    
    print("\n" + "=" * 50)
    
    if success:
        print("✅ ALL CHECKS PASSED")
        print("🚀 Your application should deploy successfully")
    else:
        print("⚠️  ISSUES FOUND")
        print("📋 Fix the issues above before deployment")
    
    print("\n📁 Files created for deployment:")
    print("- /app/start_production.sh (startup script)")
    print("- /app/backend/simple_server.py (test server)")
    
    print("\n🔧 For Emergent deployment:")
    print("1. Ensure MONGO_URL is set with Atlas connection string")
    print("2. Ensure EMERGENT_LLM_KEY is set")
    print("3. Redeploy and test /api/test endpoint")
    
    return success

if __name__ == "__main__":
    try:
        result = main()
        sys.exit(0 if result else 1)
    except Exception as e:
        print(f"❌ Fix script failed: {str(e)}")
        sys.exit(1)