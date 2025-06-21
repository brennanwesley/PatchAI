@echo off
echo 🧪 PATCHAI COMPREHENSIVE TESTING SUITE
echo =====================================

echo.
echo 📦 Installing test dependencies...
pip install -r requirements-test.txt
npm install

echo.
echo 🔧 Testing Backend APIs...
python test_suite.py

echo.
echo 📱 Testing Frontend Console Errors...
node frontend_test.js

echo.
echo ✅ Testing complete! Check reports:
echo    - Backend: test_results.json
echo    - Frontend: frontend_test_report.json

pause
