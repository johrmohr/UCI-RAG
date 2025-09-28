#!/bin/bash
# Run the Streamlit application

echo "🚀 Starting UCI Physics Research Intelligence System..."
echo "----------------------------------------"
echo "Opening in browser at: http://localhost:8501"
echo "Press Ctrl+C to stop the server"
echo "----------------------------------------"

streamlit run frontend/app.py --server.port 8501 --server.address localhost