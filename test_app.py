#!/usr/bin/env python
import sys
try:
    from app import app
    print("✓ App imported successfully")
    with app.test_client() as client:
        resp = client.get('/')
        print(f"✓ Test GET / returned {resp.status_code}")
        if resp.status_code == 200:
            print("✓ App is working correctly")
        else:
            print(f"✗ Unexpected status: {resp.status_code}")
except Exception as e:
    print(f"✗ Error: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
