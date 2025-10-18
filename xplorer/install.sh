#!/bin/bash

set -e

echo "Installing IITM BS Xplorer..."

# Check if Python 3.+ is available
python_version=$(python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
required_version="3.8"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "Error: Python 3.8+ is required. Found Python $python_version"
    exit 1
fi

echo "✓ Python version check passed: $python_version"

# Install dependencies
echo "Installing dependencies..."
rm -rf .venv
python -m venv .venv
source .venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt

echo "✓ Dependencies installed successfully"

# Make main script executable
chmod +x main.py

echo "✓ Installation completed successfully!"
echo ""
echo "Usage examples:"
echo "  # Basic usage with hierarchical storage (recommended)"
echo "  python main.py ds es --hierarchical"
echo ""
echo "  # Dry run to see what would be processed"
echo "  python main.py ds es --hierarchical --dry-run"
echo ""
echo "For more information, see README.md"
