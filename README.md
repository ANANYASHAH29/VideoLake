# LakeVideo

LakeVideo is a research prototype that curates hour-scale video datasets for foundation model training.

It ingests long videos (10–60 minutes), segments them into clips, computes multimodal embeddings, scores each clip on utility, removes semantic duplicates, and selects a compressed subset that preserves downstream value.

## Research Hypothesis

Not every video segment contributes equally to model performance. By selecting high-utility segments we can reduce dataset size while preserving downstream task accuracy.

## Tech Stack

- Python + FastAPI
- PostgreSQL + SQLAlchemy
- FAISS vector search
- PyTorch + Hugging Face Transformers (CLIP/BLIP)
- OpenCV + FFmpeg
- React + Tailwind CSS
- Docker + Docker Compose

## Fresh laptop setup (from zero)

Do these in order on a clean Windows machine. macOS/Linux equivalents are shown after each Windows step.

### 1. Git
- **Windows:** https://git-scm.com/download/win
- **Linux:** `sudo apt install git`
- **macOS:** `brew install git`

### 2. Python 3.11
- **Windows:** https://www.python.org/downloads/release/python-3119/  
  Run the installer and check **"Add Python to PATH"**.
- **Linux:** `sudo apt install python3.11 python3.11-pip`
- **macOS:** `brew install python@3.11`

### 3. Node.js 20 LTS
- **Windows:** https://nodejs.org/en/download/  
  Pick the **LTS** installer (it already includes `npm`).
- **Linux/macOS:** https://nodejs.org/en/download/package-manager

### 4. FFmpeg
- **Windows:** download from https://www.gyan.dev/ffmpeg/builds/  
  Extract to `C:\ffmpeg`, then add `C:\ffmpeg\bin` to your `PATH` in Environment Variables.
- **Linux:** `sudo apt install ffmpeg`
- **macOS:** `brew install ffmpeg`

### 5. Docker Desktop (optional but recommended)
- **Windows:** https://www.docker.com/products/docker-desktop/  
  Enable the WSL2 backend when prompted. This gives you `docker compose`.
- **Linux/macOS:** https://docs.docker.com/desktop/

### Verify everything
Open a **new** terminal and run:

```powershell
python --version      # 3.11.x
python -m pip --version
node --version        # v20.x
npm --version
git --version
ffmpeg -version
docker --version      # only if you installed Docker
```

### What gets installed automatically

- **Python packages** — FastAPI, Uvicorn, SQLAlchemy, FAISS, PyTorch, OpenCV, scikit-learn, `sentence-transformers`, `transformers`, etc. (see `backend/requirements.txt`)
- **Node packages** — React, Vite, Recharts, Tailwind CSS, etc. (see `frontend/package.json`)
- **ML model weights** — `clip-ViT-B-32` is downloaded from HuggingFace on the first backend start (~600 MB)

## Quick Start — Docker (recommended)

1. Clone the repository and enter the project folder:
   ```bash
   git clone <your-repo-url>
   cd lakevideo
   ```

2. Copy the environment file:
   ```bash
   cp .env.example .env
   # On Windows PowerShell:
   # Copy-Item .env.example .env
   ```

3. Start everything:
   ```bash
   docker compose up --build
   ```

4. Open the dashboard at `http://localhost:3000` and the API docs at `http://localhost:8000/docs`.

## Local Development — without Docker

### Backend

1. From the `lakevideo` folder, set environment variables and create data directories:
   ```bash
   # Linux / macOS
   export DATABASE_URL=sqlite+aiosqlite:///./data/lv.db
   export VIDEO_STORAGE=./data/videos
   export FAISS_INDEX_DIR=./data/faiss
   export MODEL_NAME=clip-ViT-B-32
   export DEVICE=cpu
   export PYTHONPATH=$(pwd)
   mkdir -p data/videos data/faiss
   ```

   ```powershell
   # Windows PowerShell
   $env:DATABASE_URL="sqlite+aiosqlite:///./data/lv.db"
   $env:VIDEO_STORAGE=".\data\videos"
   $env:FAISS_INDEX_DIR=".\data\faiss"
   $env:MODEL_NAME="clip-ViT-B-32"
   $env:DEVICE="cpu"
   $env:PYTHONPATH="$PWD"
   New-Item -ItemType Directory -Force -Path "data\videos","data\faiss" | Out-Null
   ```

2. Install dependencies and start the API:
   ```bash
   python -m pip install -r backend/requirements.txt
   python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
   ```

### Frontend

1. In a second terminal:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

2. Open the dashboard at the URL printed by Vite (usually `http://localhost:5173` or `http://localhost:3000`).

## Project Layout

```
lakevideo/
├── backend/          FastAPI services and workers
├── frontend/         React dashboard
├── research/         Baselines and evaluation scripts
├── docker/           Database init
└── docker-compose.yml
```

## Architecture Overview

1. **Video Ingestion** – upload videos and create processing jobs.
2. **Scene Segmentation** – detect scene changes and cut clips.
3. **Embedding Service** – extract CLIP frame/clip embeddings and store in FAISS.
4. **Utility Scoring Engine** – score each clip on diversity, novelty, caption alignment, motion, and visual quality.
5. **Semantic Deduplication** – cluster near-duplicate clips.
6. **Dataset Optimizer** – select high-utility clips at a target compression.
7. **Research Evaluation** – compare full, random, quality-only, dedup-only, and utility-based baselines.
8. **UI Dashboard** – monitor videos, scenes, scores, clusters, and reductions.

## API

- `POST /api/ingestion/upload` – upload a video.
- `POST /api/segmentation/{video_id}` – segment a video.
- `POST /api/embeddings/{video_id}` – embed scenes.
- `POST /api/utility/score/{video_id}` – score scenes.
- `POST /api/dedup/{video_id}` – run deduplication clustering.
- `POST /api/optimization` – select clips at a compression rate.
- `POST /api/research/evaluate/{video_id}` – run baseline comparison.
- `GET /api/dashboard/*` – aggregated dashboard data.

## Environment Variables

| Variable | Default | Purpose |
| --- | --- | --- |
| `DATABASE_URL` | `sqlite+aiosqlite:///./data/lv.db` | SQLAlchemy database URL |
| `VIDEO_STORAGE` | `./data/videos` | Where uploaded videos and clips are stored |
| `FAISS_INDEX_DIR` | `./data/faiss` | Directory for the FAISS index and vectors |
| `MODEL_NAME` | `clip-ViT-B-32` | CLIP/SentenceTransformer model to load |
| `DEVICE` | `cpu` | PyTorch device (`cpu` or `cuda`) |
| `BACKEND_PORT` | `8000` | FastAPI port |
| `FRONTEND_PORT` | `3000` | Nginx port when running in Docker |

## Notes

- The first backend start downloads `clip-ViT-B-32` from HuggingFace. This requires internet and may take several minutes.
- If `npm install` fails on a restricted/corporate machine, make sure `nodejs` can execute downloaded binaries (esbuild, etc.). On a clean unrestricted laptop this is not an issue.
- `docker compose up --build` is the fastest way to run the full stack without manually installing Python/Node dependencies.
