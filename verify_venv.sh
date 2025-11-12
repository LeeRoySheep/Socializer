#!/bin/bash

echo "======================================================================"
echo "🔍 VENV VERIFICATION SCRIPT"
echo "======================================================================"
echo ""

echo "1. Checking for 'venv' folder:"
if [ -d "venv" ]; then
    echo "   ❌ FOUND: venv/ still exists"
    echo "   Size: $(du -sh venv 2>/dev/null | cut -f1)"
    echo "   Do you want to delete it? (It's obsolete)"
else
    echo "   ✅ NOT FOUND: venv/ does not exist (correct!)"
fi

echo ""
echo "2. Checking for '.venv' folder:"
if [ -d ".venv" ]; then
    echo "   ✅ FOUND: .venv/ exists (correct!)"
    echo "   Size: $(du -sh .venv 2>/dev/null | cut -f1)"
    echo "   This is your ACTIVE virtual environment"
else
    echo "   ❌ NOT FOUND: .venv/ does not exist (ERROR!)"
fi

echo ""
echo "3. All directories containing 'venv':"
find . -maxdepth 1 -type d -name "*venv*" 2>/dev/null | while read dir; do
    echo "   - $dir"
done

echo ""
echo "======================================================================"
echo "To refresh your IDE:"
echo "  - PyCharm: File → Invalidate Caches → Restart"
echo "  - VS Code: Close and reopen the folder"
echo "======================================================================"
