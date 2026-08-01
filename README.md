# AudioExtract

Extract audio from any video file — upload, process, download. Built with Django, DRF, PostgreSQL, and React.

## Vercel Deployed Front-End https://audioextract-red.vercel.app/

## How it works

1. User picks a video file in the React frontend
2. **ffmpeg.wasm runs in the browser** to extract the audio track as a 16 kHz mono WAV — no server CPU used for decoding
3. The browser uploads the original video + extracted WAV to Django (falls back to server-side extraction if wasm is unavailable)
4. Django sends the audio to Sarvam AI's speech-to-text API, builds an SRT, and burns the captions into the video with ffmpeg
5. User downloads the captioned video, SRT, or audio

## Tech Stack

**Backend**
- Django + Django REST Framework — API and file handling
- PostgreSQL — stores video/audio records
- ffmpeg — server-side caption burning + audio fallback
- Sarvam AI — speech-to-text API
- Backblaze B2 — file hosting
- uv — Python package management

**Frontend**
- React + Vite
- ffmpeg.wasm — client-side audio extraction (WebAssembly)
- Axios — HTTP requests and file upload
- Tailwind CSS

**Infrastructure**
- Docker Compose — orchestrates Django + PostgreSQL services

## Project Structure

```
backend/
├── core/               # Django project settings, urls
├── extract/            # App: models, views, serializers, processor
│   ├── models.py       # Video model with video_file and audio_file fields
│   ├── views.py        # Upload, status, and download endpoints
│   ├── serializers.py  # DRF serializer for Video model
│   ├── processor.py    # Orchestrates extraction/transcription/caption burning
│   └── tasks.py        # Legacy Celery task (unused)
├── Dockerfile
├── docker-compose.yml
└── pyproject.toml

frontend/
├── src/
│   ├── App.jsx         # Single page: upload form + download link
│   └── ffmpeg.js       # ffmpeg.wasm loader + in-browser audio extraction
└── vite.config.js
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/upload/` | Upload video (+ optional pre-extracted `audio_file` WAV), returns the processed result |
| GET | `/api/status/<id>/` | Returns `processing` or `done` with `audio_url` |
| GET | `/api/download/<id>/` | Force-downloads the extracted audio |

## Getting Started

**Prerequisites:** Docker and Docker Compose installed.

1. Clone the repo

```bash
git clone https://github.com/yourusername/audioextract
cd audioextract/backend
```

2. Create `.env` file

```env
POSTGRES_DB=audioextract
POSTGRES_USER=youruser
POSTGRES_PASSWORD=yourpassword
POSTGRES_HOST=postgresql
POSTGRES_PORT=5432
```

3. Start all services

```bash
docker compose up --build
```

Django runs on `http://localhost:8000`, React dev server on `http://localhost:5173`.

4. Run the frontend

```bash
cd frontend
npm install
npm run dev
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `POSTGRES_DB` | PostgreSQL database name |
| `POSTGRES_USER` | PostgreSQL username |
| `POSTGRES_PASSWORD` | PostgreSQL password |
| `POSTGRES_HOST` | PostgreSQL host (service name in compose) |
| `POSTGRES_PORT` | PostgreSQL port |
| `VITE_API_URL` | Backend API base URL for the React app |

## Notes

- ffmpeg.wasm extracts the audio as a 16 kHz mono WAV in the browser; the backend skips its own extraction when the WAV is uploaded
- If ffmpeg.wasm fails to load (old browser, unsupported container), the frontend falls back to uploading the video only and the server extracts audio as before
- The original video is still uploaded — it's required to burn captions into it server-side
- Caption burning is done server-side with ffmpeg's `subtitles` filter
- Postgres 16 is pinned intentionally — Postgres 18 changed the data directory layout
