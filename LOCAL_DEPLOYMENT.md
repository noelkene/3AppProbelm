# Local Deployment Guide

This guide will help you deploy all three Streamlit apps locally on your Windows machine.

## Prerequisites

1. **Python 3.11 or later** - Download from [python.org](https://www.python.org/downloads/)
2. **Google Cloud credentials** (optional) - For AI features to work properly

## Quick Start

### Option 1: Automatic Deployment (Recommended)

1. **Run the deployment script:**
   ```cmd
   deploy_local.bat
   ```

2. **Or run specific apps:**
   ```cmd
   deploy_local.bat setup     # Project Setup only
   deploy_local.bat generator # Image Generator only
   deploy_local.bat preview   # Comic Preview only
   ```

The script will automatically:
- Check Python installation
- Create a virtual environment (`venv311`)
- Install all dependencies
- Set up environment variables
- Start the selected apps in separate windows

### Option 2: Manual Deployment

If you prefer to set up manually:

1. **Create virtual environment:**
   ```cmd
   python -m venv venv311
   ```

2. **Activate virtual environment:**
   ```cmd
   venv311\Scripts\activate.bat
   ```

3. **Install dependencies:**
   ```cmd
   pip install -r requirements.txt
   ```

4. **Set environment variables:**
   ```cmd
   set GOOGLE_APPLICATION_CREDENTIALS=%CD%\service_account.json
   ```

5. **Run apps individually:**
   ```cmd
   # Terminal 1 - Project Setup
   streamlit run src\apps\project_setup.py --server.port=8501
   
   # Terminal 2 - Image Generator  
   streamlit run src\apps\image_generator.py --server.port=8502
   
   # Terminal 3 - Comic Preview
   streamlit run src\apps\comic_preview.py --server.port=8503
   ```

## App Access

Once deployed, access your apps at:

- **Project Setup**: http://localhost:8501
- **Image Generator**: http://localhost:8502  
- **Comic Preview**: http://localhost:8503

## Troubleshooting

### Python Not Found
- Ensure Python is installed and added to PATH
- Try running `python --version` to verify installation

### Virtual Environment Issues
- Delete the `venv311` folder and run the script again
- Ensure you have write permissions in the project directory

### Dependencies Installation Failures
- Try upgrading pip: `pip install --upgrade pip`
- Install packages one by one to identify problematic dependencies
- Check Python version compatibility (use Python 3.11)

### Port Already in Use
- Close other applications using ports 8501, 8502, or 8503
- Or modify the ports in the deployment script

### Google Cloud Authentication
- Ensure `service_account.json` is in the project root
- Or use `gcloud auth application-default login` for CLI authentication

### PyMuPDF Issues
- If you encounter PyMuPDF import errors, try:
  ```cmd
  pip uninstall PyMuPDF
  pip install PyMuPDF==1.23.8
  ```

## File Structure

```
3AppProbelm/
├── deploy_local.bat          # Main deployment script
├── requirements.txt          # Python dependencies
├── service_account.json      # Google Cloud credentials
├── src/
│   └── apps/
│       ├── project_setup.py    # Project Setup app
│       ├── image_generator.py  # Image Generator app
│       └── comic_preview.py    # Comic Preview app
└── data/                     # Local data storage
    ├── projects/
    ├── characters/
    └── backgrounds/
```

## Stopping the Apps

- Close the browser windows
- Close the command prompt windows running the apps
- Or press `Ctrl+C` in each terminal

## Next Steps

1. **Project Setup**: Create a new comic project, upload source material, and define characters/backgrounds
2. **Image Generator**: Generate AI images for your comic panels
3. **Comic Preview**: View and manage your comic project

## Support

If you encounter issues:
1. Check the troubleshooting section above
2. Verify all prerequisites are met
3. Try the manual deployment steps
4. Check the console output for error messages 