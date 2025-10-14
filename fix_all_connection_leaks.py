#!/usr/bin/env python3
"""
Script to fix all database connection leaks in data_manager.py
Replaces all instances of `session = next(self.data_model.get_db())` 
with proper context manager usage.
"""

import re

def fix_connection_leaks(file_path):
    """Fix all connection leaks in the data_manager.py file."""
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    original_content = content
    
    # Pattern 1: Methods that use `with session.begin():` block
    # These need special handling to maintain the transaction
    pattern1 = r'(    def \w+\([^)]+\)[^:]*:\n(?:        """[^"]*"""\n)?)'
    pattern1 += r'        session = next\(self\.data_model\.get_db\(\)\)\n'
    pattern1 += r'        try:\n'
    pattern1 += r'            with session\.begin\(\):'
    
    def replace_pattern1(match):
        method_header = match.group(1)
        # Remove the try block and use context manager properly
        return (
            f'{method_header}'
            f'        with self.get_session() as session:\n'
            f'            try:'
        )
    
    content = re.sub(pattern1, replace_pattern1, content)
    
    # Pattern 2: Simple cases without nested try/with blocks
    # Replace: session = next(self.data_model.get_db())
    # With: with self.get_session() as session:
    
    # Find all remaining occurrences
    lines = content.split('\n')
    fixed_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        
        # Check if this line has the problematic pattern
        if 'session = next(self.data_model.get_db())' in line and 'with self.get_session()' not in line:
            indent = len(line) - len(line.lstrip())
            indent_str = ' ' * indent
            
            # Replace the line
            fixed_lines.append(f'{indent_str}with self.get_session() as session:')
            
            # Check if next lines need indentation adjustment
            # Look for try: block that follows
            if i + 1 < len(lines) and 'try:' in lines[i + 1]:
                # Skip the try: line and increase indentation for its contents
                i += 1
                fixed_lines.append(lines[i])  # Add the try: line
                i += 1
                
                # Now indent all contents of the try block
                try_indent = len(lines[i]) - len(lines[i].lstrip())
                while i < len(lines):
                    current_line = lines[i]
                    current_indent = len(current_line) - len(current_line.lstrip())
                    
                    # If we've dedented back, we're done with this try block
                    if current_line.strip() and current_indent <= try_indent and 'except' not in current_line:
                        break
                    
                    fixed_lines.append(current_line)
                    i += 1
                continue
            
        fixed_lines.append(line)
        i += 1
    
    content = '\n'.join(fixed_lines)
    
    # Count fixes
    original_count = original_content.count('session = next(self.data_model.get_db())')
    new_count = content.count('session = next(self.data_model.get_db())')
    fixes_applied = original_count - new_count
    
    # Write back
    with open(file_path, 'w') as f:
        f.write(content)
    
    print(f"✅ Fixed {fixes_applied} connection leaks")
    print(f"   Remaining leaks: {new_count}")
    
    if new_count > 0:
        print(f"\n⚠️  WARNING: {new_count} leaks still remain. Manual review needed.")
    else:
        print(f"\n🎉 All connection leaks fixed!")
    
    return fixes_applied

if __name__ == '__main__':
    file_path = 'datamanager/data_manager.py'
    print(f"Fixing connection leaks in: {file_path}")
    print("=" * 60)
    
    try:
        fixes = fix_connection_leaks(file_path)
        print("=" * 60)
        print(f"✅ Complete! Applied {fixes} fixes.")
        print("\n📝 Next steps:")
        print("1. Review the changes: git diff datamanager/data_manager.py")
        print("2. Restart your server")
        print("3. Test AI features")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
