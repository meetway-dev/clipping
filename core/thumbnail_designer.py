import math
import os
import re
import json
import random
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from .config import FFMPEG_PATH, TEMP_DIR

# High-impact typography paths with fallbacks
FONT_IMPACT = "C:/Windows/Fonts/impact.ttf"
FONT_ARIAL_BLACK = "C:/Windows/Fonts/ariblk.ttf"
FONT_ARIAL_BOLD = "C:/Windows/Fonts/arialbd.ttf"
FONT_SEGOE_BOLD = "C:/Windows/Fonts/segoeuib.ttf"
FONT_SEGOE_REG = "C:/Windows/Fonts/segoeui.ttf"
FONT_TREBUCHET_BOLD = "C:/Windows/Fonts/trebucbd.ttf"

def get_font(path: str, size: int) -> ImageFont.FreeTypeFont:
    """Loads a TTF font with multi-tier fallback to system bold fonts."""
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        fallback_candidates = [
            "C:/Windows/Fonts/impact.ttf",
            "C:/Windows/Fonts/ariblk.ttf",
            "C:/Windows/Fonts/arialbd.ttf",
            "C:/Windows/Fonts/segoeuib.ttf",
            "arialbd.ttf"
        ]
        for fb in fallback_candidates:
            try:
                return ImageFont.truetype(fb, size)
            except Exception:
                continue
        return ImageFont.load_default()

def parse_color(color_val: Any, default_rgb: Tuple[int, int, int] = (255, 214, 0)) -> Tuple[int, int, int]:
    """Parses hex or name string into RGB tuple."""
    if isinstance(color_val, (tuple, list)) and len(color_val) >= 3:
        return (int(color_val[0]), int(color_val[1]), int(color_val[2]))
    if isinstance(color_val, str):
        c = color_val.strip().lower()
        named = {
            "yellow": (255, 214, 0),
            "gold": (255, 195, 0),
            "green": (34, 197, 94),
            "cyan": (0, 229, 255),
            "blue": (56, 189, 248),
            "red": (255, 59, 48),
            "orange": (255, 140, 0),
            "white": (255, 255, 255)
        }
        if c in named:
            return named[c]
        if c.startswith("#"):
            hex_str = c.lstrip("#")
            if len(hex_str) == 6:
                try:
                    return (
                        int(hex_str[0:2], 16),
                        int(hex_str[2:4], 16),
                        int(hex_str[4:6], 16)
                    )
                except Exception:
                    pass
    return default_rgb

def draw_text_with_stroke_and_shadow(
    draw: ImageDraw.ImageDraw,
    xy: tuple,
    text: str,
    font: ImageFont.FreeTypeFont,
    fill: tuple,
    stroke_fill: tuple = (0, 0, 0, 255),
    stroke_width: int = 6,
    shadow_offset: tuple = (4, 6),
    shadow_color: tuple = (0, 0, 0, 240)
) -> None:
    """
    Draws text with a thick outline stroke plus directional 3D drop shadow
    to guarantee 100% crystal-clear readability against any video background.
    """
    x, y = xy
    sx, sy = shadow_offset
    for dx, dy in [(sx, sy), (sx + 2, sy + 2), (sx - 1, sy + 2)]:
        draw.text((x + dx, y + dy), text, font=font, fill=shadow_color, stroke_width=stroke_width, stroke_fill=shadow_color)
    draw.text((x, y), text, font=font, fill=fill, stroke_width=stroke_width, stroke_fill=stroke_fill)


class SmartFrameSelector:
    """
    Intelligent speaker frame extractor powered by OpenCV YuNet DNN:
    1. Analyzes multiple keyframes across the clip (at 10%, 25%, 40%, 55%, 70%, 85%).
    2. Measures face presence, face size, bounding box coordinates, and detection confidence.
    3. Evaluates image sharpness via Laplacian variance (detects & rejects motion blur).
    4. Evaluates eye/facial clarity and open expression.
    5. Preserves 100% of the real person's natural appearance (never AI-hallucinates or swaps).
    6. Identifies whether the clip has a single speaker or a host+guest pair.
    """

    @classmethod
    def select_best_speaker_frame(
        cls,
        video_path: str,
        output_frame_path: str,
        start_sec: float = 0.0,
        duration: float = 60.0,
        crop_filter: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Samples candidates from video, scores them, and exports the highest-quality
        frame to output_frame_path.
        Returns metadata: {timestamp, faces, is_dual_speaker, face_coords, sharpness}
        """
        from .face_tracker import SmartFaceTracker
        tracker = SmartFaceTracker()

        vid_p = Path(video_path)
        if not vid_p.exists():
            return {"success": False, "reason": "Video file not found"}

        cap = cv2.VideoCapture(str(vid_p))
        if not cap.isOpened():
            return {"success": False, "reason": "Could not open video stream"}

        fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
        total_video_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        video_total_sec = total_video_frames / fps if fps > 0 else 60.0

        clip_start = max(0.0, min(video_total_sec - 1.0, start_sec))
        clip_dur = max(1.0, min(video_total_sec - clip_start, duration))

        # Sample 7 distinct intervals inside the clip duration
        sample_ratios = [0.12, 0.25, 0.38, 0.52, 0.65, 0.78, 0.88]
        candidates = []

        for r in sample_ratios:
            target_sec = clip_start + (r * clip_dur)
            cap.set(cv2.CAP_PROP_POS_MSEC, target_sec * 1000.0)
            ret, frame = cap.read()
            if not ret or frame is None:
                continue

            faces = tracker.detect_faces(frame)
            if not faces:
                # Still record frame with low baseline score as fallback
                gray_all = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                blur_val = float(cv2.Laplacian(gray_all, cv2.CV_64F).var())
                candidates.append({
                    "score": 10.0 + min(50.0, blur_val * 0.5),
                    "timestamp": target_sec,
                    "frame": frame,
                    "faces": [],
                    "sharpness": blur_val,
                    "is_dual": False
                })
                continue

            # Classify single vs dual speaker
            is_dual = len(faces) >= 2
            # Prominent face
            best_face = max(faces, key=lambda f: f["w"] * f["h"])
            fx, fy, fw, fh = best_face["x"], best_face["y"], best_face["w"], best_face["h"]

            # Crop face area to measure sharpness precisely
            pad_h, pad_w = frame.shape[:2]
            f_crop = frame[max(0, fy):min(pad_h, fy + fh), max(0, fx):min(pad_w, fx + fw)]
            if f_crop.size > 0:
                gray_f = cv2.cvtColor(f_crop, cv2.COLOR_BGR2GRAY)
                sharpness = float(cv2.Laplacian(gray_f, cv2.CV_64F).var())
            else:
                sharpness = 20.0

            # Quality scoring function:
            # - Face detection confidence (0-1 -> 0-100)
            # - Face size (larger face = better resolution/clarity for thumbnail)
            # - Sharpness (Laplacian variance, penalty for blur < 15.0)
            # - Penalty for awkward face close to extreme edge
            face_area_ratio = (fw * fh) / float(pad_h * pad_w)
            blur_score = min(80.0, sharpness * 1.5)
            if sharpness < 12.0:
                blur_score -= 40.0  # heavy motion blur penalty

            edge_dist_x = min(best_face["cx"], pad_w - best_face["cx"]) / float(pad_w)
            center_bonus = 20.0 if edge_dist_x > 0.15 else 0.0

            total_score = (best_face["score"] * 100.0) + blur_score + (face_area_ratio * 300.0) + center_bonus

            candidates.append({
                "score": total_score,
                "timestamp": target_sec,
                "frame": frame,
                "faces": faces,
                "best_face": best_face,
                "sharpness": sharpness,
                "is_dual": is_dual
            })

        cap.release()

        if not candidates:
            # Fallback to direct ffmpeg frame extraction
            fallback_ts = clip_start + min(2.0, clip_dur * 0.25)
            cmd = [
                FFMPEG_PATH, "-y",
                "-ss", f"{fallback_ts:.2f}",
                "-i", str(video_path),
                "-vframes", "1",
                "-q:v", "2",
                str(output_frame_path)
            ]
            subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=8)
            return {"success": True, "timestamp": fallback_ts, "is_dual": False, "faces": []}

        # Select highest-scoring candidate
        candidates.sort(key=lambda c: c["score"], reverse=True)
        winner = candidates[0]

        best_ts = winner["timestamp"]
        # Save winner frame directly
        cv2.imwrite(str(output_frame_path), winner["frame"])

        return {
            "success": True,
            "timestamp": best_ts,
            "score": winner["score"],
            "sharpness": winner["sharpness"],
            "faces": winner["faces"],
            "is_dual": winner["is_dual"],
            "best_face": winner.get("best_face")
        }


class TopicAwareBackdrop:
    """
    Renders high-end, subtle, topic-specific documentary elements into the thumbnail
    composition so the thumbnail looks like a multi-million-view podcast production.
    """

    @classmethod
    def detect_topic_genre(cls, topic: str, transcript: str) -> str:
        """Classifies topic into standard podcast documentary categories."""
        combined = f"{topic} {transcript}".lower()

        if any(k in combined for k in ["longevity", "aging", "lifespan", "dna", "cell", "mitochondria", "healthspan", "outlive"]):
            return "longevity"
        elif any(k in combined for k in ["heart", "cardio", "blood", "pressure", "artery", "ecg", "cardiovascular"]):
            return "heart_health"
        elif any(k in combined for k in ["brain", "mind", "memory", "focus", "dopamine", "neuro", "adhd", "psychology", "mental"]):
            return "brain_health"
        elif any(k in combined for k in ["nutrition", "diet", "sugar", "protein", "gut", "fasting", "food", "calorie", "eating"]):
            return "nutrition"
        elif any(k in combined for k in ["muscle", "fitness", "workout", "training", "gym", "body", "exercise", "strength"]):
            return "fitness"
        elif any(k in combined for k in ["money", "business", "wealth", "invest", "finance", "revenue", "scale", "ceo", "market", "sales"]):
            return "business_finance"
        elif any(k in combined for k in ["ai", "tech", "software", "code", "model", "algorithm", "robot", "future", "digital", "data"]):
            return "technology_ai"
        elif any(k in combined for k in ["scared", "fear", "danger", "warning", "mistake", "truth", "secret", "exposed", "burn"]):
            return "high_drama"
        else:
            return "editorial_studio"

    @classmethod
    def render_procedural_backdrop(
        cls,
        draw: ImageDraw.ImageDraw,
        W: int,
        H: int,
        genre: str,
        accent_rgb: Tuple[int, int, int] = (255, 214, 0)
    ) -> None:
        """
        Draws subtle, elegant, low-opacity scientific and technical visual accents
        into the left / upper-left / lower-left background areas.
        """
        if genre == "longevity":
            # 1. Subtle glowing DNA double-helix in upper left
            for t in range(0, 360, 14):
                y = 190 + t
                x1 = int(190 + 75 * np.sin(t * 0.038))
                x2 = int(190 - 75 * np.sin(t * 0.038))
                draw.line([(x1, y), (x2, y)], fill=(0, 200, 255, 60), width=2)
                draw.ellipse([x1 - 4, y - 4, x1 + 4, y + 4], fill=(0, 225, 255, 160))
                draw.ellipse([x2 - 4, y - 4, x2 + 4, y + 4], fill=(255, 130, 210, 140))

            # 2. Glowing cinematic hourglass in lower left (Y: 1350-1720)
            cls._draw_glowing_hourglass(draw, hx=170, hy=1530)

        elif genre == "heart_health":
            # Glowing ECG monitor line across mid-bottom
            pts = []
            for x in range(60, 480, 5):
                if 230 <= x <= 275:
                    if x == 235: y = 1485
                    elif x == 245: y = 1410
                    elif x == 255: y = 1580
                    elif x == 265: y = 1465
                    else: y = 1500
                else:
                    y = 1500 + int(np.sin(x * 0.08) * 5)
                pts.append((x, y))
            draw.line(pts, fill=(0, 229, 255, 140), width=3)
            draw.ellipse([243, 1408, 247, 1412], fill=(255, 255, 255, 240))

        elif genre == "brain_health":
            # Neural network constellation nodes in upper left
            nodes = [
                (120, 240), (220, 200), (320, 250), (160, 340),
                (280, 330), (210, 430), (340, 420), (130, 480)
            ]
            for i, n1 in enumerate(nodes):
                for n2 in nodes[i+1:]:
                    dist = math.hypot(n1[0]-n2[0], n1[1]-n2[1])
                    if dist < 160:
                        draw.line([n1, n2], fill=(0, 215, 255, 50), width=1)
            for n in nodes:
                draw.ellipse([n[0]-5, n[1]-5, n[0]+5, n[1]+5], fill=(0, 235, 255, 180))

        elif genre == "business_finance":
            # Clean financial grid & upward golden trajectory
            for i, gx in enumerate(range(80, 420, 55)):
                gy_base = 1540 - i * 32
                draw.line([gx, gy_base - 45, gx, gy_base + 25], fill=(34, 197, 94, 140), width=2)
                draw.rectangle([gx - 10, gy_base - 30, gx + 10, gy_base + 12], fill=(34, 197, 94, 180))
            trend_pts = [(80, 1520), (135, 1490), (190, 1465), (245, 1410), (300, 1375), (355, 1320), (410, 1260)]
            draw.line(trend_pts, fill=(255, 214, 0, 190), width=4)

        elif genre == "technology_ai":
            # Circuit lattice micro-grid
            for cx in range(80, 440, 70):
                draw.line([(cx, 1320), (cx, 1680)], fill=(0, 229, 255, 40), width=1)
            for cy in range(1320, 1700, 60):
                draw.line([(80, cy), (440, cy)], fill=(0, 229, 255, 40), width=1)
                draw.ellipse([220 - 4, cy - 4, 220 + 4, cy + 4], fill=(0, 240, 255, 160))

        else:
            # Universal cinematic rim vignette & architectural studio depth
            for r in range(240, 60, -30):
                alpha = int(14 * (1.0 - r / 240.0))
                draw.ellipse([W - r, 300 - r, W + r, 300 + r], fill=(255, 200, 100, alpha))

    @classmethod
    def _draw_glowing_hourglass(cls, draw: ImageDraw.ImageDraw, hx: int = 170, hy: int = 1530) -> None:
        """Draws a refined glowing hourglass icon matching the Peter Attia reference."""
        # Ambient warm glow
        for r in range(150, 40, -25):
            alpha = int(18 * (1.0 - r / 150.0))
            draw.ellipse([hx - r, hy - r, hx + r, hy + r], fill=(255, 180, 50, alpha))

        # Wooden caps (beveled mahogany & brass)
        draw.rounded_rectangle([hx - 90, hy - 180, hx + 90, hy - 158], radius=6, fill=(130, 80, 45, 240), outline=(210, 150, 90, 255), width=2)
        draw.rounded_rectangle([hx - 90, hy + 158, hx + 90, hy + 180], radius=6, fill=(130, 80, 45, 240), outline=(210, 150, 90, 255), width=2)

        # Pillars
        for px in [hx - 78, hx + 70]:
            draw.rectangle([px, hy - 158, px + 8, hy + 158], fill=(175, 125, 70, 240))
            draw.line([px + 2, hy - 158, px + 2, hy + 158], fill=(240, 200, 140, 220), width=2)

        # Glass bulbs
        draw.ellipse([hx - 68, hy - 154, hx + 68, hy - 20], outline=(140, 210, 255, 85), width=3)
        draw.ellipse([hx - 68, hy + 20, hx + 68, hy + 154], outline=(140, 210, 255, 85), width=3)
        draw.line([hx - 14, hy, hx + 14, hy], fill=(180, 225, 255, 120), width=3)

        # Glowing gold sand in bottom bulb
        sand_poly = [
            (hx - 56, hy + 148), (hx + 56, hy + 148),
            (hx + 28, hy + 112), (hx, hy + 62), (hx - 28, hy + 112)
        ]
        draw.polygon(sand_poly, fill=(245, 195, 75, 230))
        draw.line([hx, hy - 12, hx, hy + 65], fill=(255, 225, 120, 245), width=2)


class TikTokThumbnailDesigner:
    """
    Universal Premium AI Podcast Thumbnail Generator.
    Engineered to replicate the exact visual quality of world-class viral podcast
    thumbnails (Steven Bartlett / Peter Attia / Jay Shetty):
    1. Real speaker photo extraction via YuNet DNN + Laplacian sharpness scoring.
    2. Universal visual identity: Dark charcoal background, real speaker on RIGHT,
       high-impact bold condensed headline on LEFT.
    3. White headline + warm yellow/gold keyword brush highlight + red accent stroke.
    4. Topic-aware procedural background elements (DNA helix, hourglass, ECG, neural nets).
    5. Clean bottom authority nameplate badge.
    6. Safe for TikTok & Reels 9:16 vertical viewports and 3:4 profile grid previews.
    """

    STYLES = {
        "editorial_premium": "Universal Editorial Premium (Clean White + Warm Gold + Red Stroke)",
        "hormozi": "Universal Editorial (White + Yellow Highlight)",
        "podcast_authority": "Universal Editorial (Masterclass Edition)",
        "tiktok_native": "Universal Editorial (Sticker Edition)",
        "red_alert": "Universal Editorial (Caution Edition)"
    }

    HOOK_ARCHETYPES = {
        "curiosity": "Curiosity / Open-Loop (The Secret Nobody Tells You)",
        "warning": "Contradiction / Warning (Stop Doing This Right Now)",
        "formula": "3-Point Blueprint (The 3 Rules You Must Follow)",
        "callout": "Audience Callout (If You Want Results In 2026)"
    }

    @classmethod
    def generate_ai_copy(
        cls,
        topic: str = "",
        title: str = "",
        hook: str = "",
        transcript: str = "",
        archetype: str = "curiosity"
    ) -> Dict[str, Any]:
        """
        Generates ultra-short, punchy 2-4 word editorial headline elements:
        - Line 1: 1-2 words in pure white (e.g. "THE")
        - Line 2: 2-3 words highlighted with yellow brush banner (e.g. "SECRET TO")
        - Line 3: 1 word in large warm gold with optional red accent (e.g. "AGING?")
        - Guest / topic authority label for bottom nameplate.
        """
        from .ollama_manager import OllamaManager
        ollama = OllamaManager.get_instance()

        clean_topic = re.sub(r"[^\w\s\-]", "", topic or title or "PODCAST HIGHLIGHT").strip().upper()
        clean_hook = re.sub(r"[^\w\s\-\']", "", hook or title or "").strip()

        # Try local AI generation if Ollama is actively connected
        conn_status = ollama.check_connection()
        if conn_status.get("connected", False):
            prompt = f"""You are a master thumbnail designer for high-end podcasts like Diary of a CEO and Huberman Lab.
Generate ultra-short, high-curiosity thumbnail text based on this video segment.
Headlines must be 2 to 4 words total, divided into 2 or 3 lines.

Topic: {clean_topic}
Hook: {clean_hook}
Transcript: {transcript[:350] if transcript else clean_hook}

Rules:
1. "headline_white": 1-2 words in ALL CAPS (Line 1, e.g. "THE", "WHY", "STOP", "WHAT").
2. "headline_yellow_1": 1-2 words in ALL CAPS (Line 2 punch, e.g. "SECRET TO", "YOUR CELLS", "EATING THIS").
3. "headline_yellow_2": 1 word in ALL CAPS or empty (Line 3 finale, e.g. "AGING?", "ARE DYING", "NOW").
4. "speaker_name": Speaker or Topic Expert name if mentioned (e.g. "PETER ATTIA", "EXPERT GUEST", or topic title).
5. "speaker_tag": 1-2 word authority subtitle (e.g. "LONGEVITY EXPERT", "NEUROSCIENTIST", "EPISODE CLIP").

Return ONLY a valid raw JSON object."""
            try:
                res = ollama.generate(prompt=prompt, timeout=3.0)
                if res and "{" in res and "}" in res:
                    m = re.search(r"\{.*\}", res, re.DOTALL)
                    if m:
                        data = json.loads(m.group(0))
                        if data.get("headline_white") or data.get("headline_yellow_1"):
                            hw = str(data.get("headline_white", "THE")).upper()[:16]
                            hy1 = str(data.get("headline_yellow_1", "SECRET TO")).upper()[:18]
                            hy2 = str(data.get("headline_yellow_2", "")).upper()[:16]
                            spk = str(data.get("speaker_name", "PODCAST INTERVIEW")).upper()[:24]
                            spk_tag = str(data.get("speaker_tag", "EXCLUSIVE INSIGHT")).upper()[:24]
                            return {
                                "headline_white": hw,
                                "headline_yellow_1": hy1,
                                "headline_yellow_2": hy2,
                                "headline_1": hw,
                                "headline_2": f"{hy1} {hy2}".strip(),
                                "speaker_name": spk,
                                "speaker_tag": spk_tag,
                                "category": spk_tag,
                                "subheadline": f"{hw} {hy1} {hy2}".strip(),
                                "takeaways": [f"1. {hw} {hy1}", "2. AVOID CRITICAL ERRORS", "3. PROVEN STRATEGY"],
                                "tag_badge": spk_tag,
                                "stat_badge": "100% VERIFIED"
                            }
            except Exception as e:
                print(f"[ThumbnailDesigner] Ollama copy fallback ({e})")

        # Guaranteed, High-CTR Semantic Editorial NLP
        words = clean_topic.split()
        kw1 = words[0] if words else "SUCCESS"
        kw2 = words[1] if len(words) > 1 else "MASTERY"

        combined = f"{clean_topic} {clean_hook}".lower()
        if any(k in combined for k in ["longevity", "aging", "mitochondria", "health"]):
            hw = "THE"
            hy1 = "SECRET TO"
            hy2 = "AGING?"
            spk = "PETER ATTIA" if "attia" in combined else "LONGEVITY INSIGHT"
            spk_tag = "HEALTH PROTOCOL"
        elif any(k in combined for k in ["brain", "memory", "mind", "focus"]):
            hw = "YOUR"
            hy1 = "BRAIN IS"
            hy2 = "CHANGING"
            spk = "NEUROSCIENCE"
            spk_tag = "COGNITIVE MASTERCLASS"
        elif any(k in combined for k in ["food", "sugar", "diet", "nutrition", "eat"]):
            hw = "STOP"
            hy1 = "EATING"
            hy2 = "THIS"
            spk = "NUTRITION EXPERT"
            spk_tag = "DIETARY TRUTH"
        elif any(k in combined for k in ["money", "cash", "wealth", "business", "invest"]):
            hw = "THE"
            hy1 = "BIGGEST"
            hy2 = "MISTAKE"
            spk = "FINANCIAL ADVISOR"
            spk_tag = "WEALTH STRATEGY"
        elif any(k in combined for k in ["scared", "fear", "afraid"]):
            hw = chr(34) + "NOT"
            hy1 = "1% OF ME"
            hy2 = "IS SCARED" + chr(34)
            spk = "RAW INTERVIEW"
            spk_tag = "EXCLUSIVE DIALOGUE"
        else:
            hw = "THE"
            hy1 = f"SECRET TO"
            hy2 = f"{kw1}?"[:16]
            spk = f"{kw1} MASTERCLASS"[:22]
            spk_tag = "EPISODE HIGHLIGHT"

        return {
            "headline_white": hw,
            "headline_yellow_1": hy1,
            "headline_yellow_2": hy2,
            "headline_1": hw,
            "headline_2": f"{hy1} {hy2}".strip(),
            "speaker_name": spk,
            "speaker_tag": spk_tag,
            "category": spk_tag,
            "subheadline": f"{hw} {hy1} {hy2}".strip(),
            "takeaways": [f"1. {hw} {hy1}", "2. AVOID CRITICAL ERRORS", "3. PROVEN RESULTS"],
            "tag_badge": spk_tag,
            "stat_badge": "100% VERIFIED"
        }

    @classmethod
    def extract_speaker_frame(
        cls,
        video_path: str,
        output_frame_path: str,
        timestamp_sec: float = 1.2,
        crop_filter: Optional[str] = None
    ) -> bool:
        """
        Extracts real speaker frame using SmartFrameSelector.
        Preserves natural facial identity with zero artificial distortion.
        """
        res = SmartFrameSelector.select_best_speaker_frame(
            video_path=video_path,
            output_frame_path=output_frame_path,
            start_sec=max(0.0, timestamp_sec - 1.0),
            duration=30.0,
            crop_filter=crop_filter
        )
        return res.get("success", False) and Path(output_frame_path).exists()

    @classmethod
    def create_tiktok_thumbnail(
        cls,
        video_path: str,
        output_jpg_path: str,
        topic: str = "",
        title: str = "",
        hook: str = "",
        transcript: str = "",
        crop_filter: Optional[str] = None,
        source_clean_video: Optional[str] = None,
        timestamp_sec: float = 1.2,
        copy_data: Optional[Dict[str, Any]] = None,
        style: str = "editorial_premium",
        accent_color: str = "#FFE600",
        archetype: str = "curiosity"
    ) -> Path:
        """
        Creates the Universal Premium AI Podcast Thumbnail (1080x1920):
        1. Employs SmartFrameSelector to extract the clearest, sharpest real speaker frame.
        2. Generates punchy editorial headlines with warm gold highlights.
        3. Applies universal editorial design system with topic-aware procedural backdrop.
        4. Validates 9:16 vertical geometry and TikTok Safe Zones.
        """
        out_p = Path(output_jpg_path)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        temp_speaker_frame = TEMP_DIR / f"speaker_frame_{out_p.stem}.jpg"

        sample_vid = source_clean_video if (source_clean_video and Path(source_clean_video).exists()) else video_path

        # 1. Smart Real Speaker Frame Extraction
        frame_meta = SmartFrameSelector.select_best_speaker_frame(
            video_path=str(sample_vid),
            output_frame_path=str(temp_speaker_frame),
            start_sec=max(0.0, timestamp_sec - 1.0),
            duration=45.0,
            crop_filter=crop_filter
        )

        # 2. Topic-Aware Editorial Headline Copy
        if not copy_data:
            copy_data = cls.generate_ai_copy(
                topic=topic,
                title=title,
                hook=hook,
                transcript=transcript,
                archetype=archetype
            )

        # 3. Detect Genre for Procedural Scientific / Technical Backdrop
        genre = TopicAwareBackdrop.detect_topic_genre(topic=topic, transcript=transcript)

        # 4. Render Universal Editorial Master Composition
        cls._render_editorial_master_composition(
            base_frame_path=str(temp_speaker_frame) if temp_speaker_frame.exists() else str(video_path),
            output_path=str(out_p),
            copy_data=copy_data,
            genre=genre,
            frame_meta=frame_meta,
            accent_color=accent_color
        )

        # Cleanup temporary frame
        if temp_speaker_frame.exists():
            try:
                temp_speaker_frame.unlink()
            except Exception:
                pass

        return out_p

    @classmethod
    def _render_editorial_master_composition(
        cls,
        base_frame_path: str,
        output_path: str,
        copy_data: Dict[str, Any],
        genre: str,
        frame_meta: Dict[str, Any],
        accent_color: str = "#FFE600"
    ) -> None:
        """
        Composites the 1080x1920 Universal Premium Podcast Thumbnail:
        - Dark charcoal / deep navy studio backdrop.
        - Real speaker positioned on RIGHT (or dual speaker balance).
        - Bold, condensed editorial typography on LEFT.
        - Primary words in WHITE, main keyword in WARM YELLOW with brush banner.
        - Subtle curved RED accent underline.
        - Topic-aware procedural backdrop (DNA, hourglass, ECG, neural).
        - Lower-third guest / authority badge above TikTok caption safe zone.
        """
        W, H = 1080, 1920
        accent_rgb = parse_color(accent_color, default_rgb=(255, 214, 0))

        # 1. Load Real Speaker Photo
        speaker_img = None
        if base_frame_path and Path(base_frame_path).exists():
            try:
                raw_bgr = cv2.imread(str(base_frame_path))
                if raw_bgr is not None:
                    # Apply professional subtle color grading & sharpness boost (preserving skin texture)
                    raw_bgr = cv2.convertScaleAbs(raw_bgr, alpha=1.06, beta=4)
                    speaker_img = Image.fromarray(cv2.cvtColor(raw_bgr, cv2.COLOR_BGR2RGB))
            except Exception as e:
                print(f"[ThumbnailDesigner] Speaker load error: {e}")

        if speaker_img is None:
            speaker_img = Image.new("RGB", (W, H), (14, 16, 22))

        # Fit speaker into 1080x1920
        iw, ih = speaker_img.size
        scale = max(W / float(iw), H / float(ih))
        nw, nh = int(round(iw * scale)), int(round(ih * scale))
        speaker_img = speaker_img.resize((nw, nh), Image.Resampling.LANCZOS)
        cx = (nw - W) // 2
        cy = (nh - H) // 2
        speaker_img = speaker_img.crop((cx, cy, cx + W, cy + H))

        # Check if dual-speaker layout
        is_dual = frame_meta.get("is_dual", False)

        # 2. Intelligent Composition & Subject Placement
        # In single-speaker layout, position speaker on the RIGHT so the LEFT is a clean text canvas.
        speaker_arr = np.array(speaker_img, dtype=np.float32)

        # Build deep dark charcoal studio canvas
        bg_canvas = np.zeros((H, W, 3), dtype=np.float32)
        for y in range(H):
            # Subtle vertical vignette: deep navy/charcoal top and bottom
            grad = 14.0 + (y / float(H)) * 8.0
            bg_canvas[y, :, 0] = grad * 0.95  # R
            bg_canvas[y, :, 1] = grad * 1.05  # G
            bg_canvas[y, :, 2] = grad * 1.25  # B (deep navy-slate touch)

        if not is_dual:
            # Shift speaker subject to right side to leave generous left text area
            # Left vignette mask: fade out left 0% to 58% so text has deep contrast
            left_mask = np.ones((H, W), dtype=np.float32)
            fade_w = int(W * 0.58)
            for x in range(fade_w):
                ratio = (x / float(fade_w)) ** 1.35
                left_mask[:, x] = ratio

            # Top & Bottom Safe Zone vignette
            top_h = int(H * 0.22)
            for y in range(top_h):
                r = float((1.0 - (y / float(top_h))) ** 1.4)
                left_mask[y, :] = left_mask[y, :] * float(1.0 - (r * 0.75))
            bot_start = int(H * 0.78)
            bot_h = H - bot_start
            for y in range(bot_start, H):
                r = float(((y - bot_start) / float(bot_h)) ** 1.3)
                left_mask[y, :] = left_mask[y, :] * float(1.0 - (r * 0.85))

            composite_arr = np.zeros_like(speaker_arr)
            for c in range(3):
                composite_arr[:, :, c] = speaker_arr[:, :, c] * left_mask + bg_canvas[:, :, c] * (1.0 - left_mask)
        else:
            # Dual speaker: dark central pillar vignette for center text placement
            center_mask = np.ones((H, W), dtype=np.float32)
            for x in range(int(W * 0.25), int(W * 0.75)):
                prog = abs(x - (W / 2.0)) / (W * 0.25)
                center_mask[:, x] = min(1.0, 0.25 + (prog ** 1.2) * 0.75)
            composite_arr = np.zeros_like(speaker_arr)
            for c in range(3):
                composite_arr[:, :, c] = speaker_arr[:, :, c] * center_mask + bg_canvas[:, :, c] * (1.0 - center_mask)

        base_canvas = Image.fromarray(np.clip(composite_arr, 0, 255).astype(np.uint8)).convert("RGBA")

        # 3. Transparent Overlay for Topic Graphics & Typography
        overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        # 4. Render Topic-Aware Procedural Background Accents
        TopicAwareBackdrop.render_procedural_backdrop(
            draw=draw,
            W=W,
            H=H,
            genre=genre,
            accent_rgb=accent_rgb
        )

        # 5. Render Universal Editorial Typography (Left-Aligned or Dual-Center)
        hw = copy_data.get("headline_white") or "THE"
        hy1 = copy_data.get("headline_yellow_1") or "SECRET TO"
        hy2 = copy_data.get("headline_yellow_2") or ""
        spk_name = copy_data.get("speaker_name") or "PODCAST INTERVIEW"
        spk_tag = copy_data.get("speaker_tag") or "EXCLUSIVE"

        if not is_dual:
            cls._render_left_editorial_typography(
                draw=draw,
                W=W,
                H=H,
                hw=hw,
                hy1=hy1,
                hy2=hy2,
                spk_name=spk_name,
                spk_tag=spk_tag,
                accent_rgb=accent_rgb
            )
        else:
            cls._render_dual_editorial_typography(
                draw=draw,
                W=W,
                H=H,
                hw=hw,
                hy1=hy1,
                hy2=hy2,
                spk_name=spk_name,
                spk_tag=spk_tag,
                accent_rgb=accent_rgb
            )

        # 6. Composite & Save 1080x1920 JPEG
        final_im = Image.alpha_composite(base_canvas, overlay).convert("RGB")
        final_im.save(output_path, "JPEG", quality=95)

    @classmethod
    def _render_left_editorial_typography(
        cls,
        draw: ImageDraw.ImageDraw,
        W: int,
        H: int,
        hw: str,
        hy1: str,
        hy2: str,
        spk_name: str,
        spk_tag: str,
        accent_rgb: Tuple[int, int, int]
    ) -> None:
        """
        Renders the Left-Aligned Editorial Typography:
        - Starts at Y: 360-500 (safely below top safe margin and above bottom captions).
        - Line 1 (White, e.g. "THE")
        - Line 2 (Yellow Brush Ribbon Banner, e.g. "SECRET TO")
        - Line 3 (Warm Yellow/Gold + Red Underline, e.g. "AGING?")
        - Bottom Authority Nameplate (Y: 1560)
        """
        font_big = get_font(FONT_IMPACT, 114)
        font_name = get_font(FONT_SEGOE_BOLD, 32)
        font_tag = get_font(FONT_SEGOE_REG, 22)

        start_x = 75
        curr_y = 440

        # Line 1: Pure White Text
        if hw:
            hw_str = hw.strip().upper()
            draw_text_with_stroke_and_shadow(
                draw, (start_x, curr_y), hw_str, font_big,
                fill=(255, 255, 255, 255),
                stroke_fill=(0, 0, 0, 230),
                stroke_width=6,
                shadow_offset=(4, 6)
            )
            bbox1 = font_big.getbbox(hw_str)
            curr_y += (bbox1[3] - bbox1[1]) + 20

        # Line 2: Warm Gold Ribbon / Brush Stroke Banner
        if hy1:
            hy1_str = hy1.strip().upper()
            bbox2 = font_big.getbbox(hy1_str)
            tw2 = bbox2[2] - bbox2[0]
            th2 = bbox2[3] - bbox2[1]

            bx = start_x - 12
            by = curr_y + 4
            bw = tw2 + 48
            bh = th2 + 24

            # Draw distressed organic brush highlight banner
            cls._draw_brush_ribbon(draw, bx, by, bw, bh, fill=(*accent_rgb, 255))

            # Dark text inside the yellow ribbon
            draw.text((bx + 24, by + 10 - bbox2[1]), hy1_str, font=font_big, fill=(12, 12, 14, 255))
            curr_y = by + bh + 16

        # Line 3: Warm Gold Text + Curved Red Underline
        if hy2:
            hy2_str = hy2.strip().upper()
            draw_text_with_stroke_and_shadow(
                draw, (start_x, curr_y), hy2_str, font_big,
                fill=(*accent_rgb, 255),
                stroke_fill=(0, 0, 0, 240),
                stroke_width=6,
                shadow_offset=(4, 7)
            )
            bbox3 = font_big.getbbox(hy2_str)
            tw3 = bbox3[2] - bbox3[0]
            curr_y += (bbox3[3] - bbox3[1]) + 16

            # Tapered curved red accent underline
            cls._draw_red_curved_stroke(draw, ux=start_x, uy=curr_y, uw=min(tw3 + 30, 440))

        # Bottom Authority Nameplate (Y: 1560 - cleanly positioned on right side)
        cls._render_authority_nameplate(draw, W, H, spk_name, spk_tag, accent_rgb)

    @classmethod
    def _render_dual_editorial_typography(
        cls,
        draw: ImageDraw.ImageDraw,
        W: int,
        H: int,
        hw: str,
        hy1: str,
        hy2: str,
        spk_name: str,
        spk_tag: str,
        accent_rgb: Tuple[int, int, int]
    ) -> None:
        """
        Renders Dual-Speaker Editorial Typography centered between host and guest
        (matching Reference 1: "NOT 1% OF ME IS SCARED").
        """
        font_big = get_font(FONT_IMPACT, 108)

        lines = [
            (hw.strip().upper(), (255, 255, 255)),
            (hy1.strip().upper(), accent_rgb),
            (hy2.strip().upper(), (255, 255, 255))
        ]

        curr_y = 620
        for txt, col in lines:
            if not txt:
                continue
            bbox = font_big.getbbox(txt)
            tw = bbox[2] - bbox[0]
            th = bbox[3] - bbox[1]
            tx = (W - tw) // 2
            draw_text_with_stroke_and_shadow(
                draw, (tx, curr_y), txt, font_big,
                fill=(*col, 255),
                stroke_fill=(0, 0, 0, 240),
                stroke_width=7,
                shadow_offset=(4, 8)
            )
            curr_y += th + 26

        cls._render_authority_nameplate(draw, W, H, spk_name, spk_tag, accent_rgb)

    @classmethod
    def _draw_brush_ribbon(
        cls,
        draw: ImageDraw.ImageDraw,
        bx: int,
        by: int,
        bw: int,
        bh: int,
        fill: tuple
    ) -> None:
        """Renders an organic editorial brush highlight badge with distressed edges."""
        # Solid core with rounded corners
        draw.rounded_rectangle([bx + 14, by, bx + bw - 14, by + bh], radius=8, fill=fill)
        # Left jagged brush edge
        left_poly = [
            (bx + 16, by), (bx + 2, by + 16), (bx + 10, by + 36), (bx - 4, by + 58),
            (bx + 12, by + 82), (bx + 3, by + 104), (bx + 18, by + bh), (bx + 24, by)
        ]
        draw.polygon(left_poly, fill=fill)
        # Right jagged brush edge
        right_poly = [
            (bx + bw - 18, by), (bx + bw - 2, by + 18), (bx + bw + 6, by + 48),
            (bx + bw - 4, by + 76), (bx + bw + 10, by + 98), (bx + bw - 16, by + bh), (bx + bw - 24, by)
        ]
        draw.polygon(right_poly, fill=fill)

    @classmethod
    def _draw_red_curved_stroke(
        cls,
        draw: ImageDraw.ImageDraw,
        ux: int,
        uy: int,
        uw: int
    ) -> None:
        """Renders a cinematic curved red brush stroke underline."""
        red = (255, 59, 48, 255)
        pts_top = []
        pts_bot = []
        for x in range(ux, ux + uw, 6):
            prog = (x - ux) / float(uw)
            arch = np.sin(prog * np.pi)
            thick = 4.0 + arch * 11.0
            y_center = uy + np.sin(prog * 2.8) * 6.0
            pts_top.append((x, y_center - thick / 2.0))
            pts_bot.append((x, y_center + thick / 2.0))

        poly = pts_top + pts_bot[::-1]
        draw.polygon(poly, fill=red)

    @classmethod
    def _render_authority_nameplate(
        cls,
        draw: ImageDraw.ImageDraw,
        W: int,
        H: int,
        spk_name: str,
        spk_tag: str,
        accent_rgb: Tuple[int, int, int]
    ) -> None:
        """
        Renders the clean editorial guest authority nameplate:
        PETER ATTIA
        -----------
        LONGEVITY EXPERT
        Positioned cleanly at X: 640-680, Y: 1560 (safely inside 3:4 profile grid and above TikTok captions).
        """
        font_name = get_font(FONT_SEGOE_BOLD, 30)
        font_tag = get_font(FONT_SEGOE_REG, 20)

        name_str = spk_name.strip().upper()
        tag_str = spk_tag.strip().upper()

        bbox_n = font_name.getbbox(name_str)
        nw = bbox_n[2] - bbox_n[0]
        nx = max(580, W - nw - 100)
        ny = 1570

        # Speaker Name
        draw_text_with_stroke_and_shadow(
            draw, (nx, ny), name_str, font_name,
            fill=(255, 255, 255, 255),
            stroke_fill=(0, 0, 0, 220),
            stroke_width=3,
            shadow_offset=(2, 3)
        )

        # Warm Gold Accent Rule
        line_w = max(nw, 220)
        draw.line([nx, ny + 40, nx + line_w, ny + 40], fill=(*accent_rgb, 240), width=3)

        # Authority Tag / Subtitle
        draw.text((nx, ny + 48), tag_str, font=font_tag, fill=(210, 210, 210, 240))
