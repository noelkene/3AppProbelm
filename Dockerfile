# Use Python 3.11 slim image (to match your local venv)
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    # software-properties-common \
    # git \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables for Python
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application source code needed for image_generator
# Assuming image_generator.py and its dependencies are in src/
COPY src/ src/

# Create necessary directories
RUN mkdir -p data/projects data/characters data/backgrounds

# Expose the port Streamlit will run on
# Cloud Run provides the PORT env var, Streamlit uses $PORT by default.
EXPOSE 8501

# Set environment variables
ENV PYTHONPATH=/app/src

# Create a non-root user and switch to it
RUN useradd -m -s /bin/bash -u 1000 streamlituser
USER streamlituser

# Command to run the image_generator.py application
# Using $PORT is important for Cloud Run
# Shell form allows $PORT expansion, and --server.headless true is good for Cloud Run.
CMD ["streamlit", "run", "streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"] 