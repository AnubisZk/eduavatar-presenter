# Minimal FastAPI image for local Docker Compose development.
FROM python:3.12-slim

WORKDIR /app

# FFmpeg is required for lip-synced avatar clips and final MP4 rendering.
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg poppler-utils && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Railway provides PORT at runtime; default to 8000 for local Docker runs.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
