#!/usr/bin/env python3
"""
Management script for the three Streamlit applications.
"""

import subprocess
import sys
import os
import time
import requests
from pathlib import Path

class DeploymentManager:
    def __init__(self):
        self.apps = {
            'project_setup': {
                'name': 'Project Setup',
                'file': 'src/apps/project_setup.py',
                'port': 8501
            },
            'image_generator': {
                'name': 'Image Generator',
                'file': 'src/apps/image_generator.py',
                'port': 8502
            },
            'comic_preview': {
                'name': 'Comic Preview',
                'file': 'src/apps/comic_preview.py',
                'port': 8503
            }
        }
        self.processes = {}
        
    def start_apps(self):
        """Start all three applications."""
        print("🚀 Starting all applications...")
        
        # Set environment variables
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = str(Path('service_account.json').absolute())
        os.environ['GOOGLE_CLOUD_PROJECT'] = 'platinum-banner-303105'
        os.environ['GCS_BUCKET_NAME'] = 'comic_book_heros_and_villans'
        
        python_exe = Path('venv/Scripts/python.exe') if os.name == 'nt' else Path('venv/bin/python')
        
        for app_key, app in self.apps.items():
            print(f"   Starting {app['name']} on port {app['port']}...")
            
            cmd = [
                str(python_exe), '-m', 'streamlit', 'run',
                app['file'],
                '--server.port', str(app['port']),
                '--server.headless', 'true'
            ]
            
            try:
                process = subprocess.Popen(cmd)
                self.processes[app_key] = process
                time.sleep(2)  # Give each app time to start
                print(f"   ✅ {app['name']} started (PID: {process.pid})")
            except Exception as e:
                print(f"   ❌ Failed to start {app['name']}: {e}")
        
        print("\n🎉 All applications started!")
        self.show_status()
    
    def stop_apps(self):
        """Stop all running applications."""
        print("🛑 Stopping all applications...")
        
        for app_key, process in self.processes.items():
            app_name = self.apps[app_key]['name']
            print(f"   Stopping {app_name}...")
            try:
                process.terminate()
                process.wait(timeout=5)
                print(f"   ✅ {app_name} stopped")
            except subprocess.TimeoutExpired:
                print(f"   ⚠️  {app_name} didn't stop gracefully, forcing...")
                process.kill()
            except Exception as e:
                print(f"   ❌ Error stopping {app_name}: {e}")
        
        self.processes.clear()
        print("✅ All applications stopped.")
    
    def show_status(self):
        """Show the status of all applications."""
        print("\n📊 Application Status:")
        print("=" * 50)
        
        all_running = True
        for app_key, app in self.apps.items():
            try:
                response = requests.get(f"http://localhost:{app['port']}", timeout=3)
                if response.status_code == 200:
                    print(f"✅ {app['name']} - Running on port {app['port']}")
                else:
                    print(f"⚠️  {app['name']} - Responding with status {response.status_code}")
                    all_running = False
            except:
                print(f"❌ {app['name']} - Not running on port {app['port']}")
                all_running = False
        
        print("=" * 50)
        if all_running:
            print("🎉 All applications are running!")
            print("\n📱 Access your applications at:")
            for app in self.apps.values():
                print(f"   - {app['name']}: http://localhost:{app['port']}")
        else:
            print("❌ Some applications are not running properly.")
    
    def restart_apps(self):
        """Restart all applications."""
        print("🔄 Restarting all applications...")
        self.stop_apps()
        time.sleep(2)
        self.start_apps()

def main():
    if len(sys.argv) < 2:
        print("Usage: python manage_deployment.py [start|stop|status|restart]")
        print("\nCommands:")
        print("  start   - Start all applications")
        print("  stop    - Stop all applications")
        print("  status  - Show status of all applications")
        print("  restart - Restart all applications")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    manager = DeploymentManager()
    
    if command == 'start':
        manager.start_apps()
    elif command == 'stop':
        manager.stop_apps()
    elif command == 'status':
        manager.show_status()
    elif command == 'restart':
        manager.restart_apps()
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

if __name__ == '__main__':
    main() 