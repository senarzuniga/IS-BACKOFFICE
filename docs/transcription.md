# Audio Transcription — Usage

This module provides an API endpoint and a Streamlit panel to transcribe audio files using OpenAI Whisper and produce a concise summary (English/Spanish).

API endpoint (FastAPI)

- URL: `POST /audio/transcribe`
- Form parameters:
  - `file` (binary file): audio file (mp3, wav, m4a, mp4, ogg, flac, aac, wma)
  - `language` (string): `en` or `es` (default `en`)
  - `diarize` (boolean): request speaker/time mark post-processing (optional)
  - `save_to_assets` (boolean): when true, saves outputs to `assets/transcripts/` (optional)

Example curl (requires `OPENAI_API_KEY` in env):

```bash
curl -X POST "http://localhost:8000/audio/transcribe" \
  -F "file=@/path/to/audio.mp3" \
  -F "language=en" \
  -F "diarize=true" \
  -F "save_to_assets=true"
```

Streamlit UI

- Open the app and choose `Audio Transcription` from the sidebar.
- Upload an audio file, choose language (English/Spanish), enable diarization if desired, and click "Transcribe".
- Results: full transcript, summary (3–6 bullets), download buttons, and optional saving to `assets/transcripts/`.

Notes

- Ensure you set `OPENAI_API_KEY` (recommended) for high-quality Whisper transcriptions and LLM post-processing.
- The API and UI gracefully return errors when the key is missing to avoid surprises.
