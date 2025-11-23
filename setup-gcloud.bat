@echo off
REM Initial setup script for Google Cloud
REM Run this ONCE after installing gcloud CLI

echo ============================================
echo Google Cloud Setup for NextFarming Backend
echo ============================================
echo.

REM Check if gcloud is installed
where gcloud >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: gcloud CLI is not installed
    echo.
    echo Please install from:
    echo https://cloud.google.com/sdk/docs/install
    echo.
    echo Or download directly:
    echo https://dl.google.com/dl/cloudsdk/channels/rapid/GoogleCloudSDKInstaller.exe
    echo.
    pause
    exit /b 1
)

echo ✓ gcloud CLI found
echo.

echo Step 1: Login to Google Cloud...
echo Browser will open - sign in with your Google account
echo.
gcloud auth login

echo.
echo Step 2: Initialize gcloud configuration...
echo This will help you set up your project
echo.
gcloud init

echo.
echo Step 3: Enable required APIs...
echo.
echo Enabling Cloud Run API...
gcloud services enable run.googleapis.com

echo Enabling Container Registry API...
gcloud services enable containerregistry.googleapis.com

echo Enabling Secret Manager API...
gcloud services enable secretmanager.googleapis.com

echo Enabling Cloud Build API...
gcloud services enable cloudbuild.googleapis.com

echo.
echo ============================================
echo ✓ SETUP COMPLETE!
echo ============================================
echo.
echo Next step: Run deploy.bat to deploy your backend
echo.

pause
