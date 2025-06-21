# PatchAI Testing Infrastructure

## Overview
Comprehensive testing suite to detect issues before deployment and ensure stable production releases.

## Quick Start

### Run Complete Test Suite
```bash
python test_all.py
```

### Run Individual Tests
```bash
# Backend API tests only
python final_test.py

# Simple connectivity check
python simple_test.py

# Backend diagnostics
python debug_backend.py
```

## Test Files

### Core Testing
- **`test_all.py`** - Complete test suite (recommended)
- **`final_test.py`** - Backend API + basic frontend tests
- **`simple_test.py`** - Quick connectivity check

### Diagnostics
- **`debug_backend.py`** - Detailed backend troubleshooting
- **`frontend_test.js`** - Browser-based console error detection (requires Node.js)

### Configuration
- **`package.json`** - Node.js dependencies for frontend testing
- **`requirements-test.txt`** - Python testing dependencies
- **`run_tests.bat`** - Windows batch script for easy testing

## What Gets Tested

### Backend Tests ✅
- **Health Check** - Backend API availability
- **CORS Configuration** - Cross-origin request handling
- **Authentication** - Protected endpoint security
- **API Documentation** - Swagger docs availability
- **Error Handling** - Proper HTTP status codes

### Frontend Tests ✅
- **Accessibility** - Frontend loading and availability
- **React Detection** - Framework presence
- **JavaScript Bundles** - Asset loading
- **PatchAI Branding** - Content verification
- **HTML Structure** - Meta tags and SEO
- **CSS Framework** - Styling framework detection

### Integration Tests ✅
- **CORS Integration** - Frontend-backend communication
- **API Contract** - Request/response format compatibility

## Current Status

### Live URLs
- **Backend**: `https://patchai-backend.onrender.com`
- **Frontend**: `https://patchai-frontend.vercel.app`

### Latest Test Results
- ✅ **6/7 tests PASSED**
- ❌ **0 FAILED** (no critical issues)
- ⚠️ **1 WARNING** (minor frontend detection)
- 🎯 **Overall Status: HEALTHY**

## Usage Examples

### Pre-Deployment Check
```bash
# Run before pushing to production
python test_all.py

# Check exit code
echo $?  # 0 = success, 1 = failures detected
```

### Continuous Integration
```bash
# Add to CI pipeline
python test_all.py && echo "Tests passed, deploying..." || echo "Tests failed, blocking deployment"
```

### Development Workflow
```bash
# Quick check during development
python simple_test.py

# Full check before commit
python test_all.py
```

## Report Files

### Generated Reports
- **`complete_test_report.json`** - Detailed test results with timestamps
- **`patchai_test_report.json`** - Backend/frontend test summary
- **`simple_test_results.json`** - Basic connectivity results
- **`backend_diagnostics.json`** - Backend troubleshooting data

### Report Structure
```json
{
  "timestamp": "2025-06-21T14:00:00",
  "summary": {
    "passed": 6,
    "failed": 0,
    "warnings": 1,
    "health_score": 85.7
  },
  "results": [...]
}
```

## Health Score Interpretation

- **90-100%** - Production ready, excellent health
- **80-89%** - Good health, minor warnings acceptable
- **70-79%** - Needs attention, some issues detected
- **<70%** - Critical issues, do not deploy

## Troubleshooting

### Common Issues

#### Backend 404 Errors
```bash
# Check if using correct URL
python debug_backend.py
```

#### CORS Failures
- Verify frontend URL in backend CORS settings
- Check browser console for CORS errors

#### Authentication Errors
- Ensure JWT tokens are properly configured
- Verify Supabase integration

### Getting Help
1. Run `python debug_backend.py` for detailed diagnostics
2. Check generated JSON reports for specific error details
3. Review console logs in browser developer tools

## Dependencies

### Python Requirements
```bash
pip install httpx
```

### Node.js Requirements (Optional)
```bash
npm install puppeteer
```

## Integration with Development Workflow

### Pre-Commit Hook
Add to `.git/hooks/pre-commit`:
```bash
#!/bin/bash
python test_all.py
if [ $? -ne 0 ]; then
    echo "Tests failed. Commit blocked."
    exit 1
fi
```

### GitHub Actions
```yaml
- name: Run PatchAI Tests
  run: python test_all.py
```

## Future Enhancements

### Planned Features
- [ ] E2E testing with Playwright
- [ ] Performance benchmarking
- [ ] Database migration testing
- [ ] Load testing capabilities
- [ ] Automated screenshot comparison

### Contributing
To add new tests:
1. Add test method to appropriate class
2. Update this README
3. Test locally before committing
