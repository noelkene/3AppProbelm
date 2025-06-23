@echo off
echo ========================================
echo Google Cloud Platform Deployment Script
echo ========================================
echo.

REM Check if gcloud is installed
gcloud --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Google Cloud SDK is not installed.
    echo Please install it from: https://cloud.google.com/sdk/docs/install
    pause
    exit /b 1
)

echo Google Cloud SDK found!
echo.

REM Get project ID
set /p PROJECT_ID="Enter your Google Cloud Project ID: "
if "%PROJECT_ID%"=="" (
    echo ERROR: Project ID is required.
    pause
    exit /b 1
)

echo.
echo Setting project to: %PROJECT_ID%
gcloud config set project %PROJECT_ID%

REM Check if project exists
gcloud projects describe %PROJECT_ID% >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Project %PROJECT_ID% not found or access denied.
    echo Please check your project ID and permissions.
    pause
    exit /b 1
)

echo Project verified successfully!
echo.

REM Enable required APIs
echo Enabling required APIs...
gcloud services enable appengine.googleapis.com
gcloud services enable storage.googleapis.com
gcloud services enable aiplatform.googleapis.com
gcloud services enable cloudbuild.googleapis.com

echo APIs enabled successfully!
echo.

REM Create App Engine app if it doesn't exist
echo Checking App Engine application...
gcloud app describe >nul 2>&1
if %errorlevel% neq 0 (
    echo Creating App Engine application...
    gcloud app create --region=us-central1
) else (
    echo App Engine application already exists.
)

echo.

REM Create Cloud Storage bucket
set BUCKET_NAME=comic-creation-data-%PROJECT_ID%
echo Creating Cloud Storage bucket: %BUCKET_NAME%
gsutil mb gs://%BUCKET_NAME% 2>nul
if %errorlevel% equ 0 (
    echo Bucket created successfully!
) else (
    echo Bucket already exists or creation failed.
)

echo.

REM Update app.yaml with project ID
echo Updating app.yaml with project configuration...
powershell -Command "(Get-Content app.yaml) -replace 'your-project-id', '%PROJECT_ID%' -replace 'your-bucket-name', '%BUCKET_NAME%' | Set-Content app.yaml"

echo Configuration updated!
echo.

REM Deploy to App Engine
echo.
echo ========================================
echo Deploying to Google App Engine...
echo ========================================
echo.
echo This may take several minutes...
echo.

gcloud app deploy app.yaml

if %errorlevel% equ 0 (
    echo.
    echo ========================================
    echo DEPLOYMENT SUCCESSFUL!
    echo ========================================
    echo.
    echo Your app is now live at:
    echo https://%PROJECT_ID%.uc.r.appspot.com
    echo.
    echo Opening your app in browser...
    gcloud app browse
) else (
    echo.
    echo ========================================
    echo DEPLOYMENT FAILED
    echo ========================================
    echo.
    echo Please check the error messages above.
    echo Common issues:
    echo - Billing not enabled
    echo - Insufficient permissions
    echo - Configuration errors
    echo.
    echo For help, check: GOOGLE_CLOUD_DEPLOYMENT.md
)

echo.
pause 