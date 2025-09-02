#!/bin/bash

# Start EdAgent Streamlit Frontend
# This script starts only the Streamlit frontend (assumes backend is already running)

echo "🎨 Starting EdAgent Streamlit Frontend..."

# Check if backend is running
if ! curl -s http://localhost:8000/health > /dev/null; then
    echo "⚠️  Warning: Backend API not responding at http://localhost:8000"
    echo "   Make sure the FastAPI backend is running first"
    echo "   You can start it with: uvicorn main:app --reload"
    echo ""
fi

# Set environment variables
export EDAGENT_API_URL="http://localhost:8000/api/v1"
export EDAGENT_WS_URL="ws://localhost:8000/api/v1/ws"
export USE_MOCK_DATA="false"

# Install requirements if needed
if ! python -c "import streamlit" 2>/dev/null; then
    echo "📦 Installing Streamlit requirements..."
    pip install -r streamlit_requirements.txt
fi

# Start Streamlit
echo "🚀 Starting Streamlit on http://localhost:8501"
streamlit run streamlit_app.py \
    --server.port 8501 \
    --server.address 0.0.0.0 \
    --browser.gatherUsageStats false