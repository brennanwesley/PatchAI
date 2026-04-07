@echo off
setlocal
echo.
echo ========================================
echo  PATCHAI VALIDATION SUITE
echo ========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Please install Python 3.7+
    pause
    exit /b 1
)

REM Check if npm is available
npm --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: npm not found. Please install Node.js and npm.
    pause
    exit /b 1
)

echo Running streamlined validation checks...
echo.

REM Run backend validation
call npm run test-backend
if errorlevel 1 goto :fail

REM Set placeholder frontend environment variables
set CI=true
set REACT_APP_BACKEND_URL=https://patchai-backend.onrender.com
set REACT_APP_SUPABASE_URL=https://example.supabase.co
set REACT_APP_SUPABASE_ANON_KEY=example-anon-key

REM Run frontend smoke test
call npm run test-frontend
if errorlevel 1 goto :fail

REM Run frontend build validation
call npm run build-frontend
if errorlevel 1 goto :fail

goto :success

:fail
echo.
echo ❌ VALIDATION FAILED - Review the output above
echo.
goto :end

:success
echo.
echo ✅ VALIDATION PASSED - Backend and frontend checks succeeded

:end
echo.
echo Validation complete!
endlocal
pause
