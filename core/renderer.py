import os
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional
from .config import FFMPEG_PATH, OUTPUTS_DIR, TEMP_DIR
from .bgm_manager import BGMManager
from .audio_enhancer import MediaEnhancer

class VideoRenderer:
    """
    Renders the final vertical 9:16 viral clip:
    - Slices precise segment
    - Applies face-tracked 9:16 crop & scale to 1080x1920
    - Burns kinetic word-by-word karaoke subtitles
    - Studio voice clarifier, FFT denoising & broadcast EBU R128 loudness normalization
    - Cinematic color grading LUTs & creator watermark overlay
    - High performance GPU hardware acceleration (NVIDIA NVENC) with automatic CPU fallback
    - Audio normalization & high quality H.264 export
    """

    def __init__(self, ffmpeg_path: str = FFMPEG_PATH):
        self.ffmpeg_path = ffmpeg_path
        self._nvenc_supported = self._detect_nvenc()

    def _detect_nvenc(self) -> bool:
        """Detect whether NVIDIA NVENC hardware encoder is supported."""
        try:
            cmd = [
                self.ffmpeg_path,
                "-f", "lavfi",
                "-i", "testsrc=duration=0.5:size=320x240:rate=30",
                "-c:v", "h264_nvenc",
                "-f", "null", "-"
            ]
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=4)
            available = (res.returncode == 0)
            if available:
                print("[Renderer] NVIDIA NVENC GPU Hardware Acceleration: ACTIVE")
            else:
                print("[Renderer] NVIDIA NVENC not available, using libx264 CPU encoder.")
            return available
        except Exception:
            return False

    def render_clip(
        self,
        video_path: str,
        start_sec: float,
        duration: float,
        crop_filter: str,
        ass_subtitle_path: Optional[str] = None,
        output_filename: Optional[str] = None,
        enable_punch_in_zoom: bool = True,
        progress_bar_color: Optional[str] = None,
        bgm_track: Optional[str] = None,
        bgm_volume: float = 0.12,
        color_preset: Optional[str] = "none",
        watermark_text: Optional[str] = None,
        watermark_position: str = "top_right",
        enable_voice_clarifier: bool = False,
        enable_loudnorm: bool = True
    ) -> Path:
        """
        Renders a finished 9:16 viral video clip with burned animated subtitles,
        creator watermark, cinematic color grading, studio voice clarifier,
        retention progress bar, and smart auto-ducked background music.
        Uses NVIDIA NVENC hardware acceleration when available.
        """
        video_p = Path(video_path)
        if not output_filename:
            output_filename = f"clip_{video_p.stem}_{int(start_sec)}_{int(start_sec + duration)}.mp4"

        output_path = OUTPUTS_DIR / output_filename
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Check background music
        bgm_path = BGMManager.get_track_path(bgm_track) if bgm_track else None
        extra_inputs = []
        if bgm_path and bgm_path.exists():
            extra_inputs = ["-stream_loop", "-1", "-i", str(bgm_path)]

        # Video post-processing parts (color grading, watermark, subtitles, progress bar)
        post_vf_parts = []

        # 1. Color Grading LUT
        color_vf = MediaEnhancer.get_color_filter(color_preset)
        if color_vf:
            post_vf_parts.append(color_vf)

        # 2. Watermark / Social Handle
        if watermark_text and watermark_text.strip():
            wm_vf = MediaEnhancer.get_watermark_filter(watermark_text, position=watermark_position)
            if wm_vf:
                post_vf_parts.append(wm_vf)

        # 3. Subtitles (.ass)
        safe_ass = None
        if ass_subtitle_path and Path(ass_subtitle_path).exists():
            safe_ass = Path(ass_subtitle_path).resolve().as_posix().replace(":", r"\:")
            post_vf_parts.append(f"ass='{safe_ass}'")

        # 4. Progress bar
        if progress_bar_color and progress_bar_color.lower() != "none":
            dur_val = max(1.0, duration)
            post_vf_parts.append(f"drawbox=x=0:y=1912:w=1080*(t/{dur_val:.2f}):h=8:color={progress_bar_color}@0.95:t=fill")

        # Audio Enhancements
        audio_chain = MediaEnhancer.get_audio_filter_chain(
            enable_clarifier=enable_voice_clarifier,
            enable_loudnorm=enable_loudnorm
        )

        # Build filtergraph
        is_complex = ("[" in crop_filter) or ("vstack" in crop_filter) or (";" in crop_filter) or (bgm_path is not None)

        if is_complex:
            # Complex multi-stream filtergraph
            v_chain = crop_filter
            if post_vf_parts:
                post_chain = ",".join(post_vf_parts)
                if "[vstacked]" in v_chain:
                    v_chain = v_chain.replace("[vstacked]", "[base]") + f";[base]{post_chain}[outv]"
                elif "[outv]" in v_chain:
                    v_chain = v_chain.replace("[outv]", "[base]") + f";[base]{post_chain}[outv]"
                elif ";" in v_chain or "[" in v_chain:
                    v_chain = f"{v_chain}[base];[base]{post_chain}[outv]"
                else:
                    v_chain = f"[0:v]{v_chain},{post_chain}[outv]"
            else:
                if not ("[outv]" in v_chain):
                    if "[vstacked]" in v_chain:
                        v_chain = v_chain.replace("[vstacked]", "[outv]")
                    else:
                        v_chain = f"[0:v]{v_chain}[outv]"

            if bgm_path and bgm_path.exists():
                vol_clamped = max(0.02, min(0.40, bgm_volume))
                voice_prep = f"[0:a:0]{audio_chain}[clean_voice];[clean_voice]" if audio_chain else "[0:a:0]"
                audio_fc = (
                    f"{voice_prep}asplit=2[sp_main][sp_sc];"
                    f"[1:a]volume={vol_clamped:.2f}[bgm];"
                    f"[bgm][sp_sc]sidechaincompress=threshold=0.03:ratio=5:attack=50:release=350[ducked_bgm];"
                    f"[sp_main][ducked_bgm]amix=inputs=2:duration=first:dropout_transition=2[outa]"
                )
                full_filter = f"{v_chain};{audio_fc}"
                filter_args = ["-filter_complex", full_filter, "-map", "[outv]", "-map", "[outa]"]
            else:
                if audio_chain:
                    full_filter = f"{v_chain};[0:a:0]{audio_chain}[outa]"
                    filter_args = ["-filter_complex", full_filter, "-map", "[outv]", "-map", "[outa]"]
                else:
                    filter_args = ["-filter_complex", v_chain, "-map", "[outv]", "-map", "0:a:0?"]
        else:
            # Simple single-stream -vf filtergraph (no BGM and single stream crop)
            vf_all = [crop_filter] + post_vf_parts
            filter_args = ["-vf", ",".join(vf_all)]
            if audio_chain:
                filter_args.extend(["-af", audio_chain])
            filter_args.extend(["-map", "0:v:0", "-map", "0:a:0?"])

        # Construct FFmpeg command (Attempt GPU NVENC first if supported)
        encoders_to_try = []
        if self._nvenc_supported:
            encoders_to_try.append({
                "name": "nvenc",
                "args": [
                    "-c:v", "h264_nvenc",
                    "-preset", "p2",
                    "-tune", "ll",
                    "-rc", "vbr",
                    "-cq", "22",
                    "-spatial-aq", "1",
                    "-pix_fmt", "yuv420p"
                ]
            })

        # Fallback CPU encoder
        encoders_to_try.append({
            "name": "cpu",
            "args": [
                "-c:v", "libx264",
                "-preset", "veryfast",
                "-threads", "0",
                "-profile:v", "high",
                "-level:v", "4.1",
                "-pix_fmt", "yuv420p",
                "-crf", "21"
            ]
        })

        last_err = None
        for enc in encoders_to_try:
            cmd = [
                self.ffmpeg_path,
                "-y",
                "-threads", "0",
                "-ss", f"{start_sec:.3f}",
                "-t", f"{duration:.3f}",
                "-i", str(video_p),
                *extra_inputs,
                *filter_args,
                *enc["args"],
                "-c:a", "aac",
                "-b:a", "192k",
                "-ar", "44100",
                "-ac", "2",
                "-movflags", "+faststart",
                str(output_path)
            ]

            print(f"[Renderer] Executing FFmpeg render ({enc['name']}): {' '.join(cmd[:12])}...")
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

            if result.returncode == 0:
                # Generate crisp 1080x1920 TikTok cover thumbnail image with the same name as the video
                thumb_path = output_path.with_suffix(".jpg")
                try:
                    thumb_ts = min(1.2, max(0.5, duration * 0.25))
                    self.generate_thumbnail(str(output_path), str(thumb_path), timestamp_sec=thumb_ts)
                except Exception as te:
                    print(f"[Renderer Warning] Thumbnail generation failed: {te}")
                return output_path
            else:
                last_err = result.stderr
                print(f"[Renderer Warning] Encoder {enc['name']} failed (code {result.returncode}), trying next fallback...")

        raise RuntimeError(f"FFmpeg rendering failed: {last_err[-500:] if last_err else 'Unknown error'}")

    def generate_thumbnail(
        self,
        video_path: str,
        output_jpg_path: str,
        timestamp_sec: float = 1.0,
        target_w: int = 1080,
        target_h: int = 1920
    ) -> bool:
        """
        Extracts a high-quality, crisp 9:16 (1080x1920) TikTok thumbnail cover frame
        at timestamp_sec and saves as JPEG with the same name as the video.
        """
        try:
            # Standard TikTok cover: 1080x1920, 9:16 aspect ratio
            vf = f"scale={target_w}:{target_h}:force_original_aspect_ratio=increase,crop={target_w}:{target_h}"
            cmd = [
                self.ffmpeg_path,
                "-y",
                "-ss", f"{timestamp_sec:.2f}",
                "-i", str(video_path),
                "-vf", vf,
                "-vframes", "1",
                "-q:v", "2",
                str(output_jpg_path)
            ]
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=8)
            if res.returncode == 0 and Path(output_jpg_path).exists():
                return True
            # Fallback if specific timestamp failed (e.g. video shorter than timestamp_sec)
            cmd_fallback = [
                self.ffmpeg_path,
                "-y",
                "-ss", "0.2",
                "-i", str(video_path),
                "-vf", vf,
                "-vframes", "1",
                "-q:v", "2",
                str(output_jpg_path)
            ]
            res2 = subprocess.run(cmd_fallback, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=8)
            return res2.returncode == 0 and Path(output_jpg_path).exists()
        except Exception as e:
            print(f"[Renderer] TikTok thumbnail generation error: {e}")
            return False
