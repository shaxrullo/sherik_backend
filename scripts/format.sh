#!/bin/bash

# Code Formatting Script
# Auto-formats code using Black and isort

set -e

echo "================================"
echo "Auto-Formatting Code"
echo "================================"

echo ""
echo "Formatting with Black..."
if command -v black &> /dev/null; then
    black . --exclude venv,migrations --line-length=100
    echo "✓ Black formatting complete"
else
    echo "✗ Black not installed: pip install black"
    exit 1
fi

echo ""
echo "Sorting imports with isort..."
if command -v isort &> /dev/null; then
    isort . --exclude venv,migrations --profile black
    echo "✓ isort complete"
else
    echo "✗ isort not installed: pip install isort"
    exit 1
fi

echo ""
echo "================================"
echo "✓ Code formatting complete!"
echo "================================"
echo ""
echo "Next: Run './scripts/lint.sh' to check code quality"
