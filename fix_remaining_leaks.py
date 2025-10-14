#!/usr/bin/env python3
"""
Fix remaining database connection leaks in data_manager.py
Test-Driven Approach: Fix one method at a time and verify
"""

REMAINING_METHODS = [
    ("set_user_preference", 79),
    ("delete_user_preference", 130),
    ("add_user", 174),
    ("update_user", 234),
    ("delete_user", 261),
    ("set_user_temperature", 284),
    ("save_messages", 299),
    ("add_skill", 395),
    ("get_skill_ids_for_user", 420),
    ("get_skills_for_user", 436),
    ("get_skilllevel_for_user", 452),
    ("add_training", 542),
    ("get_training_for_user", 563),
    ("get_training_for_skill", 579),
    ("update_training", 599),
]

print("=" * 60)
print("📋 REMAINING METHODS TO FIX")
print("=" * 60)

for i, (method_name, line_num) in enumerate(REMAINING_METHODS, 1):
    print(f"{i:2}. {method_name:30} (line {line_num})")

print("=" * 60)
print(f"Total: {len(REMAINING_METHODS)} methods")
print("\n✅ Fix them by running:")
print("   python fix_remaining_leaks.py --fix")
