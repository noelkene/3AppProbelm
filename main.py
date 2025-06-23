"""
Google App Engine entry point for Comic Creation Suite
"""

import os
import sys
import subprocess
import threading
import time
import requests
from flask import Flask, render_template_string

# Add the src directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the main Streamlit app
from streamlit_cloud_deploy import main as streamlit_main

app = Flask(__name__)

# Global variable to track if Streamlit is running
streamlit_running = False
streamlit_process = None

def start_streamlit():
    """Start Streamlit in a separate thread"""
    global streamlit_running, streamlit_process
    
    if not streamlit_running:
        try:
            # Start Streamlit on port 8501
            streamlit_process = subprocess.Popen([
                sys.executable, "-m", "streamlit", "run", 
                "streamlit_cloud_deploy.py",
                "--server.port=8501",
                "--server.address=0.0.0.0",
                "--server.headless=true",
                "--browser.gatherUsageStats=false"
            ])
            streamlit_running = True
            print("Streamlit started successfully")
        except Exception as e:
            print(f"Error starting Streamlit: {e}")

def check_streamlit_health():
    """Check if Streamlit is running and healthy"""
    try:
        response = requests.get("http://localhost:8501/_stcore/health", timeout=5)
        return response.status_code == 200
    except:
        return False

@app.route('/')
def index():
    """Main route that redirects to Streamlit"""
    # Start Streamlit if not running
    if not streamlit_running:
        start_streamlit()
        # Wait a moment for Streamlit to start
        time.sleep(3)
    
    # Check if Streamlit is healthy
    if check_streamlit_health():
        return render_template_string("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Comic Creation Suite</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body {
                    font-family: Arial, sans-serif;
                    margin: 0;
                    padding: 20px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    text-align: center;
                }
                .container {
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 40px 20px;
                }
                h1 {
                    font-size: 2.5rem;
                    margin-bottom: 20px;
                }
                p {
                    font-size: 1.2rem;
                    margin-bottom: 30px;
                }
                .btn {
                    display: inline-block;
                    background: #4CAF50;
                    color: white;
                    padding: 15px 30px;
                    text-decoration: none;
                    border-radius: 5px;
                    font-size: 1.1rem;
                    transition: background 0.3s;
                }
                .btn:hover {
                    background: #45a049;
                }
                .loading {
                    margin: 20px 0;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🎨 Comic Creation Suite</h1>
                <p>Your AI-powered comic creation platform is ready!</p>
                <div class="loading">
                    <p>Loading your app...</p>
                </div>
                <a href="http://localhost:8501" class="btn">Open Comic Creation Suite</a>
                <script>
                    // Auto-redirect after a short delay
                    setTimeout(function() {
                        window.location.href = 'http://localhost:8501';
                    }, 2000);
                </script>
            </div>
        </body>
        </html>
        """)
    else:
        return render_template_string("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Comic Creation Suite - Starting</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body {
                    font-family: Arial, sans-serif;
                    margin: 0;
                    padding: 20px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    text-align: center;
                }
                .container {
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 40px 20px;
                }
                h1 {
                    font-size: 2.5rem;
                    margin-bottom: 20px;
                }
                .spinner {
                    border: 4px solid #f3f3f3;
                    border-top: 4px solid #3498db;
                    border-radius: 50%;
                    width: 50px;
                    height: 50px;
                    animation: spin 1s linear infinite;
                    margin: 20px auto;
                }
                @keyframes spin {
                    0% { transform: rotate(0deg); }
                    100% { transform: rotate(360deg); }
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🎨 Comic Creation Suite</h1>
                <p>Starting your application...</p>
                <div class="spinner"></div>
                <p>Please wait while we prepare your comic creation tools.</p>
                <script>
                    // Check if Streamlit is ready every 2 seconds
                    function checkStreamlit() {
                        fetch('/health')
                            .then(response => {
                                if (response.ok) {
                                    window.location.href = 'http://localhost:8501';
                                } else {
                                    setTimeout(checkStreamlit, 2000);
                                }
                            })
                            .catch(() => {
                                setTimeout(checkStreamlit, 2000);
                            });
                    }
                    setTimeout(checkStreamlit, 2000);
                </script>
            </div>
        </body>
        </html>
        """)

@app.route('/health')
def health():
    """Health check endpoint"""
    if check_streamlit_health():
        return {"status": "healthy", "streamlit": "running"}, 200
    else:
        return {"status": "starting", "streamlit": "not ready"}, 503

if __name__ == '__main__':
    # Start Streamlit when the app starts
    start_streamlit()
    
    # Run Flask app
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080))) 