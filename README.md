# 🎬 AI Shorts Generator

> **Turn any topic into a viral short-form video in minutes.**  
> Powered by OpenAI, ElevenLabs, and FFmpeg.

---

## ✨ Features

| Feature                     | Description                                                      |
| --------------------------- | ---------------------------------------------------------------- |
| 🤖 **AI Script Generation** | OpenAI GPT-4o writes viral scripts with hooks, body, and CTA     |
| 🗣️ **AI Voice Narration**   | OpenAI TTS or ElevenLabs with 7+ voice styles                    |
| 🎞️ **Auto B-Roll**          | Searches Pexels & Pixabay for matching stock footage             |
| 📝 **Animated Subtitles**   | 6 subtitle styles (Hormozi, TikTok, Fire, Clean, Minimal, Emoji) |
| 🎵 **Background Music**     | Auto-mixed music with beat sync                                  |
| ⚡ **Dynamic Effects**      | Auto zoom, punch-in/out, cinematic transitions                   |
| 📱 **9:16 Export**          | Vertical video ready for TikTok, YouTube Shorts, Instagram Reels |
| 🖼️ **Thumbnail Generator**  | Auto-generated thumbnail at peak frame                           |
| 🖥️ **Desktop App**          | Electron desktop app (Windows, macOS, Linux)                     |
| 📦 **Batch Mode**           | Generate multiple videos in queue                                |

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.10+** — [python.org](https://www.python.org/downloads/)
- **Node.js 18+** — [nodejs.org](https://nodejs.org/)
- **FFmpeg** — [ffmpeg.org](https://ffmpeg.org/download.html)
- **OpenAI API Key** — [platform.openai.com](https://platform.openai.com/api-keys)
- **Pexels API Key** (free) — [pexels.com/api](https://www.pexels.com/api/)

### Windows

```bat
install.bat
```

### Linux / macOS

```bash
chmod +x install.sh && ./install.sh
```

### Manual Setup

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/ai-shorts-generator
cd ai-shorts-generator

# 2. Configure environment
cp .env.example .env
# Edit .env with your API keys

# 3. Backend
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python main.py

# 4. Frontend (new terminal)
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173** in your browser.

---

## 🔧 Configuration

Edit `.env` after copying from `.env.example`:

```env
# Required
OPENAI_API_KEY=sk-...
PEXELS_API_KEY=your_pexels_key

# Optional
ELEVENLABS_API_KEY=...          # Better voice quality
PIXABAY_API_KEY=...             # Extra B-roll source
REDIS_URL=redis://localhost:6379 # For Celery queue
GPU_ACCELERATION=false           # Set true for NVIDIA GPU
ENABLE_LOCAL_AI=false            # Use Ollama instead of OpenAI
```

---

## 🏗️ Architecture

```
ai-shorts-generator/
├── frontend/               # React + TypeScript + Electron
│   ├── src/
│   │   ├── pages/          # Dashboard, Generator, Templates, Batch, Settings
│   │   ├── components/     # Layout, GeneratorForm, VideoPreview, ...
│   │   ├── store/          # Zustand global state
│   │   ├── services/       # API client
│   │   └── hooks/          # WebSocket, React Query hooks
│   └── electron/           # Desktop app wrapper
│
├── backend/                # FastAPI Python backend
│   └── app/
│       ├── api/routes/     # REST API endpoints
│       ├── services/       # AI, Video, Voice, Subtitle services
│       └── models/         # Pydantic schemas
│
├── ai/                     # Standalone AI scripts (CLI)
├── video_engine/           # MoviePy + FFmpeg processing
├── subtitles/              # SRT/ASS generation + styles
├── audio/                  # Audio mixing + beat sync
└── templates/              # Video style JSON templates
```

### Render Pipeline

```
Topic → Script (GPT-4o) → Voice (OpenAI TTS / ElevenLabs)
     → B-Roll (Pexels/Pixabay) → Composite (FFmpeg)
     → Subtitles (Whisper + ASS) → Music Mix
     → Effects (Zoom, Punch, Transitions)
     → Export (H.264, 1080×1920, 9:16)
     → Thumbnail
```

---

## 📡 API Reference

| Method   | Endpoint                     | Description                      |
| -------- | ---------------------------- | -------------------------------- |
| `GET`    | `/api/health`                | Health check                     |
| `POST`   | `/api/ai/script`             | Generate video script            |
| `POST`   | `/api/ai/titles`             | Generate title variants          |
| `GET`    | `/api/projects`              | List all projects                |
| `POST`   | `/api/projects`              | Create project + generate script |
| `DELETE` | `/api/projects/{id}`         | Delete project                   |
| `POST`   | `/api/video/render/{id}`     | Start render job                 |
| `GET`    | `/api/video/status/{job_id}` | Poll render status               |
| `GET`    | `/api/export/download/{id}`  | Download MP4                     |
| `GET`    | `/api/export/thumbnail/{id}` | Get thumbnail                    |
| `GET`    | `/api/templates`             | List video templates             |

WebSocket: `ws://localhost:8000/ws/render` — real-time job updates

---

## 🎨 Video Styles

| Style            | Description                                           |
| ---------------- | ----------------------------------------------------- |
| **Hormozi**      | Bold black/white text, minimal design, business focus |
| **TikTok Story** | Colorful, fast-paced, personal storytelling           |
| **Finance**      | Clean data-driven look, investment content            |
| **Motivation**   | Fire subtitles, high energy, beat-synced cuts         |
| **Luxury**       | Cinematic, smooth, aspirational aesthetic             |
| **Documentary**  | Authoritative narration, clean subtitles              |

---

## 🐳 Docker

```bash
docker-compose up -d
```

Services: `backend` (port 8000), `redis` (port 6379), `worker` (Celery).

---

## 🖥️ Desktop App (Electron)

```bash
cd frontend
npm run electron:dev     # Development
npm run electron:build   # Build installer
```

Builds to `frontend/release/`. Supports Windows (.exe), macOS (.dmg), Linux (.AppImage).

---

## 📋 Requirements

### FFmpeg Installation

**Windows**: Download from [gyan.dev/ffmpeg/builds](https://www.gyan.dev/ffmpeg/builds/), extract to `C:\ffmpeg\`, add `C:\ffmpeg\bin` to PATH.

**macOS**: `brew install ffmpeg`

**Ubuntu/Debian**: `sudo apt install ffmpeg`

### GPU Acceleration (Optional)

For faster rendering with NVIDIA GPU, set `GPU_ACCELERATION=true` in `.env`. The system auto-detects `h264_nvenc`, `h264_videotoolbox` (Apple Silicon), and `h264_vaapi` (Linux).

---

## 📄 License

MIT License — free for personal and commercial use.

---

_Built with ❤️ using OpenAI, FastAPI, React, and FFmpeg._
