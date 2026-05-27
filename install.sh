#!/usr/bin/env bash
set -e

echo ""
echo "===================================================="
echo "  AI Shorts Generator — Linux/macOS Setup"
echo "===================================================="
echo ""

# ── Check Python ──────────────────────────────
if ! command -v python3 &>/dev/null; then
    echo "[ERROR] Python 3.10+ is required but not found."
    echo "Install via: sudo apt install python3 python3-venv (Ubuntu)"
    echo "         or: brew install python (macOS)"
    exit 1
fi
PYVER=$(python3 --version | cut -d' ' -f2)
echo "[OK] Python $PYVER found"

# ── Check Node ────────────────────────────────
if ! command -v node &>/dev/null; then
    echo "[ERROR] Node.js 18+ is required but not found."
    echo "Install via: https://nodejs.org/"
    exit 1
fi
echo "[OK] Node.js $(node --version) found"

# ── Check FFmpeg ──────────────────────────────
if ! command -v ffmpeg &>/dev/null; then
    echo "[WARN] FFmpeg not found. Installing..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        brew install ffmpeg
    elif command -v apt &>/dev/null; then
        sudo apt update -y && sudo apt install -y ffmpeg
    elif command -v dnf &>/dev/null; then
        sudo dnf install -y ffmpeg
    else
        echo "[ERROR] Please install FFmpeg manually: https://ffmpeg.org/download.html"
        exit 1
    fi
fi
echo "[OK] FFmpeg $(ffmpeg -version 2>&1 | head -1 | cut -d' ' -f3) found"

# ── Copy .env ─────────────────────────────────
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "[OK] Created .env from .env.example"
    echo "[!] IMPORTANT: Edit .env and add your API keys"
else
    echo "[OK] .env already exists"
fi

# ── Create directories ────────────────────────
mkdir -p exports assets/music assets/fonts assets/effects tmp logs
echo "[OK] Directories created"

# ── Backend setup ─────────────────────────────
echo ""
echo "[1/3] Setting up Python backend..."
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt -q
echo "[OK] Backend dependencies installed"
deactivate
cd ..

# ── Frontend setup ────────────────────────────
echo ""
echo "[2/3] Setting up frontend..."
cd frontend
npm install --silent
echo "[OK] Frontend dependencies installed"
cd ..

echo ""
echo "[3/3] Setup complete!"
echo ""
echo "===================================================="
echo "  Next steps:"
echo "  1. Edit .env and add your OpenAI + Pexels API keys"
echo "  2. Start backend:  cd backend && source .venv/bin/activate && python main.py"
echo "  3. Start frontend: cd frontend && npm run dev"
echo "  4. Open:           http://localhost:5173"
echo "===================================================="
echo ""
