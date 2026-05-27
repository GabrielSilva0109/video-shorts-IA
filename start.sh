#!/usr/bin/env bash
set -e

echo ""
echo " ===================================================="
echo "  AI Shorts Generator — Starting..."
echo " ===================================================="
echo ""

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"

# ── Verifica .venv do backend ──────────────────
if [ ! -f "$ROOT_DIR/backend/.venv/bin/activate" ]; then
    echo "[ERROR] Backend venv not found. Run install.sh first."
    exit 1
fi

# ── Verifica node_modules do frontend ─────────
if [ ! -d "$ROOT_DIR/frontend/node_modules" ]; then
    echo "[ERROR] Frontend dependencies not found. Run install.sh first."
    exit 1
fi

# ── Inicia Backend ────────────────────────────
echo "[1/2] Starting backend on http://localhost:8000 ..."
cd "$ROOT_DIR/backend"
source .venv/bin/activate
python main.py &
BACKEND_PID=$!

# ── Aguarda o backend subir ───────────────────
echo "      Waiting for backend to start..."
for i in $(seq 1 30); do
    sleep 2
    if curl -s http://localhost:8000/api/health > /dev/null 2>&1; then
        echo "[OK] Backend is up!"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "[ERROR] Backend did not start in time."
        kill $BACKEND_PID 2>/dev/null
        exit 1
    fi
done

# ── Inicia Frontend ───────────────────────────
echo "[2/2] Starting frontend on http://localhost:5173 ..."
cd "$ROOT_DIR/frontend"
npm run dev &
FRONTEND_PID=$!

echo ""
echo " ===================================================="
echo "  Backend:  http://localhost:8000"
echo "  Frontend: http://localhost:5173"
echo "  API Docs: http://localhost:8000/api/docs"
echo " ===================================================="
echo ""
echo "  Press Ctrl+C to stop all services."
echo ""

# ── Aguarda e encerra tudo com Ctrl+C ─────────
trap "echo ''; echo 'Stopping services...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0" INT TERM
wait $BACKEND_PID $FRONTEND_PID
