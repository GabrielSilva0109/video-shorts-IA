@echo off
SETLOCAL

echo.
echo  ====================================================
echo   AI Shorts Generator — Starting...
echo  ====================================================
echo.

:: ── Verifica .venv do backend ─────────────────
IF NOT EXIST "backend\.venv\Scripts\activate.bat" (
    echo [ERROR] Backend venv not found. Run install.bat first.
    pause & exit /b 1
)

:: ── Verifica node_modules do frontend ─────────
IF NOT EXIST "frontend\node_modules" (
    echo [ERROR] Frontend dependencies not found. Run install.bat first.
    pause & exit /b 1
)

:: ── Inicia Backend numa nova janela ───────────
echo [1/2] Starting backend on http://localhost:8000 ...
start "AI Shorts — Backend" cmd /k "cd /d %~dp0backend && call .venv\Scripts\activate.bat && python main.py"

:: ── Aguarda o backend subir ───────────────────
echo      Waiting for backend to start...
:WAIT_BACKEND
timeout /t 2 /nobreak >nul
curl -s http://localhost:8000/api/health >nul 2>&1
IF %ERRORLEVEL% NEQ 0 goto WAIT_BACKEND
echo [OK] Backend is up!

:: ── Inicia Frontend numa nova janela ──────────
echo [2/2] Starting frontend on http://localhost:5173 ...
start "AI Shorts — Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"

echo.
echo  ====================================================
echo   Backend:  http://localhost:8000
echo   Frontend: http://localhost:5173
echo   API Docs: http://localhost:8000/api/docs
echo  ====================================================
echo.
echo  Both services are running in separate windows.
echo  Close those windows to stop the services.
echo.
pause
