#!/bin/bash

# Setup script for deployment
echo "Setting up Manga Storyboard Generator..."

# Install Python dependencies
pip install -r requirements.txt

# Create necessary directories
mkdir -p data/projects
mkdir -p data/characters
mkdir -p data/backgrounds

echo "Setup complete!" 