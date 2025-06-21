@echo off
echo.
echo ========================================
echo  PATCHAI TESTING SUITE
echo ========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Please install Python 3.7+
    pause
    exit /b 1
)

REM Check if httpx is installed
python -c "import httpx" >nul 2>&1
if errorlevel 1 (
    echo Installing httpx...
    pip install httpx
)

echo Running comprehensive tests...
echo.

REM Run the complete test suite
python test_all.py

REM Check exit code
if errorlevel 1 (
    echo.
    echo ❌ TESTS FAILED - Issues detected
    echo Check the report files for details
    echo.
) else (
    echo.
    echo ✅ TESTS PASSED - System healthy
    echo.
)

echo Generated reports:
if exist complete_test_report.json echo   - complete_test_report.json
if exist patchai_test_report.json echo   - patchai_test_report.json
if exist simple_test_results.json echo   - simple_test_results.json

echo.
echo Testing complete!
pause
