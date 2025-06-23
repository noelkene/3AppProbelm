# PowerShell script to run all three Streamlit apps
Write-Host "Starting all three Streamlit apps..." -ForegroundColor Green

# Set environment variables
$env:GOOGLE_APPLICATION_CREDENTIALS = "$PSScriptRoot\service_account.json"
$env:GOOGLE_CLOUD_PROJECT = "platinum-banner-303105"

# Function to start an app
function Start-App {
    param(
        [string]$AppName,
        [string]$AppPath,
        [int]$Port
    )
    
    Write-Host "Starting $AppName on port $Port..." -ForegroundColor Yellow
    Start-Process -FilePath ".\venv\Scripts\python.exe" -ArgumentList "-m", "streamlit", "run", $AppPath, "--server.port=$Port" -WindowStyle Normal
    Start-Sleep -Seconds 3
}

# Start all three apps
Start-App -AppName "Project Setup" -AppPath "src/apps/project_setup.py" -Port 8501
Start-App -AppName "Image Generator" -AppPath "src/apps/image_generator.py" -Port 8502
Start-App -AppName "Comic Preview" -AppPath "src/apps/comic_preview.py" -Port 8503

Write-Host ""
Write-Host "All apps are starting..." -ForegroundColor Green
Write-Host ""
Write-Host "Access your applications at:" -ForegroundColor Cyan
Write-Host "- Project Setup: http://localhost:8501" -ForegroundColor White
Write-Host "- Image Generator: http://localhost:8502" -ForegroundColor White
Write-Host "- Comic Preview: http://localhost:8503" -ForegroundColor White
Write-Host ""
Write-Host "Press any key to close this window..." -ForegroundColor Yellow
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown") 