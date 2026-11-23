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
            "llama3.2:latest", "llama3.2", "llama3.2:3b", "llama3.2:1b",
            "qwen2.5-coder:3b", "qwen2.5-coder:7b", "deepseek-coder:6.7b", "qwen-coder-pro:latest"
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
        """Selects the best available model, preferring LLaMA 3.2 or Qwen 2.5 Coder."""
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
            timeout=25.0
        )

        if llm_resp:
            try:
                # Clean any markdown code fences if present
                clean = llm_resp.replace("```json", "").replace("```", "").strip()
                parsed = json.loads(clean)
                if "overview" in parsed and "key_takeaways" in parsed:
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
            f"Respond with ONLY a valid JSON array of 5 objects matching this schema:\n"
            f"[\n"
            f'  {{"type": "Curiosity Gap", "hook": "Headline text here (max 8 words) 🤯", "style": "curiosity"}},\n'
            f'  {{"type": "Controversial / Warning", "hook": "Headline text here (max 8 words) ⚠️", "style": "warning"}},\n'
            f'  {{"type": "Direct Question", "hook": "Headline text here (max 8 words) ❓", "style": "question"}},\n'
            f'  {{"type": "Bold Claim", "hook": "Headline text here (max 8 words) 💰", "style": "bold"}},\n'
            f'  {{"type": "Actionable Insight", "hook": "Headline text here (max 8 words) 🚀", "style": "action"}}\n'
            f"]"
        )

        resp = self.generate(prompt=prompt, system_prompt="You are a JSON-only API that writes viral short-form hooks.", timeout=15.0)
        if resp:
            try:
                clean = resp.replace("```json", "").replace("```", "").strip()
                parsed = json.loads(clean)
                if isinstance(parsed, list) and len(parsed) >= 3:
                    return parsed[:5]
            except Exception:
                pass

        # Heuristic fallback based on keywords and topic
        clean_title = (topic_title or "THIS MOMENT").strip().title()
        return [
            {"type": "Curiosity Gap", "hook": f"The 1 Truth About {clean_title} Nobody Tells You 🤯", "style": "curiosity"},
            {"type": "Controversial / Warning", "hook": f"Stop Making This Costly {clean_title} Mistake ⚠️", "style": "warning"},
            {"type": "Direct Question", "hook": f"Why Is Everyone Getting {clean_title} Wrong? ❓", "style": "question"},
            {"type": "Bold Claim", "hook": f"This Simple Shift Changes {clean_title} Forever 💰", "style": "bold"},
            {"type": "Actionable Insight", "hook": f"How To Master {clean_title} In 30 Seconds 🚀", "style": "action"}
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
            ({"money", "wealth", "cash", "million", "dollar", "profit"}, "B-ROLL: Cash Stacks & Growth Chart", "SFX: Cash Register Ding 💰"),
            ({"secret", "mistake", "wrong", "danger", "warning", "fail"}, "B-ROLL: Dramatic Warning Flash", "SFX: Deep Bass Drop / Record Scratch ⚠️"),
            ({"growth", "scale", "launch", "fast", "huge", "win"}, "B-ROLL: Rocket Launch / High Speed Timelapse", "SFX: Whoosh / Sonic Boom 🚀"),
            ({"think", "brain", "idea", "realize", "smart", "psychology"}, "B-ROLL: Neural Synapse Animation", "SFX: Lightbulb Ping 💡"),
            ({"stop", "never", "ruin", "crisis", "worst"}, "B-ROLL: Stop Sign / Red Screen Flash", "SFX: Error Buzzer 🛑")
        ]

        for word_set, b_roll, sfx in cues:
            matched = [w for w in word_set if w in lower]
            if matched:
                suggestions.append({
                    "trigger_words": matched,
                    "b_roll_suggestion": b_roll,
                    "sfx_cue": sfx
                })

        return suggestions[:4]

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
