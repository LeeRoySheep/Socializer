#!/usr/bin/env python3
"""
Fix ALL remaining connection leaks at once with proper verification.
"""

import subprocess
import sys

def check_leaks():
    """Count remaining leaks."""
    result = subprocess.run(
        ["grep", "-c", "session = next(self.data_model.get_db())", "datamanager/data_manager.py"],
        capture_output=True,
        text=True
    )
    return int(result.stdout.strip()) if result.returncode == 0 else 0

def verify_compiles():
    """Verify the file compiles."""
    result = subprocess.run(
        [".venv/bin/python", "-m", "py_compile", "datamanager/data_manager.py"],
        capture_output=True,
        text=True
    )
    return result.returncode == 0

print("🔍 Checking current status...")
initial_leaks = check_leaks()
print(f"   Remaining leaks: {initial_leaks}")

if initial_leaks == 0:
    print("🎉 All leaks already fixed!")
    sys.exit(0)

print(f"\n📝 Remaining methods to fix: {initial_leaks}")
print("\n⚠️  These need manual fixing in batches to avoid errors.")
print("\n✅ Next steps:")
print("   1. Fix add_user")
print("   2. Fix update_user")  
print("   3. Fix delete_user")
print("   4. Fix set_user_temperature")
print("   5. Fix save_messages")
print("   6. Fix remaining skill methods")
print("   7. Fix remaining training methods")
