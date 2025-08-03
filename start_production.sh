#!/bin/bash
# Production startup script for Medical Cabinet Backend

echo "🚀 Starting Medical Cabinet Backend..."

# Set working directory
cd /app/backend

# Check if requirements are installed
echo "📦 Installing requirements..."
pip install -r requirements.txt

# Install emergentintegrations if not already installed
pip install emergentintegrations --extra-index-url https://d33sy5i8bnduwe.cloudfront.net/simple/ || echo "emergentintegrations already installed"

# Set environment variables (these should be set in deployment config)
export PYTHONPATH="/app/backend:$PYTHONPATH"

# Start the server
echo "🌐 Starting FastAPI server..."
python -m uvicorn server:app --host 0.0.0.0 --port 8001 --workers 1

echo "✅ Server started successfully"
