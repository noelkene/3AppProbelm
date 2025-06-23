@echo off
setlocal enabledelayedexpansion

echo === Local Deployment Script for Windows ===
echo Setting up your Streamlit apps...

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python not found. Please install Python 3.11 or later.
    echo Download from: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo Found Python installation
python --version

REM Set up virtual environment
if not exist "venv311" (
    echo Creating virtual environment...
    python -m venv venv311
    if %errorlevel% neq 0 (
        echo Failed to create virtual environment
        pause
        exit /b 1
    )
    echo Virtual environment created successfully!
) else (
    echo Virtual environment already exists
)

REM Activate virtual environment and install dependencies
echo Installing dependencies...
call venv311\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo Failed to activate virtual environment
    pause
    exit /b 1
)

pip install --upgrade pip
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo Failed to install dependencies
    pause
    exit /b 1
)

echo Dependencies installed successfully!

REM Set up environment variables
echo Setting up environment variables...
if exist "service_account.json" (
    set GOOGLE_APPLICATION_CREDENTIALS=%CD%\service_account.json
    echo Google Cloud credentials set
) else (
    echo service_account.json not found. Some features may not work.
)

REM Create data directories
if not exist "data" mkdir data
if not exist "data\projects" mkdir data\projects
if not exist "data\characters" mkdir data\characters
if not exist "data\backgrounds" mkdir data\backgrounds

REM Determine which apps to run
set APPS_TO_RUN=
if "%1"=="setup" (
    set APPS_TO_RUN=setup
) else if "%1"=="generator" (
    set APPS_TO_RUN=generator
) else if "%1"=="preview" (
    set APPS_TO_RUN=preview
) else (
    set APPS_TO_RUN=all
)

echo Starting applications...

REM Start apps based on selection
if "%APPS_TO_RUN%"=="setup" (
    echo Starting Project Setup on port 8501...
    start "Project Setup" cmd /k "venv311\Scripts\activate.bat && streamlit run src\apps\project_setup.py --server.port=8501"
    set STARTED_APPS=1
    set APP_URLS=Project Setup: http://localhost:8501
) else if "%APPS_TO_RUN%"=="generator" (
    echo Starting Image Generator on port 8502...
    start "Image Generator" cmd /k "venv311\Scripts\activate.bat && streamlit run src\apps\image_generator.py --server.port=8502"
    set STARTED_APPS=1
    set APP_URLS=Image Generator: http://localhost:8502
) else if "%APPS_TO_RUN%"=="preview" (
    echo Starting Comic Preview on port 8503...
    start "Comic Preview" cmd /k "venv311\Scripts\activate.bat && streamlit run src\apps\comic_preview.py --server.port=8503"
    set STARTED_APPS=1
    set APP_URLS=Comic Preview: http://localhost:8503
) else (
    echo Starting all apps...
    start "Project Setup" cmd /k "venv311\Scripts\activate.bat && streamlit run src\apps\project_setup.py --server.port=8501"
    timeout /t 2 /nobreak >nul
    start "Image Generator" cmd /k "venv311\Scripts\activate.bat && streamlit run src\apps\image_generator.py --server.port=8502"
    timeout /t 2 /nobreak >nul
    start "Comic Preview" cmd /k "venv311\Scripts\activate.bat && streamlit run src\apps\comic_preview.py --server.port=8503"
    set STARTED_APPS=3
    set APP_URLS=Project Setup: http://localhost:8501^
Image Generator: http://localhost:8502^
Comic Preview: http://localhost:8503
)

echo.
echo === Deployment Summary ===
if %STARTED_APPS% gtr 0 (
    echo Successfully started %STARTED_APPS% app(s):
    echo %APP_URLS%
    echo.
    echo All apps are running in separate windows.
    echo Close the browser windows or close the command windows to stop.
) else (
    echo No apps were started successfully.
    pause
    exit /b 1
)

echo.
echo === Setup Complete ===
echo.
echo Usage:
echo   deploy_local.bat setup     - Run Project Setup app only
echo   deploy_local.bat generator - Run Image Generator app only  
echo   deploy_local.bat preview   - Run Comic Preview app only
echo   deploy_local.bat           - Run all three apps (default)
echo.
pause 