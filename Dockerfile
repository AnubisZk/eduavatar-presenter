# Railway fallback Dockerfile when the repository root is deployed.
FROM python:3.12-slim

WORKDIR /app

# FFmpeg renders MP4 outputs; Poppler lets pdf2image convert PDF slides.
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg poppler-utils && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .

# Railway injects PORT; 8000 remains useful for local container testing.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
