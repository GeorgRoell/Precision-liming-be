@echo off
REM Deployment script for Google Cloud Run
REM Run this after gcloud CLI is installed and configured

echo ============================================
echo NextFarming Backend Deployment to Cloud Run
echo ============================================
echo.

REM Check if gcloud is installed
where gcloud >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: gcloud CLI is not installed or not in PATH
    echo Please install from: https://cloud.google.com/sdk/docs/install
    pause
    exit /b 1
)

echo Step 1: Checking gcloud configuration...
gcloud config get-value project
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: No project configured
    echo Please run: gcloud init
    pause
    exit /b 1
)

echo.
echo Step 2: Creating secrets in Secret Manager...
echo.

REM Create client secret
echo f4OThVmuwkLt8TCpmrJq3UAv5obzcInI | gcloud secrets create nextfarming-client-secret --data-file=- 2>nul
if %ERRORLEVEL% EQU 0 (
    echo ✓ Created nextfarming-client-secret
) else (
    echo - nextfarming-client-secret already exists
)

REM Create client ID
echo omya | gcloud secrets create nextfarming-client-id --data-file=- 2>nul
if %ERRORLEVEL% EQU 0 (
    echo ✓ Created nextfarming-client-id
) else (
    echo - nextfarming-client-id already exists
)

REM Create server secret key
echo 0f51a36dc7e3f1f8dcf0ac6df3f3b6552e9126292cae1fde2c9fd3a7c99b8056 | gcloud secrets create server-secret-key --data-file=- 2>nul
if %ERRORLEVEL% EQU 0 (
    echo ✓ Created server-secret-key
) else (
    echo - server-secret-key already exists
)

echo.
echo Step 3: Deploying to Cloud Run...
echo This will take 3-5 minutes...
echo.

gcloud run deploy nextfarming-api ^
  --source . ^
  --region us-central1 ^
  --platform managed ^
  --allow-unauthenticated ^
  --set-secrets="NEXTFARMING_CLIENT_ID=nextfarming-client-id:latest,NEXTFARMING_CLIENT_SECRET=nextfarming-client-secret:latest,SECRET_KEY=server-secret-key:latest" ^
  --set-env-vars="ENVIRONMENT=production,NEXTFARMING_REDIRECT_URI=http://localhost:8080/callback,NEXTFARMING_AUTH_BASE=https://test-account-service.nextfarming.dev/realms/account-service/protocol/openid-connect,NEXTFARMING_API_BASE=https://test-farmmanagement.nextfarming.dev/v2,ALLOWED_ORIGINS=*" ^
  --memory 512Mi ^
  --cpu 1 ^
  --min-instances 0 ^
  --max-instances 10 ^
  --timeout 60

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ============================================
    echo ✓ DEPLOYMENT SUCCESSFUL!
    echo ============================================
    echo.
    echo Your API is now live!
    echo.
    echo Next steps:
    echo 1. Copy the Service URL shown above
    echo 2. Test it: python test_api.py ^(update BASE_URL first^)
    echo 3. View API docs at: https://YOUR-SERVICE-URL/docs
    echo.
) else (
    echo.
    echo ============================================
    echo ✗ DEPLOYMENT FAILED
    echo ============================================
    echo.
    echo Check the error messages above.
    echo Common issues:
    echo - Project not set: Run 'gcloud init'
    echo - Billing not enabled: Enable in Cloud Console
    echo - APIs not enabled: The script will prompt to enable them
    echo.
)

pause
