#!/usr/bin/env python3
"""
Pre-deployment validation for handwriting features
Ensures everything is ready for production deployment
"""

import subprocess
import sys
import os
import json

def validate_new_files():
    """Check that new handwriting files exist and are valid"""
    print("📁 Validating new handwriting files...")
    
    required_files = [
        "/app/frontend/src/components/HandwritingField.js",
        "/app/backend/requirements.txt"  # Should contain Pillow
    ]
    
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"  ✅ {file_path} exists")
        else:
            print(f"  ❌ {file_path} missing")
            return False
    
    return True

def validate_backend_changes():
    """Check backend syntax and new endpoint"""
    print("🐍 Validating backend changes...")
    
    try:
        # Check syntax
        result = subprocess.run(
            ['python', '-m', 'py_compile', '/app/backend/server.py'],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("  ✅ Backend syntax valid")
        else:
            print(f"  ❌ Backend syntax error: {result.stderr}")
            return False
        
        # Check if new endpoint exists in code
        with open('/app/backend/server.py', 'r') as f:
            content = f.read()
            if '/api/ai/refine-handwriting' in content:
                print("  ✅ New handwriting endpoint found")
            else:
                print("  ❌ Handwriting endpoint missing")
                return False
        
        return True
        
    except Exception as e:
        print(f"  ❌ Backend validation failed: {e}")
        return False

def validate_frontend_changes():
    """Check frontend syntax and imports"""
    print("⚛️  Validating frontend changes...")
    
    try:
        # Check HandwritingField component
        handwriting_file = "/app/frontend/src/components/HandwritingField.js"
        if os.path.exists(handwriting_file):
            with open(handwriting_file, 'r') as f:
                content = f.read()
                if 'const HandwritingField' in content and 'export default' in content:
                    print("  ✅ HandwritingField component valid")
                else:
                    print("  ❌ HandwritingField component malformed")
                    return False
        
        # Check Consultation.js integration
        consultation_file = "/app/frontend/src/components/Consultation.js"
        if os.path.exists(consultation_file):
            with open(consultation_file, 'r') as f:
                content = f.read()
                if "import HandwritingField from './HandwritingField'" in content:
                    print("  ✅ HandwritingField imported in Consultation.js")
                else:
                    print("  ❌ HandwritingField not imported in Consultation.js")
                    return False
        
        # Try to build frontend
        result = subprocess.run(
            ['npm', 'run', 'build'],
            capture_output=True,
            text=True,
            cwd='/app/frontend',
            env={**os.environ, 'CI': 'true'},
            timeout=120
        )
        
        if result.returncode == 0:
            print("  ✅ Frontend build successful")
            return True
        else:
            print("  ❌ Frontend build failed")
            print(f"  Error: {result.stderr[:300]}...")
            return False
        
    except Exception as e:
        print(f"  ❌ Frontend validation failed: {e}")
        return False

def create_deployment_backup_plan():
    """Create a rollback plan in case of issues"""
    print("📋 Creating deployment backup plan...")
    
    backup_plan = """# 🔄 ROLLBACK PLAN - HANDWRITING FEATURES

## IF DEPLOYMENT FAILS:

### Option 1: Quick Disable (keeps app running)
1. Comment out HandwritingField import in Consultation.js:
   // import HandwritingField from './HandwritingField';

2. Replace HandwritingField components with original textareas
3. Redeploy

### Option 2: Complete Rollback
1. Remove HandwritingField.js file
2. Restore original Consultation.js fields
3. Remove new backend endpoint
4. Redeploy

### Emergency Contacts:
- Production URL: https://docflow-system-2.emergent.host
- Login Test: medecin/medecin123
- Health Check: https://docflow-system-2.emergent.host/health

### Critical Tests After Rollback:
- Login functionality works
- Consultation modal opens
- Can create/edit consultations
- Text fields accept input normally

## Files Modified (for rollback reference):
- /app/frontend/src/components/HandwritingField.js (NEW - can delete)
- /app/frontend/src/components/Consultation.js (MODIFIED - restore from backup)
- /app/backend/server.py (MODIFIED - remove new endpoint)
- /app/backend/requirements.txt (MODIFIED - remove Pillow if needed)
"""
    
    with open("/app/ROLLBACK_PLAN.md", 'w') as f:
        f.write(backup_plan)
    
    print("  ✅ Rollback plan created: ROLLBACK_PLAN.md")
    return True

def main():
    """Main validation function"""
    print("🔍 PRE-DEPLOYMENT VALIDATION - HANDWRITING FEATURES")
    print("=" * 60)
    
    checks = [
        ("New Files", validate_new_files),
        ("Backend Changes", validate_backend_changes),
        ("Frontend Changes", validate_frontend_changes),
        ("Backup Plan", create_deployment_backup_plan)
    ]
    
    passed = 0
    total = len(checks)
    
    for check_name, check_func in checks:
        print(f"\n🔬 {check_name} validation...")
        if check_func():
            passed += 1
        else:
            print(f"❌ {check_name} validation failed")
    
    print("\n" + "=" * 60)
    print(f"🎯 VALIDATION RESULTS: {passed}/{total} checks passed")
    
    if passed == total:
        print("✅ READY FOR DEPLOYMENT!")
        print("\n📋 Next steps:")
        print("1. Deploy to production")
        print("2. Run post-deployment tests")
        print("3. Test handwriting functionality")
        print("4. Monitor for 24h")
        
        return True
    else:
        print("❌ NOT READY FOR DEPLOYMENT")
        print("Please fix failing checks above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)