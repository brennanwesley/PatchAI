@echo off
echo ========================================
echo PatchAI Database Migration Tool
echo ========================================
echo.

cd /d "%~dp0\.."

echo Checking for Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python not found. Please install Python first.
    pause
    exit /b 1
)

echo ✅ Python found
echo.

echo Installing required packages...
pip install supabase python-dotenv

echo.
echo Running database migration...
python scripts\migrate_database.py

echo.
echo Migration complete!
pause
