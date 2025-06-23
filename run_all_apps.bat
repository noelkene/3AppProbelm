@echo off
echo Starting all three Streamlit apps...

REM Set environment variables
set GOOGLE_APPLICATION_CREDENTIALS=%~dp0service_account.json
set GOOGLE_CLOUD_PROJECT=platinum-banner-303105
set GCS_BUCKET_NAME=comic_book_heros_and_villans

REM Start Project Setup App on port 8501
echo Starting Project Setup App on port 8501...
start "Project Setup" cmd /k "venv\Scripts\python.exe -m streamlit run src/apps/project_setup.py --server.port=8501"

REM Wait a moment
timeout /t 2 /nobreak > nul

REM Start Image Generator App on port 8502
echo Starting Image Generator App on port 8502...
start "Image Generator" cmd /k "venv\Scripts\python.exe -m streamlit run src/apps/image_generator.py --server.port=8502"

REM Wait a moment
timeout /t 2 /nobreak > nul

REM Start Comic Preview App on port 8503
echo Starting Comic Preview App on port 8503...
start "Comic Preview" cmd /k "venv\Scripts\python.exe -m streamlit run src/apps/comic_preview.py --server.port=8503"

echo.
echo All apps are starting...
echo.
echo Access your applications at:
echo - Project Setup: http://localhost:8501
echo - Image Generator: http://localhost:8502
echo - Comic Preview: http://localhost:8503
echo.
echo Press any key to close this window...
pause > nul 