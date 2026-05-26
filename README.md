# AudioExtract

Extract audio from any video file — upload, process, download. Built with Django, Celery, Redis, PostgreSQL, and React.

## Vercel Deployed Front-End https://audioextract-red.vercel.app/

## How it works

1. User uploads a video file via the React frontend
2. Django saves the file and queues a Celery task
3. Celery runs ffmpeg to extract audio as MP3
4. User polls for status and downloads the result

## Tech Stack

**Backend**
- Django + Django REST Framework — API and file handling
- Celery — async task queue for ffmpeg processing
- Redis — message broker between Django and Celery
- PostgreSQL — stores video/audio records
- ffmpeg — audio extraction
- uv — Python package management

**Frontend**
- React + Vite
- Axios — HTTP requests and file upload with progress
- Polling — checks task status every 3 seconds

**Infrastructure**
- Docker Compose — orchestrates all services
- Named volumes — shared media between Django and Celery containers

## Project Structure

```
backend/
├── core/               # Django project settings, urls, celery config
├── extract/            # App: models, views, serializers, tasks
│   ├── models.py       # Video model with video_file and audio_file fields
│   ├── views.py        # Upload, status, and download endpoints
│   ├── serializers.py  # DRF serializer for Video model
│   └── tasks.py        # Celery task that runs ffmpeg
├── Dockerfile
├── docker-compose.yml
└── pyproject.toml

frontend/
├── src/
│   └── App.jsx         # Single page: upload form + download link
└── vite.config.js
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/upload/` | Upload video file, returns `id` |
| GET | `/api/status/<id>/` | Returns `processing` or `done` with `audio_url` |
| GET | `/api/download/<id>/` | Force-downloads the extracted MP3 |

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

- ffmpeg re-encodes audio to MP3 using `libmp3lame` regardless of source codec
- Media files are shared between Django and Celery via a named Docker volume
- Postgres 16 is pinned intentionally — Postgres 18 changed the data directory layout
