import os
import sys
import json
import time
import shutil
import logging
import subprocess
import urllib.request
import urllib.error
from pathlib import Path
from typing import Dict, Any, List, Optional
from core.config import DEFAULT_CONFIG

logger = logging.getLogger("ClipForge.Ollama")

class OllamaManager:
    """
    Manages local Ollama lifecycle, automatic background startup,
    model detection (LLaMA 3.2, Qwen 2.5 Coder, etc.), and inference.
    100% free, runs entirely offline on local GPU with zero token fees.
    """
    _instance: Optional["OllamaManager"] = None
    _active_model: Optional[str] = None
    _is_running: bool = False

    def __init__(self):
        self.base_url = DEFAULT_CONFIG.get("ollama_url", "http://127.0.0.1:11434")
        self.preferred_models = [
            "qwen2.5:7b", "qwen2.5:14b", "qwen2.5:3b", "qwen2.5:1.5b",
            "llama3.2:3b", "llama3.2:latest", "llama3.2",
            "qwen2.5-coder:7b", "deepseek-coder:6.7b"
        ]

    @classmethod
    def get_instance(cls) -> "OllamaManager":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def get_status(self) -> Dict[str, Any]:
        """Returns connection and model status for Ollama."""
        return self.check_connection()

    def check_connection(self) -> Dict[str, Any]:
        """Checks if Ollama is running and queries available models."""
        try:
            req = urllib.request.Request(f"{self.base_url}/api/tags")
            with urllib.request.urlopen(req, timeout=1.5) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    raw_models = data.get("models", [])
                    model_names = [m.get("name", "") for m in raw_models]

                    best_model = self._select_best_model(model_names)
                    self._active_model = best_model
                    self._is_running = True

                    return {
                        "connected": True,
                        "active_model": best_model,
                        "available_models": model_names,
                        "url": self.base_url
                    }
        except Exception:
            pass

        self._is_running = False
        return {
            "connected": False,
            "active_model": None,
            "available_models": [],
            "url": self.base_url
        }

    def ensure_running(self) -> Dict[str, Any]:
        """
        Ensures Ollama is active. If not running, automatically spawns
        'ollama serve' in background without interrupting the user.
        """
        conn = self.check_connection()
        if conn["connected"]:
            return conn

        # Attempt to locate ollama executable
        ollama_bin = shutil.which("ollama")
        if not ollama_bin and sys.platform == "win32":
            win_path = Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Ollama" / "ollama.exe"
            if win_path.exists():
                ollama_bin = str(win_path)

        if not ollama_bin:
            logger.info("Ollama CLI not found on host. App will use built-in heuristic NLP.")
            return {
                "connected": False,
                "active_model": "built-in heuristic",
                "available_models": [],
                "message": "Ollama not installed; using built-in NLP."
            }

        logger.info(f"Auto-launching local Ollama daemon: {ollama_bin} serve...")
        try:
            creationflags = 0
            if sys.platform == "win32":
                creationflags = subprocess.CREATE_NO_WINDOW | getattr(subprocess, "DETACHED_PROCESS", 0)

            subprocess.Popen(
                [ollama_bin, "serve"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=creationflags
            )

            # Wait up to 3 seconds for server socket to open
            for _ in range(6):
                time.sleep(0.5)
                conn = self.check_connection()
                if conn["connected"]:
                    logger.info(f"Ollama server connected! Active model: {conn['active_model']}")
                    return conn

        except Exception as e:
            logger.warning(f"Could not auto-start Ollama server: {e}")

        return {
            "connected": False,
            "active_model": "built-in heuristic",
            "available_models": [],
            "message": "Ollama starting or offline; using built-in NLP."
        }

    def _select_best_model(self, available: List[str]) -> str:
        """Selects the strongest available general-purpose model for topic analysis."""
        for pref in self.preferred_models:
            for name in available:
                if name == pref or name.startswith(pref):
                    return name
        for name in available:
            if "embed" not in name.lower():
                return name
        return "llama3.2"

    def generate(self, prompt: str, system_prompt: str = "", model: Optional[str] = None, timeout: float = 30.0) -> Optional[str]:
        """
        Sends an inference request to Ollama. Returns response text or None if offline.
        """
        active = model or self._active_model or "llama3.2"
        payload = {
            "model": active,
            "prompt": prompt,
            "stream": False
        }
        if system_prompt:
            payload["system"] = system_prompt

        try:
            req = urllib.request.Request(f"{self.base_url}/api/generate", method="POST")
            req.add_header("Content-Type", "application/json")
            req_data = json.dumps(payload).encode("utf-8")

            with urllib.request.urlopen(req, data=req_data, timeout=timeout) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    return data.get("response", "").strip()
        except Exception as e:
            logger.debug(f"Ollama generation fallback triggered: {e}")
            return None

    def summarize_podcast(self, full_transcript: str, duration: float) -> Dict[str, Any]:
        """
        Generates an executive podcast summary, key takeaways, and topic map.
        Uses local Ollama LLM if available; gracefully falls back to built-in NLP.
        """
        prompt = (
            f"You are an elite podcast producer and video editor.\n"
            f"Analyze this podcast transcript (duration: {duration/60.0:.1f} minutes) and return a structured JSON summary.\n\n"
            f"Transcript snippet:\n{full_transcript[:3500]}\n\n"
            f"Respond with ONLY a valid JSON object matching this exact schema:\n"
            f"{{\n"
            f'  "overview": "A concise 2-3 sentence executive synopsis of the central discussion.",\n'
            f'  "key_takeaways": ["Takeaway 1", "Takeaway 2", "Takeaway 3", "Takeaway 4"],\n'
            f'  "chapters": [\n'
            f'    {{"title": "Punchy Topic Name", "start_pct": 0.05, "summary": "What is covered in this section", "energy": 94}},\n'
            f'    {{"title": "Second Topic Name", "start_pct": 0.35, "summary": "What is covered in this section", "energy": 97}}\n'
            f'  ],\n'
            f'  "notable_quotes": ["Quote 1", "Quote 2"]\n'
            f"}}"
        )

        llm_resp = self.generate(
            prompt=prompt,
            system_prompt="You are a JSON-only API that summarizes podcasts into viral topic briefs.",
            timeout=45.0
        )

        if llm_resp:
            try:
                # Clean any markdown code fences if present
                clean = llm_resp.replace("```json", "").replace("```", "").strip()
                parsed = json.loads(clean)
                if "overview" in parsed and "key_takeaways" in parsed:
                    takeaways = parsed.get("key_takeaways")
                    if not isinstance(takeaways, list):
                        takeaways = []
                    fallback_takeaways = [
                        "Prioritize the primary constraint before trying to scale.",
                        "Use clear examples and personal stakes to keep the audience engaged.",
                        "Turn the key lesson into one concrete action.",
                        "Remember the conclusion while applying the discussion to real decisions."
                    ]
                    parsed["key_takeaways"] = [
                        str(t).strip()
                        for t in takeaways
                        if isinstance(t, (str, dict)) and str(t).strip()
                    ]
                    while len(parsed["key_takeaways"]) < 3:
                        parsed["key_takeaways"].append(
                            fallback_takeaways[len(parsed["key_takeaways"])]
                        )
                    if len(parsed["key_takeaways"]) > 4:
                        parsed["key_takeaways"] = parsed["key_takeaways"][:4]
                    # Map start_pct to absolute timestamps
                    chapters = parsed.get("chapters", [])
                    for ch in chapters:
                        pct = ch.get("start_pct", 0.0)
                        ch["start"] = round(pct * duration, 1)
                        ch["end"] = round(min(duration, (pct + 0.25) * duration), 1)
                        ch["duration"] = round(ch["end"] - ch["start"], 1)
                    parsed["source"] = "ollama"
                    parsed["model"] = self._active_model
                    return parsed
            except Exception:
                pass

        # Built-in Heuristic Fallback
        return self._heuristic_podcast_summary(full_transcript, duration)

    def generate_viral_hooks(self, transcript: str, topic_title: str = "") -> List[Dict[str, str]]:
        """
        Generates 5 distinct high-retention vertical video hooks for TikTok, Shorts, and Reels.
        Uses local Ollama LLaMA 3.2 if available, with instantaneous heuristic fallback.
        """
        prompt = (
            f"You are a viral social media director specializing in TikTok, YouTube Shorts, and Instagram Reels.\n"
            f"Topic: {topic_title or 'Podcast Highlight'}\n"
            f"Transcript snippet:\n{transcript[:1500]}\n\n"
            f"Generate 5 high-converting vertical video hook headlines that stop viewers from scrolling within 2 seconds.\n"
            f"The headline should be engaging, multi-word (6 to 12 words), and crafted to fit beautifully into 2-3 lines across the spacious top safe-area banner.\n"
            f"Respond with ONLY a valid JSON array of 5 objects matching this schema:\n"
            f"[\n"
            f'  {{"type": "Curiosity Gap", "hook": "Engaging curiosity hook (6 to 12 words) 🤯", "style": "curiosity"}},\n'
            f'  {{"type": "Controversial / Warning", "hook": "High-urgency warning hook (6 to 12 words) ⚠️", "style": "warning"}},\n'
            f'  {{"type": "Direct Question", "hook": "Thought-provoking question (6 to 12 words) ❓", "style": "question"}},\n'
            f'  {{"type": "Bold Claim", "hook": "Powerful counter-intuitive claim (6 to 12 words) 💰", "style": "bold"}},\n'
            f'  {{"type": "Actionable Insight", "hook": "High-value framework or blueprint (6 to 12 words) 🚀", "style": "action"}}\n'
            f"]"
        )

        resp = self.generate(prompt=prompt, system_prompt="You are a JSON-only API that writes viral short-form hooks.", timeout=30.0)
        if resp:
            try:
                clean = resp.replace("```json", "").replace("```", "").strip()
                parsed = json.loads(clean)
                if isinstance(parsed, list) and len(parsed) >= 3:
                    normalized = []
                    styles = ["curiosity", "warning", "question", "bold", "action"]
                    types = ["Curiosity Gap", "Controversial / Warning", "Direct Question", "Bold Claim", "Actionable Insight"]
                    for i, item in enumerate(parsed[:5]):
                        if not isinstance(item, dict):
                            continue
                        hook = str(item.get("hook", "")).strip()
                        if hook:
                            normalized.append({
                                "type": str(item.get("type", types[i if i < len(types) else 0])).strip(),
                                "hook": hook,
                                "style": str(item.get("style", styles[i if i < len(styles) else 0])).strip()
                            })
                    if len(normalized) >= 3:
                        return normalized
            except Exception:
                pass

        # Heuristic fallback based on keywords and topic (6 to 12 words)
        clean_title = (topic_title or "THIS MOMENT").strip().title()
        return [
            {"type": "Curiosity Gap", "hook": f"The Untold Truth About {clean_title} Nobody Talks About 🤯", "style": "curiosity"},
            {"type": "Controversial / Warning", "hook": f"Stop Making This Costly {clean_title} Mistake Before It's Too Late ⚠️", "style": "warning"},
            {"type": "Direct Question", "hook": f"Why Do 99% Of People Get {clean_title} Completely Wrong? ❓", "style": "question"},
            {"type": "Bold Claim", "hook": f"This Simple 60-Second Shift In {clean_title} Changes Everything 💰", "style": "bold"},
            {"type": "Actionable Insight", "hook": f"The Exact Step-By-Step Blueprint To Master {clean_title} 🚀", "style": "action"}
        ]

    def translate_transcript(self, transcript: str, target_lang: str = "es") -> Dict[str, Any]:
        """
        Translates transcript text into target language (es, fr, de, hi, pt, it, ja)
        using local Ollama LLM, with fallback.
        """
        lang_names = {
            "es": "Spanish",
            "fr": "French",
            "de": "German",
            "hi": "Hindi",
            "pt": "Portuguese",
            "it": "Italian",
            "ja": "Japanese",
            "ar": "Arabic"
        }
        target_name = lang_names.get(target_lang.lower(), target_lang)

        prompt = (
            f"Translate this podcast clip transcript into fluent, natural {target_name} suitable for video captions.\n"
            f"Preserve conversational tone and punchiness.\n\n"
            f"Transcript:\n{transcript[:1500]}\n\n"
            f"Respond with ONLY a valid JSON object matching:\n"
            f'{{"translated_text": "Translated transcript here", "language": "{target_name}", "suggested_title": "Translated hook title"}}\n'
        )

        resp = self.generate(prompt=prompt, system_prompt="You are an expert multilingual video translator.", timeout=20.0)
        if resp:
            try:
                clean = resp.replace("```json", "").replace("```", "").strip()
                parsed = json.loads(clean)
                if "translated_text" in parsed:
                    parsed["language"] = target_name
                    if not str(parsed.get("suggested_title", "")).strip():
                        parsed["suggested_title"] = f"[{target_lang.upper()}] {parsed['translated_text'][:30]}..."
                    return parsed
            except Exception:
                pass

        return {
            "translated_text": transcript,
            "language": target_name,
            "suggested_title": f"[{target_name[:2].upper()}] {transcript[:30]}..."
        }

    def suggest_b_roll_moments(self, transcript: str) -> List[Dict[str, Any]]:
        """
        Scans clip speech to suggest visual B-roll clips, stickers, and sound effects
        to maximize viewer retention.
        """
        suggestions = []
        lower = transcript.lower()

        cues = [
            ({"money", "wealth", "cash", "million", "dollar", "profit", "income"}, "B-ROLL: Cash Stacks & Stock Chart", "SFX: Cash Register Ding 💰", "money stock market chart 4k"),
            ({"secret", "mistake", "wrong", "danger", "warning", "fail", "costly"}, "B-ROLL: Dramatic Warning Flash", "SFX: Deep Bass Drop / Record Scratch ⚠️", "caution warning sign dark cinematic"),
            ({"growth", "scale", "launch", "fast", "huge", "win", "10x"}, "B-ROLL: Rocket Launch / High Speed City", "SFX: Whoosh / Sonic Boom 🚀", "rocket launch cinematic timelapse"),
            ({"think", "brain", "idea", "realize", "smart", "psychology", "mind"}, "B-ROLL: 3D Neural Synapses Firing", "SFX: Lightbulb Ping 💡", "brain neural network glowing"),
            ({"stop", "never", "ruin", "crisis", "worst", "quit"}, "B-ROLL: Stop Sign / Red Screen Flash", "SFX: Error Buzzer 🛑", "red stop alert cinematic overlay"),
            ({"body", "workout", "muscle", "health", "diet", "gym"}, "B-ROLL: High-Intensity Workout", "SFX: Heartbeat Thump 🫀", "gym athlete heavy training cinematic")
        ]

        for word_set, b_roll, sfx, search_query in cues:
            matched = [w for w in word_set if w in lower]
            if matched:
                suggestions.append({
                    "trigger_words": matched,
                    "b_roll_suggestion": b_roll,
                    "sfx_cue": sfx,
                    "stock_search_query": search_query,
                    "overlay_motion": "zoom_in" if "Launch" in b_roll or "Cash" in b_roll else "slow_pan"
                })

        return suggestions[:4]

    def ai_edit_copilot(self, clip_data: Dict[str, Any], instruction: str) -> Dict[str, Any]:
        """
        AI Natural Language Video Edit Copilot.
        Allows creators to command the AI editor in plain English:
        - "Make the hook punchier and focus on money"
        - "Change subtitle style to MrBeast and boost virality"
        - "Add high-converting controversy"
        Returns structured edits ready to be applied instantly.
        """
        curr_title = str(clip_data.get("title", "")).strip()
        curr_hook = str(clip_data.get("hook", "")).strip()
        transcript = str(clip_data.get("full_transcript", curr_hook))[:1000]

        # 1. Try local Ollama if connected
        prompt = f"""You are an elite AI Video Editor and Short-Form Director.
Creator Instruction: "{instruction}"

Current Clip State:
- Title / Headline: {curr_title}
- Opening Hook: {curr_hook}
- Transcript snippet: {transcript}

Based on the creator's instruction, optimize this clip for maximum TikTok/Reels retention and viral CTR.
Respond with ONLY a raw JSON object matching this schema:
{{
  "updated_title": "PUNCHY 6 TO 12 WORD TOPIC HEADLINE IN ALL CAPS",
  "updated_hook": "Refined opening spoken hook sentence...",
  "suggested_subtitle_style": "hormozi",
  "suggested_layout": "fit_canvas",
  "headline_white": "LINE 1 WHITE WORDS",
  "headline_yellow": "LINE 2 YELLOW PUNCH WORDS",
  "hashtags": ["#podcast", "#viral", "#growth", "#motivation", "#mindset"],
  "explanation": "Why this edit boosts retention and viral distribution."
}}
"""
        resp = self.generate(prompt=prompt, system_prompt="You are an expert short-form video editor that outputs raw JSON.", timeout=6.0)
        if resp:
            try:
                clean = resp.replace("```json", "").replace("```", "").strip()
                data = json.loads(clean)
                if data.get("updated_title"):
                    return {
                        "updated_title": str(data.get("updated_title")).upper().strip(),
                        "updated_hook": str(data.get("updated_hook", curr_hook)).strip(),
                        "suggested_subtitle_style": str(data.get("suggested_subtitle_style", "hormozi")),
                        "suggested_layout": str(data.get("suggested_layout", "fit_canvas")),
                        "headline_white": str(data.get("headline_white", "THE REAL REASON")).upper(),
                        "headline_yellow": str(data.get("headline_yellow", "99% FAIL")).upper(),
                        "hashtags": data.get("hashtags", ["#viral", "#podcast", "#shorts"]),
                        "explanation": str(data.get("explanation", "AI optimized hook and pacing for high retention."))
                    }
            except Exception:
                pass

        # 2. Robust NLP Heuristic Fallback
        ins_lower = instruction.lower()
        new_title = curr_title
        new_hook = curr_hook
        suggested_style = "hormozi"
        suggested_layout = clip_data.get("layout_mode", "fit_canvas")

        if any(w in ins_lower for w in ["mrbeast", "hype", "energy", "fast"]):
            suggested_style = "hype"
        elif any(w in ins_lower for w in ["cyber", "neon", "glow", "tech"]):
            suggested_style = "cyber"
        elif any(w in ins_lower for w in ["clean", "amber", "editorial", "minimal"]):
            suggested_style = "clean"

        if "controversy" in ins_lower or "warning" in ins_lower:
            new_title = f"WHY 99% OF PEOPLE ARE COMPLETELY WRONG ABOUT {curr_title.split(':')[-1].strip()}"
        elif "money" in ins_lower or "wealth" in ins_lower:
            new_title = f"HOW TO BUILD WEALTH AND 10X YOUR INCOME IN 2024"
        elif "punchy" in ins_lower or "hook" in ins_lower:
            new_title = f"THE REAL REASON NOBODY TALKS ABOUT {curr_title.split(':')[-1].strip()}"
        else:
            new_title = f"THE UNTOLD TRUTH ABOUT {curr_title.split(':')[-1].strip()}"

        words = new_title.split()
        half = max(1, len(words) // 2)
        hw = " ".join(words[:half])
        hy = " ".join(words[half:])

        return {
            "updated_title": new_title.upper(),
            "updated_hook": new_hook,
            "suggested_subtitle_style": suggested_style,
            "suggested_layout": suggested_layout,
            "headline_white": hw,
            "headline_yellow": hy,
            "hashtags": ["#podcast", "#mindset", "#success", "#viral", "#tiktoktips"],
            "explanation": f"Applied '{instruction}' optimization: updated headline, two-tone color highlights, and tuned subtitle pacing."
        }

    def generate_social_distribution_kit(self, transcript: str, title: str = "", hook: str = "") -> Dict[str, Any]:
        """
        Generates platform-tailored social copy for TikTok, Instagram Reels, and YouTube Shorts.
        Includes high-CTR captions, search keywords, hashtags, and posting schedule.
        """
        clean_title = (title or "Viral Podcast Insight").strip().title()
        clean_hook = (hook or transcript[:80]).strip()

        # 1. Try Ollama if connected
        prompt = f"""You are a master social media manager distributing viral short-form clips.
Title: {clean_title}
Hook: {clean_hook}
Transcript: {transcript[:800]}

Generate a complete, high-converting social publishing kit for TikTok, Instagram Reels, and YouTube Shorts.
Respond ONLY with a JSON object matching this schema:
{{
  "tiktok": {{
    "caption": "Catchy first 2 lines with curiosity gap...",
    "seo_keywords": ["keyword 1", "keyword 2", "keyword 3"],
    "hashtags": ["#podcast", "#viral", "#foryou"],
    "pinned_comment": "Question to spark comment debates..."
  }},
  "instagram": {{
    "caption": "Punchy hook + bullet points + Call to Action...",
    "carousel_points": ["1. Key insight", "2. What to avoid", "3. Action step"],
    "call_to_action": "Save this reel for later 📌",
    "hashtags": ["#reels", "#growth", "#explorepage"]
  }},
  "youtube_shorts": {{
    "title": "Title with emoji and #Shorts",
    "description": "Engaging description with timestamps...",
    "tags": ["Shorts", "podcast", "advice"]
  }},
  "best_posting_times": ["12:30 PM EST", "6:45 PM EST", "9:15 PM EST"]
}}
"""
        resp = self.generate(prompt=prompt, system_prompt="You are a JSON-only API that outputs social media distribution kits.", timeout=6.0)
        if resp:
            try:
                clean = resp.replace("```json", "").replace("```", "").strip()
                data = json.loads(clean)
                if data.get("tiktok") and data.get("instagram"):
                    return data
            except Exception:
                pass

        # 2. Heuristic fallback
        return {
            "tiktok": {
                "caption": f"Wait until the end... The brutal truth about {clean_title.lower()} nobody wants to admit. 👇",
                "seo_keywords": [clean_title.lower(), "podcast clips", "life advice", "success habits"],
                "hashtags": ["#podcast", "#viral", "#foryou", "#mindset", "#lifelessons"],
                "pinned_comment": "Do you agree with this? Let me know in the comments below! 👇"
            },
            "instagram": {
                "caption": f"\"{clean_hook}\"\n\nMost people get {clean_title.lower()} completely backwards. Here is the shift you need to make:\n\n• Stop relying on motivation alone\n• Build systems that remove friction\n• Protect your focus at all costs\n\nSave this for when you need a reminder 📌",
                "carousel_points": [
                    f"1. The misconception around {clean_title.lower()}",
                    "2. The psychological bottleneck",
                    "3. The proven execution framework"
                ],
                "call_to_action": "Share this with someone who needs to hear it today ↗️",
                "hashtags": ["#reels", "#podcast", "#personaldevelopment", "#discipline", "#explorepage"]
            },
            "youtube_shorts": {
                "title": f"The Untold Truth About {clean_title} 🤯 #Shorts",
                "description": f"\"{clean_hook}\"\n\nSubscribe for daily podcast highlights and transformative insights.\n\n#Shorts #Podcast #SelfImprovement",
                "tags": ["Shorts", "podcast clips", "interview", clean_title.lower(), "motivation"]
            },
            "best_posting_times": ["12:00 PM EST", "5:30 PM EST", "8:15 PM EST"]
        }

    def _heuristic_podcast_summary(self, transcript: str, duration: float) -> Dict[str, Any]:
        """Deterministic offline fallback summary generator."""
        words = transcript.split()
        sample_len = min(len(words), 40)
        intro_sample = " ".join(words[:sample_len]) if words else "Podcast discussion"

        return {
            "source": "built-in",
            "model": "heuristic",
            "overview": (
                f"This conversation explores high-impact insights and actionable strategies. "
                f"The discussion opens with \"{intro_sample}...\" and covers key mental models, "
                f"common misconceptions, and tactical principles for execution."
            ),
            "key_takeaways": [
                "Focus on core leverage points before attempting to scale widely.",
                "Attention and clear communication are the most valuable distribution assets.",
                "Consistency in execution beats sporadic intensity every single time.",
                "Understanding the narrative arc keeps audience engagement at peak retention."
            ],
            "chapters": [
                {
                    "title": "Opening Insight & Core Premise",
                    "start": 0.0,
                    "end": round(min(duration, 45.0), 1),
                    "duration": round(min(duration, 45.0), 1),
                    "summary": "Establishes the problem statement and foundational premise.",
                    "energy": 94
                },
                {
                    "title": "Deep Dive & Strategic Breakdown",
                    "start": round(duration * 0.3, 1),
                    "end": round(min(duration, duration * 0.3 + 50.0), 1),
                    "duration": 50.0,
                    "summary": "Analyzes the primary bottlenecks and structural lessons learned.",
                    "energy": 97
                },
                {
                    "title": "Actionable Takeaways & Conclusion",
                    "start": round(max(0.0, duration - 60.0), 1),
                    "end": round(duration, 1),
                    "duration": 60.0,
                    "summary": "Synthesizes the key actionable takeaways for immediate execution.",
                    "energy": 95
                }
            ],
            "notable_quotes": [
                "Consistency beats intensity every single time.",
                "Focus on the bottleneck before scaling the system."
            ]
        }
