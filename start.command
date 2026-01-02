#!/bin/bash
# Gate Quote Pro - Web App Launcher
# Double-click this file to start the server

cd "$(dirname "$0")"

echo "Starting Gate Quote Pro..."
echo ""

# Activate virtual environment and start server
source venv/bin/activate
python webapp.py
