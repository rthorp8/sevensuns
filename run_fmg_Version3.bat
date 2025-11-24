@echo off
REM ============================================
REM FMG → Obsidian Vault Automation Runner (Windows)
REM ============================================

set MAP_FILE=map.json
set SCRIPT=fmg_to_obsidian.py
set VAULT_DIR=World

echo Checking for Python...
where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo ❌ Python not found. Please install Python 3 and add it to PATH.
    pause
    exit /b
)

echo 🚀 Running FMG → Obsidian automation...
python "%SCRIPT%" "%MAP_FILE%" "%VAULT_DIR%"

if %ERRORLEVEL% equ 0 (
    echo ✅ Vault populated successfully in %VAULT_DIR%\
) else (
    echo ❌ Something went wrong.
)

pause