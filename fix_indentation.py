#!/usr/bin/env python3
"""Fix indentation errors caused by the batch replacement."""

file_path = "datamanager/data_manager.py"

with open(file_path, 'r') as f:
    lines = f.readlines()

fixed_lines = []
i = 0

while i < len(lines):
    line = lines[i]
    
    # Check if this is a "with self.get_session()" line
    if 'with self.get_session() as session:' in line:
        fixed_lines.append(line)
        i += 1
        
        # Check if next line needs indenting
        if i < len(lines):
            next_line = lines[i]
            
            # If next line is "try:" or other code but not indented properly
            if next_line.strip() and not next_line.startswith('        '):  # Should have at least 8 spaces
                # This line and all following lines in this block need +4 spaces indent
                with_indent = len(line) - len(line.lstrip())
                
                # Indent this line and all lines in this block
                while i < len(lines):
                    current_line = lines[i]
                    
                    # Empty lines stay empty
                    if not current_line.strip():
                        fixed_lines.append(current_line)
                        i += 1
                        continue
                    
                    current_indent = len(current_line) - len(current_line.lstrip())
                    
                    # If we've dedented back to or past the with statement level, we're done
                    if current_indent <= with_indent and current_line.strip():
                        break
                    
                    # Add 4 spaces of indentation
                    fixed_lines.append('    ' + current_line)
                    i += 1
                continue
    
    fixed_lines.append(line)
    i += 1

# Write back
with open(file_path, 'w') as f:
    f.writelines(fixed_lines)

print("✅ Fixed indentation errors")

# Test if it compiles
import subprocess
result = subprocess.run(
    ['.venv/bin/python', '-m', 'py_compile', file_path],
    capture_output=True,
    text=True
)

if result.returncode == 0:
    print("🎉 File compiles successfully!")
else:
    print(f"❌ Still has errors:\n{result.stderr}")
