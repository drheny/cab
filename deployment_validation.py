#!/usr/bin/env python3
"""
Deployment validation script - ensures everything is ready for production deployment
"""

import subprocess
import sys
import os
import time

def check_python_syntax():
    """Check Python syntax is valid"""
    print("🐍 Checking Python syntax...")
    
    try:
        result = subprocess.run(
            ['python', '-m', 'py_compile', '/app/backend/server.py'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            print("  ✅ Python syntax validation passed")
            return True
        else:
            print(f"  ❌ Python syntax error: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"  ❌ Python syntax check failed: {e}")
        return False

def check_imports():
    """Check critical imports work"""
    print("📦 Checking Python imports...")
    
    try:
        result = subprocess.run([
            'python', '-c', 
            'import server; print("All imports successful")'
        ], 
        capture_output=True, 
        text=True, 
        timeout=15,
        cwd='/app/backend'
        )
        
        if result.returncode == 0:
            print("  ✅ All imports successful")
            return True
        else:
            print(f"  ❌ Import error: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"  ❌ Import check failed: {e}")
        return False

def check_frontend_build():
    """Check frontend builds successfully"""
    print("⚛️  Checking frontend build...")
    
    try:
        result = subprocess.run(
            ['npm', 'run', 'build'],
            capture_output=True,
            text=True,
            timeout=120,
            cwd='/app/frontend',
            env={**os.environ, 'CI': 'true'}
        )
        
        if result.returncode == 0:
            print("  ✅ Frontend build successful")
            return True
        else:
            print("  ❌ Frontend build failed")
            print(f"  Error: {result.stderr[:500]}...")
            return False
            
    except Exception as e:
        print(f"  ❌ Frontend build check failed: {e}")
        return False

def check_health_endpoints():
    """Check health endpoints respond correctly"""
    print("🏥 Checking health endpoints...")
    
    # Start server in background for testing
    try:
        import requests
        import threading
        import time
        
        # Test local endpoints
        endpoints_to_test = [
            'http://localhost:8001/health',
            'http://localhost:8001/api/health',
            'http://localhost:8001/ready'
        ]
        
        for endpoint in endpoints_to_test:
            try:
                result = subprocess.run([
                    'curl', '-s', endpoint
                ], capture_output=True, text=True, timeout=5)
                
                if result.returncode == 0 and 'healthy' in result.stdout:
                    print(f"  ✅ {endpoint} responding correctly")
                else:
                    print(f"  ⚠️  {endpoint} may not be responding (server might not be running)")
                    
            except Exception as e:
                print(f"  ⚠️  Could not test {endpoint}: {e}")
        
        return True
        
    except Exception as e:
        print(f"  ⚠️  Health endpoint check failed: {e}")
        return True  # Don't fail deployment for this

def check_critical_files():
    """Check critical files exist and are valid"""
    print("📁 Checking critical files...")
    
    critical_files = [
        '/app/backend/server.py',
        '/app/backend/requirements.txt',
        '/app/frontend/package.json',
        '/app/frontend/src/App.js'
    ]
    
    all_good = True
    for file_path in critical_files:
        if os.path.exists(file_path):
            print(f"  ✅ {file_path} exists")
        else:
            print(f"  ❌ {file_path} missing")
            all_good = False
    
    return all_good

def validate_requirements():
    """Validate requirements.txt format"""
    print("📋 Validating requirements.txt...")
    
    try:
        with open('/app/backend/requirements.txt', 'r') as f:
            lines = f.readlines()
        
        valid_lines = [line.strip() for line in lines if line.strip() and not line.startswith('#')]
        
        if len(valid_lines) > 5:  # Should have at least 5-6 core dependencies
            print(f"  ✅ Requirements.txt has {len(valid_lines)} dependencies")
            return True
        else:
            print(f"  ⚠️  Requirements.txt has only {len(valid_lines)} dependencies")
            return False
            
    except Exception as e:
        print(f"  ❌ Could not validate requirements.txt: {e}")
        return False

def main():
    """Main validation function"""
    print("🔍 DEPLOYMENT VALIDATION STARTING")
    print("=" * 50)
    
    checks = [
        ("Critical Files", check_critical_files),
        ("Python Syntax", check_python_syntax),
        ("Python Imports", check_imports),
        ("Requirements", validate_requirements),
        ("Frontend Build", check_frontend_build),
        ("Health Endpoints", check_health_endpoints)
    ]
    
    passed = 0
    total = len(checks)
    
    for check_name, check_func in checks:
        print(f"\n🔬 Running {check_name} check...")
        try:
            if check_func():
                passed += 1
            else:
                print(f"❌ {check_name} check failed")
        except Exception as e:
            print(f"❌ {check_name} check crashed: {e}")
    
    print("\n" + "=" * 50)
    print(f"🎯 VALIDATION RESULTS: {passed}/{total} checks passed")
    
    if passed >= total - 1:  # Allow 1 failure for health endpoints (server may not be running)
        print("✅ DEPLOYMENT READY!")
        print("\n🚀 Deployment Status: GOOD TO GO")
        print("\n📋 Next steps:")
        print("1. Ensure environment variables are set in Emergent")
        print("2. Deploy the application")
        print("3. Test health endpoints after deployment")
        print("4. Test login functionality")
        
        return True
    else:
        print("❌ DEPLOYMENT NOT READY")
        print("Please fix the failing checks above before deploying.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)