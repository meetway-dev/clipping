import math
import re
from pathlib import Path
from typing import List, Dict, Any, Optional

class SubtitleGenerator:
    """
    Generates professional, viral-style Advanced SubStation Alpha (.ass) subtitles
    with:
    1. Word-by-word kinetic karaoke highlighting in the lower third.
    2. Submagic-style Power Keyword Color Highlighting (Gold, Neon Green, Coral Red, Cyan).
    3. Auto-Emoji Injection (💰, 🔥, 🚀, 💡, ⚠️, 🤯) on high-impact spoken words.
    4. Opus Clip-style Top Topic Headline Banners with series part badges.
    """

    STYLES = {
        "hormozi": {
            "name": "Hormozi",
            "fontname": "Impact",
            "fontsize": 64,
            "primary_color": "&H00FFFFFF",     # White (inactive words)
            "secondary_color": "&H0000E5FF",   # Vivid Amber/Gold Yellow (active word)
            "outline_color": "&H00000000",     # Deep Black Outline
            "back_color": "&H60000000",        # Subtle shadow
            "bold": 1,
            "outline": 5.0,
            "shadow": 3.0,
            "margin_v": 340,                   # Lower third (chest level in 1080x1920)
            "uppercase": True
        },
        "beast": {
            "name": "Beast Green",
            "fontname": "Arial Black",
            "fontsize": 60,
            "primary_color": "&H00FFFFFF",
            "secondary_color": "&H0000FF55",   # Neon Toxic Green
            "outline_color": "&H00000000",
            "back_color": "&H80000000",
            "bold": 1,
            "outline": 5.0,
            "shadow": 3.0,
            "margin_v": 340,
            "uppercase": True
        },
        "cyber": {
            "name": "Cyber Neon",
            "fontname": "Trebuchet MS",
            "fontsize": 58,
            "primary_color": "&H00F0F0F0",
            "secondary_color": "&H00FFFF00",   # Electric Cyan
            "outline_color": "&H00200020",
            "back_color": "&H00FF0077",
            "bold": 1,
            "outline": 4.5,
            "shadow": 3.5,
            "margin_v": 340,
            "uppercase": True
        },
        "clean": {
            "name": "Clean Modern",
            "fontname": "Arial",
            "fontsize": 56,
            "primary_color": "&H00FFFFFF",
            "secondary_color": "&H001EB7FF",   # Warm Coral/Gold
            "outline_color": "&H00111111",
            "back_color": "&H40000000",
            "bold": 1,
            "outline": 3.0,
            "shadow": 2.0,
            "margin_v": 330,
            "uppercase": False
        }
    }

    # High-impact emotional and contextual keyword categories
    POWER_CATEGORIES = {
        "money": {
            "words": {"money", "wealth", "cash", "million", "billion", "dollar", "dollars", "rich", "profit", "revenue", "broke", "financial", "fund", "funds", "cost", "costs", "price", "pay", "paid", "buy", "buying", "invest", "investor", "investors", "crypto", "bitcoin"},
            "color": "&H0000E5FF",  # Vivid Gold
            "emoji": "💰"
        },
        "fire": {
            "words": {"secret", "secrets", "truth", "viral", "crazy", "craziest", "hack", "power", "explosive", "massive", "insane", "fast", "huge", "shocking", "wild", "unbelievable"},
            "color": "&H000080FF",  # Bright Orange/Amber
            "emoji": "🔥"
        },
        "growth": {
            "words": {"growth", "scale", "scaling", "launch", "grow", "success", "winning", "win", "10x", "millionaire", "business", "company", "career", "champion", "freedom"},
            "color": "&H0000FF55",  # Neon Toxic Green
            "emoji": "🚀"
        },
        "warning": {
            "words": {"mistake", "mistakes", "wrong", "fail", "failed", "failure", "danger", "stop", "never", "ruin", "ruined", "lose", "lost", "disaster", "trap", "warning", "dead", "crisis", "worst", "fatal"},
            "color": "&H003333FF",  # Vivid Coral Red
            "emoji": "⚠️"
        },
        "brain": {
            "words": {"mindset", "focus", "focused", "brain", "think", "thinking", "lesson", "realize", "realized", "smart", "genius", "idea", "advice", "rule", "rules", "learn", "psychology"},
            "color": "&H00FFFF00",  # Electric Cyan
            "emoji": "💡"
        }
    }

    @staticmethod
    def format_timestamp(seconds: float) -> str:
        """Format seconds into ASS timestamp format: H:MM:SS.cs"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        centiseconds = int(round((seconds - int(seconds)) * 100))
        if centiseconds >= 100:
            centiseconds = 99
        return f"{hours}:{minutes:02d}:{secs:02d}.{centiseconds:02d}"

    @classmethod
    def _analyze_word_emphasis(cls, raw_word: str) -> Dict[str, Any]:
        """Detects if a word belongs to a power category and returns emoji + custom color."""
        clean = re.sub(r"[^\w]", "", raw_word).lower()
        for cat_name, cat_data in cls.POWER_CATEGORIES.items():
            if clean in cat_data["words"]:
                return {
                    "is_power": True,
                    "color": cat_data["color"],
                    "emoji": cat_data["emoji"]
                }
        return {"is_power": False, "color": None, "emoji": None}

    @classmethod
    def format_multiline_headline(cls, text: str, max_chars_per_line: int = 28) -> str:
        """Formats the top viral headline into punchy, balanced lines for 9:16 vertical video."""
        if not text:
            return ""
        clean = re.sub(r"[\[\]]", "", str(text)).strip()
        if not clean:
            return ""

        if len(clean) <= max_chars_per_line:
            return clean

        # Natural punctuation splits (: - — ?)
        for sep in [": ", " - ", " — "]:
            if sep in clean:
                parts = clean.split(sep, 1)
                p0 = parts[0].strip()
                p1 = parts[1].strip()
                if len(p0) <= max_chars_per_line and len(p1) <= max_chars_per_line * 1.8:
                    sep_char = ":" if sep == ": " else " -"
                    if len(p1) > max_chars_per_line:
                        sub_wrapped = cls.format_multiline_headline(p1, max_chars_per_line=max_chars_per_line)
                        return f"{p0}{sep_char}\\N{sub_wrapped}"
                    return f"{p0}{sep_char}\\N{p1}"

        # Word wrapping into balanced lines
        words = clean.split()
        lines = []
        curr = []
        curr_len = 0
        for w in words:
            if curr and (curr_len + len(w) + 1 > max_chars_per_line):
                lines.append(" ".join(curr))
                curr = [w]
                curr_len = len(w)
            else:
                curr.append(w)
                curr_len += len(w) + (1 if curr_len > 0 else 0)
        if curr:
            lines.append(" ".join(curr))

        return "\\N".join(lines[:3])

    @classmethod
    def create_ass_file(
        cls,
        words: List[Dict[str, Any]],
        output_path: Path,
        style_key: str = "hormozi",
        words_per_batch: int = 3,
        clip_start_offset: float = 0.0,
        clip_duration: Optional[float] = None,
        topic_headline: Optional[str] = None,
        part_info: Optional[str] = None,
        show_headline_banner: bool = True,
        enable_auto_emojis: bool = True,
        layout_mode: str = "speaker_focus",
        top_space: int = 450,
        video_h: int = 608,
        top_padding: float = 0.0,
        bottom_padding: float = 0.0
    ) -> Path:
        """
        Creates an animated .ass subtitle file with:
        1. Word-by-word kinetic karaoke highlighting in the lower third or dedicated bottom canvas.
        2. Submagic-style Power Keyword Highlighting and Auto-Emojis.
        3. Top Topic Headline Banner (Opus Clip style) visible across the whole clip.
        4. Multi-part series indicator (e.g. PART 1/2) if in parting mode.
        5. Adaptive vertical alignment respecting Top and Bottom Safe Area Padding:
           - In fit_canvas mode: Top hook centered in top canvas, captions centered in bottom canvas.
           - In split-screen mode: Captions positioned at center dividing line or dedicated bottom padding.
           - In speaker focus / face center / crop mode: Dedicated safe zones or cinematic lower third.
        """
        style = cls.STYLES.get(style_key, cls.STYLES["hormozi"])
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        top_pct = max(0.0, min(45.0, float(top_padding))) / 100.0
        bottom_pct = max(0.0, min(45.0, float(bottom_padding))) / 100.0
        if top_pct + bottom_pct > 0.80:
            scale_pad = 0.80 / (top_pct + bottom_pct)
            top_pct *= scale_pad
            bottom_pct *= scale_pad

        top_pad_px = int(round(1920 * top_pct))
        bottom_pad_px = int(round(1920 * bottom_pct))
        available_h = max(100, 1920 - top_pad_px - bottom_pad_px)
        has_padding = (top_pad_px > 0 or bottom_pad_px > 0)

        is_fit_canvas = layout_mode in ["fit_canvas", "fit_center", "fit_hook", "fit_video"]

        # 1. Pre-format Top Viral Hook Headline to dynamically compute adaptive dimensions
        line_count = 1
        formatted_headline = ""
        banner_dialogue_line = ""
        if show_headline_banner:
            raw_headline = re.sub(r"[\[\]]", "", str(topic_headline or "VIRAL PODCAST TOPIC")).strip().upper()
            if part_info and part_info.upper() not in raw_headline:
                raw_headline = f"{raw_headline} ({part_info.upper()})"
            formatted_headline = cls.format_multiline_headline(raw_headline, max_chars_per_line=28)
            line_elements = formatted_headline.split("\\N")
            line_count = max(1, len(line_elements))

            # Style: Line 1 crisp white, Line 2 high-CTR neon yellow punch, Line 3 white
            # &H0000E5FF is neon bright yellow in ASS BGR, &H00FFFFFF is crisp white, Outline &H00000000 (black 4.5px)
            if len(line_elements) == 2:
                banner_dialogue_line = (
                    f"{{\\fad(250,0)\\3c&H00000000&}}"
                    f"{{\\c&H00FFFFFF&}}{line_elements[0]}\\N"
                    f"{{\\c&H0000E5FF&}}{line_elements[1]}"
                )
            elif len(line_elements) >= 3:
                banner_dialogue_line = (
                    f"{{\\fad(250,0)\\3c&H00000000&}}"
                    f"{{\\c&H00FFFFFF&}}{line_elements[0]}\\N"
                    f"{{\\c&H0000E5FF&}}{line_elements[1]}\\N"
                    f"{{\\c&H00FFFFFF&}}{'\\N'.join(line_elements[2:])}"
                )
            else:
                banner_dialogue_line = f"{{\\fad(250,0)\\c&H0000E5FF&\\3c&H00000000&}}{formatted_headline}"

        # Adaptive header font size based on line count and canvas space
        if line_count >= 3:
            header_font_size = 46
        elif line_count == 2:
            header_font_size = 50
        else:
            header_font_size = 54
        est_banner_h = line_count * (header_font_size + 12)

        if is_fit_canvas:
            actual_top_space = top_pad_px if has_padding else max(80, min(950, top_space))
            bottom_space = max(160, 1920 - (actual_top_space + video_h))
            active_margin_v = max(120, int(bottom_space / 2))
            header_margin_v = max(35, int((actual_top_space - est_banner_h) / 2))
        elif layout_mode == "split_screen":
            if bottom_pad_px >= 280:
                active_margin_v = max(120, int(bottom_pad_px / 2))
            else:
                split_h = available_h // 2
                active_margin_v = max(240, bottom_pad_px + split_h - 70)

            if top_pad_px > 0:
                header_margin_v = max(35, int((top_pad_px - est_banner_h) / 2))
            else:
                header_margin_v = 120
        else:
            if bottom_pad_px >= 280:
                active_margin_v = max(140, int(bottom_pad_px / 2))
            elif bottom_pad_px > 0:
                active_margin_v = max(style.get("margin_v", 340), bottom_pad_px + 120)
            else:
                active_margin_v = style.get("margin_v", 340)

            if top_pad_px >= 180:
                header_margin_v = max(35, int((top_pad_px - est_banner_h) / 2))
            else:
                header_margin_v = 120

        header = f"""[Script Info]
Title: ClipForge Viral Subtitles
ScriptType: v4.00+
WrapStyle: 0
ScaledBorderAndShadow: yes
YCbCr Matrix: TV.601
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{style['fontname']},{style['fontsize']},{style['primary_color']},{style['secondary_color']},{style['outline_color']},{style['back_color']},{style['bold']},0,0,0,100,100,2,0,1,{style['outline']},{style['shadow']},2,50,50,{active_margin_v},1
Style: TopicHeader,Impact,{header_font_size},&H0000E5FF,&H0000FFFF,&H00000000,&H80000000,1,0,0,0,100,100,2,0,1,4.5,2.0,8,40,40,{header_margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

        events = []
        total_duration = clip_duration if clip_duration and clip_duration > 0 else 60.0

        # 1. Top Viral Hook Engaging Headline Banner (High-CTR Yellow Impact Text, 0:00 to End)
        if show_headline_banner and formatted_headline:
            h_start = cls.format_timestamp(0.0)
            h_end = cls.format_timestamp(total_duration)
            events.append(f"Dialogue: 1,{h_start},{h_end},TopicHeader,,0,0,0,,{banner_dialogue_line}")

        # 2. Filter and normalize spoken words relative to clip start
        normalized_words = []
        for w in words:
            w_start = max(0.0, w["start"] - clip_start_offset)
            w_end = max(w_start + 0.08, w["end"] - clip_start_offset)
            text = w["word"].strip()
            if style["uppercase"]:
                text = text.upper()
            if text:
                emphasis = cls._analyze_word_emphasis(w["word"])
                normalized_words.append({
                    "word": text,
                    "start": w_start,
                    "end": w_end,
                    "emphasis": emphasis
                })

        if not normalized_words:
            output_path.write_text(header + "\n".join(events) + "\n", encoding="utf-8")
            return output_path

        # Group words into short punchy spoken batches (2-3 words for vertical)
        batches = []
        curr_batch = []
        for w in normalized_words:
            curr_batch.append(w)
            has_break = any(p in w["word"] for p in [".", "?", "!", ","])
            if len(curr_batch) >= words_per_batch or (has_break and len(curr_batch) >= 2):
                batches.append(curr_batch)
                curr_batch = []
        if curr_batch:
            batches.append(curr_batch)

        # Generate karaoke events for each batch
        for batch in batches:
            batch_start = batch[0]["start"]
            batch_end = batch[-1]["end"]
            batch_end = max(batch_end, batch_start + 0.35)

            start_str = cls.format_timestamp(batch_start)
            end_str = cls.format_timestamp(batch_end)

            karaoke_text_parts = []
            for w_idx, word_info in enumerate(batch):
                # Calculate active duration until next word or word end to keep highlight perfectly synced
                if w_idx < len(batch) - 1:
                    next_start = batch[w_idx + 1]["start"]
                    dur_sec = max(0.10, next_start - word_info["start"])
                else:
                    dur_sec = max(0.12, word_info["end"] - word_info["start"])

                dur_cs = int(round(dur_sec * 100))
                dur_cs = max(8, dur_cs)

                display_word = word_info["word"]
                emph = word_info.get("emphasis") or {}

                # If word has power keyword and auto-emojis are enabled
                if enable_auto_emojis and emph.get("is_power") and emph.get("emoji"):
                    # Use explicit font switch for emoji to prevent Impact baseline jumping or font fallback corruption
                    display_word = f"{display_word} {{\\fnSegoe UI Emoji\\1c&H00FFFFFF}}{emph['emoji']}{{\\fn{style['fontname']}}}"
                    color_tag = f"\\1c{emph['color']}"
                    karaoke_text_parts.append(f"{{\\kf{dur_cs}{color_tag}}}{display_word}{{\\1c{style['primary_color']}}}")
                elif emph.get("is_power"):
                    color_tag = f"\\1c{emph['color']}"
                    karaoke_text_parts.append(f"{{\\kf{dur_cs}{color_tag}}}{display_word}{{\\1c{style['primary_color']}}}")
                else:
                    karaoke_text_parts.append(f"{{\\kf{dur_cs}}}{display_word}")

            batch_text = " ".join(karaoke_text_parts)
            # Subtle bounce scale animation on active speech batch
            animated_line = f"{{\\fscx106\\fscy106\\t(0,70,\\fscx100\\fscy100)}}{batch_text}"

            events.append(f"Dialogue: 0,{start_str},{end_str},Default,,0,0,0,,{animated_line}")

        content = header + "\n".join(events) + "\n"
        output_path.write_text(content, encoding="utf-8")
        return output_path
