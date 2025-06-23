# Local Deployment Script for Windows
# This script sets up and runs all three Streamlit apps locally

param(
    [switch]$Setup,
    [switch]$Generator,
    [switch]$Preview,
    [switch]$All,
    [switch]$Help
)

# Function to write colored output
function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host $Message -ForegroundColor $Color
}

# Function to check if command exists
function Test-Command {
    param([string]$Command)
    try {
        Get-Command $Command -ErrorAction Stop | Out-Null
        return $true
    }
    catch {
        return $false
    }
}

# Function to create virtual environment
function New-VirtualEnvironment {
    param([string]$PythonPath, [string]$VenvPath)
    
    Write-ColorOutput "Creating virtual environment..." "Yellow"
    
    if (Test-Path $VenvPath) {
        Write-ColorOutput "Virtual environment already exists at $VenvPath" "Green"
        return $true
    }
    
    try {
        & $PythonPath -m venv $VenvPath
        if ($LASTEXITCODE -eq 0) {
            Write-ColorOutput "Virtual environment created successfully!" "Green"
            return $true
        } else {
            Write-ColorOutput "Failed to create virtual environment" "Red"
            return $false
        }
    }
    catch {
        Write-ColorOutput "Error creating virtual environment: $($_.Exception.Message)" "Red"
        return $false
    }
}

# Function to install dependencies
function Install-Dependencies {
    param([string]$VenvPath)
    
    Write-ColorOutput "Installing dependencies..." "Yellow"
    
    $pipPath = Join-Path $VenvPath "Scripts\pip.exe"
    $requirementsPath = Join-Path $PSScriptRoot "requirements.txt"
    
    if (-not (Test-Path $pipPath)) {
        Write-ColorOutput "pip not found in virtual environment" "Red"
        return $false
    }
    
    if (-not (Test-Path $requirementsPath)) {
        Write-ColorOutput "requirements.txt not found" "Red"
        return $false
    }
    
    try {
        # Upgrade pip first
        & $pipPath install --upgrade pip
        if ($LASTEXITCODE -ne 0) {
            Write-ColorOutput "Failed to upgrade pip" "Red"
            return $false
        }
        
        # Install dependencies
        & $pipPath install -r $requirementsPath
        if ($LASTEXITCODE -eq 0) {
            Write-ColorOutput "Dependencies installed successfully!" "Green"
            return $true
        } else {
            Write-ColorOutput "Failed to install dependencies" "Red"
            return $false
        }
    }
    catch {
        Write-ColorOutput "Error installing dependencies: $($_.Exception.Message)" "Red"
        return $false
    }
}

# Function to set up environment variables
function Set-EnvironmentVariables {
    Write-ColorOutput "Setting up environment variables..." "Yellow"
    
    # Set Google Cloud credentials
    $serviceAccountPath = Join-Path $PSScriptRoot "service_account.json"
    if (Test-Path $serviceAccountPath) {
        $env:GOOGLE_APPLICATION_CREDENTIALS = $serviceAccountPath
        Write-ColorOutput "Google Cloud credentials set" "Green"
    } else {
        Write-ColorOutput "service_account.json not found. Some features may not work." "Yellow"
    }
    
    # Create data directories
    $dataDirs = @("data", "data/projects", "data/characters", "data/backgrounds")
    foreach ($dir in $dataDirs) {
        $fullPath = Join-Path $PSScriptRoot $dir
        if (-not (Test-Path $fullPath)) {
            New-Item -ItemType Directory -Path $fullPath -Force | Out-Null
            Write-ColorOutput "Created directory: $dir" "Green"
        }
    }
}

# Function to run a Streamlit app
function Start-StreamlitApp {
    param(
        [string]$AppPath,
        [int]$Port,
        [string]$AppName,
        [string]$VenvPath
    )
    
    $streamlitPath = Join-Path $VenvPath "Scripts\streamlit.exe"
    $fullAppPath = Join-Path $PSScriptRoot $AppPath
    
    if (-not (Test-Path $streamlitPath)) {
        Write-ColorOutput "Streamlit not found in virtual environment" "Red"
        return $false
    }
    
    if (-not (Test-Path $fullAppPath)) {
        Write-ColorOutput "App not found: $fullAppPath" "Red"
        return $false
    }
    
    Write-ColorOutput "Starting $AppName on port $Port..." "Yellow"
    
    try {
        Start-Process -FilePath $streamlitPath -ArgumentList "run", $fullAppPath, "--server.port=$Port" -WindowStyle Normal
        Write-ColorOutput "$AppName started successfully!" "Green"
        return $true
    }
    catch {
        Write-ColorOutput "Error starting $AppName: $($_.Exception.Message)" "Red"
        return $false
    }
}

# Main execution
if ($Help) {
    Write-ColorOutput "Local Deployment Script for Windows" "Cyan"
    Write-ColorOutput "Usage: .\deploy_local.ps1 [options]" "White"
    Write-ColorOutput "" "White"
    Write-ColorOutput "Options:" "White"
    Write-ColorOutput "  -Setup     Run Project Setup app only" "White"
    Write-ColorOutput "  -Generator Run Image Generator app only" "White"
    Write-ColorOutput "  -Preview   Run Comic Preview app only" "White"
    Write-ColorOutput "  -All       Run all three apps (default)" "White"
    Write-ColorOutput "  -Help      Show this help message" "White"
    Write-ColorOutput "" "White"
    Write-ColorOutput "Examples:" "White"
    Write-ColorOutput "  .\deploy_local.ps1 -All" "White"
    Write-ColorOutput "  .\deploy_local.ps1 -Setup" "White"
    Write-ColorOutput "  .\deploy_local.ps1 -Generator -Preview" "White"
    exit 0
}

Write-ColorOutput "=== Local Deployment Script ===" "Cyan"
Write-ColorOutput "Setting up your Streamlit apps..." "White"

# Check Python installation
Write-ColorOutput "Checking Python installation..." "Yellow"
$pythonVersions = @("python", "python3", "py")
$pythonPath = $null

foreach ($version in $pythonVersions) {
    if (Test-Command $version) {
        $pythonPath = (Get-Command $version).Source
        Write-ColorOutput "Found Python: $pythonPath" "Green"
        break
    }
}

if (-not $pythonPath) {
    Write-ColorOutput "Python not found. Please install Python 3.11 or later." "Red"
    Write-ColorOutput "Download from: https://www.python.org/downloads/" "Yellow"
    exit 1
}

# Check Python version
$pythonVersion = & $pythonPath --version 2>&1
Write-ColorOutput "Python version: $pythonVersion" "Green"

# Set up virtual environment
$venvPath = Join-Path $PSScriptRoot "venv311"
if (-not (New-VirtualEnvironment -PythonPath $pythonPath -VenvPath $venvPath)) {
    exit 1
}

# Install dependencies
if (-not (Install-Dependencies -VenvPath $venvPath)) {
    exit 1
}

# Set up environment variables
Set-EnvironmentVariables

# Determine which apps to run
$appsToRun = @()

if ($Setup) { $appsToRun += @{Path="src/apps/project_setup.py"; Port=8501; Name="Project Setup"} }
if ($Generator) { $appsToRun += @{Path="src/apps/image_generator.py"; Port=8502; Name="Image Generator"} }
if ($Preview) { $appsToRun += @{Path="src/apps/comic_preview.py"; Port=8503; Name="Comic Preview"} }
if ($All -or ($appsToRun.Count -eq 0)) {
    $appsToRun = @(
        @{Path="src/apps/project_setup.py"; Port=8501; Name="Project Setup"},
        @{Path="src/apps/image_generator.py"; Port=8502; Name="Image Generator"},
        @{Path="src/apps/comic_preview.py"; Port=8503; Name="Comic Preview"}
    )
}

# Start apps
Write-ColorOutput "Starting applications..." "Yellow"
$startedApps = @()

foreach ($app in $appsToRun) {
    if (Start-StreamlitApp -AppPath $app.Path -Port $app.Port -AppName $app.Name -VenvPath $venvPath) {
        $startedApps += $app
    }
}

# Display results
Write-ColorOutput "" "White"
Write-ColorOutput "=== Deployment Summary ===" "Cyan"

if ($startedApps.Count -gt 0) {
    $count = $startedApps.Count
    Write-ColorOutput "Successfully started $count app(s):" "Green"
    foreach ($app in $startedApps) {
        $url = "http://localhost:" + $app.Port
        Write-ColorOutput "   - $($app.Name): $url" "White"
    }
    
    Write-ColorOutput "" "White"
    Write-ColorOutput "All apps are running in separate windows." "Green"
    Write-ColorOutput "Close the browser windows or press Ctrl+C in the terminal to stop." "Yellow"
} else {
    Write-ColorOutput "No apps were started successfully." "Red"
    exit 1
}

Write-ColorOutput "" "White"
Write-ColorOutput "=== Setup Complete ===" "Cyan" 