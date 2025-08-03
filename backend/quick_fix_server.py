#!/usr/bin/env python3
"""
Quick fix: Force use of 'test' database for Atlas deployment
"""

import os
import re

def fix_database_name():
    """Change database name to 'test' for Atlas compatibility"""
    server_file = "/app/backend/server.py"
    
    with open(server_file, 'r') as f:
        content = f.read()
    
    # Replace all references to cabinet_medical with test
    content = content.replace('get_database("cabinet_medical")', 'get_database("test")')
    content = content.replace('client.cabinet_medical', 'client.test')
    content = content.replace('"cabinet_medical"', '"test"')
    content = content.replace("'cabinet_medical'", "'test'")
    
    with open(server_file, 'w') as f:
        f.write(content)
    
    print("✅ Database name changed to 'test' for Atlas compatibility")

if __name__ == "__main__":
    fix_database_name()
    print("🔄 Quick fix applied - redeploy now!")