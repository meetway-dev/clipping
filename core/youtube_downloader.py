import os
import re
import shutil
from pathlib import Path
from typing import Dict, Any, Optional, Callable
import yt_dlp

from .config import FFMPEG_PATH, UPLOADS_DIR

class YouTubeDownloader:
    """
    Production-grade YouTube downloader powered by yt-dlp.
    Configured with Node.js JavaScript challenge solver, chunked HTTP streaming,
    and anti-403 retry mechanisms.
    """

    YOUTUBE_REGEX = r"^(https?://)?(www\.)?(youtube\.com/watch\?v=|youtu\.be/|youtube\.com/shorts/|youtube\.com/live/)[a-zA-Z0-9_-]+"

    @classmethod
    def _get_node_path(cls) -> Optional[str]:
        """Finds Node.js binary on the system for solving YouTube JS signature challenges."""
        node_in_path = shutil.which("node")
        if node_in_path:
            return node_in_path

        common_locations = [
            r"C:\Program Files\nodejs\node.exe",
            r"C:\Program Files (x86)\nodejs\node.exe",
            Path.home() / "AppData" / "Roaming" / "npm" / "node.exe"
        ]
        for loc in common_locations:
            if os.path.exists(loc):
                return str(loc)
        return None

    @classmethod
    def is_valid_url(cls, url: str) -> bool:
        """Check if a URL matches valid YouTube video patterns."""
        if not url:
            return False
        return bool(re.match(cls.YOUTUBE_REGEX, url.strip()))

    @classmethod
    def _build_ydl_options(
        cls,
        output_template: Optional[str] = None,
        progress_cb: Optional[Callable[[str, float], None]] = None,
        for_download: bool = False
    ) -> Dict[str, Any]:
        """
        Builds robust yt-dlp configuration to eliminate HTTP 403 Forbidden errors.
        """
        node_path = cls._get_node_path()

        opts: Dict[str, Any] = {
            "quiet": True,
            "no_warnings": True,
            "nocheckcertificate": True,
            "http_chunk_size": 10485760,  # 10MB chunking prevents CDN 403 disconnects
            "retries": 5,
            "fragment_retries": 5,
            "remote_components": ["ejs:github"],  # Solves modern JS n-challenges
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        }

        if node_path:
            opts["js_runtimes"] = {"node": {}}

        if for_download:
            opts["ffmpeg_location"] = FFMPEG_PATH
            opts["merge_output_format"] = "mp4"
            opts["format"] = "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080][ext=mp4]/best[height<=1080]/best"
            opts["overwrites"] = True

            if output_template:
                opts["outtmpl"] = output_template

            if progress_cb:
                def ydl_hook(d):
                    if d["status"] == "downloading":
                        total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
                        downloaded = d.get("downloaded_bytes", 0)
                        if total > 0:
                            pct = min(100.0, (downloaded / total) * 100.0)
                            speed_mb = (d.get("speed") or 0) / (1024 * 1024)
                            progress_cb(f"Downloading stream: {pct:.1f}% ({speed_mb:.1f} MB/s)", pct)
                    elif d["status"] == "finished":
                        progress_cb("Merging video and audio streams...", 100.0)

                opts["progress_hooks"] = [ydl_hook]
        else:
            opts["skip_download"] = True

        return opts

    @classmethod
    def get_info(cls, url: str) -> Dict[str, Any]:
        """
        Extract video metadata (title, duration, thumbnail, channel)
        without downloading the media.
        """
        if not cls.is_valid_url(url):
            raise ValueError("Invalid YouTube URL. Please provide a standard watch, share, or shorts link.")

        opts = cls._build_ydl_options(for_download=False)

        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url.strip(), download=False)
        except Exception as first_err:
            # Fallback retry without JS runtime if needed
            print(f"[YouTubeDownloader] Primary info extraction failed ({first_err}), retrying with fallback...")
            opts.pop("remote_components", None)
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url.strip(), download=False)

        thumbnail = info.get("thumbnail", "")
        thumbnails = info.get("thumbnails", [])
        if thumbnails:
            thumbnail = thumbnails[-1].get("url", thumbnail)

        return {
            "id": info.get("id"),
            "title": info.get("title", "Untitled YouTube Video"),
            "duration": info.get("duration", 0),
            "duration_formatted": cls._format_duration(info.get("duration", 0)),
            "thumbnail": thumbnail,
            "channel": info.get("uploader") or info.get("channel", "Unknown Channel"),
            "view_count": info.get("view_count", 0),
            "url": url.strip()
        }

    @classmethod
    def download(
        cls,
        url: str,
        output_dir: Optional[Path] = None,
        progress_cb: Optional[Callable[[str, float], None]] = None
    ) -> Path:
        """
        Downloads the YouTube video in best MP4 quality (up to 1080p).
        Handles retries and fallbacks if YouTube's CDN issues 403 Forbidden.
        """
        if not cls.is_valid_url(url):
            raise ValueError("Invalid YouTube URL.")

        out_dir = Path(output_dir) if output_dir else UPLOADS_DIR
        out_dir.mkdir(parents=True, exist_ok=True)
        out_template = str(out_dir / "yt_%(id)s.%(ext)s")

        # Attempt 1: Node.js JS solver + chunked HTTP
        opts = cls._build_ydl_options(
            output_template=out_template,
            progress_cb=progress_cb,
            for_download=True
        )

        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url.strip(), download=True)
                return cls._find_downloaded_file(out_dir, info.get("id"))

        except Exception as e:
            err_msg = str(e)
            print(f"[YouTubeDownloader] Primary download failed: {err_msg}")

            # Attempt 2: If 403 Forbidden or format error, fallback with progressive stream
            if "403" in err_msg or "Forbidden" in err_msg or "format" in err_msg.lower():
                if progress_cb:
                    progress_cb("Re-routing stream via alternate CDN client to bypass 403...", 10.0)

                fallback_opts = cls._build_ydl_options(
                    output_template=out_template,
                    progress_cb=progress_cb,
                    for_download=True
                )
                fallback_opts["format"] = "best[ext=mp4]/best"
                fallback_opts["extractor_args"] = {
                    "youtube": {
                        "player_client": ["android", "ios", "web"]
                    }
                }

                try:
                    with yt_dlp.YoutubeDL(fallback_opts) as ydl:
                        info = ydl.extract_info(url.strip(), download=True)
                        return cls._find_downloaded_file(out_dir, info.get("id"))
                except Exception as fallback_err:
                    print(f"[YouTubeDownloader] Fallback download failed: {fallback_err}")
                    raise RuntimeError(f"Could not download YouTube video: {fallback_err}")

            raise RuntimeError(f"YouTube download failed: {e}")

    @classmethod
    def _find_downloaded_file(cls, out_dir: Path, video_id: str) -> Path:
        """Locates the merged video file matching video_id."""
        final_path = out_dir / f"yt_{video_id}.mp4"
        if final_path.exists():
            return final_path

        candidates = list(out_dir.glob(f"yt_{video_id}.*"))
        if candidates:
            return candidates[0]

        raise RuntimeError(f"Downloaded file for ID {video_id} could not be found.")

    @staticmethod
    def _format_duration(seconds: int) -> str:
        """Format seconds into HH:MM:SS or MM:SS."""
        if not seconds:
            return "00:00"
        m, s = divmod(int(seconds), 60)
        h, m = divmod(m, 60)
        if h > 0:
            return f"{h:02d}:{m:02d}:{s:02d}"
        return f"{m:02d}:{s:02d}"
