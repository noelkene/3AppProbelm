@echo off
echo Starting all three apps...
echo.
echo Main App will be at: http://localhost:8501
echo Comic Preview will be at: http://localhost:8502
echo Image Generator will be at: http://localhost:8503
echo.
start "Main App" cmd /k "streamlit run streamlit_app.py --server.port 8501"
timeout /t 3 /nobreak >nul
start "Comic Preview" cmd /k "streamlit run src/apps/comic_preview.py --server.port 8502"
timeout /t 3 /nobreak >nul
start "Image Generator" cmd /k "streamlit run src/apps/image_generator.py --server.port 8503"
echo.
echo All apps started! Check the browser windows that opened.
echo.
pause 