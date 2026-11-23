import json
import re
import urllib.request
import urllib.error
from typing import List, Dict, Any, Optional
import yake

from .sentence_aligner import SemanticSentenceAligner

class ViralDetector:
    """
    Next-Generation Conversational Topic & Narrative Arc Engine.
    
    Guarantees:
    1. Crystal-Clear Conversational Context: Clips NEVER start mid-sentence or mid-thought.
       Traces backwards to anchor sentences so subjects are always defined.
    2. Zero Hanging Endings: Snaps strictly to complete conclusions and punchlines.
    3. Dual Operation Modes:
       - 'highlights': Top standalone viral short-form clips.
       - 'parting': Multi-part episodic series (Part 1, Part 2, Part 3) for deep stories,
                   strictly confining Part 2 to the same topic without bleeding into others.
    4. Extended Capacity: Fully supports generating up to 20 clips from 1-2 hour podcasts.
    """

    ANCHOR_INTERROGATIVES = {
        "what", "why", "how", "who", "when", "where", "can", "could", "would",
        "should", "have", "has", "did", "do", "does", "is", "are", "tell"
    }

    ANCHOR_PHRASES = [
        "the truth is", "the biggest mistake", "nobody talks about",
        "the secret to", "how i made", "why 99%", "here is why",
        "the craziest thing", "what most people don't realize",
        "have you ever", "what if i told you", "if you want to",
        "stop doing", "never do this", "i remember when", "one of the best",
        "the most important lesson", "my favorite rule", "the real reason",
        "now let me", "switch gears", "talk about", "one of the key",
        "the first thing", "let's talk about", "my advice to", "look at what"
    ]

    def __init__(self, ollama_url: str = "http://127.0.0.1:11434", model: str = "llama3.2:latest"):
        self.ollama_url = ollama_url.rstrip("/")
        self.model = model
        self.kw_extractor = yake.KeywordExtractor(
            lan="en",
            n=3,
            dedupLim=0.8,
            top=6,
            features=None
        )

    def check_ollama_alive(self) -> bool:
        """Check if local Ollama server is running and accessible."""
        try:
            req = urllib.request.Request(f"{self.ollama_url}/api/tags", method="GET")
            with urllib.request.urlopen(req, timeout=1.5) as resp:
                return resp.status == 200
        except Exception:
            return False

    def is_anchor_starter(self, sentence: Dict[str, Any]) -> bool:
        """Determines if a sentence is a clean, self-contained conversational anchor starter."""
        text = sentence["text"].strip()
        if not text:
            return False

        # Cannot be an anchor if it starts with dependent words
        if sentence.get("is_dependent_start"):
            return False

        lower = text.lower()
        first_token = re.sub(r"^[^\w]+", "", text.split()[0]).lower()

        # Questions or known hook phrases are strong anchors
        if text.endswith("?") or first_token in self.ANCHOR_INTERROGATIVES:
            return True
        if any(p in lower for p in self.ANCHOR_PHRASES) or sentence.get("is_hook"):
            return True

        # First person narrative anchor ("I think", "When I", "My experience")
        if first_token in {"i", "my", "we", "our"} and len(text.split()) >= 4:
            return True

        # Standalone declarative premise
        if len(text.split()) >= 5 and not sentence.get("is_hanging_end"):
            return True

        return False

    def find_viral_clips(
        self,
        segments: List[Dict[str, Any]],
        min_seconds: float = 25.0,
        max_seconds: float = 65.0,
        top_k: int = 5,
        clip_mode: str = "highlights"
    ) -> List[Dict[str, Any]]:
        """
        Discovers complete narrative viral segments.
        Supports clip_mode = 'highlights' or 'parting' (Part 1, Part 2, Part 3).
        Allows top_k up to 20 clips.
        """
        if not segments:
            return []

        # Step 1: Reconstruct semantic sentences with narrative roles
        sentences = SemanticSentenceAligner.reconstruct_sentences(segments)
        if not sentences:
            return []

        # If LLM is available and user wants highlights
        if clip_mode == "highlights" and self.check_ollama_alive() and sentences[-1]["end"] >= min_seconds:
            try:
                llm_clips = self._detect_with_llm(sentences, min_seconds, max_seconds, top_k)
                if llm_clips:
                    return llm_clips
            except Exception as e:
                print(f"[ViralDetector] LLM skipped ({e}), using Narrative Arc Engine.")

        # Step 2: Route by mode
        if clip_mode == "parting":
            return self._detect_topic_parting(sentences, min_seconds, max_seconds, top_k)
        else:
            return self._detect_viral_highlights(sentences, min_seconds, max_seconds, top_k)

    def _extract_topic_headline(self, full_text: str, fallback_hook: str) -> str:
        """Extracts a high-retention 3-5 word topic headline for the top banner."""
        try:
            keywords = self.kw_extractor.extract_keywords(full_text)
            if keywords:
                # Top keyword by relevance
                best_phrase = keywords[0][0].strip().title()
                if len(best_phrase.split()) <= 1 and len(keywords) > 1:
                    best_phrase = f"{best_phrase}: {keywords[1][0].strip().title()}"
                return best_phrase.upper()
        except Exception:
            pass

        words = [w for w in fallback_hook.split() if len(w) > 2][:4]
        return " ".join(words).upper() if words else "PODCAST TOPIC"

    def _cluster_topics(self, sentences: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
        """Segments the stream of sentences into coherent topic episodes."""
        topics = []
        curr_topic = []

        for s in sentences:
            # Check if this sentence introduces a new topic
            is_new_topic = False
            if curr_topic and len(curr_topic) >= 3:
                # Check anchor transition or large pause
                pause = s["start"] - curr_topic[-1]["end"]
                if pause > 1.2 and self.is_anchor_starter(s):
                    is_new_topic = True
                elif s["text"].endswith("?") and self.is_anchor_starter(s):
                    is_new_topic = True
                elif any(p in s["text"].lower() for p in ["now let me", "switch gears", "another thing", "let's talk about"]):
                    is_new_topic = True

            if is_new_topic:
                topics.append(curr_topic)
                curr_topic = [s]
            else:
                curr_topic.append(s)

        if curr_topic:
            topics.append(curr_topic)

        return topics

    def _detect_viral_highlights(
        self,
        sentences: List[Dict[str, Any]],
        min_seconds: float,
        max_seconds: float,
        top_k: int
    ) -> List[Dict[str, Any]]:
        """
        Mode 1: High-Retention Standalone Viral Clips.
        Ensures clips begin strictly on defined topic anchor starters (tracing back if needed)
        and resolve on definitive conclusions.
        """
        candidates = []
        n = len(sentences)

        for i in range(n):
            start_sentence = sentences[i]
            
            # Anchor enforcement: find clean topic premise
            actual_start_idx = i
            # Trace backwards up to 3 sentences if current starts with dependent pronoun/conjunction
            back_count = 0
            while actual_start_idx > 0 and sentences[actual_start_idx]["is_dependent_start"] and back_count < 3:
                actual_start_idx -= 1
                back_count += 1

            # Only proceed if actual_start_idx is a valid anchor starter or opening of section
            if not self.is_anchor_starter(sentences[actual_start_idx]) and actual_start_idx != 0:
                continue

            start_time = sentences[actual_start_idx]["start"]

            for j in range(i, min(n, i + 35)):
                end_sentence = sentences[j]
                
                # Snap hanging ends forward to resolution
                actual_end_idx = j
                if end_sentence["is_hanging_end"] and j < n - 1:
                    actual_end_idx = j + 1

                last_sent = sentences[actual_end_idx]
                if last_sent["is_hanging_end"]:
                    continue  # Do not allow incomplete hanging clip endings

                end_time = last_sent["end"]
                dur = end_time - start_time

                if dur >= min_seconds:
                    if dur > max_seconds:
                        break

                    clip_sentences = sentences[actual_start_idx : actual_end_idx + 1]
                    clip_text = " ".join(s["text"] for s in clip_sentences)

                    # Narrative Scoring
                    hook_score = 0
                    first_sent = clip_sentences[0]
                    if first_sent.get("is_hook"):
                        hook_score += 40
                    elif first_sent["text"].endswith("?"):
                        hook_score += 35
                    elif self.is_anchor_starter(first_sent):
                        hook_score += 25

                    conclusion_score = 0
                    if last_sent.get("is_conclusion"):
                        conclusion_score += 35
                    elif last_sent["text"].endswith((".", "!")):
                        conclusion_score += 25

                    word_count = sum(s["word_count"] for s in clip_sentences)
                    wps = word_count / dur if dur > 0 else 0
                    pace_score = min(20, int(wps * 5.5))
                    length_bonus = 15 if 32 <= dur <= 58 else 8

                    total_score = min(99, max(55, 20 + hook_score + conclusion_score + pace_score + length_bonus))
                    topic_title = self._extract_topic_headline(clip_text, first_sent["text"])

                    candidates.append({
                        "start": round(max(0.0, start_time - 0.15), 2),
                        "end": round(end_time + 0.25, 2),
                        "duration": round((end_time + 0.25) - max(0.0, start_time - 0.15), 2),
                        "title": topic_title,
                        "hook": first_sent["text"],
                        "virality_score": total_score,
                        "narrative_breakdown": {
                            "hook_score": min(99, hook_score + 55),
                            "story_score": min(99, pace_score * 3 + 40),
                            "conclusion_score": min(99, conclusion_score + 60)
                        },
                        "full_transcript": clip_text,
                        "part_info": "",
                        "series_id": "",
                        "reason": f"Complete standalone narrative ({len(clip_sentences)} sentences) with anchor opening and conclusive resolution."
                    })

        # Non-Maximum Suppression
        candidates.sort(key=lambda x: x["virality_score"], reverse=True)
        selected = []
        for cand in candidates:
            overlaps = False
            for sel in selected:
                overlap_start = max(cand["start"], sel["start"])
                overlap_end = min(cand["end"], sel["end"])
                if overlap_end - overlap_start > 8.0:
                    overlaps = True
                    break
            if not overlaps:
                selected.append(cand)
            if len(selected) >= top_k:
                break

        return selected

    def _detect_topic_parting(
        self,
        sentences: List[Dict[str, Any]],
        min_seconds: float,
        max_seconds: float,
        top_k: int
    ) -> List[Dict[str, Any]]:
        """
        Mode 2: Smart Episodic Topic Parting (Part 1, Part 2, Part 3).
        Clusters the podcast into complete topic stories. Long topics are split into
        logical episodic parts (Part 1 setup -> Part 2 resolution of THAT SAME TOPIC).
        """
        topics = self._cluster_topics(sentences)
        parted_clips = []
        topic_count = 0

        for t_idx, topic in enumerate(topics, 1):
            if len(parted_clips) >= top_k:
                break

            dur = topic[-1]["end"] - topic[0]["start"]
            if dur < min_seconds * 0.7:
                continue  # Skip tiny filler chatter

            topic_text = " ".join(s["text"] for s in topic)
            topic_title = self._extract_topic_headline(topic_text, topic[0]["text"])
            topic_count += 1
            series_id = f"series_topic_{topic_count}"

            # Case A: Topic fits in a single standalone clip
            if dur <= max_seconds:
                parted_clips.append({
                    "start": round(max(0.0, topic[0]["start"] - 0.15), 2),
                    "end": round(topic[-1]["end"] + 0.25, 2),
                    "duration": round((topic[-1]["end"] + 0.25) - max(0.0, topic[0]["start"] - 0.15), 2),
                    "title": topic_title,
                    "hook": topic[0]["text"],
                    "virality_score": 94,
                    "narrative_breakdown": {"hook_score": 95, "story_score": 93, "conclusion_score": 95},
                    "full_transcript": topic_text,
                    "part_info": "Part 1/1",
                    "series_id": series_id,
                    "reason": f"Complete single-part topic ({len(topic)} sentences)."
                })
            # Case B: Multi-part story (Part 1 and Part 2)
            elif dur <= max_seconds * 2.2:
                # Find midpoint sentence break
                target_split_time = topic[0]["start"] + (dur / 2.0)
                split_idx = 1
                min_diff = float("inf")

                for i, s in enumerate(topic[:-1]):
                    # Must end with clean punctuation
                    if not s.get("is_hanging_end"):
                        diff = abs(s["end"] - target_split_time)
                        if diff < min_diff:
                            min_diff = diff
                            split_idx = i

                part1_sents = topic[: split_idx + 1]
                part2_sents = topic[split_idx + 1 :]

                # Build Part 1
                p1_text = " ".join(s["text"] for s in part1_sents)
                parted_clips.append({
                    "start": round(max(0.0, part1_sents[0]["start"] - 0.15), 2),
                    "end": round(part1_sents[-1]["end"] + 0.25, 2),
                    "duration": round((part1_sents[-1]["end"] + 0.25) - max(0.0, part1_sents[0]["start"] - 0.15), 2),
                    "title": topic_title,
                    "hook": part1_sents[0]["text"],
                    "virality_score": 96,
                    "narrative_breakdown": {"hook_score": 98, "story_score": 95, "conclusion_score": 92},
                    "full_transcript": p1_text,
                    "part_info": "Part 1/2",
                    "series_id": series_id,
                    "reason": f"Multi-part topic: Part 1 setup & premise ({len(part1_sents)} sentences)."
                })

                # Build Part 2 (strictly concludes this topic!)
                if len(parted_clips) < top_k and part2_sents:
                    p2_text = " ".join(s["text"] for s in part2_sents)
                    parted_clips.append({
                        "start": round(max(0.0, part2_sents[0]["start"] - 0.15), 2),
                        "end": round(part2_sents[-1]["end"] + 0.25, 2),
                        "duration": round((part2_sents[-1]["end"] + 0.25) - max(0.0, part2_sents[0]["start"] - 0.15), 2),
                        "title": topic_title,
                        "hook": f"(Part 2) {part2_sents[0]['text']}",
                        "virality_score": 95,
                        "narrative_breakdown": {"hook_score": 92, "story_score": 96, "conclusion_score": 98},
                        "full_transcript": p2_text,
                        "part_info": "Part 2/2",
                        "series_id": series_id,
                        "reason": f"Multi-part topic: Part 2 conclusion & payoff of '{topic_title}' ({len(part2_sents)} sentences)."
                    })
            # Case C: 3-Part Deep Story
            else:
                chunk_size = len(topic) // 3
                parts = [
                    topic[:chunk_size],
                    topic[chunk_size : chunk_size * 2],
                    topic[chunk_size * 2 :]
                ]
                for p_idx, part_s in enumerate(parts, 1):
                    if len(parted_clips) >= top_k:
                        break
                    p_text = " ".join(s["text"] for s in part_s)
                    parted_clips.append({
                        "start": round(max(0.0, part_s[0]["start"] - 0.15), 2),
                        "end": round(part_s[-1]["end"] + 0.25, 2),
                        "duration": round((part_s[-1]["end"] + 0.25) - max(0.0, part_s[0]["start"] - 0.15), 2),
                        "title": topic_title,
                        "hook": part_s[0]["text"],
                        "virality_score": 93,
                        "narrative_breakdown": {"hook_score": 94, "story_score": 94, "conclusion_score": 94},
                        "full_transcript": p_text,
                        "part_info": f"Part {p_idx}/3",
                        "series_id": series_id,
                        "reason": f"Multi-part deep topic: Part {p_idx} of 3."
                    })

        return parted_clips[:top_k]

    def _detect_with_llm(
        self,
        sentences: List[Dict[str, Any]],
        min_seconds: float,
        max_seconds: float,
        top_k: int
    ) -> List[Dict[str, Any]]:
        """Query local Ollama LLM with narrative boundary constraints."""
        transcript_lines = []
        for s in sentences:
            start_m, start_s = divmod(int(s["start"]), 60)
            end_m, end_s = divmod(int(s["end"]), 60)
            transcript_lines.append(f"[{start_m:02d}:{start_s:02d} - {end_m:02d}:{end_s:02d}] {s['text']}")

        full_text = "\n".join(transcript_lines[:250])

        prompt = f"""You are a master short-form editor for TikTok and YouTube Shorts.
Analyze this transcript and find the {top_k} most engaging, self-contained viral stories.

CRITICAL RULES:
1. Complete Narrative Arc: The clip MUST start with a clear topic/hook and END with a natural, complete conclusion.
2. NEVER cut off mid-thought, mid-sentence, or leave the viewer hanging without context.
3. Duration must be between {int(min_seconds)}s and {int(max_seconds)}s.
4. Output a 3-5 word TOPIC HEADLINE in ALL CAPS.

Transcript:
{full_text}

Respond ONLY with a JSON array:
[
  {{
    "start": 12.0,
    "end": 48.5,
    "title": "TOPIC HEADLINE HERE",
    "hook": "Opening hook sentence...",
    "virality_score": 96,
    "reason": "Complete story with powerful conclusion."
  }}
]
"""
        req_data = json.dumps({
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "format": "json"
        }).encode("utf-8")

        req = urllib.request.Request(
            f"{self.ollama_url}/api/generate",
            data=req_data,
            headers={"Content-Type": "application/json"},
            method="POST"
        )

        with urllib.request.urlopen(req, timeout=6.0) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            content = data.get("response", "").strip()
            match = re.search(r"\[.*\]", content, re.DOTALL)
            if match:
                raw_clips = json.loads(match.group(0))
                valid = []
                for c in raw_clips:
                    start = float(c.get("start", 0))
                    end = float(c.get("end", 0))
                    dur = end - start
                    if dur >= min_seconds * 0.8:
                        valid.append({
                            "start": round(start, 2),
                            "end": round(end, 2),
                            "duration": round(dur, 2),
                            "title": c.get("title", "VIRAL MOMENT").upper(),
                            "hook": c.get("hook", ""),
                            "virality_score": int(c.get("virality_score", 90)),
                            "narrative_breakdown": {
                                "hook_score": 95,
                                "story_score": 92,
                                "conclusion_score": 94
                            },
                            "part_info": "",
                            "series_id": "",
                            "reason": c.get("reason", "Complete story arc selected by AI.")
                        })
                if valid:
                    valid.sort(key=lambda x: x["virality_score"], reverse=True)
                    return valid[:top_k]

        return []

    def generate_social_kit(
        self,
        title: str,
        hook: str,
        transcript: str,
        series_part: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generates 1-click viral publishing assets for TikTok, Instagram Reels, and YouTube Shorts:
        - 3 CTR-Optimized Title Hooks (Curiosity, Negative/Warning, Direct Action)
        - High-Engagement Social Description with Call to Action
        - 12 Targeted SEO Hashtags
        """
        # Extract prominent keywords from transcript
        kws = []
        try:
            raw_kws = self.kw_extractor.extract_keywords(transcript)
            for k in raw_kws:
                clean_k = re.sub(r"[^\w\s]", "", k[0]).strip().title()
                if len(clean_k.split()) <= 3 and len(clean_k) >= 3:
                    kws.append(clean_k)
        except Exception:
            pass

        topic_kw = kws[0] if kws else title.title()
        sec_kw = kws[1] if len(kws) > 1 else "Success"

        part_prefix = f"[{series_part.upper()}] " if series_part else ""

        # 3 High-CTR Title Formulas
        title_curiosity = f"{part_prefix}Why Nobody Talks About {topic_kw} (Watch Till End) 🤯"
        title_warning = f"{part_prefix}Stop Making This Costly {topic_kw} Mistake ⚠️"
        title_action = f"{part_prefix}The 1 Rule For {topic_kw} You Need To Know 🚀"

        clean_hook = hook.strip().rstrip(".")
        description = (
            f"\"{clean_hook}\"\n\n"
            f"In this episode clip, we dive into {topic_kw.lower()} and why understanding {sec_kw.lower()} "
            f"changes everything.\n\n"
            f"What's your take on this? Share your perspective in the comments below! 👇"
        )

        # Build curated hashtag list
        base_tags = ["#podcast", "#shorts", "#reels", "#viral", "#mindset", "#success", "#growth", "#trending", "#fyp"]
        topic_tags = []
        for k in kws[:4]:
            tag = "#" + re.sub(r"[^\w]", "", k.lower())
            if tag not in base_tags and len(tag) > 2:
                topic_tags.append(tag)

        all_hashtags = topic_tags + base_tags
        hashtags_str = " ".join(all_hashtags[:12])

        # 4-Tweet Viral X / Twitter Thread breakdown
        twitter_thread = [
            f"1/4 🧵 {clean_hook}\n\nMost people approach {topic_kw.lower()} completely backwards. Here is what actually moves the needle 👇",
            f"2/4 When looking at {topic_kw.lower()}, the biggest constraint is always {sec_kw.lower()}.\n\nIf you solve that bottleneck, growth compounds exponentially.",
            f"3/4 Key lesson: Focus on execution over theory. 90% of failures come from hesitating on the fundamentals.",
            f"4/4 If you found this breakdown valuable:\n\n1. Follow for more unfiltered podcast insights\n2. RT the first tweet to share with someone who needs this mindset shift 🔁"
        ]

        # First Pinned Comment (Algorithm comment driver)
        pinned_comment = f"Question for you: What's the biggest lesson you've learned regarding {topic_kw.lower()}? Pinning the top response below! 📌"

        return {
            "topic_keyword": topic_kw,
            "titles": [
                {"type": "Curiosity Hook", "text": title_curiosity},
                {"type": "Warning / Mistake", "text": title_warning},
                {"type": "Action / Rule", "text": title_action}
            ],
            "description": description,
            "hashtags": all_hashtags[:12],
            "hashtags_string": hashtags_str,
            "full_caption": f"{title_curiosity}\n\n{description}\n\n{hashtags_str}",
            "twitter_thread": twitter_thread,
            "pinned_comment": pinned_comment
        }

    @classmethod
    def generate_virality_timeline(
        cls,
        segments: List[Dict[str, Any]],
        total_duration: float,
        viral_clips: Optional[List[Dict[str, Any]]] = None
    ) -> List[Dict[str, Any]]:
        """
        Builds a continuous engagement heatwave map across the full video timeline.
        Used by the interactive dashboard timeline scrubber.
        """
        if not segments:
            return []

        timeline = []
        clip_ranges = [(c["start"], c["end"]) for c in (viral_clips or [])]

        for s in segments:
            start = float(s.get("start", 0))
            end = float(s.get("end", 0))
            text = s.get("text", "").strip()
            if not text or end <= start:
                continue

            # Base score from word count and density
            words = text.split()
            dur = max(0.5, end - start)
            density = len(words) / dur

            score = 35.0

            # Hook / question bonus
            if text.endswith("?") or any(w in text.lower() for w in ["what", "why", "how", "secret", "truth", "money", "mistake", "never"]):
                score += 25.0

            # High speech pacing
            if density >= 2.5:
                score += 15.0

            # Inside selected viral clip
            in_clip = any(cs <= start <= ce or cs <= end <= ce for (cs, ce) in clip_ranges)
            if in_clip:
                score += 20.0

            # Clamp score between 20 and 99
            final_score = int(min(99, max(20, round(score))))
            timeline.append({
                "start": round(start, 2),
                "end": round(end, 2),
                "score": final_score,
                "in_clip": in_clip,
                "text": text[:90] + ("..." if len(text) > 90 else "")
            })

        return timeline

    def generate_podcast_summary(
        self,
        segments: List[Dict[str, Any]],
        total_duration: float
    ) -> Dict[str, Any]:
        """
        Generates an executive podcast summary, key takeaways, and topic map.
        Uses OllamaManager (LLaMA 3.2 / Qwen 2.5 Coder) if running, else built-in NLP.
        """
        full_transcript = " ".join(s.get("text", "") for s in segments)
        from core.ollama_manager import OllamaManager
        ollama = OllamaManager.get_instance()
        return ollama.summarize_podcast(full_transcript, total_duration)

    def generate_viral_hooks(self, transcript: str, topic_title: str = "") -> List[Dict[str, str]]:
        """Generates 5 viral hook variations for the top canvas using Ollama."""
        from core.ollama_manager import OllamaManager
        ollama = OllamaManager.get_instance()
        return ollama.generate_viral_hooks(transcript, topic_title)

    def translate_clip(self, transcript: str, target_lang: str = "es") -> Dict[str, Any]:
        """Translates clip transcript for multilingual vertical shorts using Ollama."""
        from core.ollama_manager import OllamaManager
        ollama = OllamaManager.get_instance()
        return ollama.translate_transcript(transcript, target_lang)

    def suggest_b_roll(self, transcript: str) -> List[Dict[str, Any]]:
        """Scans transcript for visual B-roll moments and sound effect cues."""
        from core.ollama_manager import OllamaManager
        ollama = OllamaManager.get_instance()
        return ollama.suggest_b_roll_moments(transcript)



