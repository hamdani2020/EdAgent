#!/bin/bash

# Start EdAgent in Demo Mode
# This script starts the Streamlit frontend with mock data (no backend required)

echo "🎭 Starting EdAgent in Demo Mode..."
echo "   This mode uses mock data and doesn't require the backend API"

# Set environment variables for demo mode
export EDAGENT_API_URL="http://localhost:8000/api/v1"
export EDAGENT_WS_URL="ws://localhost:8000/api/v1/ws"
export USE_MOCK_DATA="true"

# Install requirements if needed
if ! python -c "import streamlit" 2>/dev/null; then
    echo "📦 Installing Streamlit requirements..."
    pip install -r streamlit_requirements.txt
fi

# Start Streamlit
echo "🚀 Starting Streamlit Demo on http://localhost:8501"
echo "   Demo features:"
echo "   - Mock user data and conversations"
echo "   - Sample learning paths and assessments"
echo "   - Interactive UI components"
echo "   - No backend API required"
echo ""

streamlit run streamlit_app.py \
    --server.port 8501 \
    --server.address 0.0.0.0 \
    --browser.gatherUsageStats false