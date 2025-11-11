#!/usr/bin/env python3
"""Test Flask app"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

try:
    print("1. Importing Flask app...")
    from frontend.app import app
    print("   ✓ App imported successfully")
    
    print("\n2. Creating test client...")
    client = app.test_client()
    print("   ✓ Test client created")
    
    print("\n3. Testing /health endpoint...")
    resp = client.get('/health')
    print(f"   Status: {resp.status_code}")
    print(f"   Data: {resp.get_json()}")
    
    print("\n4. Testing /api/autocomplete/players...")
    resp = client.get('/api/autocomplete/players')
    print(f"   Status: {resp.status_code}")
    print(f"   Data sample: {resp.get_json()[:2]}")
    
    print("\n✓ All tests passed!")
    
except Exception as e:
    import traceback
    print(f"\n✗ Error:")
    traceback.print_exc()
