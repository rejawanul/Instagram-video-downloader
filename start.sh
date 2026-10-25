#!/usr/bin/env bash
# ==============================================================================
# Instagram Video Downloader Launcher (Mac mini M4 Edition)
# ==============================================================================

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

echo "🚀 Starting Instagram Video Downloader Pro..."
echo "📍 Location: $DIR"
echo "🖥️  Platform: Apple Silicon macOS (Mac mini M4)"

# Check virtual environment
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
    ./venv/bin/pip install --upgrade pip
    ./venv/bin/pip install -r requirements.txt
fi

PORT=5055
URL="http://localhost:$PORT"

echo "🌐 Web Dashboard starting at: $URL"
echo "✨ Press Ctrl+C in terminal to stop."

# Open browser after 1.5 seconds in background
(sleep 1.5 && open "$URL") &

# Start Uvicorn FastAPI server
./venv/bin/python3 -m uvicorn app:app --host 127.0.0.1 --port $PORT --log-level info
