# PatchAI Testing Infrastructure

## Overview
The default PatchAI validation flow now focuses on a small set of trustworthy checks that are simple to run locally and in CI.

## Current Default Validation Flow

### Backend Validation
- **Python compile validation** for the active backend runtime surface
- **Coverage target**: `backend/main.py`, `backend/core`, `backend/models`, `backend/routes`, and `backend/services`

### Frontend Validation
- **Smoke test** for the current app shell using the active React test setup
- **Production build check** to ensure the frontend still bundles successfully

### CI Coverage
- **Backend job** installs backend dependencies and validates Python files
- **Frontend job** installs frontend dependencies, runs the smoke test, and builds the app

## Quick Start

### Run The Default Local Validation Flow
```bash
npm run test-backend
npm run test-frontend
npm run build-frontend
```

### Run Combined Backend And Frontend Checks
```bash
npm run test-all
```

### Run Windows Wrappers
```bash
run_tests.bat
test.bat
```

## Active Test Entry Points

### Root Scripts
- **`npm run test-backend`** - Python compile validation for the active backend code
- **`npm run test-frontend`** - Frontend smoke test
- **`npm run build-frontend`** - Frontend production build validation
- **`npm run test-all`** - Combined backend compile validation and frontend smoke test

### Frontend Test Files
- **`frontend/src/App.test.js`** - Lightweight app-shell smoke test
- **`frontend/src/setupTests.js`** - Jest DOM setup

### CI Workflow
- **`.github/workflows/test.yml`** - Current GitHub Actions validation pipeline

## Legacy Diagnostic Scripts

The following scripts still exist in the repository, but they are no longer the default CI path:

- **`final_test.py`**
- **`simple_test.py`**
- **`debug_backend.py`**
- **`frontend_test.js`**

These should be treated as manual diagnostics only unless they are intentionally modernized later.

## What The Current Flow Verifies

### Backend
- **Syntax and compile validity** across the active backend runtime surface
- **Protection against broken commits** caused by invalid Python files in key runtime directories

### Frontend
- **Basic app shell rendering** via the smoke test
- **Build integrity** for the React application

## Windows Wrapper Behavior

- **`run_tests.bat`** - Installs required dependencies, runs backend validation, runs the frontend smoke test, and runs the frontend build
- **`test.bat`** - Validates local tools are present and runs the same streamlined local checks without reinstalling dependencies

The wrappers set safe placeholder frontend environment variables for local smoke testing and build validation so real production secrets are not required for these checks.

## Usage Examples

### Pre-Commit Validation
```bash
npm run test-backend
npm run test-frontend
```

### Pre-Deployment Validation
```bash
npm run test-backend
npm run test-frontend
npm run build-frontend
```

### Continuous Integration Reference
```yaml
- name: Validate backend Python files
  run: python -m compileall backend/main.py backend/core backend/models backend/routes backend/services

- name: Run frontend smoke tests
  run: npm test -- --watchAll=false

- name: Build frontend
  run: npx react-scripts build
```

## Dependencies

### Backend
```bash
pip install -r backend/requirements.txt
```

### Frontend
```bash
npm --prefix frontend install
```

## Troubleshooting

### Frontend Test Fails Due To Missing Environment Variables
- Use the Windows wrappers or set placeholder `REACT_APP_*` values before running the frontend checks manually

### Backend Compile Validation Fails
- Fix the reported Python syntax or import-surface issue in the file listed by the compiler output

### Need Deeper Manual Investigation
- Use the legacy diagnostic scripts only as manual troubleshooting tools, not as the default release gate

## Future Enhancements

- **Add more meaningful frontend tests around authenticated routing and paywall states**
- **Introduce targeted backend unit tests once key services are less environment-coupled**
- **Add linting only when it can be introduced cleanly and consistently across the repo**
