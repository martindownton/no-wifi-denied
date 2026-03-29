#!/bin/bash

# No WiFi! Denied! - Linting Script
# This script runs ruff to check and format the codebase.

set -e

echo "🔍 Linting 'No WiFi! Denied!'..."

# Ensure we're in a virtual environment
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "⚠️ Warning: Not running in a virtual environment. Use 'source venv/bin/activate' first if possible."
fi

# Run ruff check
echo "Checking for issues..."
python3 -m ruff check --fix src scripts

# Run ruff format
echo "Formatting code..."
python3 -m ruff format src scripts

echo "✅ All clear!"
