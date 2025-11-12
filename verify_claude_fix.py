"""
Verify Claude 4.0 Model Name Fix
==================================

This script verifies that all references to the old Claude model names
have been updated to the new Claude 4.0 naming convention.
"""

import os
import sys
from pathlib import Path

def check_file_for_old_claude_names(filepath):
    """Check a file for old Claude model names"""
    old_names = [
        "claude-3-5-sonnet-20241022",
        "claude-3-7-sonnet-20250219",
    ]
    
    issues = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                for old_name in old_names:
                    if old_name in line and 'legacy' not in line.lower() and '#' not in line:
                        issues.append((line_num, old_name, line.strip()))
    except Exception as e:
        return [f"Error reading file: {e}"]
    
    return issues


def main():
    print("=" * 70)
    print("🔍 VERIFYING CLAUDE 4.0 MODEL NAME FIX")
    print("=" * 70)
    
    # Files to check
    files_to_check = [
        "llm_manager.py",
        "llm_config.py",
        "llm_provider_manager.py",
        "app/ote_logger.py",
        "test_claude_integration.py",
    ]
    
    all_clear = True
    
    for filepath in files_to_check:
        full_path = Path(filepath)
        if not full_path.exists():
            print(f"⚠️  File not found: {filepath}")
            continue
        
        print(f"\n📄 Checking: {filepath}")
        issues = check_file_for_old_claude_names(full_path)
        
        if issues:
            all_clear = False
            print(f"   ❌ Found {len(issues)} issue(s):")
            for line_num, old_name, line in issues[:5]:  # Show first 5
                print(f"      Line {line_num}: {old_name}")
                print(f"         {line[:80]}")
        else:
            print(f"   ✅ No issues found")
    
    print("\n" + "=" * 70)
    print("📊 CURRENT LLM CONFIGURATION")
    print("=" * 70)
    
    try:
        from llm_config import LLMSettings
        print(f"✅ Default Provider: {LLMSettings.DEFAULT_PROVIDER}")
        print(f"✅ Default Model: {LLMSettings.DEFAULT_MODEL}")
        print(f"✅ Default Temperature: {LLMSettings.DEFAULT_TEMPERATURE}")
    except Exception as e:
        print(f"❌ Error loading config: {e}")
        all_clear = False
    
    print("\n" + "=" * 70)
    print("🧪 TESTING CLAUDE 4.0 INITIALIZATION")
    print("=" * 70)
    
    try:
        from llm_manager import LLMManager
        
        # Test default Claude
        llm = LLMManager.get_llm("claude")
        print(f"✅ Claude LLM initialized")
        print(f"   Model: {llm.model}")
        print(f"   Expected: claude-sonnet-4-0")
        
        if llm.model == "claude-sonnet-4-0":
            print(f"   ✅ Correct model!")
        else:
            print(f"   ❌ Wrong model! Expected claude-sonnet-4-0")
            all_clear = False
            
    except Exception as e:
        print(f"❌ Error initializing Claude: {e}")
        all_clear = False
    
    print("\n" + "=" * 70)
    print("📋 SUMMARY")
    print("=" * 70)
    
    if all_clear:
        print("🎉 ALL CHECKS PASSED!")
        print("\n✅ Claude 4.0 integration is correctly configured")
        print("\n📝 NEXT STEPS:")
        print("   1. RESTART your backend server")
        print("   2. Clear browser cache (Cmd+Shift+R)")
        print("   3. Test in frontend")
        print("\n⚠️  IMPORTANT: You must restart the backend for changes to take effect!")
    else:
        print("⚠️  SOME ISSUES FOUND")
        print("\nPlease review the issues above and fix them.")
    
    print("=" * 70)
    
    return 0 if all_clear else 1


if __name__ == "__main__":
    sys.exit(main())
