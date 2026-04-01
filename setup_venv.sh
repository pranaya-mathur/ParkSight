#!/bin/bash

# ParkSight AI - Environment Setup Script
# Initializes a local virtual environment and installs all dependencies.

echo "🚀 Starting ParkSight AI Environment Setup..."

# 1. Create Virtual Environment
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment (.venv)..."
    python3 -m venv .venv
else
    echo "✅ Virtual environment already exists."
fi

# 2. Activate & Install
echo "🔌 Activating virtual environment..."
source .venv/bin/activate

echo "⬆️ Upgrading pip..."
pip install --upgrade pip

echo "🛠️ Installing dependencies from requirements.txt..."
pip install -r requirements.txt

echo "✨ Environment Ready! To activate, run: source .venv/bin/activate"
