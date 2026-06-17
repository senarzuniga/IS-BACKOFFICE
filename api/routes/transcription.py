"""Audio transcription API routes.

Provides a simple endpoint to upload audio and receive a transcription
and summary. The route gracefully returns an informative error when
`OPENAI_API_KEY` is not configured to avoid surprising failures.
"""
from __future__ import annotations

import os
import tempfile
from typing import Optional

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse

from backoffice.agents.transcription_agent import TranscriptionAgent

router = APIRouter(prefix="/audio", tags=["audio"])


@router.post("/transcribe")
async def transcribe_audio(
    file: UploadFile = File(...),
    language: str = Form("en"),
    diarize: bool = Form(False),
    save_to_assets: bool = Form(False),
) -> JSONResponse:
    """Accept an audio file and return transcription + summary.

    - `language`: "en" or "es"
    - `diarize`: whether to request speaker/time mark post-processing
    - `save_to_assets`: save outputs to `assets/transcripts/`
    """

    # Early guard: OpenAI key required for transcription
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        raise HTTPException(status_code=503, detail="OPENAI_API_KEY not configured; transcription disabled")

    # Validate content type / filename
    fname = (file.filename or "upload").strip()
    ext = fname.rsplit('.', 1)[-1].lower() if '.' in fname else ''
    allowed = {"mp3", "wav", "m4a", "mp4", "ogg", "flac", "aac", "wma"}
    if ext and ext not in allowed:
        raise HTTPException(status_code=400, detail=f"Unsupported audio extension: .{ext}")

    # Save to a temporary file
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = f"{tmpdir}/{fname}"
        with open(tmp_path, "wb") as out:
            out.write(await file.read())

        agent = TranscriptionAgent(openai_api_key=key)
        try:
            resp = agent.transcribe_file(tmp_path, language=language)
        except Exception as exc:
            # Return 503 to indicate the external transcription service is unavailable
            raise HTTPException(status_code=503, detail=f"Transcription failed: {exc}")

        raw_text = resp.get("text") or ""

        # Summarise using the agent (non-blocking enough for modest audio)
        try:
            summary = agent.summarise_text(raw_text, language=language)
        except Exception:
            summary = None

        result = {
            "filename": fname,
            "language": language,
            "transcription": raw_text,
            "summary": summary,
            "raw_response": None,
        }

        # Optionally save outputs
        if save_to_assets:
            try:
                os.makedirs(os.path.join("assets", "transcripts"), exist_ok=True)
                base = fname.rsplit('.', 1)[0]
                ts = base + "_transcription.txt"
                sm = base + "_summary.md"
                with open(os.path.join("assets", "transcripts", ts), "w", encoding="utf-8") as f:
                    f.write(raw_text or "")
                if summary:
                    with open(os.path.join("assets", "transcripts", sm), "w", encoding="utf-8") as f:
                        f.write(summary or "")
                result["saved_to"] = f"assets/transcripts/{ts}, assets/transcripts/{sm}"
            except Exception as exc:
                result["save_error"] = str(exc)

        # Include raw API response when available (for debugging)
        if resp.get("raw") is not None:
            try:
                result["raw_response"] = resp.get("raw")
            except Exception:
                result["raw_response"] = None

        return JSONResponse(status_code=200, content=result)
