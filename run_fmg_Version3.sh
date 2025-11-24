#!/bin/bash
# ============================================
# FMG → Obsidian Vault Automation Runner (Linux/macOS)
# ============================================

MAP_FILE="map.json"
SCRIPT="fmg_to_obsidian.py"
VAULT_DIR="World"

# Check for Python 3
if ! command -v python3 &> /dev/null
then
    echo "❌ Python3 not found. Please install Python 3."
    exit 1
fi

echo "🚀 Running FMG → Obsidian automation..."
python3 "$SCRIPT" "$MAP_FILE" "$VAULT_DIR"

if [ $? -eq 0 ]; then
    echo "✅ Vault populated successfully in $VAULT_DIR/"
else
    echo "❌ Something went wrong."
fi