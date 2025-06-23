@echo off
cd /d "%~dp0"
streamlit run src/apps/comic_preview.py --server.port 8502
pause 