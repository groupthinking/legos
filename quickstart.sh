#!/bin/bash
# Quick Start Guide for License RAG System

set -e

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║         License RAG System - Quick Start Guide                ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Check Python
if ! command -v python &> /dev/null; then
    echo "❌ Python not found. Please install Python 3.8+"
    exit 1
fi

echo "✓ Python found: $(python --version)"
echo ""

# Check if dependencies are installed
if ! python -c "import fastapi" 2>/dev/null; then
    echo "📦 Installing dependencies..."
    pip install -r requirements.txt
    playwright install chromium
    echo ""
fi

# Check for OpenAI API key
if [ -z "$OPENAI_API_KEY" ]; then
    echo "⚠️  OPENAI_API_KEY not set"
    echo "   To use RAG features, set your API key:"
    echo "   export OPENAI_API_KEY='sk-...'"
    echo ""
    echo "   Continuing without LLM features..."
    echo ""
fi

# Check if licenses.jsonl exists
if [ ! -f "licenses.jsonl" ]; then
    echo "📝 Creating sample license data..."
    python example.py > /dev/null
    mv example_licenses.jsonl licenses.jsonl
    echo "✓ Sample data created"
    echo ""
fi

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                    Starting RAG Server                        ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "Server will start on: http://localhost:8000"
echo ""
echo "Next steps:"
echo "  1. Open index.html in your browser"
echo "  2. Browse licenses in the left panel"
echo "  3. Chat with the AI analyst in the right panel"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""
echo "────────────────────────────────────────────────────────────────"
echo ""

# Start server
python server.py
