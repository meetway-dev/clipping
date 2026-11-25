import os
import sys

# Compatibility patch for PyAV 19+ with faster-whisper
try:
    import av
    _orig_av_open = av.open
    def _safe_av_open(*args, **kwargs):
        kwargs.pop("metadata_errors", None)
        return _orig_av_open(*args, **kwargs)
    av.open = _safe_av_open
except Exception:
    pass

import uuid
import shutil
import threading
import asyncio
import io
import re
import zipfile
import json
import time
import math
import subprocess
import cv2
from pathlib import Path
from typing import Dict, Any, Optional, List

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks, Body
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse, Response, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from starlette.concurrency import run_in_threadpool

from core.config import BASE_DIR, UPLOADS_DIR, OUTPUTS_DIR, TEMP_DIR, FFMPEG_PATH, DEFAULT_CONFIG
from core.pipeline import ClipForgePipeline, sanitize_topic_filename
from core.viral_detector import ViralDetector
from core.youtube_downloader import YouTubeDownloader
from core.history_manager import HistoryManager
from core.bgm_manager import BGMManager
from core.subtitles import SubtitleGenerator
from core.renderer import VideoRenderer
from core.face_tracker import SmartFaceTracker
from core.ollama_manager import OllamaManager
from core.gdrive_manager import GoogleDriveManager
from core.docs_generator import (
    add_session_docs_to_zip,
    generate_session_docx,
    generate_session_text,
    generate_session_markdown,
    generate_clip_docx,
    generate_clip_text,
    generate_clip_markdown,
    create_clip_docs_files
)
from core.thumbnail_designer import TikTokThumbnailDesigner
from core.ai_engine import AIEngineError, MultiModelAIEngine, PROCESSING_MODES

# Initialize FastAPI Application
app = FastAPI(title="ClipForge AI Studio", version="1.1.0")

@app.on_event("startup")
async def startup_event():
    """Check local AI availability without starting hidden Ollama processes."""
    def _bg_check():
        try:
            status = MultiModelAIEngine.get_instance().get_status()
            print(
                f"[Ollama] Startup check: {status.get('active_model') or 'no assigned model available'} "
                f"(connected: {status.get('connected')})"
            )
        except Exception as e:
            print(f"[Ollama] Startup check notice: {e}")
    threading.Thread(target=_bg_check, daemon=True).start()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Static Directories
STATIC_DIR = BASE_DIR / "web" / "static"
TEMPLATES_DIR = BASE_DIR / "web" / "templates"
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# In-Memory Jobs Tracker
JOBS: Dict[str, Dict[str, Any]] = {}
EDITOR_RENDER_JOBS: Dict[str, Dict[str, Any]] = {}
EDITOR_RENDER_JOBS_LOCK = threading.Lock()


def _set_editor_render_progress(job_id: Optional[str], progress: float, stage: str, detail: str = ""):
    if not job_id:
        return
    with EDITOR_RENDER_JOBS_LOCK:
        job = EDITOR_RENDER_JOBS.get(job_id)
        if job and job["status"] == "running":
            progress = max(progress, job.get("progress", 0))
            job.update({
                "progress": max(0, min(100, round(progress, 1))),
                "stage": stage,
                "detail": detail
            })


def _run_editor_render_job(job_id: str, project_id: str, payload: Dict[str, Any]):
    try:
        with EDITOR_RENDER_JOBS_LOCK:
            EDITOR_RENDER_JOBS[job_id].update({
                "status": "running",
                "stage": "Preparing render",
                "detail": "Checking project and source video",
                "progress": 2
            })
        result = asyncio.run(apply_timeline_edits(project_id, payload))
        with EDITOR_RENDER_JOBS_LOCK:
            EDITOR_RENDER_JOBS[job_id].update({
                "status": "completed",
                "progress": 100,
                "stage": "Complete",
                "detail": f"Rendered {len(result.get('clips', []))} clips successfully",
                "result": {"status": result.get("status")}
            })
    except HTTPException as exc:
        error = exc.detail if isinstance(exc.detail, str) else json.dumps(exc.detail, ensure_ascii=False)
        with EDITOR_RENDER_JOBS_LOCK:
            EDITOR_RENDER_JOBS[job_id].update({
                "status": "failed",
                "stage": "Render failed",
                "detail": error,
                "error": error
            })
    except Exception as exc:
        print(f"[Editor Render Job {job_id}] {type(exc).__name__}: {exc}")
        with EDITOR_RENDER_JOBS_LOCK:
            EDITOR_RENDER_JOBS[job_id].update({
                "status": "failed",
                "stage": "Render failed",
                "detail": str(exc) or type(exc).__name__,
                "error": f"{type(exc).__name__}: {exc}"
            })


def _run_custom_extract_job(job_id: str, payload: Dict[str, Any]):
    try:
        with EDITOR_RENDER_JOBS_LOCK:
            EDITOR_RENDER_JOBS[job_id].update({
                "status": "running",
                "stage": "Preparing chapter",
                "detail": "Checking project and source video",
                "progress": 2
            })
        result = asyncio.run(extract_custom_clip(payload))
        clip = result.get("clip") or {}
        with EDITOR_RENDER_JOBS_LOCK:
            EDITOR_RENDER_JOBS[job_id].update({
                "status": "completed",
                "progress": 100,
                "stage": "Chapter clip ready",
                "detail": f'Added "{clip.get("title", "Chapter clip")}" to the project',
                "result": {"status": result.get("status"), "clip_id": clip.get("id")}
            })
    except HTTPException as exc:
        error = exc.detail if isinstance(exc.detail, str) else json.dumps(exc.detail, ensure_ascii=False)
        with EDITOR_RENDER_JOBS_LOCK:
            EDITOR_RENDER_JOBS[job_id].update({
                "status": "failed",
                "stage": "Chapter extraction failed",
                "detail": error,
                "error": error
            })
    except Exception as exc:
        print(f"[Chapter Extract Job {job_id}] {type(exc).__name__}: {exc}")
        with EDITOR_RENDER_JOBS_LOCK:
            EDITOR_RENDER_JOBS[job_id].update({
                "status": "failed",
                "stage": "Chapter extraction failed",
                "detail": str(exc) or type(exc).__name__,
                "error": f"{type(exc).__name__}: {exc}"
            })


def _public_editor_render_job(job: Dict[str, Any]) -> Dict[str, Any]:
    result = job.get("result")
    return {
        "job_id": job["job_id"],
        "project_id": job["project_id"],
        "kind": job.get("kind", "timeline_render"),
        "status": job["status"],
        "progress": job["progress"],
        "stage": job["stage"],
        "detail": job.get("detail", ""),
        "error": job.get("error"),
        "result": result
    }

class YouTubeInfoRequest(BaseModel):
    url: str

@app.get("/", response_class=HTMLResponse)
@app.get("/app", response_class=HTMLResponse)
@app.get("/app/{rest:path}", response_class=HTMLResponse)
async def serve_index(rest: Optional[str] = None):
    index_file = TEMPLATES_DIR / "index.html"
    if not index_file.exists():
        raise HTTPException(status_code=404, detail="Template not found")
    return HTMLResponse(
        content=index_file.read_text(encoding="utf-8"),
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        }
    )

@app.get("/brand/{name}")
async def serve_brand_asset(name: str):
    p = STATIC_DIR / "brand" / name
    if p.exists():
        return FileResponse(p)
    raise HTTPException(status_code=404, detail="Brand asset not found")

@app.get("/assets/{name}")
async def serve_static_asset(name: str):
    p = STATIC_DIR / name
    if p.exists():
        return FileResponse(p)
    raise HTTPException(status_code=404, detail="Asset not found")

@app.get("/api/status")
async def get_peakcut_status():
    ollama = OllamaManager.get_instance()
    st = ollama.get_status()
    return {
        "user": {"name": "Studio Director", "role": "admin", "is_admin": True},
        "ai": {
            "ready": st.get("connected", False) and st.get("configured_primary_available", False),
            "connected": st.get("connected", False),
            "provider": "Ollama (on this machine)",
            "model": st.get("configured_primary"),
            "models": st.get("available_models", []),
            "model_assignments": st.get("model_assignments", {}),
            "processing_mode": st.get("processing_mode", "balanced"),
            "base_url": st.get("url"),
            "error": st.get("error"),
            "hardware": st.get("hardware", {}),
            "missing_assignments": st.get("missing_assignments", {}),
        },
        "styles": {
            "bounce": "Hormozi (Bounce)",
            "hype": "MrBeast (Hype)",
            "clean": "Modern Clean",
            "cyber": "Cyber Neon"
        },
        "layouts": {
            "blur": "Blurred fill",
            "crop": "Fill screen",
            "split": "Split screen (Host/Guest)",
            "gameplay": "Active speaker tracking"
        },
        "speech": {
            "en": {"label": "English", "state": "ready", "size_mb": 480}
        },
        "no_ffmpeg": False
    }

@app.get("/api/sync")
async def sync_peakcut_data():
    ollama = OllamaManager.get_instance()
    st = ollama.get_status()
    projects = HistoryManager.get_all_projects()

    formatted_jobs = []
    # Add active in-memory running or failed jobs first
    for jid, job in JOBS.items():
        if job.get("status") in ("queued", "running"):
            formatted_jobs.append({
                "id": jid,
                "title": job.get("options", {}).get("original_title", "Processing Video"),
                "duration": 0,
                "thumbnail_url": "",
                "status": job.get("status", "running"),
                "stage": job.get("status_message", "Processing..."),
                "progress": (job.get("progress", 0) / 100.0),
                "step_index": job.get("step_index", 1),
                "step_name": job.get("step_name", "Transcribe"),
                "step_detail": job.get("step_detail", job.get("status_message", "")),
                "clips": []
            })
        elif job.get("status") == "failed":
            formatted_jobs.append({
                "id": jid,
                "title": job.get("options", {}).get("original_title", "Video Clipping Failed"),
                "duration": 0,
                "thumbnail_url": "",
                "status": "failed",
                "stage": job.get("status_message") or job.get("error") or "Failed to process video",
                "progress": 0,
                "error": job.get("error", "Error processing video"),
                "clips": []
            })

    # Add finished projects from persistent DB
    for p in projects:
        if any(fj["id"] == p["id"] for fj in formatted_jobs):
            continue

        clips_formatted = []
        for c in p.get("clips", []):
            fn = c.get("filename", "")
            cover_name = c.get("cover") or (Path(fn).with_suffix(".jpg").name if fn else "")
            covers = c.get("covers") or ([cover_name] if cover_name else [])
            folder_name = c.get("folder_name") or ""
            clips_formatted.append({
                "id": c.get("id"),
                "project_id": p.get("id"),
                "filename": fn,
                "cover": cover_name,
                "covers": covers,
                "folder_name": folder_name,
                "title": c.get("title", ""),
                "hook": c.get("hook", ""),
                "virality_score": c.get("virality_score", 90),
                "score": c.get("virality_score", 90),
                "start": c.get("start_sec", 0),
                "end": c.get("end_sec", 30),
                "duration": c.get("duration", 30),
                "status": "done",
                "subtitle_style": c.get("subtitle_style", "hormozi"),
                "layout_mode": c.get("layout_mode", "speaker_focus"),
                "top_padding": float(c.get("top_padding") or 0.0),
                "bottom_padding": float(c.get("bottom_padding") or 0.0),
                "words": c.get("words", []),
                "model_provenance": c.get("model_provenance"),
                "social_kit": c.get("social_kit", {}),
                "output_file": str(OUTPUTS_DIR / fn) if fn else ""
            })

        formatted_jobs.append({
            "id": p.get("id"),
            "title": p.get("title", "Podcast Episode"),
            "duration": p.get("duration", 0),
            "thumbnail_url": p.get("thumbnail_url", ""),
            "status": "done",
            "stage": "Finished",
            "progress": 1.0,
            "clips": clips_formatted,
            "podcast_summary": p.get("podcast_summary"),
            "transcript_segments": p.get("transcript_segments")
        })

    return {
        "v": str(int(time.time())),
        "jobs": formatted_jobs,
        "creators": [{"id": "all", "name": "Main Studio", "channel": ""}],
        "accounts": [],
        "ai": {
            "ready": st.get("connected", False) and st.get("configured_primary_available", False),
            "connected": st.get("connected", False),
            "provider": "Ollama (on this machine)",
            "model": st.get("configured_primary"),
            "models": st.get("available_models", []),
            "model_assignments": st.get("model_assignments", {}),
            "processing_mode": st.get("processing_mode", "balanced"),
            "base_url": st.get("url"),
            "error": st.get("error"),
            "hardware": st.get("hardware", {}),
            "missing_assignments": st.get("missing_assignments", {}),
        }
    }

@app.get("/api/preview")
async def preview_video_link(url: str):
    url = url.strip()
    if not url:
        raise HTTPException(status_code=400, detail="URL is required")
    try:
        info = YouTubeDownloader.get_info(url)
        return {
            "title": info.get("title", "Video"),
            "uploader": info.get("channel", "YouTube"),
            "duration": info.get("duration", 0),
            "thumb": info.get("thumbnail", "")
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

def _resolve_video_source(source: Optional[str]) -> Optional[Path]:
    """Helper to resolve a video source path from ID, filename, or candidate pool."""
    if source and source.strip():
        s = source.strip()
        p = Path(s)
        if p.exists() and p.is_file():
            return p
        # Check project ID
        proj = HistoryManager.get_project_by_id(s)
        if proj and proj.get("source_video"):
            project_source = Path(proj["source_video"])
            if project_source.is_file():
                return project_source
        # Check directory candidates
        for v_dir in [UPLOADS_DIR, TEMP_DIR, OUTPUTS_DIR]:
            candidate = v_dir / s
            if candidate.exists() and candidate.is_file():
                return candidate
            if not s.lower().endswith(".mp4"):
                cand_mp4 = v_dir / f"{s}.mp4"
                if cand_mp4.exists() and cand_mp4.is_file():
                    return cand_mp4
        for v_dir in [UPLOADS_DIR, TEMP_DIR, OUTPUTS_DIR]:
            project_matches = list(v_dir.glob(f"*{s[:8]}*.mp4"))
            for match in project_matches:
                if match.is_file():
                    return match

    # Fallback to any available video in uploads or temp
    for v_dir in [UPLOADS_DIR, TEMP_DIR]:
        all_vids = list(v_dir.glob("*.mp4"))
        if all_vids:
            all_vids.sort(key=lambda f: f.stat().st_mtime, reverse=True)
            return all_vids[0]
    return None

@app.post("/api/preview/upload_draft")
async def upload_draft_video(file: UploadFile = File(...)):
    """Uploads a draft video file or snippet to generate instant server layout previews."""
    try:
        suffix = Path(file.filename).suffix or ".mp4"
        draft_name = f"draft_{int(time.time())}{suffix}"
        draft_path = TEMP_DIR / draft_name
        draft_path.parent.mkdir(parents=True, exist_ok=True)
        with open(draft_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        cap = cv2.VideoCapture(str(draft_path))
        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or 1920
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) or 1080
        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        frames = cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0
        dur = round(frames / fps, 2) if fps > 0 else 0.0
        cap.release()

        return {
            "status": "success",
            "draft_name": draft_name,
            "width": w,
            "height": h,
            "duration": dur,
            "url": f"/media/temp/{draft_name}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/preview/layout_frame")
async def preview_layout_frame(
    source: Optional[str] = None,
    time_sec: float = 5.0,
    layout: str = "speaker_focus",
    top_padding: float = 0.0,
    bottom_padding: float = 0.0,
    canvas_bg: str = "solid_black",
    banner_text: Optional[str] = None,
    show_banner: bool = True,
    subtitle_style: str = "hormozi",
    caption_text: Optional[str] = None,
    show_caption: bool = True
):
    """
    Renders an exact, real pixel-perfect 1080x1920 preview frame showing the 9:16 TikTok layout,
    safe area top/bottom padding, active video framing, topic headline banner, and kinetic subtitles.
    """
    v_path = _resolve_video_source(source)
    if not v_path or not v_path.exists():
        raise HTTPException(status_code=404, detail="No video source found for preview.")

    top_padding = max(0.0, min(45.0, float(top_padding)))
    bottom_padding = max(0.0, min(45.0, float(bottom_padding)))
    top_pct = top_padding / 100.0
    bottom_pct = bottom_padding / 100.0
    if top_pct + bottom_pct > 0.80:
        scale_pad = 0.80 / (top_pct + bottom_pct)
        top_pct *= scale_pad
        bottom_pct *= scale_pad
    top_pad_px = int(round(1920 * top_pct))
    bottom_pad_px = int(round(1920 * bottom_pct))
    available_h = max(100, 1920 - top_pad_px - bottom_pad_px)

    tracker = SmartFaceTracker()
    crop_filter, actual_layout = tracker.build_layout_filter(
        video_path=str(v_path),
        start_sec=time_sec,
        duration=2.0,
        layout_mode=layout,
        top_padding=top_padding,
        bottom_padding=bottom_padding,
        canvas_bg=canvas_bg,
        target_w=1080,
        target_h=1920,
        enable_hook_zoom=False
    )

    filter_args = []
    ass_path = None
    if show_banner or show_caption:
        ass_path = TEMP_DIR / f"prev_{uuid.uuid4().hex[:8]}.ass"
        headline_title = banner_text if (banner_text and banner_text.strip()) else "THE REAL REASON 99% OF PEOPLE FAIL AT THIS HABIT"
        cap_words = []
        if show_caption:
            sample_phrase = caption_text if (caption_text and caption_text.strip()) else "STOP SCROLLING AND LISTEN"
            for w in sample_phrase.split():
                cap_words.append({"word": w, "start": time_sec, "end": time_sec + 2.0})

        SubtitleGenerator.create_ass_file(
            words=cap_words,
            output_path=ass_path,
            style_key=subtitle_style,
            words_per_batch=3,
            clip_start_offset=time_sec,
            clip_duration=2.0,
            topic_headline=headline_title if show_banner else "",
            show_headline_banner=show_banner,
            enable_auto_emojis=True,
            layout_mode=actual_layout,
            top_padding=top_padding,
            bottom_padding=bottom_padding
        )

        safe_ass = Path(ass_path).resolve().as_posix().replace(":", r"\:")
        if "[outv]" in crop_filter:
            full_filter = crop_filter.replace("[outv]", f"[base];[base]ass='{safe_ass}'[outv]")
            filter_args = ["-filter_complex", full_filter, "-map", "[outv]"]
        else:
            full_filter = f"{crop_filter},ass='{safe_ass}'"
            filter_args = ["-vf", full_filter]
    else:
        if "[outv]" in crop_filter:
            filter_args = ["-filter_complex", crop_filter, "-map", "[outv]"]
        else:
            filter_args = ["-vf", crop_filter]

    out_jpg = TEMP_DIR / f"frame_{uuid.uuid4().hex[:8]}.jpg"
    cmd = [
        FFMPEG_PATH, "-y",
        "-ss", f"{time_sec:.3f}",
        "-i", str(v_path),
        "-vframes", "1",
        *filter_args,
        "-f", "image2",
        "-c:v", "mjpeg",
        "-q:v", "2",
        str(out_jpg)
    ]
    try:
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=8)
        if res.returncode != 0 or not out_jpg.exists():
            print(f"[Preview Frame Error] FFmpeg stderr: {res.stderr[:400]}")
            raise HTTPException(status_code=500, detail="Failed to render preview frame.")

        data = out_jpg.read_bytes()
        try:
            out_jpg.unlink(missing_ok=True)
            if ass_path and ass_path.exists():
                ass_path.unlink(missing_ok=True)
        except Exception:
            pass
        return Response(content=data, media_type="image/jpeg")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/preview/layout_info")
async def preview_layout_info(
    source: Optional[str] = None,
    time_sec: float = 5.0,
    layout: str = "speaker_focus",
    top_padding: float = 0.0,
    bottom_padding: float = 0.0
):
    """
    Returns layout telemetry: active dimensions, crop size, zoom factor,
    percentage of 16:9 view preserved, and detected faces from YuNet DNN.
    """
    v_path = _resolve_video_source(source)
    orig_w, orig_h = 1920, 1080
    duration = 60.0
    detected_faces = []
    if v_path and v_path.exists():
        try:
            cap = cv2.VideoCapture(str(v_path))
            orig_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or 1920
            orig_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) or 1080
            fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
            total_f = cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0
            duration = round(total_f / fps, 2) if fps > 0 else 60.0

            target_frame_idx = int(max(0, time_sec * fps))
            cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame_idx)
            ret, frame = cap.read()
            if ret and frame is not None:
                tracker = SmartFaceTracker()
                faces = tracker.detect_faces(frame)
                detected_faces = faces
            cap.release()
        except Exception:
            pass

    top_padding = max(0.0, min(45.0, float(top_padding)))
    bottom_padding = max(0.0, min(45.0, float(bottom_padding)))
    top_pct = top_padding / 100.0
    bottom_pct = bottom_padding / 100.0
    if top_pct + bottom_pct > 0.80:
        scale_pad = 0.80 / (top_pct + bottom_pct)
        top_pct *= scale_pad
        bottom_pct *= scale_pad
    top_pad_px = int(round(1920 * top_pct))
    bottom_pad_px = int(round(1920 * bottom_pct))
    available_h = max(100, 1920 - top_pad_px - bottom_pad_px)
    active_area_pct = round((available_h / 1920.0) * 100, 1)

    center_ar = 1080 / float(available_h)
    if (orig_w / float(orig_h)) >= center_ar:
        crop_h = orig_h if orig_h % 2 == 0 else orig_h - 1
        crop_w = int(round(crop_h * center_ar))
        if crop_w % 2 != 0: crop_w -= 1
        if crop_w > orig_w: crop_w = orig_w if orig_w % 2 == 0 else orig_w - 1
    else:
        crop_w = orig_w if orig_w % 2 == 0 else orig_w - 1
        crop_h = int(round(crop_w / center_ar))
        if crop_h % 2 != 0: crop_h -= 1
        if crop_h > orig_h: crop_h = orig_h if orig_h % 2 == 0 else orig_h - 1

    fov_preserved_pct = round((crop_w / float(orig_w)) * 100, 1) if orig_w > 0 else 50.0
    std_9_16_w = int(round(orig_h * (9.0 / 16.0)))
    std_fov_pct = round((std_9_16_w / float(orig_w)) * 100, 1) if orig_w > 0 else 31.6
    zoom_gain_pct = round(((crop_w - std_9_16_w) / float(std_9_16_w)) * 100, 1) if std_9_16_w > 0 else 0.0

    return {
        "status": "success",
        "video": {
            "source": str(v_path) if v_path else "",
            "width": orig_w,
            "height": orig_h,
            "duration": duration
        },
        "canvas": {
            "target_w": 1080,
            "target_h": 1920,
            "top_pad_px": top_pad_px,
            "bottom_pad_px": bottom_pad_px,
            "available_h": available_h,
            "active_area_pct": active_area_pct,
            "top_padding_pct": round(top_pct * 100, 1),
            "bottom_padding_pct": round(bottom_pct * 100, 1)
        },
        "crop": {
            "crop_w": crop_w,
            "crop_h": crop_h,
            "aspect_ratio": round(crop_w / float(max(1, crop_h)), 3),
            "fov_preserved_pct": fov_preserved_pct,
            "std_9_16_fov_pct": std_fov_pct,
            "more_content_pct": zoom_gain_pct
        },
        "faces": detected_faces,
        "layout_mode": layout
    }

@app.get("/media/{name}")
async def serve_flat_media(name: str):
    """Serve a file directly from a flat output/temporary directory."""
    if "/" in name or "\\" in name:
        raise HTTPException(status_code=400, detail="Invalid media filename")

    for directory in [OUTPUTS_DIR, TEMP_DIR, UPLOADS_DIR]:
        candidate = directory / name
        if candidate.is_file():
            if candidate.suffix.lower() in (".jpg", ".jpeg", ".png"):
                return FileResponse(candidate, media_type="image/jpeg")
            if candidate.suffix.lower() in (".mp4", ".webm", ".mov"):
                return FileResponse(candidate, media_type="video/mp4")
            return FileResponse(candidate)

    raise HTTPException(status_code=404, detail="Media file not found")


@app.get("/media/{jid}/{name:path}")
async def serve_media(jid: str, name: str):
    # Resolve file inside OUTPUTS_DIR or topic subfolder
    clean_name = name.lstrip("/")
    target_path = OUTPUTS_DIR / clean_name
    if not target_path.exists():
        fname_only = Path(clean_name).name
        candidates = list(OUTPUTS_DIR.rglob(fname_only))
        if candidates:
            target_path = candidates[0]

    # Handle image thumbnails (.jpg, .jpeg, .png)
    if clean_name.lower().endswith((".jpg", ".jpeg", ".png")):
        if target_path.exists():
            return FileResponse(target_path, media_type="image/jpeg")
        # On-the-fly TikTok thumbnail cover generation with real speaker body & topic text
        base_video_name = Path(clean_name).stem.split("_thumb_")[0] + ".mp4"
        for v_dir in [OUTPUTS_DIR, UPLOADS_DIR, TEMP_DIR]:
            vid_p = v_dir / base_video_name
            if not vid_p.exists():
                v_cands = list(v_dir.rglob(base_video_name))
                if v_cands:
                    vid_p = v_cands[0]
            if vid_p.exists():
                try:
                    clip_obj = HistoryManager.get_clip_by_filename(base_video_name) or {}
                    topic = clip_obj.get("title") or clip_obj.get("hook") or Path(clean_name).stem.replace("_", " ").title()
                    TikTokThumbnailDesigner.create_tiktok_thumbnail(
                        video_path=str(vid_p),
                        output_jpg_path=str(target_path),
                        topic=topic,
                        title=topic,
                        hook=clip_obj.get("hook", ""),
                        transcript=clip_obj.get("full_transcript", ""),
                        timestamp_sec=1.2
                    )
                    if target_path.exists():
                        return FileResponse(target_path, media_type="image/jpeg")
                except Exception:
                    pass
                try:
                    VideoRenderer().generate_thumbnail(str(vid_p), str(target_path), timestamp_sec=1.0)
                    if target_path.exists():
                        return FileResponse(target_path, media_type="image/jpeg")
                except Exception:
                    pass
        raise HTTPException(status_code=404, detail="Thumbnail not found")

    if target_path.exists():
        return FileResponse(target_path, media_type="video/mp4")
    p_up = UPLOADS_DIR / clean_name
    if p_up.exists():
        return FileResponse(p_up, media_type="video/mp4")
    p_tmp = TEMP_DIR / clean_name
    if p_tmp.exists():
        return FileResponse(p_tmp, media_type="video/mp4")
    raise HTTPException(status_code=404, detail="Media file not found")

@app.post("/api/jobs/{jid}/clips/{cid}/render")
async def remake_clip(jid: str, cid: str, payload: Dict[str, Any] = Body(...)):
    start_sec = float(payload.get("start", 0))
    end_sec = float(payload.get("end", start_sec + 30))
    hook_text = payload.get("hook", "")
    style = payload.get("style", "hormozi")
    layout = payload.get("layout", "speaker_focus")
    canvas_top_space = int(payload.get("top_space", payload.get("canvas_top_space", 450)))
    canvas_bg = payload.get("canvas_bg", "solid_black")
    top_padding = float(payload.get("top_padding", payload.get("pad_top", 0.0)))
    bottom_padding = float(payload.get("bottom_padding", payload.get("pad_bottom", 0.0)))
    color_preset = payload.get("color_preset", "none")
    watermark_text = payload.get("watermark", payload.get("watermark_text"))
    watermark_pos = payload.get("watermark_pos", payload.get("watermark_position", "top_right"))
    enable_voice_clarifier = bool(payload.get("voice_clarifier", True))
    edited_words = payload.get("words")
    
    proj = HistoryManager.get_project_by_id(jid)
    resolved_source = _resolve_video_source(jid)
    if not resolved_source:
        raise HTTPException(status_code=404, detail="Source video not found")
        
    duration = max(3.0, end_sec - start_sec)
    source_video = str(resolved_source)
    
    # 1. Use user-edited words if provided from the interactive transcript editor
    words = []
    if edited_words and isinstance(edited_words, list) and len(edited_words) > 0:
        words = edited_words
    else:
        # Try to reuse existing precise word timestamps if available
        existing_clip = HistoryManager.get_clip_by_id(cid)
        if existing_clip and existing_clip.get("words"):
            for w in existing_clip["words"]:
                if (w.get("start", 0) >= start_sec - 0.5) and (w.get("end", 0) <= end_sec + 0.5):
                    words.append(w)

    if not words:
        segments = proj.get("transcript_segments", [])
        matching_text = [s.get("text", "") for s in segments if s.get("start", 0) <= end_sec and s.get("end", 0) >= start_sec]
        full_text = " ".join(matching_text) or hook_text or "HIGHLIGHT"
        approx_words = full_text.split()
        w_dur = duration / max(1, len(approx_words))
        for i, w in enumerate(approx_words):
            words.append({"word": w, "start": round(start_sec + i * w_dur, 2), "end": round(start_sec + (i + 0.9) * w_dur, 2)})

    top_pct = max(0.0, min(45.0, float(top_padding))) / 100.0
    bottom_pct = max(0.0, min(45.0, float(bottom_padding))) / 100.0
    if top_pct + bottom_pct > 0.80:
        scale_pad = 0.80 / (top_pct + bottom_pct)
        top_pct *= scale_pad
        bottom_pct *= scale_pad
    has_padding = (top_pct > 0 or bottom_pct > 0)
    top_pad_px = int(round(1920 * top_pct))
    bottom_pad_px = int(round(1920 * bottom_pct))
    available_h = max(100, 1920 - top_pad_px - bottom_pad_px)

    fit_top_space = max(top_pad_px, max(80, min(950, canvas_top_space))) if not has_padding else top_pad_px
    fit_video_h = min(608, available_h)

    tracker = SmartFaceTracker()
    crop_filter, actual_layout = tracker.build_layout_filter(
        video_path=source_video,
        start_sec=start_sec,
        duration=duration,
        layout_mode=layout,
        top_padding=top_padding,
        bottom_padding=bottom_padding,
        canvas_bg=canvas_bg,
        target_w=1080,
        target_h=1920,
        enable_hook_zoom=False,
        canvas_top_space=canvas_top_space
    )

    ass_path = TEMP_DIR / f"reburn_{jid}_{cid}_{int(time.time())}.ass"
    SubtitleGenerator.create_ass_file(
        words=words,
        output_path=ass_path,
        style_key=style,
        words_per_batch=3,
        clip_start_offset=start_sec,
        clip_duration=duration,
        topic_headline=hook_text,
        show_headline_banner=bool(hook_text),
        enable_auto_emojis=True,
        layout_mode=actual_layout,
        top_space=fit_top_space,
        video_h=fit_video_h,
        top_padding=top_padding,
        bottom_padding=bottom_padding
    )
    
    renderer = VideoRenderer()
    out_filename = f"reburn_{jid[:8]}_{cid}_{int(time.time())}.mp4"
    rendered_path = renderer.render_clip(
        video_path=source_video,
        start_sec=start_sec,
        duration=duration,
        crop_filter=crop_filter,
        ass_subtitle_path=str(ass_path),
        output_filename=out_filename,
        color_preset=color_preset,
        watermark_text=watermark_text,
        watermark_position=watermark_pos,
        enable_voice_clarifier=enable_voice_clarifier
    )
    
    # Generate matching AI TikTok cover thumbnail
    thumb_path = OUTPUTS_DIR / f"{Path(out_filename).stem}.jpg"
    try:
        topic_val = hook_text or "HIGHLIGHT"
        TikTokThumbnailDesigner.create_tiktok_thumbnail(
            video_path=str(rendered_path),
            output_jpg_path=str(thumb_path),
            topic=topic_val,
            title=topic_val,
            hook=hook_text,
            transcript=" ".join(w.get("word", "") for w in words),
            crop_filter=crop_filter,
            source_clean_video=source_video,
            timestamp_sec=start_sec + min(2.0, max(0.5, duration * 0.2))
        )
    except Exception as te:
        print(f"[Thumbnail Warning] Remake thumbnail error: {te}")

    # Update persistent database so changes are visible immediately
    HistoryManager.update_clip(cid, {
        "filename": out_filename,
        "cover": f"{Path(out_filename).stem}.jpg",
        "duration": round(duration, 2),
        "start_sec": start_sec,
        "end_sec": end_sec,
        "hook": hook_text,
        "subtitle_style": style,
        "layout_mode": layout,
        "top_padding": top_padding,
        "bottom_padding": bottom_padding,
        "words": words,
        "output_file": str(rendered_path)
    })
    
    updated_clip = HistoryManager.get_clip_by_id(cid)
    return {"status": "success", "file": out_filename, "clip": updated_clip, "output_file": str(rendered_path)}

@app.delete("/api/jobs/{jid}")
async def delete_job(jid: str):
    HistoryManager.delete_project(jid)
    return {"status": "deleted"}

@app.delete("/api/jobs/{jid}/clips/{cid}")
async def delete_clip(jid: str, cid: str):
    HistoryManager.delete_clip(cid)
    return {"status": "deleted"}

@app.post("/api/bulk/delete")
async def bulk_delete(payload: Dict[str, Any] = Body(...)):
    vids = payload.get("videos", [])
    clips = payload.get("clips", [])
    deleted_vids = 0
    deleted_clips = 0
    for v in vids:
        HistoryManager.delete_project(v)
        deleted_vids += 1
    for c in clips:
        if isinstance(c, list) and len(c) == 2:
            HistoryManager.delete_clip(c[1])
            deleted_clips += 1
        elif isinstance(c, str):
            HistoryManager.delete_clip(c)
            deleted_clips += 1
    return {"videos": deleted_vids, "clips": deleted_clips}

def package_clips_into_zip(zf: zipfile.ZipFile, clips: List[Dict[str, Any]], session_title: str = "ClipForge Session"):
    """
    Packages clips into a clean multi-folder structure:
    Every clip gets its own dedicated topic folder containing:
    - 1 topic-named video file (.mp4)
    - 3 distinct viral thumbnails (_thumb_1, _thumb_2, _thumb_3) for TikTok
    - 1 clip-specific documentation file (.docx and .txt)
    Plus overall session documentation.
    """
    for i, clip in enumerate(clips, 1):
        raw_topic = clip.get("topic") or clip.get("title") or f"Clip_{i}"
        safe_name = re.sub(r"[^\w\-]", "_", str(raw_topic)).strip("_") or f"Clip_{i}"
        if clip.get("part_info") and "part" not in safe_name.lower():
            safe_name = f"{safe_name}_{clip['part_info'].lower().replace(' ', '_')}"

        folder_name = clip.get("folder_name") or safe_name
        zip_folder = f"{i:02d}_{folder_name}" if len(clips) > 1 else folder_name

        # 1. Resolve video file
        vid_path = None
        fn = clip.get("filename")
        if fn and (OUTPUTS_DIR / fn).exists():
            vid_path = OUTPUTS_DIR / fn
        elif clip.get("output_file") and Path(clip["output_file"]).exists():
            vid_path = Path(clip["output_file"])
        else:
            folder_vid = OUTPUTS_DIR / folder_name / f"{safe_name}.mp4"
            if folder_vid.exists():
                vid_path = folder_vid

        if vid_path and vid_path.exists():
            arc_video_name = f"{zip_folder}/{vid_path.name}"
            zf.write(vid_path, arcname=arc_video_name)

            stem = vid_path.stem
            # 2. Add 3 Viral Thumbnails
            explicit_covers = clip.get("covers") or []
            thumb_written = False
            if explicit_covers:
                for c_idx, cov_rel in enumerate(explicit_covers, 1):
                    cov_p = OUTPUTS_DIR / cov_rel
                    if not cov_p.exists():
                        cov_p = OUTPUTS_DIR / Path(cov_rel).name
                    if not cov_p.exists() and folder_name:
                        cov_p = OUTPUTS_DIR / folder_name / Path(cov_rel).name
                    if cov_p.exists():
                        tag = "curiosity" if c_idx == 1 else "warning" if c_idx == 2 else "blueprint"
                        zf.write(cov_p, arcname=f"{zip_folder}/{stem}_thumb_{c_idx}_{tag}.jpg")
                        if c_idx == 1:
                            zf.write(cov_p, arcname=f"{zip_folder}/{stem}.jpg")
                        thumb_written = True

            if not thumb_written:
                t1 = OUTPUTS_DIR / folder_name / f"{stem}_thumb_1.jpg"
                if not t1.exists():
                    t1 = OUTPUTS_DIR / f"{stem}_thumb_1.jpg"
                if not t1.exists():
                    t1 = OUTPUTS_DIR / f"{stem}.jpg"
                if t1.exists():
                    zf.write(t1, arcname=f"{zip_folder}/{stem}_thumb_1_curiosity.jpg")
                    zf.write(t1, arcname=f"{zip_folder}/{stem}.jpg")

                t2 = OUTPUTS_DIR / folder_name / f"{stem}_thumb_2.jpg"
                if not t2.exists():
                    t2 = OUTPUTS_DIR / f"{stem}_thumb_2.jpg"
                if t2.exists():
                    zf.write(t2, arcname=f"{zip_folder}/{stem}_thumb_2_warning.jpg")

                t3 = OUTPUTS_DIR / folder_name / f"{stem}_thumb_3.jpg"
                if not t3.exists():
                    t3 = OUTPUTS_DIR / f"{stem}_thumb_3.jpg"
                if t3.exists():
                    zf.write(t3, arcname=f"{zip_folder}/{stem}_thumb_3_blueprint.jpg")

            # Fallback if no thumbnails found on disk
            if not thumb_written and not (OUTPUTS_DIR / f"{stem}.jpg").exists() and vid_path.exists():
                try:
                    fallback_thumb = TEMP_DIR / f"{stem}_temp.jpg"
                    VideoRenderer().generate_thumbnail(str(vid_path), str(fallback_thumb), timestamp_sec=1.0)
                    if fallback_thumb.exists():
                        zf.write(fallback_thumb, arcname=f"{zip_folder}/{stem}_thumb_1_curiosity.jpg")
                        zf.write(fallback_thumb, arcname=f"{zip_folder}/{stem}.jpg")
                except Exception:
                    pass

            # 3. Add single clip documentation
            try:
                clip_docx = generate_clip_docx(clip)
                zf.writestr(f"{zip_folder}/{stem}_docs.docx", clip_docx)
                clip_txt = generate_clip_text(clip)
                zf.writestr(f"{zip_folder}/{stem}_docs.txt", clip_txt.encode("utf-8"))
            except Exception as d_err:
                print(f"[ZIP Packaging] Single clip doc error: {d_err}")

    # Add full session documentation
    if clips:
        add_session_docs_to_zip(zf, clips, session_title=session_title)

@app.get("/api/clips/{clip_id}/download-zip")
async def download_single_clip_zip(clip_id: str):
    """
    Downloads a single clip's complete production package as a ZIP:
    - 1 Topic-named video file (.mp4)
    - 3 distinct viral TikTok cover thumbnails (_thumb_1, _thumb_2, _thumb_3)
    - 1 Clip-specific documentation file (.docx and .txt)
    """
    clip = HistoryManager.get_clip_by_id(clip_id)
    if not clip:
        for jid, j in JOBS.items():
            for c in j.get("result", {}).get("clips", []):
                if c.get("id") == clip_id:
                    clip = c
                    break
            if clip:
                break
    if not clip:
        raise HTTPException(status_code=404, detail="Clip not found")

    raw_topic = clip.get("topic") or clip.get("title") or "clip"
    safe_name = re.sub(r"[^\w\-]", "_", str(raw_topic)).strip("_") or "podcast_clip"
    filename = f"{safe_name}_package.zip"

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        package_clips_into_zip(zf, [clip], session_title=safe_name)

    buf.seek(0)
    return Response(
        content=buf.getvalue(),
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@app.get("/api/clips.zip")
async def get_clips_zip(ids: Optional[str] = None):
    projects = HistoryManager.get_all_projects()
    target_clips = []
    
    if ids:
        id_set = set(ids.split(","))
        for p in projects:
            for c in p.get("clips", []):
                key = f"{p['id']}.{c['id']}"
                if key in id_set or c.get("id") in id_set or any(x == str(c.get("id")) or x.endswith("." + str(c.get("id"))) for x in id_set):
                    target_clips.append(c)
    else:
        for p in projects:
            for c in p.get("clips", []):
                target_clips.append(c)

    if not target_clips:
        for jid, j in JOBS.items():
            for c in j.get("result", {}).get("clips", []):
                target_clips.append(c)
                    
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        package_clips_into_zip(zf, target_clips, session_title="ClipForge Clips")
            
    buf.seek(0)
    return Response(
        content=buf.getvalue(),
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=clipforge_clips_by_topic.zip"}
    )

@app.get("/api/overview")
async def get_overview():
    projects = HistoryManager.get_all_projects()
    total_clips = sum(len(p.get("clips", [])) for p in projects)
    return {
        "recording": 0,
        "creators": [{"id": "all", "name": "Main Studio", "clips_today": total_clips, "clips_total": total_clips, "posted_today": 0, "posted_total": 0, "queued": 0, "failed": 0, "views": 0, "earnings": 0}],
        "daily": [{"day": time.strftime("%Y-%m-%d"), "clips": total_clips, "posted": 0}],
        "posts": [],
        "paused": False
    }

@app.get("/api/ai")
async def get_ai_config():
    st = MultiModelAIEngine.get_instance().get_status()
    return {
        "ready": st.get("connected", False) and st.get("configured_primary_available", False),
        "provider": "ollama",
        "models": st.get("available_models", []),
        "model_details": st.get("models", []),
        "model": st.get("configured_primary"),
        "model_assignments": st.get("model_assignments", {}),
        "processing_mode": st.get("processing_mode", "balanced"),
        "base_url": st.get("url"),
        "connected": st.get("connected", False),
        "error": st.get("error"),
        "hardware": st.get("hardware", {}),
        "running_models": st.get("running_models", []),
        "missing_assignments": st.get("missing_assignments", {}),
    }

@app.post("/api/ai/models")
async def get_ai_models():
    try:
        models = MultiModelAIEngine.get_instance().discover_models(force=True)
    except AIEngineError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    return {"models": models, "names": [model["name"] for model in models]}

@app.post("/api/ai/save")
async def save_ai_config(payload: Dict[str, Any] = Body(...)):
    engine = MultiModelAIEngine.get_instance()
    try:
        settings = engine.update_settings(payload)
    except AIEngineError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    status = engine.get_status(refresh=True)
    return {
        "status": "ok",
        "connected": status.get("connected", False),
        "settings": settings,
        "status_detail": status,
    }

@app.post("/api/ai/test")
async def test_ai(payload: Dict[str, Any] = Body(default={})):
    engine = MultiModelAIEngine.get_instance()
    try:
        result = engine.generate_text(
            "Reply with exactly: ClipForge AI connection verified.",
            role=payload.get("role", "primary"),
            model=payload.get("model"),
            timeout=90.0,
        )
    except AIEngineError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    return {
        "status": "ok",
        "model": result["model"],
        "role": result["role"],
        "elapsed_seconds": result["elapsed_seconds"],
        "warning": result.get("warning"),
    }

@app.post("/api/ai/generate-hooks")
async def generate_viral_hooks_endpoint(payload: Dict[str, Any] = Body(...)):
    """Generates five hook headlines using the assigned local AI model."""
    transcript = payload.get("transcript", "")
    topic = payload.get("topic", "")
    clip_id = payload.get("clip_id")

    if not transcript and clip_id:
        c = HistoryManager.get_clip_by_id(clip_id)
        if c:
            topic = c.get("title", topic)
            words = c.get("words", [])
            transcript = " ".join(w.get("word", "") for w in words) or c.get("hook", "")

    detector = ViralDetector()
    hooks = detector.generate_viral_hooks(transcript, topic)
    generation = OllamaManager.get_instance().last_generation
    return {
        "status": "success",
        "hooks": hooks,
        "source": generation.get("source", "heuristic"),
        "model": generation.get("model"),
        "warning": generation.get("error"),
    }

@app.post("/api/ai/translate")
async def translate_transcript_endpoint(payload: Dict[str, Any] = Body(...)):
    """Translates clip transcript into foreign languages for global reach shorts."""
    transcript = payload.get("transcript", "")
    target_lang = payload.get("target_lang", "es")
    clip_id = payload.get("clip_id")

    if not transcript and clip_id:
        c = HistoryManager.get_clip_by_id(clip_id)
        if c:
            words = c.get("words", [])
            transcript = " ".join(w.get("word", "") for w in words) or c.get("hook", "")

    detector = ViralDetector()
    res = detector.translate_clip(transcript, target_lang)
    generation = OllamaManager.get_instance().last_generation
    return {
        "status": "success",
        **res,
        "source": generation.get("source", "heuristic"),
        "model": generation.get("model"),
        "warning": generation.get("error"),
    }

@app.post("/api/ai/b-roll")
async def suggest_b_roll_endpoint(payload: Dict[str, Any] = Body(...)):
    """Analyzes transcript and returns B-roll suggestions & sound effect cues."""
    transcript = payload.get("transcript", "")
    detector = ViralDetector()
    suggestions = detector.suggest_b_roll(transcript)
    return {"status": "success", "suggestions": suggestions, "source": "heuristic"}

@app.post("/api/ai/research-clips")
async def research_viral_clips_endpoint(payload: Dict[str, Any] = Body(...)):
    """
    AI Viral Clip Research Engine.
    Searches an episode/video transcript using semantic natural language query
    and viral angle archetypes (controversial, mindset, story, blueprint, reveal).
    """
    project_id = payload.get("project_id")
    source = payload.get("source")
    query = payload.get("query", "").strip()
    archetype = payload.get("archetype", "all").strip().lower()
    min_dur = float(payload.get("min_duration", 60.0))
    max_dur = float(payload.get("max_duration", 90.0))
    top_k = int(payload.get("top_k", 5))

    segments = []
    # 1. Check Project History
    if project_id:
        proj = HistoryManager.get_project_by_id(project_id)
        if proj:
            if proj.get("transcript_segments"):
                segments = proj["transcript_segments"]
            elif proj.get("clips"):
                for c in proj["clips"]:
                    if c.get("words"):
                        segments.append({"words": c["words"], "text": c.get("full_transcript", c.get("hook", ""))})

    # 2. Check active JOBS or cached transcription if source is provided
    if not segments and source:
        if source in JOBS and "result" in JOBS[source]:
            res = JOBS[source]["result"]
            segments = res.get("transcript_segments", [])
        if not segments:
            v_path = _resolve_video_source(source)
            if v_path and v_path.exists():
                cache_file = TEMP_DIR / f"{v_path.stem}_transcript.json"
                if cache_file.exists():
                    try:
                        segments = json.loads(cache_file.read_text(encoding="utf-8"))
                    except Exception:
                        pass

    # 3. If still empty, search all recent clips or projects
    if not segments:
        all_projs = HistoryManager.get_all_projects()
        if all_projs:
            latest = HistoryManager.get_project_by_id(all_projs[0]["id"])
            if latest and latest.get("transcript_segments"):
                segments = latest["transcript_segments"]

    detector = ViralDetector()
    results = detector.research_viral_clips(
        segments=segments,
        query=query,
        archetype=archetype,
        min_seconds=min_dur,
        max_seconds=max_dur,
        top_k=top_k
    )
    return {
        "status": "success",
        "query": query,
        "archetype": archetype,
        "clips": results,
        "sources": sorted({
            (clip.get("model_provenance") or {}).get("source", "heuristic")
            for clip in results
        }),
    }

@app.post("/api/ai/edit-copilot")
async def ai_edit_copilot_endpoint(payload: Dict[str, Any] = Body(...)):
    """
    AI Natural Language Video Edit Copilot.
    Takes clip state and creator instruction to suggest optimal hooks, titles, styles, and pacing.
    """
    clip_id = payload.get("clip_id")
    instruction = payload.get("instruction", "").strip()
    current_state = payload.get("current_state", {})

    clip_data = dict(current_state)
    if clip_id:
        c = HistoryManager.get_clip_by_id(clip_id)
        if c:
            clip_data.update(c)

    from core.ollama_manager import OllamaManager
    ollama = OllamaManager.get_instance()
    edits = ollama.ai_edit_copilot(clip_data, instruction)
    return {
        "status": "success",
        "edits": edits,
        "source": ollama.last_generation.get("source", "heuristic"),
        "model": ollama.last_generation.get("model"),
        "warning": ollama.last_generation.get("error"),
    }

@app.post("/api/ai/social-kit")
async def generate_social_kit_endpoint(payload: Dict[str, Any] = Body(...)):
    """
    Generates multi-platform publishing copy for TikTok, Instagram Reels, and YouTube Shorts.
    """
    clip_id = payload.get("clip_id")
    transcript = payload.get("transcript", "")
    title = payload.get("title", "")
    hook = payload.get("hook", "")

    if clip_id and (not transcript or not title):
        c = HistoryManager.get_clip_by_id(clip_id)
        if c:
            title = title or c.get("title", "")
            hook = hook or c.get("hook", "")
            if not transcript and c.get("words"):
                transcript = " ".join(w.get("word", "") for w in c["words"])

    from core.ollama_manager import OllamaManager
    ollama = OllamaManager.get_instance()
    kit = ollama.generate_social_distribution_kit(transcript=transcript, title=title, hook=hook)
    return {
        "status": "success",
        "social_kit": kit,
        "source": ollama.last_generation.get("source", "heuristic"),
        "model": ollama.last_generation.get("model"),
        "warning": ollama.last_generation.get("error"),
    }

@app.get("/api/system/status")
async def get_system_status():
    """Detect local GPU, FFmpeg, and Ollama status."""
    import ctranslate2

    has_cuda = False
    try:
        has_cuda = (ctranslate2.get_cuda_device_count() > 0)
    except Exception:
        pass

    gpu_name = "NVIDIA RTX 3050 (NVENC Hardware Active)"

    ai_status = MultiModelAIEngine.get_instance().get_status()
    ollama_alive = ai_status.get("connected", False)

    return {
        "status": "online",
        "ffmpeg_path": FFMPEG_PATH,
        "cuda_available": has_cuda,
        "gpu_name": gpu_name,
        "ollama_alive": ollama_alive,
        "ai_processing_mode": ai_status.get("processing_mode"),
        "ai_model_assignments": ai_status.get("model_assignments", {}),
        "ai_hardware": ai_status.get("hardware", {}),
        "whisper_model": DEFAULT_CONFIG["whisper_model"]
    }

# ============================================================
# Google Drive Cloud Integration Endpoints
# ============================================================

@app.get("/api/gdrive/status")
async def gdrive_status():
    """Returns current Google Drive connection telemetry and folder name."""
    gdm = GoogleDriveManager.get_instance()
    return gdm.get_status()

@app.post("/api/gdrive/configure")
async def gdrive_configure(payload: Dict[str, Any] = Body(...)):
    """Saves Google OAuth Client ID, Secret, and target folder."""
    gdm = GoogleDriveManager.get_instance()
    status = gdm.configure(
        client_id=payload.get("client_id"),
        client_secret=payload.get("client_secret"),
        redirect_uri=payload.get("redirect_uri"),
        folder_name=payload.get("folder_name")
    )
    auth_url = ""
    try:
        if status["has_credentials"]:
            auth_url = gdm.get_auth_url(payload.get("redirect_uri"))
    except Exception:
        pass
    return {"status": "success", "config": status, "auth_url": auth_url}

@app.get("/api/gdrive/auth-url")
async def gdrive_auth_url(redirect_uri: Optional[str] = None):
    """Generates the Google OAuth 2.0 consent URL."""
    gdm = GoogleDriveManager.get_instance()
    try:
        url = gdm.get_auth_url(redirect_uri=redirect_uri)
        return {"status": "success", "auth_url": url}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/gdrive/callback")
async def gdrive_callback(code: Optional[str] = None, error: Optional[str] = None):
    """Handles Google OAuth redirect, exchanges code for access & refresh tokens."""
    if error:
        return HTMLResponse(f"<html><body><h2>Google Drive Authentication Failed</h2><p>{error}</p><script>setTimeout(()=>window.close(),3000);</script></body></html>", status_code=400)
    if not code:
        raise HTTPException(status_code=400, detail="Missing authorization code.")

    gdm = GoogleDriveManager.get_instance()
    try:
        gdm.exchange_code(code)
        return HTMLResponse("""<!doctype html>
<html>
<head><title>Google Drive Connected</title>
<style>
body { background:#0E0C0A; color:#E0DACB; font-family:-apple-system,BlinkMacSystemFont,sans-serif; display:flex; flex-direction:column; align-items:center; justify-content:center; height:100vh; margin:0; text-align:center; }
.card { background:#1E1612; border:1px solid #FF8B33; border-radius:16px; padding:32px 40px; box-shadow:0 12px 36px rgba(0,0,0,0.7); max-width:440px; }
h2 { color:#00E5FF; margin-top:0; }
p { color:#A89F91; line-height:1.5; }
.btn { background:linear-gradient(135deg,#FF8B33,#FFB800); color:#1E1612; border:none; padding:10px 24px; border-radius:8px; font-weight:700; cursor:pointer; text-decoration:none; display:inline-block; margin-top:16px; }
</style>
</head>
<body>
<div class="card">
  <h2>⚡ Google Drive Connected!</h2>
  <p>Your ClipForge Studio is now connected to Google Drive. You can close this window and start uploading your clips directly to Drive for mobile TikTok posting!</p>
  <a href="/app" class="btn" onclick="if(window.opener){window.opener.postMessage('gdrive_connected','*');window.close();return false;}">Return to Studio</a>
</div>
<script>
if(window.opener) {
  try { window.opener.postMessage('gdrive_connected', '*'); } catch(e){}
  setTimeout(() => window.close(), 1800);
}
</script>
</body>
</html>""")
    except Exception as e:
        return HTMLResponse(f"<html><body style='background:#0E0C0A;color:#FF5555;padding:40px'><h2>Google Drive Connection Error</h2><p>{e}</p></body></html>", status_code=500)

@app.post("/api/gdrive/upload")
async def gdrive_upload(payload: Dict[str, Any] = Body(...)):
    """Uploads one or multiple clips to Google Drive."""
    gdm = GoogleDriveManager.get_instance()
    if not gdm.is_connected():
        raise HTTPException(status_code=401, detail="Google Drive is not connected. Please connect in Settings -> Google Drive.")

    clip_ids = payload.get("clip_ids", [])
    if not clip_ids and payload.get("clip_id"):
        clip_ids = [payload.get("clip_id")]
    if not clip_ids and payload.get("cid"):
        clip_ids = [payload.get("cid")]

    # If project_id provided, gather all clips of that project
    project_id = payload.get("project_id") or payload.get("jid")
    if not clip_ids and project_id:
        proj = HistoryManager.get_project_by_id(project_id)
        if proj and proj.get("clips"):
            clip_ids = [c["id"] for c in proj["clips"]]

    if not clip_ids:
        raise HTTPException(status_code=400, detail="No clips specified for upload.")

    uploaded_results = []
    all_projects = HistoryManager.get_all_projects()

    for cid in clip_ids:
        clip = HistoryManager.get_clip_by_id(cid)
        filename = clip.get("filename") if clip else None
        title = (clip.get("title") or clip.get("hook") or "TikTok Clip") if clip else "Clip"

        if not filename:
            for p in all_projects:
                for c in p.get("clips", []):
                    if c.get("id") == cid:
                        filename = c.get("filename")
                        title = c.get("title") or c.get("hook") or title
                        break
                if filename:
                    break

        if not filename:
            continue

        file_path = OUTPUTS_DIR / filename
        if not file_path.exists():
            for cand in [TEMP_DIR, UPLOADS_DIR]:
                if (cand / filename).exists():
                    file_path = cand / filename
                    break

        if not file_path.exists():
            continue

        try:
            res = gdm.upload_file(str(file_path), title=title)
            uploaded_results.append({
                "clip_id": cid,
                "filename": filename,
                **res
            })
        except Exception as ue:
            uploaded_results.append({
                "clip_id": cid,
                "filename": filename,
                "status": "error",
                "error": str(ue)
            })

    if not uploaded_results:
        raise HTTPException(status_code=404, detail="Could not find rendered video files on disk for the specified clips.")

    successful = [r for r in uploaded_results if r.get("status") == "success"]
    return {
        "status": "success" if successful else "error",
        "total": len(clip_ids),
        "uploaded_count": len(successful),
        "folder_name": gdm.config.get("folder_name", "ClipForge Clips"),
        "results": uploaded_results
    }

@app.post("/api/gdrive/disconnect")
async def gdrive_disconnect():
    """Disconnects Google Drive and purges stored OAuth tokens."""
    gdm = GoogleDriveManager.get_instance()
    gdm.disconnect()
    return {"status": "success", "message": "Google Drive disconnected."}

@app.post("/api/youtube/info")
async def get_youtube_info(req: YouTubeInfoRequest):
    """Fetches video metadata (title, duration, thumbnail) for preview."""
    url = req.url.strip()
    if not url:
        raise HTTPException(status_code=400, detail="YouTube URL is required")
    try:
        info = YouTubeDownloader.get_info(url)
        return info
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

def run_pipeline_task(job_id: str, video_path: Optional[str], youtube_url: Optional[str], options: Dict[str, Any]):
    """Background worker for video processing (handles both local uploads & YouTube downloads)."""
    try:
        def on_progress(message: str, percent: float, step: int = 1, step_name: str = "", detail: str = ""):
            if job_id in JOBS:
                JOBS[job_id]["progress"] = percent
                JOBS[job_id]["status_message"] = message
                JOBS[job_id]["step_index"] = step
                JOBS[job_id]["step_name"] = step_name or "Processing"
                JOBS[job_id]["step_detail"] = detail or message

        # Step 0: Download from YouTube if URL provided
        if youtube_url:
            on_progress("Connecting to YouTube and downloading video stream...", 5, step=1, step_name="Download", detail="Fetching video stream from YouTube")
            def yt_progress(msg: str, pct: float):
                scaled_pct = 5 + (pct * 0.15)  # 5% to 20%
                on_progress(msg, scaled_pct, step=1, step_name="Download", detail=msg)

            downloaded_video = YouTubeDownloader.download(
                url=youtube_url,
                output_dir=UPLOADS_DIR,
                progress_cb=yt_progress
            )
            video_path = str(downloaded_video)

        if not video_path or not Path(video_path).exists():
            raise FileNotFoundError(f"Source video file not found: {video_path}")

        # Run ClipForge Pipeline
        pipeline = ClipForgePipeline(config={
            "device": "auto",
            "whisper_model": "base"
        })

        result = pipeline.process_video(
            video_path=video_path,
            subtitle_style=options.get("subtitle_style", "hormozi"),
            max_clips=int(options.get("max_clips", 5)),
            min_clip_seconds=float(options.get("min_clip_seconds", 25.0)),
            max_clip_seconds=float(options.get("max_clip_seconds", 65.0)),
            show_headline_banner=options.get("show_headline_banner", True),
            enable_face_tracking=options.get("face_tracking", True),
            clip_mode=options.get("clip_mode", "highlights"),
            layout_mode=options.get("layout_mode", "speaker_focus"),
            canvas_top_space=int(options.get("canvas_top_space", 450)),
            canvas_bg=options.get("canvas_bg", "solid_black"),
            enable_tightcut=options.get("enable_tightcut", False),
            enable_auto_emojis=options.get("enable_auto_emojis", True),
            progress_bar_color=options.get("progress_bar_color", "#00E5FF"),
            bgm_track=options.get("bgm_track", "none"),
            bgm_volume=float(options.get("bgm_volume", 0.12)),
            color_preset=options.get("color_preset", "none"),
            watermark_text=options.get("watermark_text"),
            watermark_position=options.get("watermark_position", "top_right"),
            enable_voice_clarifier=bool(options.get("enable_voice_clarifier", True)),
            enable_hook_zoom=options.get("enable_hook_zoom", True),
            custom_headline=options.get("custom_headline"),
            top_padding=float(options.get("top_padding", options.get("pad_top", 0.0))),
            bottom_padding=float(options.get("bottom_padding", options.get("pad_bottom", 0.0))),
            language=options.get("language", "en"),
            ai_processing_mode=options.get("ai_processing_mode"),
            progress_cb=on_progress
        )

        JOBS[job_id]["status"] = "completed"
        JOBS[job_id]["progress"] = 100
        JOBS[job_id]["status_message"] = "Processing completed!"
        JOBS[job_id]["result"] = result

        # Determine Project Title & Metadata for History
        project_title = options.get("original_title") or "Podcast Session"
        thumbnail_url = options.get("thumbnail_url", "")
        source_type = "youtube" if youtube_url else "upload"
        source_identifier = youtube_url or project_title

        if youtube_url:
            try:
                yt_info = YouTubeDownloader.get_info(youtube_url)
                project_title = yt_info.get("title") or project_title
                thumbnail_url = yt_info.get("thumbnail") or thumbnail_url
            except Exception:
                pass
        else:
            clean_name = Path(project_title).stem.replace("_", " ").replace("-", " ").title()
            project_title = clean_name

        # Save to persistent history database
        try:
            HistoryManager.save_project_with_clips(
                project_id=job_id,
                title=project_title,
                source_type=source_type,
                source_identifier=source_identifier,
                thumbnail_url=thumbnail_url,
                duration=float(result.get("duration", 0)),
                clips=result.get("clips", []),
                source_video=video_path,
                virality_timeline=result.get("virality_timeline", []),
                podcast_summary=result.get("podcast_summary"),
                transcript_segments=result.get("transcript_segments", [])
            )
        except Exception as db_err:
            print(f"[HistoryManager Error] Failed to persist project: {db_err}")

    except Exception as e:
        import traceback
        traceback.print_exc()
        JOBS[job_id]["status"] = "failed"
        JOBS[job_id]["error"] = str(e)
        JOBS[job_id]["status_message"] = f"Error: {e}"

@app.post("/api/clips/create")
async def create_clips(
    background_tasks: BackgroundTasks,
    file: Optional[UploadFile] = File(None),
    youtube_url: Optional[str] = Form(None),
    custom_headline: Optional[str] = Form(None),
    language: Optional[str] = Form("en"),
    subtitle_style: str = Form("hormozi"),
    clip_mode: str = Form("highlights"),
    layout_mode: str = Form("speaker_focus"),
    canvas_top_space: int = Form(450),
    canvas_bg: str = Form("solid_black"),
    max_clips: int = Form(5),
    min_clip_seconds: float = Form(25.0),
    max_clip_seconds: float = Form(65.0),
    face_tracking: bool = Form(True),
    show_headline_banner: bool = Form(True),
    enable_tightcut: bool = Form(False),
    enable_auto_emojis: bool = Form(True),
    progress_bar_color: str = Form("#00E5FF"),
    bgm_track: str = Form("none"),
    bgm_volume: float = Form(0.12),
    color_preset: str = Form("none"),
    watermark_text: Optional[str] = Form(None),
    watermark_position: str = Form("top_right"),
    enable_voice_clarifier: bool = Form(True),
    enable_hook_zoom: bool = Form(True),
    top_padding: float = Form(0.0),
    bottom_padding: float = Form(0.0),
    pad_top: Optional[float] = Form(None),
    pad_bottom: Optional[float] = Form(None),
    ai_processing_mode: Optional[str] = Form(None)
):
    """
    Accepts either a local video file OR a direct YouTube video link
    and starts the viral clipping pipeline.
    Supports layout_mode ('speaker_focus', 'split_screen', 'blur', 'center_crop'),
    TightCut dead-air removal, Submagic auto-emojis,
    retention progress bar, and smart auto-ducked background music.
    """
    # Validation: Must provide either file or youtube_url
    has_file = file is not None and file.filename
    has_yt = bool(youtube_url and youtube_url.strip())

    if not has_file and not has_yt:
        raise HTTPException(status_code=400, detail="Please upload a video file or provide a YouTube link.")
    if ai_processing_mode and ai_processing_mode not in PROCESSING_MODES:
        raise HTTPException(
            status_code=422,
            detail="AI processing mode must be fast, balanced, or maximum_quality.",
        )

    job_id = str(uuid.uuid4())
    upload_dest = None

    if has_file:
        file_ext = Path(file.filename).suffix.lower()
        allowed_exts = [".mp4", ".mov", ".mkv", ".webm", ".avi", ".mp3", ".wav", ".m4a"]
        if file_ext not in allowed_exts:
            raise HTTPException(status_code=400, detail=f"Unsupported format {file_ext}. Use MP4, MOV, or MKV.")

        upload_filename = f"{job_id}_{file.filename}"
        upload_dest = str(UPLOADS_DIR / upload_filename)

        with open(upload_dest, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

    yt_link = youtube_url.strip() if has_yt else None

    final_top_pad = float(pad_top) if pad_top is not None else float(top_padding)
    final_bot_pad = float(pad_bottom) if pad_bottom is not None else float(bottom_padding)

    options = {
        "original_title": file.filename if has_file else "YouTube Podcast",
        "custom_headline": custom_headline,
        "language": language,
        "subtitle_style": subtitle_style,
        "clip_mode": clip_mode,
        "layout_mode": layout_mode,
        "canvas_top_space": canvas_top_space,
        "canvas_bg": canvas_bg,
        "top_padding": final_top_pad,
        "bottom_padding": final_bot_pad,
        "pad_top": final_top_pad,
        "pad_bottom": final_bot_pad,
        "max_clips": min(20, max(1, max_clips)),
        "min_clip_seconds": min_clip_seconds,
        "max_clip_seconds": max_clip_seconds,
        "face_tracking": face_tracking,
        "show_headline_banner": show_headline_banner,
        "enable_tightcut": enable_tightcut,
        "enable_auto_emojis": enable_auto_emojis,
        "progress_bar_color": progress_bar_color,
        "bgm_track": bgm_track,
        "bgm_volume": bgm_volume,
        "color_preset": color_preset,
        "watermark_text": watermark_text,
        "watermark_position": watermark_position,
        "enable_voice_clarifier": enable_voice_clarifier,
        "enable_hook_zoom": enable_hook_zoom,
        "ai_processing_mode": ai_processing_mode
    }

    JOBS[job_id] = {
        "id": job_id,
        "status": "queued",
        "progress": 0,
        "status_message": "Task queued. Initializing pipeline...",
        "step_index": 1,
        "step_name": "Transcribe",
        "step_detail": "Queue initialized. Waiting for pipeline start...",
        "result": None,
        "error": None,
        "options": options
    }


    # Start task in background thread
    threading.Thread(
        target=run_pipeline_task,
        args=(job_id, upload_dest, yt_link, options),
        daemon=True
    ).start()

    return {"job_id": job_id, "status": "started"}

@app.get("/api/jobs/{job_id}")
async def get_job_status(job_id: str):
    if job_id not in JOBS:
        raise HTTPException(status_code=404, detail="Job not found")
    return JOBS[job_id]

@app.get("/api/projects")
async def list_projects():
    """Returns all projects with their clips grouped, newest first."""
    projects = HistoryManager.get_all_projects()
    return {"projects": projects}

@app.delete("/api/projects/{project_id}")
async def delete_project(project_id: str):
    """Deletes an entire project, its database entries, and its MP4 files."""
    success = HistoryManager.delete_project(project_id)
    return {"status": "success", "deleted_project_id": project_id}

@app.get("/api/projects/{project_id}")
async def get_project_details(project_id: str):
    """Retrieves full project details including clips, source video path, and transcript segments for the timeline editor."""
    proj = HistoryManager.get_project_by_id(project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")
    return proj

@app.get("/api/projects/{project_id}/source-video")
async def stream_project_source_video(project_id: str):
    """Streams the full source video with byte-range support for smooth timeline seeking and playback."""
    proj = HistoryManager.get_project_by_id(project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")

    resolved_source = _resolve_video_source(project_id)
    if not resolved_source:
        raise HTTPException(status_code=404, detail="Source video file not found on disk")

    return FileResponse(
        path=str(resolved_source),
        media_type="video/mp4",
        filename=resolved_source.name
    )

@app.post("/api/projects/{project_id}/editor-state")
async def save_editor_state(project_id: str, payload: Dict[str, Any] = Body(...)):
    """Saves the complete editable studio project document for reopening."""
    proj = HistoryManager.get_project_by_id(project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")

    editor_project = payload.get("editor_project") or payload.get("project") or payload
    if not isinstance(editor_project, dict):
        raise HTTPException(status_code=400, detail="editor_project must be an object")

    title = payload.get("title") or editor_project.get("title")
    if not HistoryManager.save_editor_project(project_id, editor_project, title):
        raise HTTPException(status_code=500, detail="Failed to persist editor state")
    return {"status": "success", "saved_at": time.time(), "project": HistoryManager.get_project_by_id(project_id)}


@app.post("/api/projects/{project_id}/apply-timeline-edits/start", status_code=202)
async def start_timeline_edit_job(project_id: str, payload: Dict[str, Any] = Body(...)):
    if not HistoryManager.get_project_by_id(project_id):
        raise HTTPException(status_code=404, detail="Project not found")

    with EDITOR_RENDER_JOBS_LOCK:
        if any(
            job["project_id"] == project_id and job["status"] in ("queued", "running")
            for job in EDITOR_RENDER_JOBS.values()
        ):
            raise HTTPException(status_code=409, detail="A render is already running for this project")

        job_id = str(uuid.uuid4())
        job = {
            "job_id": job_id,
            "project_id": project_id,
            "kind": "timeline_render",
            "status": "queued",
            "progress": 0,
            "stage": "Queued",
            "detail": "Waiting for the render worker",
            "created_at": time.time()
        }
        EDITOR_RENDER_JOBS[job_id] = job

    job_payload = dict(payload)
    job_payload["_progress_job_id"] = job_id
    threading.Thread(
        target=_run_editor_render_job,
        args=(job_id, project_id, job_payload),
        daemon=True
    ).start()
    return {"job_id": job_id, "status": "queued"}


@app.get("/api/render-jobs/{job_id}")
@app.get("/api/editor-render-jobs/{job_id}")
async def get_editor_render_job(job_id: str):
    with EDITOR_RENDER_JOBS_LOCK:
        job = EDITOR_RENDER_JOBS.get(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Render job not found")
        return _public_editor_render_job(job)


@app.post("/api/projects/{project_id}/apply-timeline-edits")
async def apply_timeline_edits(project_id: str, payload: Dict[str, Any] = Body(...)):
    """
    Applies timeline edits: re-renders vertical clips from the source video
    based on user-adjusted start/end points, updated titles, and hook captions.
    Re-generates 3 viral thumbnails & docs per clip, updates DB, and returns updated project.
    """
    proj = HistoryManager.get_project_by_id(project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")
    progress_job_id = payload.get("_progress_job_id")
    _set_editor_render_progress(progress_job_id, 5, "Preparing source", "Validating the original video and edited clips")

    source_video = proj.get("source_video")
    if not source_video or not Path(source_video).is_file():
        for d in [UPLOADS_DIR, TEMP_DIR, OUTPUTS_DIR]:
            matches = list(d.glob(f"*{project_id[:8]}*.mp4"))
            for match in matches:
                if match.is_file():
                    source_video = str(match)
                    break
            if source_video and Path(source_video).is_file():
                break
    if not source_video or not Path(source_video).is_file():
        raise HTTPException(status_code=404, detail="Source video file not found on disk")

    editor_project = payload.get("editor_project") or payload.get("project")
    raw_clips = payload.get("clips", [])
    if editor_project and isinstance(editor_project, dict):
        editor_clips = []
        for track in editor_project.get("tracks", []):
            for clip in track.get("clips", []):
                timeline_start = float(clip.get("timelineStartSec", clip.get("timelineStart", 0.0)))
                duration = float(clip.get("timelineDurationSec", clip.get("durationSec", clip.get("durationFrames", 0.0) / 30.0)))
                source_in = float(clip.get("sourceInSec", clip.get("sourceInFrames", 0.0) / 30.0))
                editor_clips.append({
                    "id": clip.get("id"),
                    "start": source_in,
                    "end": source_in + duration,
                    "title": clip.get("title") or clip.get("name") or "Viral Clip",
                    "hook": clip.get("hook") or clip.get("title") or "",
                    "subtitle_style": clip.get("subtitleStyle", "hormozi"),
                    "layout_mode": clip.get("layoutMode", "speaker_focus"),
                    "top_padding": clip.get("topPadding", 0),
                    "bottom_padding": clip.get("bottomPadding", 0),
                    "canvas_top_space": clip.get("canvasTopSpace", 450),
                    "watermark": clip.get("watermark"),
                    "virality_score": clip.get("viralityScore", 92),
                })
        if editor_clips:
            raw_clips = editor_clips
    if not raw_clips or not isinstance(raw_clips, list):
        raise HTTPException(status_code=400, detail="No clips provided to render")

    detector = ViralDetector()
    tracker = SmartFaceTracker()
    renderer = VideoRenderer()
    segments = proj.get("transcript_segments", [])

    rendered_clips = []
    total_clips = len(raw_clips)

    for idx, c_in in enumerate(raw_clips):
        progress_base = 8 + (idx / total_clips) * 82
        progress_span = 82 / total_clips
        clip_label = f"Clip {idx + 1} of {total_clips}"
        _set_editor_render_progress(
            progress_job_id, progress_base, "Analyzing framing",
            f"{clip_label}: preparing safe framing and crop settings"
        )
        start_sec = max(0.0, float(c_in.get("start", c_in.get("start_sec", 0.0))))
        end_sec = float(c_in.get("end", c_in.get("end_sec", start_sec + 30.0)))
        if end_sec <= start_sec:
            end_sec = start_sec + 30.0
        duration = max(3.0, end_sec - start_sec)

        raw_topic = c_in.get("title") or c_in.get("topic") or f"Viral Clip {idx + 1}"
        safe_topic_name = sanitize_topic_filename(raw_topic)
        hook_text = c_in.get("hook", "") or raw_topic
        subtitle_style = c_in.get("subtitle_style", "hormozi")
        layout_mode = c_in.get("layout_mode", "speaker_focus")
        top_padding = float(c_in.get("top_padding", 0.0))
        bottom_padding = float(c_in.get("bottom_padding", 0.0))
        canvas_top_space = int(c_in.get("canvas_top_space", 450))
        color_preset = c_in.get("color_preset", "none")
        watermark_text = c_in.get("watermark", c_in.get("watermark_text"))
        voice_clarifier = bool(c_in.get("voice_clarifier", True))

        # Word alignment for subtitles
        words = []
        if c_in.get("words") and isinstance(c_in["words"], list) and len(c_in["words"]) > 0:
            words = c_in["words"]
        else:
            matching_texts = []
            for s in segments:
                s_st = float(s.get("start", 0))
                s_en = float(s.get("end", 0))
                s_tx = s.get("text", "").strip()
                if s_st <= end_sec and s_en >= start_sec and s_tx:
                    matching_texts.append(s_tx)
            full_text = " ".join(matching_texts) or hook_text or raw_topic
            approx_words = full_text.split()
            w_dur = duration / max(1, len(approx_words))
            for i, w in enumerate(approx_words):
                words.append({
                    "word": w,
                    "start": round(start_sec + i * w_dur, 2),
                    "end": round(start_sec + (i + 0.9) * w_dur, 2)
                })

        # Calculate padding and spaces
        top_pct = max(0.0, min(45.0, float(top_padding))) / 100.0
        bottom_pct = max(0.0, min(45.0, float(bottom_padding))) / 100.0
        if top_pct + bottom_pct > 0.80:
            scale_pad = 0.80 / (top_pct + bottom_pct)
            top_pct *= scale_pad
            bottom_pct *= scale_pad
        has_padding = (top_pct > 0 or bottom_pct > 0)
        top_pad_px = int(round(1920 * top_pct))
        bottom_pad_px = int(round(1920 * bottom_pct))
        available_h = max(100, 1920 - top_pad_px - bottom_pad_px)
        fit_top_space = max(top_pad_px, max(80, min(950, canvas_top_space))) if not has_padding else top_pad_px
        fit_video_h = min(608, available_h)

        crop_filter, actual_layout = tracker.build_layout_filter(
            video_path=source_video,
            start_sec=start_sec,
            duration=duration,
            layout_mode=layout_mode,
            top_padding=top_padding,
            bottom_padding=bottom_padding,
            canvas_bg="solid_black",
            target_w=1080,
            target_h=1920,
            enable_hook_zoom=False,
            canvas_top_space=canvas_top_space
        )

        _set_editor_render_progress(
            progress_job_id, progress_base + progress_span * 0.12, "Preparing subtitles",
            f"{clip_label}: aligning caption timing and visual style"
        )
        ass_path = TEMP_DIR / f"timeline_{project_id[:8]}_{idx}_{int(time.time())}.ass"
        SubtitleGenerator.create_ass_file(
            words=words,
            output_path=ass_path,
            style_key=subtitle_style,
            words_per_batch=3,
            clip_start_offset=start_sec,
            clip_duration=duration,
            topic_headline=hook_text,
            show_headline_banner=bool(hook_text),
            enable_auto_emojis=True,
            layout_mode=actual_layout,
            top_space=fit_top_space,
            video_h=fit_video_h,
            top_padding=top_padding,
            bottom_padding=bottom_padding
        )

        # Output folder organization
        clip_folder_name = f"Clip_{idx+1}_{safe_topic_name}"
        clip_dir = OUTPUTS_DIR / clip_folder_name
        clip_dir.mkdir(parents=True, exist_ok=True)
        out_filename = f"{safe_topic_name}.mp4"
        folder_video_path = clip_dir / out_filename
        flat_video_path = OUTPUTS_DIR / out_filename

        _set_editor_render_progress(
            progress_job_id, progress_base + progress_span * 0.24, "Rendering video",
            f"{clip_label}: FFmpeg is encoding video and audio; this stage may take a few minutes"
        )
        def on_render_progress(percent: float):
            overall_progress = progress_base + progress_span * (0.24 + 0.46 * percent / 100.0)
            _set_editor_render_progress(
                progress_job_id,
                overall_progress,
                "Rendering video",
                f"{clip_label}: video and audio encoding is {round(percent)}% complete"
            )

        rendered_path = renderer.render_clip(
            video_path=source_video,
            start_sec=start_sec,
            duration=duration,
            crop_filter=crop_filter,
            ass_subtitle_path=str(ass_path),
            output_filename=out_filename,
            color_preset=color_preset,
            watermark_text=watermark_text,
            enable_voice_clarifier=voice_clarifier,
            progress_cb=on_render_progress if progress_job_id else None
        )
        if rendered_path.exists() and folder_video_path.resolve() != rendered_path.resolve():
            try:
                shutil.copy2(str(rendered_path), str(folder_video_path))
            except Exception as cpy_err:
                print(f"[Folder Video Warning] {cpy_err}")

        _set_editor_render_progress(
            progress_job_id, progress_base + progress_span * 0.70, "Generating thumbnails",
            f"{clip_label}: creating cover images"
        )
        # 3 Distinct High-Converting TikTok Thumbnails (Editorial, Red Alert, Authority Blueprint)
        thumb_configs = [
            ("thumb_1", "curiosity", "editorial_premium", "#FFE600", "Curiosity Editorial"),
            ("thumb_2", "warning", "red_alert", "#EF4444", "Red Alert Warning"),
            ("thumb_3", "formula", "podcast_authority", "#00E5FF", "Authority Blueprint")
        ]
        generated_covers = []
        for t_suffix, t_arch, t_style, t_accent, t_label in thumb_configs:
            t_filename = f"{safe_topic_name}_{t_suffix}.jpg"
            t_folder_path = clip_dir / t_filename
            t_flat_path = OUTPUTS_DIR / t_filename
            try:
                TikTokThumbnailDesigner.create_tiktok_thumbnail(
                    video_path=str(rendered_path),
                    output_jpg_path=str(t_folder_path),
                    topic=raw_topic,
                    title=raw_topic,
                    hook=hook_text,
                    transcript=" ".join(w.get("word", "") for w in words),
                    crop_filter=crop_filter,
                    source_clean_video=source_video,
                    timestamp_sec=start_sec + min(2.0, max(0.8, duration * 0.2)),
                    copy_data=None,
                    style=t_style,
                    accent_color=t_accent
                )
                if t_folder_path.exists():
                    shutil.copy2(str(t_folder_path), str(t_flat_path))
                    generated_covers.append(f"{clip_folder_name}/{t_filename}")
            except Exception as t_err:
                print(f"[Thumbnail Error] {t_label}: {t_err}")
                try:
                    renderer.generate_thumbnail(str(rendered_path), str(t_folder_path), timestamp_sec=1.0)
                    if t_folder_path.exists():
                        shutil.copy2(str(t_folder_path), str(t_flat_path))
                        generated_covers.append(f"{clip_folder_name}/{t_filename}")
                except Exception:
                    pass

        default_cover = generated_covers[0] if generated_covers else f"{safe_topic_name}.jpg"

        _set_editor_render_progress(
            progress_job_id, progress_base + progress_span * 0.90, "Preparing clip details",
            f"{clip_label}: generating social copy and project documents"
        )
        # Generate Social Media Kit & Docs
        part_info = f"Part {idx + 1}"
        social_kit = detector.generate_social_kit(
            title=raw_topic,
            hook=hook_text,
            transcript=" ".join(w.get("word", "") for w in words),
            series_part=part_info
        )
        clip_data_for_docs = {
            "topic": raw_topic,
            "title": raw_topic,
            "filename": out_filename,
            "part_info": part_info,
            "start_sec": start_sec,
            "end_sec": end_sec,
            "duration": round(duration, 2),
            "hook": hook_text,
            "social_kit": social_kit
        }
        try:
            clip_docs_paths = create_clip_docs_files(clip_data_for_docs, output_dir=clip_dir, base_name=safe_topic_name)
        except Exception as doc_err:
            print(f"[Timeline Docs Warning] {doc_err}")
            clip_docs_paths = {}

        clip_id = c_in.get("id") or str(uuid.uuid4())
        rendered_clips.append({
            "id": clip_id,
            "project_id": project_id,
            "topic": raw_topic,
            "title": raw_topic,
            "hook": hook_text,
            "virality_score": int(c_in.get("virality_score", 92)),
            "narrative_breakdown": {
                "hook_score": 92,
                "story_score": 90,
                "conclusion_score": 91
            },
            "start": start_sec,
            "end": end_sec,
            "start_sec": start_sec,
            "end_sec": end_sec,
            "duration": round(duration, 2),
            "output_file": str(folder_video_path if folder_video_path.exists() else rendered_path),
            "filename": out_filename,
            "folder_name": clip_folder_name,
            "folder_video": f"{clip_folder_name}/{safe_topic_name}.mp4",
            "cover": default_cover,
            "covers": generated_covers,
            "docs_file": f"{clip_folder_name}/{safe_topic_name}_docs.docx",
            "docs_paths": clip_docs_paths,
            "part_info": part_info,
            "series_id": project_id[:8],
            "subtitle_style": subtitle_style,
            "layout_mode": actual_layout,
            "top_padding": float(top_padding),
            "bottom_padding": float(bottom_padding),
            "social_kit": social_kit,
            "words": words
        })
        _set_editor_render_progress(
            progress_job_id, progress_base + progress_span * 0.98, "Finishing clip",
            f"{clip_label}: saving generated files"
        )

    # Save to database
    if payload.get("editor_project") or payload.get("project"):
        submitted_project = payload.get("editor_project") or payload.get("project")
        if isinstance(submitted_project, dict):
            HistoryManager.save_editor_project(project_id, submitted_project, submitted_project.get("title"))
    HistoryManager.replace_project_clips(project_id, rendered_clips)
    updated_project = HistoryManager.get_project_by_id(project_id)
    _set_editor_render_progress(progress_job_id, 98, "Saving project", "Updating the project library")
    return {"status": "success", "project": updated_project, "clips": rendered_clips}

@app.delete("/api/clips/{clip_id}")
async def delete_clip(clip_id: str):
    """Deletes a single clip and its video file."""
    success = HistoryManager.delete_single_clip(clip_id)
    return {"status": "success", "deleted_clip_id": clip_id}

@app.get("/api/outputs")
async def list_outputs():
    """List all previously generated clips."""
    # First check HistoryManager
    all_projects = HistoryManager.get_all_projects()
    if all_projects:
        flat_clips = []
        for p in all_projects:
            for c in p.get("clips", []):
                flat_clips.append({
                    **c,
                    "project_title": p.get("title", "Podcast Session"),
                    "project_id": p.get("id")
                })
        return {"clips": flat_clips}

    # Fallback to direct output directory scanning
    clips = []
    for f in OUTPUTS_DIR.glob("*.mp4"):
        stat = f.stat()
        clips.append({
            "filename": f.name,
            "title": f.stem.replace("_", " ").title(),
            "duration": 30.0,
            "virality_score": 92,
            "subtitle_style": "Hormozi",
            "created_at": stat.st_mtime
        })
    clips.sort(key=lambda x: x["created_at"], reverse=True)
    return {"clips": clips}

@app.get("/api/video/{filename}")
async def stream_video(filename: str):
    """Stream vertical video file with byte-range support."""
    video_path = OUTPUTS_DIR / filename
    if not video_path.exists():
        raise HTTPException(status_code=404, detail="Video file not found")
    return FileResponse(
        path=str(video_path),
        media_type="video/mp4",
        filename=filename
    )

@app.get("/api/projects/{project_id}/download-zip")
async def download_project_zip(project_id: str):
    """Downloads all generated 9:16 vertical clips for a project organized in separate topic folders with 3 viral thumbnails & docs."""
    all_projects = HistoryManager.get_all_projects()
    project = next((p for p in all_projects if p["id"] == project_id), None)
    if not project or not project.get("clips"):
        raise HTTPException(status_code=404, detail="Project or clips not found")

    raw_title = project.get("title", "project")
    safe_title = re.sub(r"[^\w\-]", "_", raw_title).strip("_") or "podcast_clips"
    filename = f"{safe_title}_all_clips.zip"
    zip_path = TEMP_DIR / f"{project_id}_{filename}"

    with zipfile.ZipFile(zip_path, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        package_clips_into_zip(zf, project["clips"], session_title=raw_title)

    return FileResponse(
        path=str(zip_path),
        filename=filename,
        media_type="application/zip"
    )

@app.get("/api/jobs/{job_id}/download-zip")
async def download_job_zip(job_id: str):
    """Downloads all clips generated in active job session organized in separate topic folders with 3 viral thumbnails & docs."""
    if job_id not in JOBS or not JOBS[job_id].get("result"):
        raise HTTPException(status_code=404, detail="Job or clips not found")

    clips = JOBS[job_id]["result"].get("clips", [])
    if not clips:
        raise HTTPException(status_code=404, detail="No clips available in this session")

    session_name = f"ClipForge_Session_{job_id[:8]}"
    filename = f"{session_name}_all_clips.zip"
    zip_path = TEMP_DIR / f"{job_id}_{filename}"

    with zipfile.ZipFile(zip_path, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        package_clips_into_zip(zf, clips, session_title=session_name)

    return FileResponse(
        path=str(zip_path),
        filename=filename,
        media_type="application/zip"
    )

@app.get("/api/projects/{project_id}/download-docs")
async def download_project_docs(project_id: str, format: str = "docx"):
    """Downloads a docs file containing topic, title, and hashtags for all clips in the project."""
    all_projects = HistoryManager.get_all_projects()
    project = next((p for p in all_projects if p["id"] == project_id), None)
    if not project or not project.get("clips"):
        raise HTTPException(status_code=404, detail="Project or clips not found")

    raw_title = project.get("title", "Project")
    safe_title = re.sub(r"[^\w\-]", "_", raw_title).strip("_") or "session"
    if format.lower() == "txt":
        content = generate_session_text(project["clips"], session_title=raw_title)
        return Response(
            content=content,
            media_type="text/plain; charset=utf-8",
            headers={"Content-Disposition": f"attachment; filename={safe_title}_clips_info.txt"}
        )
    docx_bytes = generate_session_docx(project["clips"], session_title=raw_title)
    return Response(
        content=docx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f"attachment; filename={safe_title}_clips_info.docx"}
    )

@app.get("/api/jobs/{job_id}/download-docs")
async def download_job_docs(job_id: str, format: str = "docx"):
    """Downloads a docs file containing topic, title, and hashtags for all clips in the active job session."""
    if job_id not in JOBS or not JOBS[job_id].get("result"):
        raise HTTPException(status_code=404, detail="Job or clips not found")

    clips = JOBS[job_id]["result"].get("clips", [])
    if not clips:
        raise HTTPException(status_code=404, detail="No clips available in this session")

    session_name = f"ClipForge_Session_{job_id[:8]}"
    if format.lower() == "txt":
        content = generate_session_text(clips, session_title=session_name)
        return Response(
            content=content,
            media_type="text/plain; charset=utf-8",
            headers={"Content-Disposition": f"attachment; filename={session_name}_clips_info.txt"}
        )
    docx_bytes = generate_session_docx(clips, session_title=session_name)
    return Response(
        content=docx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f"attachment; filename={session_name}_clips_info.docx"}
    )

class TrimClipRequest(BaseModel):
    clip_id: str
    delta_start: float = 0.0
    delta_end: float = 0.0
    new_start: Optional[float] = None
    new_end: Optional[float] = None
    subtitle_style: Optional[str] = None
    layout_mode: Optional[str] = None

@app.post("/api/clips/trim")
async def trim_clip(req: TrimClipRequest):
    """
    Fine-nudge trimming engine (±1s / ±2s buttons).
    Rapidly re-slices and re-renders a single clip with GPU NVENC in ~2-3 seconds,
    re-aligns subtitles, and updates the database in place!
    """
    clip = HistoryManager.get_clip_by_id(req.clip_id)
    if not clip:
        raise HTTPException(status_code=404, detail="Clip not found in history")

    source_video = clip.get("source_video")
    if not source_video or not Path(source_video).is_file():
        # Fallback: check UPLOADS_DIR for matching project files
        possible = list(UPLOADS_DIR.glob(f"*{clip.get('project_id', '')}*"))
        if possible:
            source_video = str(possible[0])
        else:
            raise HTTPException(status_code=400, detail="Original source video not found on disk for re-trimming.")

    curr_start = float(clip.get("start_sec") or 0.0)
    curr_end = float(clip.get("end_sec") or (curr_start + clip.get("duration", 30.0)))

    if req.new_start is not None:
        target_start = max(0.0, float(req.new_start))
    else:
        target_start = max(0.0, curr_start + req.delta_start)

    if req.new_end is not None:
        target_end = max(target_start + 5.0, float(req.new_end))
    else:
        target_end = max(target_start + 5.0, curr_end + req.delta_end)

    new_duration = target_end - target_start
    style = req.subtitle_style or clip.get("subtitle_style", "hormozi")
    layout = req.layout_mode or clip.get("layout_mode", "speaker_focus")

    top_padding = float(clip.get("top_padding") or 0.0)
    bottom_padding = float(clip.get("bottom_padding") or 0.0)

    pipeline = ClipForgePipeline()

    # Step 1: Reframe with unified layout engine
    crop_filter, actual_layout = pipeline.face_tracker.build_layout_filter(
        video_path=source_video,
        start_sec=target_start,
        duration=new_duration,
        layout_mode=layout,
        top_padding=top_padding,
        bottom_padding=bottom_padding
    )

    # Step 2: Subtitles (transcribe segment)
    from core.subtitles import SubtitleGenerator
    from core.config import TEMP_DIR
    sub_words = pipeline.transcriber.transcribe_segment(source_video, target_start, new_duration)
    ass_path = TEMP_DIR / f"trim_{req.clip_id}_{int(target_start)}.ass"
    SubtitleGenerator.create_ass_file(
        words=sub_words,
        output_path=ass_path,
        style_key=style,
        clip_start_offset=target_start,
        clip_duration=new_duration,
        topic_headline=clip.get("title", ""),
        part_info=clip.get("part_info", ""),
        show_headline_banner=True,
        layout_mode=actual_layout,
        top_padding=top_padding,
        bottom_padding=bottom_padding
    )

    # Step 3: Render MP4 with GPU NVENC
    out_filename = f"trimmed_{clip['project_id']}_{int(target_start)}_{int(target_end)}.mp4"
    rendered_path = pipeline.renderer.render_clip(
        video_path=source_video,
        start_sec=target_start,
        duration=new_duration,
        crop_filter=crop_filter,
        ass_subtitle_path=str(ass_path),
        output_filename=out_filename
    )

    # Step 4: Update Social Kit
    full_text = " ".join(w["word"] for w in sub_words) if sub_words else clip.get("full_transcript", "")
    social_kit = pipeline.viral_detector.generate_social_kit(
        title=clip.get("title", ""),
        hook=clip.get("hook", ""),
        transcript=full_text,
        series_part=clip.get("part_info", "")
    )

    # Step 5: Update History DB
    HistoryManager.update_clip(req.clip_id, {
        "filename": out_filename,
        "duration": round(new_duration, 2),
        "start_sec": round(target_start, 2),
        "end_sec": round(target_end, 2),
        "full_transcript": full_text,
        "social_kit": social_kit
    })

    updated = HistoryManager.get_clip_by_id(req.clip_id)
    return {"status": "success", "clip": updated}


@app.get("/api/bgm/tracks")
async def get_bgm_tracks():
    """Returns available royalty-free background music tracks."""
    return {"tracks": BGMManager.get_tracks()}


@app.post("/api/clips/reburn")
async def reburn_clip_subtitles(payload: Dict[str, Any] = Body(...)):
    """
    In-Browser Subtitle Editor Re-Burn Endpoint:
    Re-generates ASS subtitles with custom user-edited words & power colors,
    and rapidly re-renders the 9:16 clip via NVIDIA NVENC in ~2 seconds!
    """
    clip_id = payload.get("clip_id")
    words = payload.get("words", [])
    subtitle_style = payload.get("subtitle_style", "hormozi")
    progress_bar_color = payload.get("progress_bar_color", "#00E5FF")
    bgm_track = payload.get("bgm_track", "none")
    bgm_volume = float(payload.get("bgm_volume", 0.12))

    clip = HistoryManager.get_clip_by_id(clip_id)
    if not clip:
        raise HTTPException(status_code=404, detail="Clip not found in history.")

    source_video = clip.get("source_video")
    if not source_video or not Path(source_video).is_file():
        raise HTTPException(status_code=400, detail="Original source video not found on disk for re-burn.")

    start_sec = float(clip.get("start_sec", 0.0))
    duration = float(clip.get("duration", 30.0))
    layout_mode = payload.get("layout_mode", clip.get("layout_mode", "speaker_focus"))
    topic_title = payload.get("title", clip.get("title", ""))
    part_info = clip.get("part_info", "")
    top_padding = float(payload.get("top_padding", payload.get("pad_top", clip.get("top_padding", 0.0))))
    bottom_padding = float(payload.get("bottom_padding", payload.get("pad_bottom", clip.get("bottom_padding", 0.0))))
    canvas_bg = payload.get("canvas_bg", clip.get("canvas_bg", "solid_black"))
    top_space = int(payload.get("top_space", clip.get("canvas_top_space", 450)))

    # Step 1: Compute framing filter via unified layout engine
    tracker = SmartFaceTracker()
    crop_filter, actual_layout = tracker.build_layout_filter(
        video_path=source_video,
        start_sec=start_sec,
        duration=duration,
        layout_mode=layout_mode,
        top_padding=top_padding,
        bottom_padding=bottom_padding,
        canvas_bg=canvas_bg,
        target_w=1080,
        target_h=1920,
        enable_hook_zoom=False,
        canvas_top_space=top_space
    )

    # Step 2: Generate updated .ass subtitle file with safe area spacing
    ass_path = TEMP_DIR / f"reburn_{clip_id}_{int(time.time())}.ass"
    SubtitleGenerator.create_ass_file(
        words=words,
        output_path=ass_path,
        style_key=subtitle_style,
        words_per_batch=3,
        clip_start_offset=start_sec,
        clip_duration=duration,
        topic_headline=topic_title,
        part_info=part_info,
        show_headline_banner=True,
        enable_auto_emojis=True,
        layout_mode=actual_layout,
        top_padding=top_padding,
        bottom_padding=bottom_padding
    )

    # Step 3: Fast GPU re-render
    renderer = VideoRenderer()
    out_filename = f"edited_{clip['project_id']}_{int(start_sec)}_{int(time.time())}.mp4"
    rendered_path = renderer.render_clip(
        video_path=source_video,
        start_sec=start_sec,
        duration=duration,
        crop_filter=crop_filter,
        ass_subtitle_path=str(ass_path),
        output_filename=out_filename,
        progress_bar_color=progress_bar_color,
        bgm_track=bgm_track,
        bgm_volume=bgm_volume
    )

    # Step 4: Update full transcript and history DB
    full_text = " ".join(w.get("word", "") for w in words)
    HistoryManager.update_clip(clip_id, {
        "filename": out_filename,
        "subtitle_style": subtitle_style,
        "full_transcript": full_text,
        "words_json": json.dumps(words),
        "top_padding": top_padding,
        "bottom_padding": bottom_padding,
        "layout_mode": actual_layout,
        "output_file": str(rendered_path)
    })

    updated = HistoryManager.get_clip_by_id(clip_id)
    return {
        "status": "success",
        "clip": updated,
        "filename": out_filename,
        "output_file": str(rendered_path)
    }


@app.post("/api/ai/ollama-generate")
async def generate_with_ollama(payload: Dict[str, Any] = Body(...)):
    """Run a prompt through the centralized, installed-model-aware AI engine."""
    prompt = payload.get("prompt", "")
    try:
        result = MultiModelAIEngine.get_instance().generate_text(
            prompt,
            model=payload.get("model"),
            system_prompt=str(payload.get("system_prompt", "")),
        )
    except AIEngineError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    return {
        "source": result["source"],
        "model": result["model"],
        "response": result["text"],
        "warning": result.get("warning"),
    }


@app.get("/api/ai/ollama-status")
async def get_ollama_status():
    """Returns local Ollama status, connectivity, and active model."""
    return MultiModelAIEngine.get_instance().get_status()


@app.post("/api/podcast/summarize")
async def get_podcast_summary(payload: Dict[str, Any] = Body(...)):
    """
    Returns an executive summary and topic map for a project or active video.
    """
    project_id = payload.get("project_id")
    if project_id:
        proj = HistoryManager.get_project_by_id(project_id)
        if proj and proj.get("podcast_summary"):
            return {
                "status": "success",
                "summary": proj["podcast_summary"],
                "transcript": proj.get("transcript_segments", [])
            }

    segments = payload.get("segments", [])
    duration = float(payload.get("duration", 60.0))
    if segments:
        detector = ViralDetector()
        summary = detector.generate_podcast_summary(segments, duration)
        return {"status": "success", "summary": summary}

    raise HTTPException(status_code=400, detail="Missing project_id or transcript segments")


@app.post("/api/clips/custom-extract/start", status_code=202)
async def start_custom_extract_job(payload: Dict[str, Any] = Body(...)):
    project_id = payload.get("project_id")
    if not isinstance(project_id, str) or not project_id:
        raise HTTPException(status_code=400, detail="project_id is required")

    project = HistoryManager.get_project_by_id(project_id)
    if not project or not _resolve_video_source(project_id):
        raise HTTPException(status_code=404, detail="Source video not found for this project.")

    try:
        start_sec = float(payload.get("start_sec", 0.0))
        end_sec = float(payload.get("end_sec", start_sec + 30.0))
        project_duration = float(project.get("duration") or 0.0)
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail="Chapter start and end must be valid numbers")
    if not math.isfinite(start_sec) or not math.isfinite(end_sec):
        raise HTTPException(status_code=400, detail="Chapter start and end must be finite numbers")
    if start_sec < 0 or end_sec <= start_sec or (project_duration and start_sec >= project_duration):
        raise HTTPException(status_code=400, detail="Chapter time range is outside the source video")
    if project_duration:
        end_sec = min(end_sec, project_duration)
    if end_sec <= start_sec:
        raise HTTPException(status_code=400, detail="Chapter time range is outside the source video")

    with EDITOR_RENDER_JOBS_LOCK:
        if any(
            job["project_id"] == project_id and job["status"] in ("queued", "running")
            for job in EDITOR_RENDER_JOBS.values()
        ):
            raise HTTPException(status_code=409, detail="Another render is already running for this project")

        job_id = str(uuid.uuid4())
        EDITOR_RENDER_JOBS[job_id] = {
            "job_id": job_id,
            "project_id": project_id,
            "kind": "chapter_extraction",
            "status": "queued",
            "progress": 0,
            "stage": "Queued",
            "detail": "Waiting to extract this topic chapter",
            "created_at": time.time()
        }

    job_payload = dict(payload)
    job_payload["start_sec"] = start_sec
    job_payload["end_sec"] = end_sec
    job_payload["_progress_job_id"] = job_id
    threading.Thread(
        target=_run_custom_extract_job,
        args=(job_id, job_payload),
        daemon=True
    ).start()
    return {"job_id": job_id, "status": "queued"}


@app.post("/api/clips/custom-extract")
async def extract_custom_clip(payload: Dict[str, Any] = Body(...)):
    """
    Extracts a custom 9:16 vertical short from specified timestamps.
    Automatically formats subtitles, facial tracking, and BGM ducking!
    """
    project_id = payload.get("project_id")
    progress_job_id = payload.get("_progress_job_id")
    start_sec = float(payload.get("start_sec", 0.0))
    end_sec = float(payload.get("end_sec", start_sec + 30.0))
    custom_title = payload.get("title", "CUSTOM HIGHLIGHT")
    subtitle_style = payload.get("subtitle_style", "hormozi")
    layout_mode = payload.get("layout_mode", "speaker_focus")
    canvas_top_space = int(payload.get("top_space", payload.get("canvas_top_space", 450)))
    canvas_bg = payload.get("canvas_bg", "solid_black")
    progress_bar_color = payload.get("progress_bar_color", "#00E5FF")
    bgm_track = payload.get("bgm_track", "none")
    bgm_volume = float(payload.get("bgm_volume", 0.12))

    duration = max(3.0, end_sec - start_sec)

    proj = HistoryManager.get_project_by_id(project_id)
    resolved_source = _resolve_video_source(project_id)
    if not proj or not resolved_source:
        raise HTTPException(status_code=404, detail="Source video not found for this project.")
    _set_editor_render_progress(
        progress_job_id, 5, "Preparing chapter",
        "Finding transcript text and checking the selected chapter range"
    )

    source_video = str(resolved_source)
    clip_id = f"{project_id}_custom_{uuid.uuid4().hex[:12]}"

    segments = proj.get("transcript_segments", [])
    matching_text = []
    start_idx = None
    end_idx = None
    for s in segments:
        if s.get("start", 0) <= end_sec and s.get("end", 0) >= start_sec:
            if start_idx is None:
                start_idx = s
            end_idx = s
            matching_text.append(s.get("text", ""))

    # Snapping custom selections to Whisper sentence boundaries prevents
    # manually selected clips from starting or ending on half of a thought.
    if start_idx is not None:
        start_sec = max(0.0, float(start_idx.get("start", start_sec)) - 0.15)
        end_sec = float(end_idx.get("end", end_sec)) + 0.25
        duration = max(3.0, end_sec - start_sec)

    full_text = " ".join(matching_text) or custom_title
    _set_editor_render_progress(
        progress_job_id, 12, "Transcribing chapter captions",
        "Extracting word-level caption timings from the selected audio"
    )
    pipeline = ClipForgePipeline()
    custom_words = pipeline.transcriber.transcribe_segment(source_video, start_sec, duration)
    if not custom_words:
        approx_words = full_text.split()
        w_dur = duration / max(1, len(approx_words))
        custom_words = [
            {
                "word": word,
                "start": round(start_sec + i * w_dur, 2),
                "end": round(start_sec + (i + 0.9) * w_dur, 2)
            }
            for i, word in enumerate(approx_words)
        ]
    chapter_hook = (
        str(custom_words[0].get("word") or "").strip()
        if custom_words else custom_title
    ) or custom_title

    _set_editor_render_progress(
        progress_job_id, 30, "Analyzing framing",
        "Preparing vertical framing for the chapter clip"
    )
    top_padding = float(payload.get("top_padding", payload.get("pad_top", 0.0)))
    bottom_padding = float(payload.get("bottom_padding", payload.get("pad_bottom", 0.0)))
    top_pct = max(0.0, min(45.0, float(top_padding))) / 100.0
    bottom_pct = max(0.0, min(45.0, float(bottom_padding))) / 100.0
    if top_pct + bottom_pct > 0.80:
        scale_pad = 0.80 / (top_pct + bottom_pct)
        top_pct *= scale_pad
        bottom_pct *= scale_pad
    has_padding = (top_pct > 0 or bottom_pct > 0)
    top_pad_px = int(round(1920 * top_pct))
    bottom_pad_px = int(round(1920 * bottom_pct))
    available_h = max(100, 1920 - top_pad_px - bottom_pad_px)

    fit_top_space = max(top_pad_px, max(80, min(950, canvas_top_space))) if not has_padding else top_pad_px
    fit_video_h = min(608, available_h)

    # Compute framing crop via unified layout engine
    tracker = SmartFaceTracker()
    crop_filter, actual_layout = tracker.build_layout_filter(
        video_path=source_video,
        start_sec=start_sec,
        duration=duration,
        layout_mode=layout_mode,
        top_padding=top_padding,
        bottom_padding=bottom_padding,
        canvas_bg=canvas_bg,
        target_w=1080,
        target_h=1920,
        enable_hook_zoom=False,
        canvas_top_space=canvas_top_space
    )

    # Generate .ass subtitles
    _set_editor_render_progress(
        progress_job_id, 38, "Preparing subtitles",
        "Applying the selected caption style and topic headline"
    )
    ass_path = TEMP_DIR / f"custom_{clip_id}.ass"
    SubtitleGenerator.create_ass_file(
        words=custom_words,
        output_path=ass_path,
        style_key=subtitle_style,
        words_per_batch=3,
        clip_start_offset=start_sec,
        clip_duration=duration,
        topic_headline=custom_title,
        show_headline_banner=True,
        enable_auto_emojis=True,
        layout_mode=actual_layout,
        top_space=fit_top_space,
        video_h=fit_video_h,
        top_padding=top_padding,
        bottom_padding=bottom_padding
    )

    # Fast GPU Render
    renderer = VideoRenderer()
    out_filename = f"custom_{project_id[:8]}_{int(start_sec)}_{clip_id[-8:]}.mp4"
    _set_editor_render_progress(
        progress_job_id, 48, "Rendering chapter",
        "FFmpeg is encoding the vertical video and audio"
    )

    def on_render_progress(percent: float):
        _set_editor_render_progress(
            progress_job_id,
            48 + 0.40 * percent,
            "Rendering chapter",
            f"Video and audio encoding is {round(percent)}% complete"
        )

    rendered_path = renderer.render_clip(
        video_path=source_video,
        start_sec=start_sec,
        duration=duration,
        crop_filter=crop_filter,
        ass_subtitle_path=str(ass_path),
        output_filename=out_filename,
        progress_bar_color=progress_bar_color,
        bgm_track=bgm_track,
        bgm_volume=bgm_volume,
        progress_cb=on_render_progress if progress_job_id else None
    )

    # Generate matching AI TikTok cover thumbnail
    _set_editor_render_progress(
        progress_job_id, 90, "Creating chapter cover",
        "Designing a matching thumbnail and social caption"
    )
    thumb_path = OUTPUTS_DIR / f"{Path(out_filename).stem}.jpg"
    try:
        TikTokThumbnailDesigner.create_tiktok_thumbnail(
            video_path=str(rendered_path),
            output_jpg_path=str(thumb_path),
            topic=custom_title,
            title=custom_title,
            hook=chapter_hook,
            transcript=full_text,
            crop_filter=crop_filter,
            source_clean_video=source_video,
            timestamp_sec=start_sec + min(2.0, max(0.5, duration * 0.2))
        )
    except Exception as te:
        print(f"[Thumbnail Warning] Custom clip thumbnail error: {te}")

    # Generate social media kit
    detector = ViralDetector()
    social_kit = detector.generate_social_kit(
        title=custom_title,
        hook=chapter_hook,
        transcript=full_text
    )

    new_clip = {
        "id": clip_id,
        "project_id": project_id,
        "filename": out_filename,
        "cover": f"{Path(out_filename).stem}.jpg",
        "title": custom_title,
        "hook": chapter_hook,
        "virality_score": 93,
        "narrative_breakdown": {"hook_score": 93, "story_score": 92, "conclusion_score": 94},
        "duration": round(duration, 2),
        "start": start_sec,
        "end": end_sec,
        "subtitle_style": subtitle_style,
        "layout_mode": layout_mode,
        "top_padding": top_padding,
        "bottom_padding": bottom_padding,
        "social_kit": social_kit,
        "full_transcript": full_text,
        "words": custom_words,
        "output_file": str(rendered_path)
    }

    # Save into DB
    _set_editor_render_progress(
        progress_job_id, 97, "Adding clip to project",
        "Saving the rendered clip to this project's library"
    )
    HistoryManager.add_single_clip(new_clip)
    _set_editor_render_progress(progress_job_id, 99, "Refreshing project", "Chapter clip saved")

    return {"status": "success", "clip": new_clip}

@app.post("/api/clips/{clip_id}/thumbnail/generate-hooks")
async def generate_clip_thumbnail_hooks(clip_id: str, payload: Dict[str, Any] = Body(default={})):
    """Generates four transcript-grounded TikTok thumbnail copy options."""
    clip = HistoryManager.get_clip_by_id(clip_id)
    topic = payload.get("topic") or (clip.get("title") if clip else "") or "PODCAST TOPIC"
    transcript = payload.get("transcript") or (clip.get("full_transcript") if clip else "") or ""
    hook = payload.get("hook") or (clip.get("hook") if clip else "") or ""

    archetypes = [
        ("curiosity", "🤯 Curiosity Loop"),
        ("warning", "⚠️ Shock / Warning"),
        ("formula", "📋 3-Rule Blueprint"),
        ("callout", "🎯 Audience Callout")
    ]

    copies = await run_in_threadpool(
        TikTokThumbnailDesigner.generate_ai_copy_variations,
        topic=topic,
        title=topic,
        hook=hook,
        transcript=transcript,
        archetypes=[key for key, _label in archetypes],
    )
    results = []
    for arch_key, arch_label in archetypes:
        copy = copies[arch_key]
        copy["archetype"] = arch_key
        copy["label"] = arch_label
        copy["full_headline"] = f"{copy.get('headline_1', '')} {copy.get('headline_2', '')}".strip()
        results.append(copy)

    return {
        "status": "success",
        "topic": topic,
        "hooks": results,
        "source": results[0].get("generation_source", "heuristic_fallback") if results else "none",
        "model": results[0].get("model", "") if results else "",
        "warning": results[0].get("generation_warning") if results else None,
    }

@app.post("/api/clips/{clip_id}/thumbnail/regenerate")
async def regenerate_clip_thumbnail(clip_id: str, payload: Dict[str, Any] = Body(default={})):
    """Regenerates the AI TikTok cover thumbnail for a specific clip with custom styles, colors, and hooks."""
    clip = HistoryManager.get_clip_by_id(clip_id)
    if not clip:
        raise HTTPException(status_code=404, detail="Clip not found")

    fn = clip.get("filename")
    if not fn:
        raise HTTPException(status_code=400, detail="Clip has no video filename")

    vid_path = OUTPUTS_DIR / fn
    if not vid_path.exists():
        raise HTTPException(status_code=404, detail="Rendered video not found on disk")

    thumb_path = OUTPUTS_DIR / f"{Path(fn).stem}.jpg"
    topic = payload.get("topic") or clip.get("title") or "HIGHLIGHT"
    hook = payload.get("hook") or clip.get("hook") or ""
    transcript = payload.get("transcript") or clip.get("full_transcript") or ""

    style = payload.get("style", "hormozi")
    accent_color = payload.get("accent_color", "#FFE600")
    archetype = payload.get("archetype", "curiosity")
    timestamp_sec = float(payload.get("timestamp_sec", 1.2))

    # Preserve the user's edits while filling any unfinished fields from a grounded draft.
    headline_1 = str(payload.get("headline_1") or "").strip()
    headline_2 = str(payload.get("headline_2") or "").strip()
    copy_data = None
    if not headline_1 or not headline_2:
        copy_data = await run_in_threadpool(
            TikTokThumbnailDesigner.generate_ai_copy,
            topic=topic,
            title=clip.get("title") or topic,
            hook=hook,
            transcript=transcript,
            archetype=archetype,
        )
    if copy_data is None:
        copy_data = {
            "archetype": archetype,
            "exact_topic": TikTokThumbnailDesigner.extract_clean_topic(
                topic=topic, title=clip.get("title") or topic, hook=hook, transcript=transcript
            ),
            "category": str(payload.get("category") or "INSIGHT").strip()[:20].upper(),
            "pill_badge": str(payload.get("category") or "INSIGHT").strip()[:20].upper(),
            "headline_white": headline_1[:38].upper(),
            "headline_yellow_1": headline_2[:38].upper(),
            "headline_yellow_2": str(payload.get("subheadline") or "").strip()[:40].upper(),
            "headline_1": headline_1[:38].upper(),
            "headline_2": headline_2[:38].upper(),
            "subheadline": str(payload.get("subheadline") or "").strip()[:40].upper(),
            "speaker_name": "PODCAST GUEST",
            "speaker_tag": "PODCAST CLIP",
            "generation_source": payload.get("copy_source") or "custom",
            "model": payload.get("copy_model") or "",
            "generation_warning": payload.get("copy_warning") or None,
        }
    else:
        copy_data.update({
            "archetype": archetype,
            "category": str(payload.get("category") or copy_data["category"]).strip()[:20].upper(),
            "pill_badge": str(payload.get("category") or copy_data["pill_badge"]).strip()[:20].upper(),
            "headline_white": headline_1[:38].upper() or copy_data["headline_white"],
            "headline_yellow_1": headline_2[:38].upper() or copy_data["headline_yellow_1"],
            "headline_yellow_2": str(payload.get("subheadline") or "").strip()[:40].upper(),
            "headline_1": headline_1[:38].upper() or copy_data["headline_white"],
            "headline_2": headline_2[:38].upper() or copy_data["headline_yellow_1"],
            "subheadline": str(payload.get("subheadline") or "").strip()[:40].upper(),
            "generation_source": (
                payload.get("copy_source")
                or ("custom" if headline_1 or headline_2 else copy_data.get("generation_source", "ollama"))
            ),
            "model": payload.get("copy_model") or copy_data.get("model", ""),
            "generation_warning": payload.get("copy_warning") or copy_data.get("generation_warning"),
        })

    await run_in_threadpool(
        TikTokThumbnailDesigner.create_tiktok_thumbnail,
        video_path=str(vid_path),
        output_jpg_path=str(thumb_path),
        topic=topic,
        title=clip.get("title") or topic,
        hook=hook,
        transcript=transcript,
        timestamp_sec=timestamp_sec,
        copy_data=copy_data,
        style=style,
        accent_color=accent_color,
        archetype=archetype,
    )

    return {
        "status": "success",
        "thumbnail_url": f"/media/{clip['project_id']}/{thumb_path.name}?t={int(time.time())}",
        "filename": thumb_path.name,
        "style": style,
        "accent_color": accent_color,
        "timestamp_sec": timestamp_sec,
        "copy_data": copy_data
    }


@app.post("/api/clips/{clip_id}/set-cover")
async def set_active_clip_cover(clip_id: str, payload: Dict[str, Any] = Body(...)):
    """Sets the chosen cover thumbnail as the default primary cover for the clip."""
    cover_file = payload.get("cover")
    if not cover_file:
        raise HTTPException(status_code=400, detail="Cover filename is required")

    clip = HistoryManager.get_clip_by_id(clip_id)
    if not clip:
        raise HTTPException(status_code=404, detail="Clip not found")

    HistoryManager.update_clip(clip_id, {"cover": cover_file})

    # Also update in active JOBS cache if present
    for jid, job in JOBS.items():
        if job.get("result") and job["result"].get("clips"):
            for c in job["result"]["clips"]:
                if c.get("id") == clip_id:
                    c["cover"] = cover_file

    project_id = clip.get("project_id", "")
    return {
        "status": "success",
        "clip_id": clip_id,
        "cover": cover_file,
        "thumbnail_url": f"/media/{project_id}/{cover_file}?t={int(time.time())}"
    }


if __name__ == "__main__":
    import socket
    import sys
    import uvicorn

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_check:
        server_check.settimeout(0.25)
        if server_check.connect_ex(("127.0.0.1", 8000)) == 0:
            print("ClipForge is already running at http://127.0.0.1:8000; not starting a duplicate server.")
            sys.exit(0)

    print("\n" + "=" * 60)
    print("  ClipForge AI Studio is starting up!")
    print("  Open your browser at: http://localhost:8000")
    print("=" * 60 + "\n")
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=False)
