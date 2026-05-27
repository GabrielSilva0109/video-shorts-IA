@echo off
SETLOCAL ENABLEDELAYEDEXPANSION

echo.
echo  ====================================================
echo   AI Shorts Generator — Windows Setup
echo  ====================================================
echo.

:: ── Check Python ──────────────────────────────
where python >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python 3.10+ is required but not found.
    echo Download from: https://www.python.org/downloads/
    pause & exit /b 1
)
for /f "tokens=2 delims= " %%v in ('python --version 2^>^&1') do set PYVER=%%v
echo [OK] Python %PYVER% found

:: ── Check Node ────────────────────────────────
where node >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Node.js 18+ is required but not found.
    echo Download from: https://nodejs.org/
    pause & exit /b 1
)
for /f "tokens=1" %%v in ('node --version') do set NODEVER=%%v
echo [OK] Node.js %NODEVER% found

:: ── Check FFmpeg ──────────────────────────────
where ffmpeg >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo.
    echo [WARN] FFmpeg not found in PATH.
    echo Please install FFmpeg:
    echo   1. Download from: https://www.gyan.dev/ffmpeg/builds/
    echo   2. Extract to C:\ffmpeg\
    echo   3. Add C:\ffmpeg\bin to your System PATH
    echo   4. Set FFMPEG_PATH=C:\ffmpeg\bin\ffmpeg.exe in .env
    echo.
    pause
) ELSE (
    echo [OK] FFmpeg found
)

:: ── Copy .env ─────────────────────────────────
IF NOT EXIST ".env" (
    copy .env.example .env
    echo [OK] Created .env from .env.example
    echo [!] IMPORTANT: Edit .env and add your API keys
) ELSE (
    echo [OK] .env already exists
)

:: ── Create directories ────────────────────────
mkdir exports 2>nul
mkdir assets\music 2>nul
mkdir assets\fonts 2>nul
mkdir assets\effects 2>nul
mkdir tmp 2>nul
mkdir logs 2>nul
echo [OK] Directories created

:: ── Backend setup ─────────────────────────────
echo.
echo [1/3] Setting up Python backend...
cd backend
python -m venv .venv
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet
echo [OK] Backend dependencies installed
cd ..

:: ── Frontend setup ────────────────────────────
echo.
echo [2/3] Setting up frontend...
cd frontend
call npm install --silent
echo [OK] Frontend dependencies installed
cd ..

echo.
echo [3/3] Setup complete!
echo.
echo  ====================================================
echo   Next steps:
echo   1. Edit .env and add your OpenAI + Pexels API keys
echo   2. Start backend:  cd backend ^& .venv\Scripts\activate ^& python main.py
echo   3. Start frontend: cd frontend ^& npm run dev
echo   4. Open: http://localhost:5173
echo  ====================================================
echo.
pause
