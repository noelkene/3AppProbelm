# Check if the correct virtual environment exists
if (-not (Test-Path -Path "venv311")) {
    Write-Host "Virtual environment 'venv311' not found. Please create it using 'python -m venv venv311' with Python 3.11."
    exit 1
}

# Activate the virtual environment
. .\venv311\Scripts\Activate.ps1

Write-Host "Checking Google Cloud configuration..."
$serviceAccountFile = Join-Path $PSScriptRoot "service_account.json"
if (Test-Path -Path $serviceAccountFile) {
    Write-Host "✅ Found service_account.json"
    $env:GOOGLE_APPLICATION_CREDENTIALS = $serviceAccountFile
} else {
    Write-Warning "service_account.json not found. You may need to use gcloud CLI for authentication."
    Write-Host "  Run: gcloud auth application-default login"
    Write-Host "  You can also create a service account key from the Google Cloud Console."
}

# Check for .env file (basic implementation)
$envFile = Join-Path $PSScriptRoot ".env"
if (Test-Path -Path $envFile) {
    Write-Host "✅ Found .env file"
    Get-Content $envFile | ForEach-Object {
        if ($_ -match "^\s*([^#\s=]+)\s*=\s*(.*)") {
            $key = $matches[1]
            $value = $matches[2]
            # Remove potential quotes
            $value = $value -replace '^"|"$' -replace "^'|'$"
            [System.Environment]::SetEnvironmentVariable($key, $value, "Process")
        }
    }
} else {
    Write-Warning ".env file not found. Using default configuration."
    Write-Host "  Create a .env file with your Google Cloud settings for better operation."
    Write-Host "  See gcp_setup_instructions.md for details."
}

# Check required environment variables
if (-not $env:GOOGLE_CLOUD_PROJECT) {
    Write-Warning "GOOGLE_CLOUD_PROJECT not set. Some features may not work correctly."
}

if (-not $env:GCS_BUCKET_NAME) {
    Write-Warning "GCS_BUCKET_NAME not set. Cloud storage features may not work correctly."
}

# Create data directory structure if it doesn't exist
New-Item -ItemType Directory -Force -Path "data/projects" | Out-Null
New-Item -ItemType Directory -Force -Path "data/characters" | Out-Null
New-Item -ItemType Directory -Force -Path "data/backgrounds" | Out-Null

# Define function to run an app
function Run-App {
    param(
        [string]$app_path,
        [int]$port,
        [string]$app_name
    )
    
    Write-Host "Starting $app_name on port $port..."
    # Using Start-Process to run streamlit in a new window
    # This avoids blocking the main script and is easier to manage than Start-Job for this case.
    Start-Process python -ArgumentList "-m streamlit run $app_path --server.port $port"
    Write-Host "$app_name started."
}

# Help message
function Show-Help {
    Write-Host "Usage: .\run_apps.ps1 [option]"
    Write-Host "Options:"
    Write-Host "  setup     Run Project Setup app only"
    Write-Host "  generator Run Image Generator app only"
    Write-Host "  preview   Run Comic Preview app only"
    Write-Host "  all       Run all three apps (default)"
    Write-Host "  -h, --help  Show this help message"
}

# Default to 'all' if no arguments
$option = if ($args.Count -gt 0) { $args[0].ToLower() } else { "all" }

# Run the appropriate app(s)
switch ($option) {
    "setup" {
        Run-App -app_path "src/apps/project_setup.py" -port 8501 -app_name "Project Setup App"
    }
    "generator" {
        Run-App -app_path "src/apps/image_generator.py" -port 8502 -app_name "Image Generator App"
    }
    "preview" {
        Run-App -app_path "src/apps/comic_preview.py" -port 8503 -app_name "Comic Preview App"
    }
    "all" {
        Run-App -app_path "src/apps/project_setup.py" -port 8501 -app_name "Project Setup App"
        Run-App -app_path "src/apps/image_generator.py" -port 8502 -app_name "Image Generator App"
        Run-App -app_path "src/apps/comic_preview.py" -port 8503 -app_name "Comic Preview App"
    }
    "-h" { Show-Help }
    "--help" { Show-Help }
    default {
        Write-Host "Unknown option: $option"
        Show-Help
        exit 1
    }
}

if ($option -in "all", "setup", "generator", "preview") {
    # Display application access information
    Write-Host ""
    Write-Host "Access your applications at:"
    if ($option -in "all", "setup") { Write-Host "- Project Setup: http://localhost:8501" }
    if ($option -in "all", "generator") { Write-Host "- Image Generator: http://localhost:8502" }
    if ($option -in "all", "preview") { Write-Host "- Comic Preview: http://localhost:8503" }
    Write-Host ""
    Write-Host "Apps are running in separate windows. Close the windows to stop the apps."
} 