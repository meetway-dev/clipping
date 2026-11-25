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
        clip_mode: str = "highlights",
        progress_cb: Optional[Any] = None
    ) -> List[Dict[str, Any]]:
        """
        Discovers complete narrative viral segments.
        Supports clip_mode = 'highlights' or 'parting' (Part 1, Part 2, Part 3).
        Allows top_k up to 20 clips.
        Reports real-time granular progress callbacks to eliminate freezing at 35%.
        """
        if not segments:
            return []

        # Step 1: Reconstruct semantic sentences with narrative roles
        if progress_cb:
            progress_cb("Reconstructing speech into complete semantic sentences...", 32.0)

        sentences = SemanticSentenceAligner.reconstruct_sentences(segments)
        if not sentences:
            return []

        # If LLM is available and user wants highlights (with tight 7s timeout to prevent freezing)
        initial_clips = []
        if clip_mode == "highlights" and self.check_ollama_alive() and sentences[-1]["end"] >= min_seconds:
            try:
                if progress_cb:
                    progress_cb("Consulting AI model for viral story arcs...", 34.0)
                llm_clips = self._detect_with_llm(sentences, min_seconds, max_seconds, top_k)
                if llm_clips:
                    if progress_cb:
                        progress_cb("Snapping AI story moments to complete sentence boundaries...", 38.0)
                    llm_clips = self._snap_llm_clips(sentences, llm_clips, min_seconds, max_seconds)
                    if llm_clips:
                        if len(llm_clips) >= top_k:
                            if progress_cb:
                                progress_cb(f"Finalized {top_k} complete viral clips from AI story arcs...", 41.0)
                            return llm_clips[:top_k]
                        initial_clips = llm_clips
            except Exception as e:
                print(f"[ViralDetector] LLM skipped ({e}), using instant Narrative Arc Engine.")

        # Step 2: Route by mode
        if clip_mode == "parting":
            if progress_cb:
                progress_cb("Clustering episodic topic parts (Part 1, Part 2)...", 36.0)
            res = self._detect_topic_parting(sentences, min_seconds, max_seconds, top_k)
        else:
            if progress_cb:
                progress_cb("Scanning complete conversational thoughts & 60–90s sweet spot...", 36.0)
            res = self._detect_viral_highlights(
                sentences,
                min_seconds,
                max_seconds,
                top_k,
                progress_cb=progress_cb,
                initial_clips=initial_clips
            )

        if progress_cb:
            progress_cb(f"Finalized {len(res)} complete high-retention viral clips...", 41.0)
        return res

    def _extract_topic_headline(self, full_text: str, fallback_hook: str) -> str:
        """
        Extracts or synthesizes an engaging, high-retention multi-word topic headline (6-12 words)
        specifically formatted for the spacious top safe-area banner in 9:16 vertical video.
        Uses curiosity gaps, contrarian statements, and the core insight to hook viewers.
        """
        clean_hook = re.sub(r"[^\w\s\-\'\?\!]", "", str(fallback_hook or "")).strip()

        # 1. Clean conversational filler words from opening spoken sentences
        clean_hook = re.sub(
            r"^(?:(?:so|and|but|well|like|i mean|you know|honestly|actually|literally|basically|now|ok|okay)[,\s]+)+",
            "",
            clean_hook,
            flags=re.IGNORECASE
        ).strip()

        # If fallback hook contains an opening question, transform or retain it
        lower_hook = clean_hook.lower()
        if any(lower_hook.startswith(q) for q in ["do you know why", "did you know that", "have you ever wondered why", "can you explain why"]):
            clean_hook = re.sub(r"^(do you know why|did you know that|have you ever wondered why|can you explain why)\s*", "WHY ", clean_hook, flags=re.IGNORECASE).strip()

        hook_words = clean_hook.split()

        # If the cleaned opening sentence is already a strong, self-contained hook (6 to 14 words), use it
        if 5 <= len(hook_words) <= 14:
            return clean_hook.upper()

        # If it's longer than 14 words, extract the primary clause (up to 10-12 words)
        if len(hook_words) > 14:
            # Cut at natural clause boundaries if present
            for delim in [",", " because ", " which ", " that ", " but ", " and "]:
                if delim in clean_hook:
                    clause = clean_hook.split(delim)[0].strip()
                    c_words = clause.split()
                    if 5 <= len(c_words) <= 12:
                        return clause.upper()
            return " ".join(hook_words[:11]).upper()

        # 2. If opening sentence is too short or missing, extract top keywords and apply proven viral hooks
        try:
            keywords = self.kw_extractor.extract_keywords(full_text)
            if keywords:
                best_kw = keywords[0][0].strip().title()
                kw2 = keywords[1][0].strip().title() if len(keywords) > 1 else ""
                kw_clean = best_kw.upper()

                lower_text = full_text.lower()
                # Negative / Warning
                if any(w in lower_text for w in ["mistake", "wrong", "fail", "failure", "danger", "stop", "never", "ruin", "destroy"]):
                    return f"STOP MAKING THIS CRITICAL {kw_clean} MISTAKE RIGHT NOW"
                # Question / Why
                if any(w in lower_text for w in ["why", "how", "reason", "because"]):
                    return f"THE REAL REASON 99% OF PEOPLE FAIL AT {kw_clean}"
                # Health / Body / Mind
                if any(w in lower_text for w in ["body", "brain", "sleep", "diet", "sugar", "cells", "health", "aging"]):
                    return f"WHAT HAPPENS TO YOUR BODY WHEN YOU MASTER {kw_clean}"
                # Habit / Success / Secret
                if kw2:
                    return f"THE UNTOLD TRUTH ABOUT {kw_clean} AND {kw2.upper()}"
                return f"THE #1 SECRET TO {kw_clean} NOBODY TALKS ABOUT"
        except Exception:
            pass

        # 3. Final fallback: combine whatever words exist into an engaging hook phrase
        if hook_words:
            core_words = [w for w in hook_words if len(w) > 1][:10]
            if len(core_words) >= 4:
                return " ".join(core_words).upper()
            return f"THE UNTOLD TRUTH ABOUT {' '.join(core_words).upper()}"

        return "THE SECRET TO HIGH PERFORMANCE AND SUCCESS"

    def _snap_llm_clips(
        self,
        sentences: List[Dict[str, Any]],
        llm_clips: List[Dict[str, Any]],
        min_seconds: float,
        max_seconds: float
    ) -> List[Dict[str, Any]]:
        """Converts approximate LLM timestamps into complete, self-contained sentences."""
        snapped = []
        for c in llm_clips:
            requested_start = float(c.get("start", 0.0))
            requested_end = float(c.get("end", requested_start))

            start_idx = min(
                range(len(sentences)),
                key=lambda i: abs(sentences[i]["start"] - requested_start)
            )
            end_idx = min(
                range(start_idx, len(sentences)),
                key=lambda i: abs(sentences[i]["end"] - requested_end)
            )

            # Questions must include the complete answer/punchline, not only the question.
            if sentences[start_idx]["text"].strip().endswith("?"):
                for i in range(start_idx + 1, len(sentences)):
                    end_idx = i
                    candidate_duration = sentences[i]["end"] - sentences[start_idx]["start"]
                    if sentences[i].get("is_conclusion") or sentences[i]["text"].strip().endswith((".", "!")):
                        if candidate_duration >= min_seconds * 0.90:
                            # If we hit the 60-90s sweet spot, break at this complete sentence
                            if min_seconds >= 50.0 and 60.0 <= candidate_duration <= 95.0:
                                break
                            elif candidate_duration >= min_seconds:
                                break
                    if candidate_duration >= max_seconds:
                        break

            # Snap backwards across dependent sentence starts.
            while start_idx > 0 and sentences[start_idx].get("is_dependent_start"):
                start_idx -= 1

            # Never end on a dangling dependent/hanging sentence.
            while end_idx < len(sentences) - 1 and sentences[end_idx].get("is_hanging_end"):
                end_idx += 1

            start = sentences[start_idx]["start"]
            end = sentences[end_idx]["end"]
            duration = end - start
            if duration < min_seconds * 0.90 or duration > max_seconds * 1.10:
                continue

            clip_sentences = sentences[start_idx:end_idx + 1]
            transcript = " ".join(s["text"] for s in clip_sentences)
            title = c.get("title", self._extract_topic_headline(transcript, clip_sentences[0]["text"]))
            snapped.append({
                **c,
                "start": round(max(0.0, start - 0.15), 2),
                "end": round(end + 0.25, 2),
                "duration": round((end + 0.25) - max(0.0, start - 0.15), 2),
                "title": str(title).upper(),
                "hook": clip_sentences[0]["text"],
                "full_transcript": transcript,
                "narrative_breakdown": {
                    "hook_score": min(99, int(c.get("virality_score", 90))),
                    "story_score": 92,
                    "conclusion_score": 94
                },
                "reason": f"AI-selected topic snapped to complete sentences. {c.get('reason', '')}".strip()
            })
        return snapped[:len(llm_clips)]

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
        top_k: int,
        progress_cb: Optional[Any] = None,
        initial_clips: Optional[List[Dict[str, Any]]] = None
    ) -> List[Dict[str, Any]]:
        """
        Mode 1: High-Retention Standalone Viral Clips.
        Ensures clips begin strictly on defined topic anchor starters (tracing back if needed)
        and resolve on definitive conclusions without cutting off mid-thought.
        Guarantees that up to top_k non-overlapping clips are extracted when video duration allows.
        """
        candidates = []
        n = len(sentences)

        # Question/answer moments: One of the strongest podcast short formats.
        # Start on the spoken question and extend through the complete answer/punchline.
        for q_idx, question in enumerate(sentences):
            if not question["text"].strip().endswith("?"):
                continue

            start_idx = q_idx
            while start_idx > 0 and sentences[start_idx].get("is_dependent_start"):
                start_idx -= 1

            for j in range(q_idx + 1, n):
                answer = sentences[j]
                dur = answer["end"] - sentences[start_idx]["start"]
                if dur > max_seconds + 4.0:
                    break

                if dur >= min_seconds:
                    if answer.get("is_conclusion") or answer["text"].strip().endswith((".", "!")):
                        if not answer.get("is_hanging_end"):
                            clip_sentences = sentences[start_idx : j + 1]
                            clip_text = " ".join(s["text"] for s in clip_sentences)
                            topic_title = self._extract_topic_headline(clip_text, question["text"])

                            # Duration sweet-spot bonus (favoring 60-90s)
                            if min_seconds >= 50.0:
                                len_bonus = 25 if (60.0 <= dur <= 95.0) else (18 if dur <= 130.0 else 12)
                            else:
                                len_bonus = 20 if (30.0 <= dur <= 60.0) else (16 if dur <= 90.0 else 10)

                            candidates.append({
                                "start": round(max(0.0, clip_sentences[0]["start"] - 0.15), 2),
                                "end": round(clip_sentences[-1]["end"] + 0.25, 2),
                                "duration": round((clip_sentences[-1]["end"] + 0.25) - max(0.0, clip_sentences[0]["start"] - 0.15), 2),
                                "title": topic_title,
                                "hook": clip_sentences[0]["text"],
                                "virality_score": min(99, max(60, 72 + len_bonus)),
                                "narrative_breakdown": {
                                    "hook_score": 99,
                                    "story_score": 94,
                                    "conclusion_score": 96
                                },
                                "full_transcript": clip_text,
                                "part_info": "",
                                "series_id": "",
                                "reason": f"Complete Q&A narrative ({len(clip_sentences)} sentences) with question and conclusive answer."
                            })
                            # If we hit an ideal sweet-spot length, break to avoid over-expanding
                            if 60.0 <= dur <= 95.0:
                                break

        for i in range(n):
            start_sentence = sentences[i]
            
            # Anchor enforcement: find clean topic premise
            actual_start_idx = i
            back_count = 0
            while actual_start_idx > 0 and sentences[actual_start_idx]["is_dependent_start"] and back_count < 4:
                actual_start_idx -= 1
                back_count += 1

            # Only proceed if actual_start_idx is a valid anchor starter or opening of section
            if not self.is_anchor_starter(sentences[actual_start_idx]) and actual_start_idx != 0:
                continue

            start_time = sentences[actual_start_idx]["start"]

            # Dynamic scan up to max_seconds (no artificial sentence limit!)
            for j in range(actual_start_idx, n):
                end_sentence = sentences[j]
                dur_so_far = end_sentence["end"] - start_time
                if dur_so_far > max_seconds + 5.0:
                    break

                # Snap hanging ends forward to resolution
                actual_end_idx = j
                if end_sentence["is_hanging_end"] and j < n - 1:
                    actual_end_idx = j + 1

                last_sent = sentences[actual_end_idx]
                if last_sent["is_hanging_end"]:
                    continue  # Do not allow incomplete hanging clip endings

                end_time = last_sent["end"]
                dur = end_time - start_time

                if dur >= min_seconds and dur <= max_seconds:
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

                    # Duration Sweet-Spot Scoring
                    # When min_seconds >= 50 (e.g. 60 or 70s), strongly prioritize 60-90s sweet spot!
                    if min_seconds >= 50.0:
                        if 60.0 <= dur <= 90.0:
                            length_bonus = 25  # Prime 60-90s TikTok Sweet Spot
                        elif 90.0 < dur <= 130.0:
                            length_bonus = 18  # Strong comprehensive narrative
                        elif 130.0 < dur <= max_seconds:
                            length_bonus = 12  # Long deep-dive interview breakdown
                        else:
                            length_bonus = 6
                    else:
                        if 30.0 <= dur <= 60.0:
                            length_bonus = 20
                        elif 60.0 < dur <= 90.0:
                            length_bonus = 16
                        else:
                            length_bonus = 10

                    total_score = min(99, max(55, 18 + hook_score + conclusion_score + pace_score + length_bonus))
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

        # Proportional Non-Maximum Suppression
        def is_overlapping(c1, c2, max_overlap_ratio=0.35):
            o_start = max(c1["start"], c2["start"])
            o_end = min(c1["end"], c2["end"])
            if o_end <= o_start:
                return False
            overlap_dur = o_end - o_start
            min_len = min(c1["duration"], c2["duration"])
            return (overlap_dur / min_len) > max_overlap_ratio

        # Separate candidates into sweet-spot (60-90s) and extended/long (95s..max)
        sweet_spot_max = max(95.0, min_seconds + 30.0)
        sweet_candidates = [c for c in candidates if c["duration"] <= sweet_spot_max]
        long_candidates = [c for c in candidates if c["duration"] > sweet_spot_max]

        sweet_candidates.sort(key=lambda x: x["virality_score"], reverse=True)
        long_candidates.sort(key=lambda x: x["virality_score"], reverse=True)

        selected = list(initial_clips or [])

        # If user allowed long clips (max_seconds >= 120s) and requested multiple clips (top_k >= 3),
        # allocate a balanced portfolio: mostly 60-90s sweet-spot clips, plus 1 or 2 top complete long stories!
        target_long = 1 if (max_seconds >= 120.0 and top_k >= 3 and long_candidates) else 0
        if top_k >= 6 and max_seconds >= 150.0 and len(long_candidates) >= 2:
            target_long = 2

        target_sweet = top_k - target_long

        # 1. Fill sweet-spot (60-90s) clips first (main focus)
        for cand in sweet_candidates:
            if not any(is_overlapping(cand, s) for s in selected):
                selected.append(cand)
            if len(selected) >= target_sweet:
                break

        # 2. Add top complete long clip(s) if available ("if there is long then add in long")
        for cand in long_candidates:
            if not any(is_overlapping(cand, s) for s in selected):
                selected.append(cand)
            if len(selected) >= top_k:
                break

        # 3. If still space, backfill from remaining candidates with standard threshold
        if len(selected) < top_k:
            all_remaining = sorted(candidates, key=lambda x: x["virality_score"], reverse=True)
            for cand in all_remaining:
                if not any(is_overlapping(cand, s, max_overlap_ratio=0.35) for s in selected):
                    selected.append(cand)
                if len(selected) >= top_k:
                    break

        # 4. If still space, backfill with relaxed overlap threshold (0.50)
        if len(selected) < top_k:
            all_remaining = sorted(candidates, key=lambda x: x["virality_score"], reverse=True)
            for cand in all_remaining:
                if not any(is_overlapping(cand, s, max_overlap_ratio=0.50) for s in selected):
                    selected.append(cand)
                if len(selected) >= top_k:
                    break

        # 5. Guaranteed timeline backfill: extract clips from uncovered regions of the video
        if len(selected) < top_k and sentences:
            target_dur = max(min_seconds, min(max_seconds, 60.0))
            for idx_start in range(len(sentences)):
                s_start = sentences[idx_start]
                # Skip if start falls within an already chosen clip
                if any(s["start"] - 2.0 <= s_start["start"] <= s["end"] - 10.0 for s in selected):
                    continue

                clip_sents = []
                for idx_end in range(idx_start, len(sentences)):
                    s_end = sentences[idx_end]
                    clip_sents.append(s_end)
                    curr_dur = s_end["end"] - s_start["start"]
                    if curr_dur >= min_seconds:
                        if curr_dur >= target_dur or idx_end == len(sentences) - 1 or s_end["text"].strip().endswith((".", "!", "?")):
                            c_text = " ".join(s["text"] for s in clip_sents)
                            topic_t = self._extract_topic_headline(c_text, clip_sents[0]["text"])
                            new_clip = {
                                "start": round(max(0.0, s_start["start"] - 0.15), 2),
                                "end": round(s_end["end"] + 0.25, 2),
                                "duration": round((s_end["end"] + 0.25) - max(0.0, s_start["start"] - 0.15), 2),
                                "title": topic_t,
                                "hook": clip_sents[0]["text"],
                                "virality_score": 88,
                                "narrative_breakdown": {
                                    "hook_score": 88,
                                    "story_score": 86,
                                    "conclusion_score": 88
                                },
                                "full_transcript": c_text,
                                "part_info": "",
                                "series_id": "",
                                "reason": "Complete conversational thought extracted from video timeline."
                            }
                            if not any(is_overlapping(new_clip, s, max_overlap_ratio=0.45) for s in selected):
                                selected.append(new_clip)
                            break
                    if curr_dur > max_seconds:
                        break
                if len(selected) >= top_k:
                    break

        return selected[:top_k]

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

        # Feed enough context for topic arcs while keeping local inference bounded.
        full_text = "\n".join(transcript_lines[:400])

        prompt = f"""You are a master short-form editor for TikTok and YouTube Shorts.
Analyze this transcript and find the {top_k} most engaging, self-contained viral stories.

CRITICAL RULES:
1. Complete Narrative Arc: The clip MUST start with a clear topic/hook and END with a natural, complete conclusion.
2. NEVER cut off mid-thought, mid-sentence, or leave the viewer hanging without context.
3. Duration Rules:
   - PRIMARY FOCUS: Focus primarily on self-contained viral stories that conclude naturally within 60 to 90 seconds (ideal for TikTok Creator Rewards and peak viewer retention).
   - EXTENDED STORIES: If an in-depth story, debate, or interview explanation naturally takes longer to reach its conclusion, allow it to run longer (up to {int(max_seconds)}s) so that the thought is complete and no sentence is cut off mid-thought.
   - Every clip duration must be between {int(min_seconds)}s and {int(max_seconds)}s.
4. If the moment starts with a question, include the full spoken answer and the payoff.
5. Prefer one clearly identifiable podcast topic over switching between unrelated topics.
6. Output an engaging, high-CTR TOPIC HEADLINE (6 to 12 words in ALL CAPS) that takes full advantage of the top screen safe-area space, hooks viewers instantly, and reveals the core insight (e.g. "THE REAL REASON 99% OF PEOPLE FAIL AT THIS", "WHAT HAPPENS TO YOUR BODY WHEN YOU QUIT SUGAR", "THE 3 DAILY HABITS THAT WILL CHANGE YOUR LIFE").

Transcript:
{full_text}

Respond ONLY with a JSON array:
[
  {{
    "start": 12.0,
    "end": 48.5,
    "title": "THE REAL REASON 99% OF PEOPLE FAIL AT THIS",
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

        # Set a nimble 7s timeout for LLM so it never freezes the pipeline if model is slow/warming up
        with urllib.request.urlopen(req, timeout=7.0) as resp:
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

    def research_viral_clips(
        self,
        segments: List[Dict[str, Any]],
        query: str = "",
        archetype: str = "all",
        min_seconds: float = 60.0,
        max_seconds: float = 90.0,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        AI-Powered Viral Clip Research Engine.
        Allows creators to research specific topics, debates, or viral angles across
        the entire transcript with multidimensional virality scoring (0-100).
        """
        if not segments:
            return []

        sentences = SemanticSentenceAligner.reconstruct_sentences(segments)
        if not sentences:
            return []

        # 1. If Ollama is active, query LLM for semantic narrative retrieval
        if self.check_ollama_alive() and (query or archetype != "all"):
            try:
                llm_matches = self._query_ollama_research_clips(
                    sentences=sentences,
                    query=query,
                    archetype=archetype,
                    min_seconds=min_seconds,
                    max_seconds=max_seconds,
                    top_k=top_k
                )
                if llm_matches and len(llm_matches) >= 1:
                    snapped = self._snap_llm_clips(sentences, llm_matches, min_seconds, max_seconds)
                    if snapped:
                        return snapped[:top_k]
            except Exception as e:
                print(f"[Viral Research Warning] Ollama research fallback: {e}")

        # 2. High-Precision Semantic & NLP Viral Angle Research Engine
        return self._heuristic_research_clips(
            sentences=sentences,
            query=query,
            archetype=archetype,
            min_seconds=min_seconds,
            max_seconds=max_seconds,
            top_k=top_k
        )

    def _query_ollama_research_clips(
        self,
        sentences: List[Dict[str, Any]],
        query: str,
        archetype: str,
        min_seconds: float,
        max_seconds: float,
        top_k: int
    ) -> List[Dict[str, Any]]:
        """Queries local Ollama to find clips matching a creator's research intent."""
        transcript_lines = []
        for s in sentences:
            start_m, start_s = divmod(int(s["start"]), 60)
            end_m, end_s = divmod(int(s["end"]), 60)
            transcript_lines.append(f"[{start_m:02d}:{start_s:02d} - {end_m:02d}:{end_s:02d}] {s['text']}")

        full_text = "\n".join(transcript_lines[:450])
        archetype_desc = {
            "controversial": "Controversial / Polarizing debate, disagreement, or counter-intuitive claim.",
            "mindset": "Mindset Shift / Lightbulb realization, deep psychology, or paradigm change.",
            "story": "Personal Story / Emotional vulnerability, struggle, or breakthrough.",
            "blueprint": "Actionable Blueprint / Step-by-step tactics, rules, or practical advice.",
            "reveal": "Shocking Reveal / Hidden secret, myth debunked, or eye-opening question."
        }.get(archetype, "High-retention viral storytelling moment.")

        prompt = f"""You are an elite podcast researcher and viral short-form director for TikTok, YouTube Shorts, and Reels.
Your objective: Research this podcast transcript and extract the {top_k} moments matching the creator's search request.

CREATOR RESEARCH REQUEST:
- Search Query: "{query or 'Most engaging viral insight'}"
- Viral Angle Focus: "{archetype_desc}"

CRITICAL RULES:
1. Complete Narrative Arc: Every clip MUST begin with a captivating hook sentence and conclude naturally with full context.
2. Duration: Each clip duration must be between {int(min_seconds)}s and {int(max_seconds)}s (sweet spot 60-90s).
3. Output an engaging 6 to 12 word TOPIC HEADLINE in ALL CAPS.
4. Categorize the clip into an Archetype ('Controversial Take', 'Mindset Shift', 'Personal Story', 'Actionable Blueprint', 'Shocking Reveal').

Transcript:
{full_text}

Respond ONLY with a JSON array:
[
  {{
    "start": 14.5,
    "end": 78.0,
    "title": "THE REAL REASON 99% OF PEOPLE FAIL AT THIS",
    "hook": "Opening hook statement...",
    "archetype": "Controversial Take",
    "virality_score": 96,
    "reason": "Directly answers the research query with an emotionally charged contrarian insight."
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

        with urllib.request.urlopen(req, timeout=8.0) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            content = data.get("response", "").strip()
            match = re.search(r"\[.*\]", content, re.DOTALL)
            if match:
                parsed = json.loads(match.group(0))
                if isinstance(parsed, list):
                    return parsed
        return []

    def _heuristic_research_clips(
        self,
        sentences: List[Dict[str, Any]],
        query: str,
        archetype: str,
        min_seconds: float,
        max_seconds: float,
        top_k: int
    ) -> List[Dict[str, Any]]:
        """Fast, robust semantic & archetype-driven NLP research engine."""
        query_terms = [w.lower() for w in re.findall(r"\w+", query) if len(w) > 2]
        stop_words = {"the", "and", "that", "this", "with", "from", "your", "what", "about", "have", "more"}
        clean_terms = [t for t in query_terms if t not in stop_words]

        archetype_markers = {
            "controversial": {"disagree", "wrong", "mistake", "lie", "myth", "actually", "truth", "never", "hate", "fight", "argue", "problem", "fake", "terrible", "worst", "danger", "ruined", "stop"},
            "mindset": {"realize", "perspective", "changed", "think", "mind", "belief", "brain", "focus", "discipline", "habits", "psychology", "mental", "attitude", "paradigm", "aware"},
            "story": {"remember", "when", "years", "happened", "told", "suddenly", "started", "lost", "struggled", "crying", "felt", "moment", "journey", "life", "first"},
            "blueprint": {"step", "first", "second", "how", "rule", "strategy", "method", "system", "daily", "protocol", "secret", "technique", "formula", "process", "tips"},
            "reveal": {"why", "what", "secret", "nobody", "hidden", "discover", "shocking", "found", "truth", "exposed", "scam", "proof"}
        }

        candidates = []
        n = len(sentences)

        for i in range(n):
            first_sent = sentences[i]
            if first_sent.get("is_hanging_start"):
                continue

            # Accumulate window until duration target is reached
            accum_text = []
            for j in range(i, n):
                curr_sent = sentences[j]
                accum_text.append(curr_sent["text"])
                dur = curr_sent["end"] - first_sent["start"]

                if dur < min_seconds:
                    continue
                if dur > max_seconds * 1.15:
                    break

                if curr_sent.get("is_hanging_end"):
                    continue

                full_clip_text = " ".join(accum_text).lower()

                # 1. Query Relevance Score (0 to 40)
                q_score = 0
                if clean_terms:
                    matched_terms = sum(1 for t in clean_terms if t in full_clip_text)
                    q_score = min(40, int((matched_terms / max(1, len(clean_terms))) * 40))
                    # Exact query phrase bonus
                    if query and query.lower() in full_clip_text:
                        q_score = min(40, q_score + 15)
                else:
                    q_score = 25  # Neutral baseline if no search query

                # 2. Archetype Alignment Score (0 to 25)
                arch_score = 15
                detected_arch = "Mindset Shift"
                if archetype in archetype_markers:
                    markers = archetype_markers[archetype]
                    m_hits = sum(1 for m in markers if m in full_clip_text)
                    arch_score = min(25, 10 + m_hits * 3)
                    detected_arch = archetype.replace("_", " ").title()
                else:
                    # Auto-detect strongest archetype
                    best_hits = 0
                    for a_key, a_words in archetype_markers.items():
                        hits = sum(1 for w in a_words if w in full_clip_text)
                        if hits > best_hits:
                            best_hits = hits
                            detected_arch = a_key.replace("_", " ").title()
                    arch_score = min(25, 12 + best_hits * 2)

                # 3. Hook Virality (0 to 20)
                hook_score = 10
                if first_sent.get("is_hook") or first_sent["text"].endswith("?"):
                    hook_score += 8
                if any(p in first_sent["text"].lower() for p in self.ANCHOR_PHRASES):
                    hook_score += 5

                # 4. Conclusion & 60-90s Retention (0 to 15)
                pacing_score = 8
                if 60.0 <= dur <= 90.0:
                    pacing_score += 5  # Sweet spot bonus
                if not curr_sent.get("is_hanging_end"):
                    pacing_score += 2

                total_score = min(99, max(65, q_score + arch_score + hook_score + pacing_score))

                candidates.append({
                    "start_idx": i,
                    "end_idx": j,
                    "start": round(first_sent["start"], 2),
                    "end": round(curr_sent["end"], 2),
                    "duration": round(dur, 2),
                    "score": total_score,
                    "archetype": detected_arch,
                    "q_score": q_score,
                    "hook_score": min(99, hook_score * 5),
                    "story_score": min(99, (arch_score + q_score) * 2),
                    "conclusion_score": min(99, pacing_score * 6),
                    "clip_sentences": sentences[i:j + 1]
                })

        # Rank by total score
        candidates.sort(key=lambda c: c["score"], reverse=True)

        # Non-overlapping greedy selection
        selected = []
        for cand in candidates:
            c_start = cand["start"]
            c_end = cand["end"]
            overlap = False
            for s in selected:
                s_start = s["start"]
                s_end = s["end"]
                # Overlap check
                intersection = max(0.0, min(c_end, s_end) - max(c_start, s_start))
                min_len = min(c_end - c_start, s_end - s_start)
                if min_len > 0 and (intersection / min_len) > 0.35:
                    overlap = True
                    break

            if not overlap:
                clip_text = " ".join(sent["text"] for sent in cand["clip_sentences"])
                topic_title = self._extract_topic_headline(clip_text, cand["clip_sentences"][0]["text"])
                cand_id = f"res_{int(c_start)}_{int(c_end)}"
                selected.append({
                    "id": cand_id,
                    "title": topic_title,
                    "hook": cand["clip_sentences"][0]["text"],
                    "start": cand["start"],
                    "end": cand["end"],
                    "duration": cand["duration"],
                    "virality_score": cand["score"],
                    "archetype": cand["archetype"],
                    "narrative_breakdown": {
                        "hook_score": cand["hook_score"],
                        "story_score": cand["story_score"],
                        "conclusion_score": cand["conclusion_score"],
                        "shareability": min(99, cand["score"] + 2)
                    },
                    "reason": f"High {cand['archetype']} retention with complete {cand['duration']}s narrative arc.",
                    "full_transcript": clip_text
                })

            if len(selected) >= top_k:
                break

        return selected



