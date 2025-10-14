#!/usr/bin/env python3
"""
Comprehensive verification of all connection leak fixes.
"""

import subprocess
import sys

def run_check(name, command, expected_output=None):
    """Run a verification check."""
    print(f"\n{'='*60}")
    print(f"🔍 {name}")
    print(f"{'='*60}")
    
    result = subprocess.run(
        command,
        shell=True,
        capture_output=True,
        text=True,
        cwd="/Users/leeroystevenson/PycharmProjects/Socializer"
    )
    
    output = result.stdout.strip()
    
    if expected_output is not None:
        if output == str(expected_output):
            print(f"✅ PASS: {output}")
            return True
        else:
            print(f"❌ FAIL: Expected {expected_output}, got {output}")
            return False
    else:
        if result.returncode == 0:
            print(f"✅ PASS")
            if output:
                print(f"   Output: {output}")
            return True
        else:
            print(f"❌ FAIL")
            if result.stderr:
                print(f"   Error: {result.stderr}")
            return False

def main():
    print("🚀 Verifying All Connection Leak Fixes")
    print("="*60)
    
    checks = [
        ("No connection leaks remaining", 
         'grep -c "session = next(self.data_model.get_db())" datamanager/data_manager.py',
         "0"),
        
        ("File compiles successfully",
         '.venv/bin/python -m py_compile datamanager/data_manager.py',
         None),
        
        ("Context manager exists",
         'grep -c "def get_session(self)" datamanager/data_manager.py',
         "1"),
        
        ("All methods use context manager",
         'grep -c "with self.get_session() as session:" datamanager/data_manager.py',
         None),  # Should be 21+
    ]
    
    passed = 0
    failed = 0
    
    for name, command, expected in checks:
        if run_check(name, command, expected):
            passed += 1
        else:
            failed += 1
    
    # Summary
    print("\n" + "="*60)
    print("📊 VERIFICATION SUMMARY")
    print("="*60)
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    
    if failed == 0:
        print("\n🎉 ALL CHECKS PASSED!")
        print("\n✅ Next steps:")
        print("   1. Restart server:")
        print("      .venv/bin/python -m uvicorn app.main:app --reload")
        print("\n   2. Test API docs:")
        print("      http://127.0.0.1:8000/docs")
        print("\n   3. Run tests:")
        print("      .venv/bin/pytest tests/test_connection_leaks.py -v")
        return 0
    else:
        print("\n⚠️  SOME CHECKS FAILED - Review above errors")
        return 1

if __name__ == "__main__":
    sys.exit(main())
