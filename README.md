# EduAvatar Presenter Studio

EduAvatar Presenter Studio is a consent-first full-stack web application for building educational avatar presentations. A user uploads an approved person image or short video, an approved voice sample, and a PDF or PPTX presentation, then writes a script, selects a target language, generates placeholder speech and avatar clips, previews the presentation, and exports a final MP4.

The project is designed for Erasmus+, VET, training, product demos, and promotional presentation workflows. Heavy AI models are intentionally not implemented yet; the backend exposes clean service interfaces that can later be connected to production TTS and avatar systems.

## Ethical Consent Warning

Before any upload, the user must confirm:

- I have permission to use this person's image/video.
- I have permission to use this person's voice.
- I understand that this avatar will be generated only for educational, presentation, or promotional purposes.
- I will not use this system for impersonation, fraud, political manipulation, or harmful content.

The backend stores the consent record as JSON in `backend/app/storage/uploads/{project_id}/consent.json` with the user name, UTC date/time, checkbox values, uploaded file names, and project id.

## Project Structure

```text
eduavatar-presenter/
  frontend/
    src/
      components/
      pages/
      services/
      App.jsx
      main.jsx
  backend/
    app/
      main.py
      routes/
      services/
      storage/
    requirements.txt
  README.md
  docker-compose.yml
```

## Requirements

- Python 3.11+
- Node.js 20+
- FFmpeg available on your system path
- Poppler recommended for full PDF conversion through `pdf2image`

On macOS, you can install media tools with:

```bash
brew install ffmpeg poppler
```

## Backend Setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

The API runs at `http://localhost:8000`.

Main endpoints:

- `POST /upload` accepts consent fields plus avatar, voice, and presentation files.
- `POST /presentation/script` divides a script into slide-based narration sections.
- `POST /voice/generate` creates placeholder audio files.
- `POST /avatar/generate` creates placeholder avatar clips.
- `POST /render/final` renders the final MP4 with FFmpeg.

## Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

The frontend runs at `http://localhost:5173` and communicates with `http://localhost:8000` by default. To change the API URL, set `VITE_API_BASE_URL`.

## Docker Compose

```bash
docker compose up --build
```

The compose setup runs the backend on port `8000` and the frontend on port `5173`.

## Placeholder Modules

The backend is modular by design:

- `backend/app/services/tts_service.py` contains `generate_voice(...)`.
- `backend/app/services/avatar_service.py` contains `generate_avatar_video(...)`.
- `backend/app/services/presentation_service.py` contains PDF/PPTX conversion helpers.
- `backend/app/services/video_service.py` contains FFmpeg final rendering.

Current placeholders:

- TTS generates silent WAV files with valid durations.
- Avatar generation creates simple MP4 clips from the source image or a generic video marker.
- PPTX processing extracts slide text and creates placeholder slide images.
- PDF processing uses `pdf2image` when Poppler is available and falls back to a placeholder slide.

## Future AI Integrations

Replace the placeholder services with consent-aware integrations such as:

- Voice: XTTS, OpenVoice, GPT-SoVITS, ElevenLabs
- Avatar video: MuseTalk, SadTalker, Wav2Lip
- Presentation conversion: LibreOffice or a cloud renderer for pixel-accurate PPTX slide images
- Translation: a dedicated translation API before TTS generation

## Future Roadmap

- Add authenticated users and project history.
- Add per-slide script editing and timing controls.
- Add model provider configuration screens.
- Add subtitle styling controls.
- Add multi-language batch exports.
- Add audit logs for consent and generated media.
- Add cloud storage for long-running render jobs.
