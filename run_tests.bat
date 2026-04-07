@echo off
setlocal
echo 🧪 PATCHAI LOCAL VALIDATION SUITE
echo =================================

echo.
echo 📦 Installing backend dependencies...
pip install -r backend\requirements.txt
if errorlevel 1 goto :fail

echo.
echo 📦 Installing frontend dependencies...
npm --prefix frontend install
if errorlevel 1 goto :fail

echo.
echo 🔧 Validating backend Python files...
call npm run test-backend
if errorlevel 1 goto :fail

echo.
echo 📱 Running frontend smoke test...
set CI=true
set REACT_APP_BACKEND_URL=https://patchai-backend.onrender.com
set REACT_APP_SUPABASE_URL=https://example.supabase.co
set REACT_APP_SUPABASE_ANON_KEY=example-anon-key
call npm run test-frontend
if errorlevel 1 goto :fail

echo.
echo 🏗️ Building frontend...
call npm run build-frontend
if errorlevel 1 goto :fail

echo.
echo ✅ Validation complete. All streamlined checks passed.
goto :end

:fail
echo.
echo ❌ Validation failed. Review the command output above.

:end
endlocal
pause
