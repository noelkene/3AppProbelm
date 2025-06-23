@echo off
echo Setting up environment variables...
set GOOGLE_APPLICATION_CREDENTIALS=C:\Users\hirko\Cursor Projects\3AppProbelm\service_account.json

echo Starting Streamlit app...
call .\venv311\Scripts\activate
python -m streamlit run src/apps/project_setup.py --server.port=8506

pause 