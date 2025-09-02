#!/usr/bin/env python3
"""
Startup script to run both FastAPI backend and Streamlit frontend
"""

import subprocess
import sys
import time
import threading
import signal
import os
from pathlib import Path

def run_fastapi():
    """Run the FastAPI backend server"""
    print("🚀 Starting FastAPI backend server...")
    try:
        # Change to the project directory
        os.chdir(Path(__file__).parent)
        
        # Run the FastAPI server
        subprocess.run([
            sys.executable, "-m", "uvicorn", 
            "main:app", 
            "--host", "0.0.0.0", 
            "--port", "8000", 
            "--reload"
        ], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ FastAPI server failed to start: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n🛑 FastAPI server stopped")

def run_streamlit():
    """Run the Streamlit frontend"""
    print("🎨 Starting Streamlit frontend...")
    
    # Wait a bit for FastAPI to start
    time.sleep(3)
    
    try:
        # Change to the project directory
        os.chdir(Path(__file__).parent)
        
        # Run the Streamlit app
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            "streamlit_app.py",
            "--server.port", "8501",
            "--server.address", "0.0.0.0",
            "--browser.gatherUsageStats", "false"
        ], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Streamlit frontend failed to start: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n🛑 Streamlit frontend stopped")

def check_dependencies():
    """Check if required dependencies are installed"""
    required_packages = [
        "fastapi", "uvicorn", "streamlit", "requests", 
        "pandas", "plotly", "streamlit-chat"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("❌ Missing required packages:")
        for package in missing_packages:
            print(f"   - {package}")
        print("\n📦 Install missing packages with:")
        print(f"   pip install {' '.join(missing_packages)}")
        return False
    
    return True

def setup_environment():
    """Setup environment variables if not set"""
    env_vars = {
        "EDAGENT_API_URL": "http://localhost:8000/api/v1",
        "EDAGENT_WS_URL": "ws://localhost:8000/api/v1/ws",
        "USE_MOCK_DATA": "true"
    }
    
    for var, default_value in env_vars.items():
        if var not in os.environ:
            os.environ[var] = default_value
            print(f"🔧 Set {var}={default_value}")

def main():
    """Main function to start both servers"""
    print("🎓 Starting EdAgent Application")
    print("=" * 50)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Setup environment
    setup_environment()
    
    # Create threads for both servers
    fastapi_thread = threading.Thread(target=run_fastapi, daemon=True)
    streamlit_thread = threading.Thread(target=run_streamlit, daemon=True)
    
    try:
        # Start FastAPI in background
        fastapi_thread.start()
        
        # Start Streamlit in background
        streamlit_thread.start()
        
        print("\n✅ Both servers started successfully!")
        print("🌐 FastAPI Backend: http://localhost:8000")
        print("🎨 Streamlit Frontend: http://localhost:8501")
        print("📚 API Documentation: http://localhost:8000/docs")
        print("\n💡 Press Ctrl+C to stop both servers")
        
        # Keep the main thread alive
        while True:
            time.sleep(1)
            
            # Check if threads are still alive
            if not fastapi_thread.is_alive():
                print("❌ FastAPI server stopped unexpectedly")
                break
            
            if not streamlit_thread.is_alive():
                print("❌ Streamlit frontend stopped unexpectedly")
                break
    
    except KeyboardInterrupt:
        print("\n🛑 Shutting down servers...")
        
        # Terminate subprocesses
        try:
            # Kill any running uvicorn processes
            subprocess.run(["pkill", "-f", "uvicorn"], check=False)
            # Kill any running streamlit processes
            subprocess.run(["pkill", "-f", "streamlit"], check=False)
        except:
            pass
        
        print("✅ Servers stopped successfully")

if __name__ == "__main__":
    main()