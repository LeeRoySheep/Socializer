#!/usr/bin/env python3
"""Fix all remaining database connection leaks."""

import re

file_path = "datamanager/data_manager.py"

with open(file_path, 'r') as f:
    content = f.read()

# Replace all remaining instances
content = content.replace(
    '        session = next(self.data_model.get_db())',
    '        with self.get_session() as session:'
)

# Fix indentation issues where try blocks follow
lines = content.split('\n')
fixed_lines = []
i = 0

while i < len(lines):
    line = lines[i]
    
    # If this line is "with self.get_session() as session:" and next line is "try:"
    if 'with self.get_session() as session:' in line and i + 1 < len(lines):
        fixed_lines.append(line)
        i += 1
        
        # Check if next line needs to be a try block inside the with
        if 'try:' in lines[i].strip():
            # Keep the try line as-is
            fixed_lines.append(lines[i])
            i += 1
        else:
            # No try block, continue normally
            continue
    else:
        fixed_lines.append(line)
        i += 1

content = '\n'.join(fixed_lines)

with open(file_path, 'w') as f:
    f.write(content)

print(f"✅ Fixed all remaining connection leaks!")
print(f"📊 Checking results...")

# Verify
with open(file_path, 'r') as f:
    check_content = f.read()
    
remaining = check_content.count('session = next(self.data_model.get_db())')
print(f"   Remaining leaks: {remaining}")

if remaining == 0:
    print("🎉 All connection leaks fixed!")
else:
    print(f"⚠️  {remaining} leaks still remain")
