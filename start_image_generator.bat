@echo off
cd /d "%~dp0"
streamlit run src/apps/image_generator.py --server.port 8503
pause 