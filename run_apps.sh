#!/bin/bash

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Creating one..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

# Check for service account key and .env file
echo "Checking Google Cloud configuration..."
if [ -f "service_account.json" ]; then
    echo "✅ Found service_account.json"
    export GOOGLE_APPLICATION_CREDENTIALS=$(pwd)/service_account.json
else
    echo "⚠️ service_account.json not found. You may need to use gcloud CLI for authentication."
    echo "  Run: gcloud auth application-default login"
    echo "  You can also create a service account key from the Google Cloud Console."
fi

# Check for .env file
if [ -f ".env" ]; then
    echo "✅ Found .env file"
    # Load environment variables from .env file
    export $(grep -v '^#' .env | xargs)
else
    echo "⚠️ .env file not found. Using default configuration."
    echo "  Create a .env file with your Google Cloud settings for better operation."
    echo "  See gcp_setup_instructions.md for details."
fi

# Check required environment variables
if [ -z "$GOOGLE_CLOUD_PROJECT" ]; then
    echo "⚠️ GOOGLE_CLOUD_PROJECT not set. Some features may not work correctly."
fi

if [ -z "$GCS_BUCKET_NAME" ]; then
    echo "⚠️ GCS_BUCKET_NAME not set. Cloud storage features may not work correctly."
fi

# Create data directory structure if it doesn't exist
mkdir -p data/projects
mkdir -p data/characters
mkdir -p data/backgrounds

# Define function to run an app
run_app() {
    local app_path=$1
    local port=$2
    local app_name=$3
    
    echo "Starting $app_name on port $port..."
    streamlit run $app_path --server.port=$port &
    echo "$app_name started with PID: $!"
}

# Usage message
if [ "$1" == "-h" ] || [ "$1" == "--help" ]; then
    echo "Usage: ./run_apps.sh [option]"
    echo "Options:"
    echo "  setup     Run Project Setup app only"
    echo "  generator Run Image Generator app only"
    echo "  preview   Run Comic Preview app only"
    echo "  all       Run all three apps (default)"
    exit 0
fi

# Run the appropriate app(s)
case "$1" in
    setup)
        run_app "src/apps/project_setup.py" 8501 "Project Setup App"
        ;;
    generator)
        run_app "src/apps/image_generator.py" 8502 "Image Generator App"
        ;;
    preview)
        run_app "src/apps/comic_preview.py" 8503 "Comic Preview App"
        ;;
    all|"")
        run_app "src/apps/project_setup.py" 8501 "Project Setup App"
        run_app "src/apps/image_generator.py" 8502 "Image Generator App"
        run_app "src/apps/comic_preview.py" 8503 "Comic Preview App"
        ;;
    *)
        echo "Unknown option: $1"
        echo "Run './run_apps.sh --help' for usage information"
        exit 1
        ;;
esac

# Display application access information
echo ""
echo "Access your applications at:"
echo "- Project Setup: http://localhost:8501"
echo "- Image Generator: http://localhost:8502"
echo "- Comic Preview: http://localhost:8503"
echo ""
echo "All apps are running. Press Ctrl+C to stop."
wait 