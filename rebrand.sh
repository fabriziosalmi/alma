#!/bin/bash

# --- Rebranding Script: ALMA to ALMA ---

# Safety check: exit if any command fails
set -e

echo "🚀 Starting rebranding process from ALMA to ALMA..."

# --- 1. Find and Replace text content ---

# List of files to process. We exclude directories like .git, venv, etc.
# and specific file types like .pyc to avoid issues.
FILES=$(find . -type f -not -path "./.git/*" -not -path "./venv/*" -not -path "./htmlcov/*" -not -path "./.ruff_cache/*" -not -name "*.pyc")

echo "Found $(echo "$FILES" | wc -l) files to process for text replacement."

  # Use a loop for robust handling of file paths
  echo "$FILES" | while read -r file; do
    # Set LC_ALL=C for sed to handle potential encoding issues
    export LC_ALL=C
    # Replace 'alma' with 'alma' (case-insensitive for the pattern)
    # The replacement is always lowercase 'alma'
    sed -i.bak 's/alma/alma/gI' "$file"
    
    # Replace 'ALMA' with 'ALMA' (case-insensitive for the pattern)
    # The replacement is always uppercase 'ALMA'
    sed -i.bak 's/ALMA/ALMA/gI' "$file"
  done
# Clean up the backup files created by sed
find . -name "*.bak" -delete

echo "✅ Text content replaced in all relevant files."


# --- 2. Rename directory ---

# Check if the alma directory exists before trying to move it
if [ -d "alma" ]; then
  echo "Renaming 'alma' directory to 'alma'..."
  mv alma alma
  echo "✅ Directory renamed."
else
  echo "⚠️  'alma' directory not found, skipping rename."
fi


# --- 3. Final Manual Steps ---

echo -e "\n🎉 Rebranding script finished! 🎉"
echo
echo "--- IMPORTANT: MANUAL STEPS REQUIRED ---"
echo "1. Review the changes:"
echo "   git status"
echo "   git diff"

echo "2. The 'pyproject.toml' was updated, but you should double-check:"
echo "   - The [project.scripts] entry should be: alma = \"alma.cli.main:app\""
echo "   - The setuptools 'include' path might need to be updated if it was too specific."

echo "3. After renaming 'alma' to 'alma', you must update your virtual environment:"
echo "   pip install -e ."

echo "4. Test everything thoroughly!"
echo "   pytest"
echo "----------------------------------------"
