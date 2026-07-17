# EduAvatar Presenter Studio

EduAvatar Presenter Studio is a consent-first full-stack web application for building educational avatar presentations. A user uploads an approved person image or short video, an approved voice sample, and a PDF or PPTX presentation, then writes a script, selects a target language, generates natural narration and lip-synced avatar clips, previews the presentation, and exports a final MP4.

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
- `POST /voice/generate` creates natural narration with Edge TTS by default.
- `POST /avatar/generate` creates CPU-friendly moving, lip-synced avatar clips by default.
- `POST /render/final` renders the final MP4 with FFmpeg.

## Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

The frontend runs at `http://localhost:5173` and communicates with `http://localhost:8000` by default. To change the API URL, set `VITE_API_BASE_URL`.

## Production Deployment

The Netlify frontend needs a separately deployed backend for uploads, speech, avatar animation, and MP4 rendering:

1. Deploy the repository root to Railway with the included root `Dockerfile`.
2. Set `FRONTEND_ORIGINS=https://eduavatar-presenter.netlify.app` on Railway.
3. Set `VITE_API_BASE_URL=https://YOUR-BACKEND.up.railway.app` on Netlify.
4. Redeploy Netlify so Vite embeds the backend URL in the production build.

Generated media is stored on the backend filesystem. Use a Railway volume or object storage before relying on persistent project history.

## Docker Compose

```bash
docker compose up --build
```

The compose setup runs the backend on port `8000` and the frontend on port `5173`.

## Voice and Avatar Providers

The backend is modular by design:

- `backend/app/services/tts_service.py` contains `generate_voice(...)`.
- `backend/app/services/avatar_service.py` contains `generate_avatar_video(...)`.
- `backend/app/services/presentation_service.py` contains PDF/PPTX conversion helpers.
- `backend/app/services/video_service.py` contains FFmpeg final rendering.

The default voice provider is Edge TTS. It creates natural speech without an API key, but it uses an online service and does not clone the uploaded voice sample. The creation wizard can also select XTTS to synthesize every slide in the uploaded reference voice.

```bash
TTS_PROVIDER=edge
EDGE_TTS_VOICE=tr-TR-EmelNeural
EDGE_TTS_RATE=+0%
```

Use `TTS_PROVIDER=placeholder` only for offline pipeline tests; it generates silent WAV files.

### Uploaded Voice Cloning with XTTS

Use a 6-30 second WAV or MP3 recording with one speaker, clear speech, and little background noise. The application normalizes the upload to mono 24 kHz WAV and uses it as `speaker_wav` for every slide.

XTTS is optional because PyTorch must match the server's CPU or CUDA environment. Install PyTorch, `torchaudio`, and `torchcodec` when required by your PyTorch version, then install:

```bash
cd backend
pip install -r requirements-xtts.txt
```

Configuration:

```bash
TTS_PROVIDER=xtts
XTTS_DEVICE=cuda
XTTS_MODEL_NAME=tts_models/multilingual/multi-dataset/xtts_v2
```

The web UI can override the default provider per project. Review and accept the XTTS model license before setting any model-license acceptance environment variable. The model is loaded once per backend process and then reused for all slides.

CPU inference is supported but can be slow. For production presentations, a CUDA backend or a separate GPU worker is recommended; the normal Railway/Netlify frontend deployment does not itself provide GPU inference.

Presentation limitations:

- PPTX processing extracts slide text and creates representative slide images rather than pixel-accurate PowerPoint renders.
- PDF processing uses `pdf2image` when Poppler is available and falls back to a placeholder slide.

## Avatar Provider Configuration

Avatar generation is provider-based. The default is a CPU-friendly local animation:

```bash
AVATAR_PROVIDER=animated
```

Available provider names:

- `animated` / `animated_2d`: audio-amplitude lip movement and subtle head motion; no GPU required.
- `placeholder`: static avatar card video, works with FFmpeg.
- `wav2lip`: local Wav2Lip CLI integration.
- `sadtalker`: local SadTalker CLI integration for more realistic facial motion.
- `musetalk`: scaffold for future MuseTalk integration.
- `api`: scaffold for a future remote GPU worker or avatar API.

### SadTalker

Install SadTalker and its model checkpoints separately, then point the backend to the checkout:

```bash
AVATAR_PROVIDER=sadtalker
SADTALKER_HOME=/path/to/SadTalker
SADTALKER_PYTHON=/path/to/sadtalker/python
SADTALKER_PREPROCESS=crop
SADTALKER_EXPRESSION_SCALE=1.0
SADTALKER_STILL=true
```

Set `SADTALKER_ENHANCER=gfpgan` when the enhancer and its weights are installed.

### Wav2Lip

Install Wav2Lip and download its checkpoint separately:

```bash
AVATAR_PROVIDER=wav2lip
WAV2LIP_HOME=/path/to/Wav2Lip
WAV2LIP_CHECKPOINT=/path/to/wav2lip_gan.pth
WAV2LIP_PYTHON=/path/to/wav2lip/python
```

For a remote GPU worker later, configure:

```bash
AVATAR_PROVIDER=api
AVATAR_API_URL=https://your-avatar-worker.example.com
```

The provider contract is:

```python
generate(project_id, avatar_source_path, audio_path) -> {
  "path": "...",
  "url": "...",
  "duration_seconds": 5.0,
  "provider": "..."
}
```

## Future AI Integrations

Additional consent-aware integrations can include:

- Voice: OpenVoice, GPT-SoVITS, ElevenLabs
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
