#!/bin/bash

# Deployment script for Manga Storyboard Generator

echo "🚀 Manga Storyboard Generator Deployment Script"
echo "================================================"

# Check if we're in the right directory
if [ ! -f "streamlit_app.py" ]; then
    echo "❌ Error: streamlit_app.py not found. Please run this script from the project root."
    exit 1
fi

# Check if required files exist
echo "📋 Checking required files..."
required_files=("requirements.txt" ".streamlit/config.toml" "src/app.py")
for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file found"
    else
        echo "❌ $file missing"
        exit 1
    fi
done

echo ""
echo "🎯 Choose your deployment method:"
echo "1. Streamlit Cloud (Recommended - Free)"
echo "2. Docker Local"
echo "3. Docker Compose"
echo "4. Heroku"
echo "5. Railway"

read -p "Enter your choice (1-5): " choice

case $choice in
    1)
        echo "📚 Streamlit Cloud Deployment"
        echo "=============================="
        echo "1. Push your code to GitHub"
        echo "2. Go to https://share.streamlit.io"
        echo "3. Connect your GitHub repository"
        echo "4. Set main file path to: streamlit_app.py"
        echo "5. Add environment variables in the settings"
        echo ""
        echo "Environment variables needed:"
        echo "- GOOGLE_APPLICATION_CREDENTIALS_JSON"
        echo "- GOOGLE_CLOUD_PROJECT"
        echo "- GOOGLE_CLOUD_STORAGE_BUCKET"
        ;;
    2)
        echo "🐳 Docker Local Deployment"
        echo "=========================="
        docker build -t manga-generator .
        docker run -p 8501:8501 \
            -e GOOGLE_APPLICATION_CREDENTIALS_JSON="$GOOGLE_APPLICATION_CREDENTIALS_JSON" \
            -e GOOGLE_CLOUD_PROJECT="$GOOGLE_CLOUD_PROJECT" \
            -e GOOGLE_CLOUD_STORAGE_BUCKET="$GOOGLE_CLOUD_STORAGE_BUCKET" \
            manga-generator
        ;;
    3)
        echo "🐳 Docker Compose Deployment"
        echo "============================"
        if [ -z "$GOOGLE_APPLICATION_CREDENTIALS_JSON" ]; then
            echo "❌ Error: GOOGLE_APPLICATION_CREDENTIALS_JSON environment variable not set"
            exit 1
        fi
        docker-compose up --build
        ;;
    4)
        echo "🦸 Heroku Deployment"
        echo "===================="
        if ! command -v heroku &> /dev/null; then
            echo "❌ Heroku CLI not installed. Please install it first."
            exit 1
        fi
        read -p "Enter your Heroku app name: " app_name
        heroku create $app_name
        heroku config:set GOOGLE_APPLICATION_CREDENTIALS_JSON="$GOOGLE_APPLICATION_CREDENTIALS_JSON"
        heroku config:set GOOGLE_CLOUD_PROJECT="$GOOGLE_CLOUD_PROJECT"
        heroku config:set GOOGLE_CLOUD_STORAGE_BUCKET="$GOOGLE_CLOUD_STORAGE_BUCKET"
        git push heroku main
        ;;
    5)
        echo "🚂 Railway Deployment"
        echo "===================="
        echo "1. Go to https://railway.app"
        echo "2. Connect your GitHub repository"
        echo "3. Add environment variables in the dashboard"
        echo "4. Deploy automatically"
        ;;
    *)
        echo "❌ Invalid choice"
        exit 1
        ;;
esac

echo ""
echo "✅ Deployment instructions completed!"
echo "📖 For detailed instructions, see DEPLOYMENT_GUIDE.md" 