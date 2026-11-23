"""
ClipForge Studio - Audio Voice Clarifier & Color Grading Engine.
Provides broadcast-grade voice enhancement (FFT denoising, EQ, dynamic compression,
EBU R128 loudness normalization) and cinematic color grading filters.
100% Free and powered by native FFmpeg DSP.
"""

from typing import Optional, Dict

class MediaEnhancer:
    """Handles audio voice enhancement, broadcast loudness normalization, and visual color grading."""

    COLOR_PRESETS = {
        "none": {
            "name": "Natural (Original Colors)",
            "filter": None
        },
        "cinematic_pop": {
            "name": "Cinematic Pop (Vibrant Contrast)",
            "filter": "eq=contrast=1.08:brightness=0.02:saturation=1.18,unsharp=5:5:0.6:5:5:0.0"
        },
        "moody_studio": {
            "name": "Moody Studio (Dramatic Shadows)",
            "filter": "eq=contrast=1.12:brightness=-0.02:saturation=0.92"
        },
        "clean_crisp": {
            "name": "Clean Crisp (Sharpened Daylight)",
            "filter": "unsharp=5:5:0.8:5:5:0.0,eq=contrast=1.04:brightness=0.01:saturation=1.06"
        },
        "warm_golden": {
            "name": "Warm Golden (Studio Amber Glow)",
            "filter": "colorbalance=rs=0.08:gs=0.02:bs=-0.06,eq=saturation=1.10"
        }
    }

    @classmethod
    def get_color_filter(cls, preset_key: Optional[str]) -> Optional[str]:
        """Returns the FFmpeg video filter for the selected color grading preset."""
        if not preset_key or preset_key not in cls.COLOR_PRESETS:
            return None
        return cls.COLOR_PRESETS[preset_key]["filter"]

    @classmethod
    def get_audio_filter_chain(
        cls,
        enable_clarifier: bool = True,
        enable_loudnorm: bool = True
    ) -> Optional[str]:
        """
        Builds a multi-stage studio audio filter chain:
        1. Highpass 80Hz: Removes microphone table thumps, AC rumble, and wind puffing.
        2. Lowpass 12000Hz: Eliminates harsh digital sizzle/hiss.
        3. afftdn: Fast FFT spectral noise suppressor to strip ambient fan and background room noise.
        4. acompressor: Smooth voice compression to balance whisper-to-shout speech levels.
        5. loudnorm: Broadcast standard EBU R128 (-14 LUFS) for optimal loudness on TikTok, Reels & Shorts.
        """
        parts = []
        if enable_clarifier:
            # Stage 1: Clean voice frequencies & remove room rumble
            parts.append("highpass=f=80,lowpass=f=12000")
            # Stage 2: FFT spectral noise suppression (subtle & artifact-free)
            parts.append("afftdn=nr=10:nf=-30")
            # Stage 3: Smooth voice leveling compression
            parts.append("acompressor=threshold=-18dB:ratio=3:attack=20:release=250")

        if enable_loudnorm:
            # Stage 4: Broadcast standard EBU R128 loudness target (-14 LUFS, LRA 7, True Peak -1.5)
            parts.append("loudnorm=I=-14:LRA=7:tp=-1.5")

        if not parts:
            return None
        return ",".join(parts)

    @classmethod
    def get_watermark_filter(
        cls,
        text: Optional[str] = None,
        position: str = "top_right",
        opacity: float = 0.85
    ) -> Optional[str]:
        """
        Generates FFmpeg drawtext expression for a clean, professional channel handle
        or creator watermark (e.g. '@podcastmaster').
        Positions: top_right, top_left, bottom_right, bottom_left
        """
        if not text or not text.strip():
            return None

        clean_text = text.strip().replace("'", "").replace(":", "")
        op = max(0.2, min(1.0, opacity))

        # Coordinates for 1080x1920 portrait canvas
        pos_map = {
            "top_right": "x=w-tw-50:y=60",
            "top_left": "x=50:y=60",
            "bottom_right": "x=w-tw-50:y=h-th-80",
            "bottom_left": "x=50:y=h-th-80"
        }
        coords = pos_map.get(position, pos_map["top_right"])

        return (
            f"drawtext=text='{clean_text}':font='Arial':fontsize=28:fontcolor=white@{op:.2f}:"
            f"box=1:boxcolor=black@{op*0.6:.2f}:boxborderw=8:{coords}"
        )
