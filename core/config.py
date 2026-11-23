import os
import sys
from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent.parent
STORAGE_DIR = BASE_DIR / "storage"
UPLOADS_DIR = STORAGE_DIR / "uploads"
OUTPUTS_DIR = STORAGE_DIR / "outputs"
TEMP_DIR = STORAGE_DIR / "temp"

# Ensure directories exist
for directory in [STORAGE_DIR, UPLOADS_DIR, OUTPUTS_DIR, TEMP_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

def get_ffmpeg_binary() -> str:
    """Find FFmpeg binary: checks PATH first, then imageio_ffmpeg, then common install locations."""
    import shutil
    ffmpeg_in_path = shutil.which("ffmpeg")
    if ffmpeg_in_path:
        return ffmpeg_in_path

    # Try imageio_ffmpeg
    try:
        import imageio_ffmpeg
        exe = imageio_ffmpeg.get_ffmpeg_exe()
        if exe and os.path.exists(exe):
            return exe
    except Exception:
        pass

    # Common Windows fallbacks
    fallbacks = [
        r"C:\ProgramData\chocolatey\bin\ffmpeg.exe",
        r"C:\ffmpeg\bin\ffmpeg.exe",
        Path.home() / "AppData" / "Local" / "Microsoft" / "WinGet" / "Links" / "ffmpeg.exe"
    ]
    for path in fallbacks:
        if os.path.exists(path):
            return str(path)

    return "ffmpeg"

FFMPEG_PATH = get_ffmpeg_binary()

# Default Pipeline Config
DEFAULT_CONFIG = {
    "whisper_model": "base",       # tiny, base, small, medium, large-v3-turbo
    "device": "auto",              # cuda, cpu, auto
    "compute_type": "float16",     # float16 for GPU, int8/float32 for CPU
    "ollama_url": "http://127.0.0.1:11434",
    "ollama_model": "llama3.2:latest",
    "min_clip_seconds": 25,
    "max_clip_seconds": 65,
    "target_width": 1080,
    "target_height": 1920,
    "subtitle_style": "hormozi",   # hormozi, beast, clean, neon
    "smooth_factor": 0.12          # Camera panning smoothing (0.05 to 0.25)
}
