#!/bin/bash

# Update dependencies script for Socializer
set -e

echo "🚀 Starting dependency update..."

# Create backup of current requirements
if [ -f "requirements.txt" ]; then
    cp requirements.txt requirements.txt.bak
    echo "✅ Created backup of requirements.txt"
fi

# Update pip
echo "🔄 Updating pip..."
python -m pip install --upgrade pip

# Install updated requirements
echo "📦 Installing updated requirements..."
pip install -r requirements-updated.txt

# Install test requirements
echo "🧪 Installing test requirements..."
pip install -r test-requirements-minimal.txt

# Run tests to verify everything works
echo "🔍 Running tests..."
python -m pytest tests/ -v

echo "✨ Update complete!"
