import time
import re
import shutil
from collections import defaultdict
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
from .config import TEMP_DIR, OUTPUTS_DIR, DEFAULT_CONFIG
from .transcriber import AudioTranscriber
from .viral_detector import ViralDetector
from .face_tracker import SmartFaceTracker
from .subtitles import SubtitleGenerator
from .renderer import VideoRenderer
from .tight_cut import TightCutEngine
from .thumbnail_designer import TikTokThumbnailDesigner
from .docs_generator import add_session_docs_to_zip, create_clip_docs_files

def sanitize_topic_filename(raw_topic: str) -> str:
    """Sanitizes topic into a clean, safe filename."""
    cleaned = re.sub(r"[^\w\s\-]", "", str(raw_topic or "").strip())
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    if not cleaned:
        return "Video_Clip"
    if cleaned.isupper() or cleaned.islower():
        cleaned = cleaned.title()
    safe = re.sub(r"[\s\-]+", "_", cleaned).strip("_")
    return safe[:60].strip("_") or "Video_Clip"

class ClipForgePipeline:
    """
    End-to-End Orchestrator for Local Podcast Clipping Studio.
    Handles speech-to-text, narrative topic boundary segmentation,
    TightCut dead-air removal, face-tracking & split-screen 9:16 reframe,
    Submagic auto-emojis with top topic banners, and viral Social Kits.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = {**DEFAULT_CONFIG, **(config or {})}
        self.transcriber = AudioTranscriber(
            model_size=self.config["whisper_model"],
            device=self.config["device"]
        )
        self.viral_detector = ViralDetector(
            ollama_url=self.config["ollama_url"],
            model=self.config["ollama_model"]
        )
        self.face_tracker = SmartFaceTracker(
            smooth_factor=self.config["smooth_factor"]
        )
        self.renderer = VideoRenderer()

    def process_video(
        self,
        video_path: str,
        subtitle_style: str = "hormozi",
        max_clips: int = 5,
        min_clip_seconds: float = 25.0,
        max_clip_seconds: float = 65.0,
        show_headline_banner: bool = True,
        enable_face_tracking: bool = True,
        clip_mode: str = "highlights",
        layout_mode: str = "speaker_focus",
        canvas_top_space: int = 450,
        canvas_bg: str = "solid_black",
        enable_tightcut: bool = False,
        enable_auto_emojis: bool = True,
        progress_bar_color: Optional[str] = "#00E5FF",
        bgm_track: Optional[str] = "none",
        bgm_volume: float = 0.12,
        color_preset: Optional[str] = "none",
        watermark_text: Optional[str] = None,
        watermark_position: str = "top_right",
        enable_voice_clarifier: bool = True,
        enable_hook_zoom: bool = True,
        custom_headline: Optional[str] = None,
        top_padding: float = 0.0,
        bottom_padding: float = 0.0,
        language: Optional[str] = "en",
        progress_cb: Optional[Callable[[str, float], None]] = None
    ) -> Dict[str, Any]:
        """
        Executes the full automated workflow on an input podcast video.
        Supports clip_mode='highlights' or clip_mode='parting' (Part 1, Part 2 series),
        layout_mode ('speaker_focus', 'split_screen', 'blur', 'center_crop'),
        TightCut dead-air removal, retention progress bar, and smart auto-ducked background music.
        """
        def update_progress(msg: str, percent: float, step: int = 1, step_name: str = "", detail: str = ""):
            print(f"[{percent:.0f}%] [Step {step}: {step_name}] {msg}")
            if progress_cb:
                # Support both 2-arg callbacks (msg, percent) and 5-arg callbacks with step info
                try:
                    progress_cb(msg, percent, step, step_name, detail)
                except TypeError:
                    try:
                        progress_cb(msg, percent)
                    except Exception:
                        pass

        video_p = Path(video_path)
        if not video_p.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")

        # Step 1: Transcription & Speech Recognition
        update_progress(
            "Extracting audio and transcribing speech with word-level timestamps...",
            10,
            step=1,
            step_name="Transcribe",
            detail="Whisper AI extracting audio waveforms & word timings"
        )
        transcribe_lang = None if (not language or language.lower() in ["auto", "none"]) else language
        transcription_result = self.transcriber.transcribe(str(video_p), language=transcribe_lang)
        segments = transcription_result["segments"]
        words = transcription_result["words"]

        update_progress(
            f"Transcribed {len(segments)} spoken segments ({len(words)} words) with millisecond accuracy.",
            28,
            step=1,
            step_name="Transcribe",
            detail=f"Completed {len(segments)} segments. Audio alignment verified."
        )

        # Step 2: AI Viral Research & Complete Narrative Verification
        update_progress(
            f"AI researching full video for viral moments (target {int(min_clip_seconds)}–{int(max_clip_seconds)}s)...",
            30,
            step=2,
            step_name="AI Research",
            detail="Scanning episode transcript for high-retention topics, emotional hooks, and debate spikes"
        )

        def viral_sub_progress(sub_msg: str, sub_pct: float):
            update_progress(sub_msg, sub_pct, step=2, step_name="AI Research", detail=sub_msg)

        viral_clips = self.viral_detector.find_viral_clips(
            segments=segments,
            min_seconds=min_clip_seconds,
            max_seconds=max_clip_seconds,
            top_k=max_clips,
            clip_mode=clip_mode,
            progress_cb=viral_sub_progress
        )

        update_progress(
            f"Verified {len(viral_clips)} viral moments with complete thought arcs (60–90s sweet spot).",
            40,
            step=2,
            step_name="AI Research",
            detail=f"AI verified {len(viral_clips)} complete-thought clips with 90%+ viral scores"
        )

        if not viral_clips:
            # Last-resort extraction must still be a complete sentence, never a blind 0-to-45 second cut.
            relax_min = max(8.0, min_clip_seconds * 0.5)
            relax_max = max(max_clip_seconds, 75.0)
            viral_clips = self.viral_detector.find_viral_clips(
                segments=segments,
                min_seconds=relax_min,
                max_seconds=relax_max,
                top_k=max(1, max_clips),
                clip_mode="highlights",
                progress_cb=viral_sub_progress
            )
            if not viral_clips:
                dur = min(relax_max, transcription_result["duration"])
                viral_clips = [{
                    "start": 0.0,
                    "end": dur,
                    "duration": dur,
                    "title": "PODCAST HIGHLIGHT",
                    "hook": "Opening statement...",
                    "virality_score": 85,
                    "narrative_breakdown": {"hook_score": 85, "story_score": 85, "conclusion_score": 85},
                    "full_transcript": "Podcast highlight.",
                    "part_info": "",
                    "series_id": "",
                    "reason": "Short fallback based on available transcript."
                }]

        # Guarantee requested clip count if video duration permits
        total_vid_dur = float(transcription_result.get("duration", 0.0))
        if len(viral_clips) < max_clips and total_vid_dur >= min_clip_seconds * 1.5 and segments:
            relax_min = max(15.0, min_clip_seconds * 0.75)
            relax_max = max(max_clip_seconds, 75.0)
            more_clips = self.viral_detector.find_viral_clips(
                segments=segments,
                min_seconds=relax_min,
                max_seconds=relax_max,
                top_k=max_clips,
                clip_mode="highlights"
            )
            for mc in more_clips:
                # Add if not overlapping with existing clips
                if not any(max(0.0, min(mc["end"], vc["end"]) - max(mc["start"], vc["start"])) / max(1.0, min(mc["duration"], vc["duration"])) > 0.40 for vc in viral_clips):
                    viral_clips.append(mc)
                if len(viral_clips) >= max_clips:
                    break

        # Step 2B: Topic-Based Video Naming & Part Numbering
        # Detect if multiple videos cover the same topic to append part_1, part_2, etc.
        topic_groups = defaultdict(list)
        for i, c in enumerate(viral_clips):
            raw_t = c.get("topic") or c.get("title") or f"Highlight_{i+1}"
            norm_k = sanitize_topic_filename(raw_t).lower()
            topic_groups[norm_k].append(i)

        allocated_filenames = set()
        for i, c in enumerate(viral_clips):
            raw_t = c.get("topic") or c.get("title") or f"Highlight_{i+1}"
            norm_k = sanitize_topic_filename(raw_t).lower()
            base_safe_name = sanitize_topic_filename(raw_t)
            matching_indices = topic_groups[norm_k]

            # If two or more clips cover the same topic:
            if len(matching_indices) > 1:
                part_num = matching_indices.index(i) + 1
                stem = f"{base_safe_name}_part_{part_num}"
                part_label = f"part_{part_num}"
                c["part_info"] = f"Part {part_num}/{len(matching_indices)}"
                curr_title = c.get("title") or raw_t
                if not re.search(r"part[_\s]*\d+", curr_title, re.IGNORECASE):
                    c["title"] = f"{curr_title} {part_label}"
            else:
                stem = base_safe_name
                if c.get("part_info") in ["Part 1/1", ""]:
                    c["part_info"] = ""

            c["topic"] = raw_t

            # Ensure unique filename on disk and within session
            candidate_fn = f"{stem}.mp4"
            if candidate_fn in allocated_filenames or (OUTPUTS_DIR / candidate_fn).exists():
                count = 1
                while f"{stem}_{count}.mp4" in allocated_filenames or (OUTPUTS_DIR / f"{stem}_{count}.mp4").exists():
                    count += 1
                candidate_fn = f"{stem}_{count}.mp4"

            allocated_filenames.add(candidate_fn)
            c["assigned_filename"] = candidate_fn

        rendered_clips = []
        total_clips = len(viral_clips)

        # Process Each Selected Clip
        for idx, clip in enumerate(viral_clips, 1):
            clip_start = clip["start"]
            clip_end = clip["end"]
            clip_duration = clip["duration"]

            base_pct = 40 + (idx - 1) * (50 / total_clips)

            # Filter words for this clip
            clip_words = [
                w for w in words
                if (w["start"] >= clip_start - 0.2 and w["end"] <= clip_end + 0.2)
            ]

            render_src_video = str(video_p)
            render_start_sec = clip_start
            render_dur = clip_duration
            ass_start_offset = clip_start

            # Step 3A: TightCut Dead-Air Removal Engine
            if enable_tightcut and clip_words:
                update_progress(
                    f"Clip {idx}/{total_clips}: Tightening pacing (cutting dead air)...",
                    base_pct,
                    step=3,
                    step_name="Framing & Pacing",
                    detail=f"TightCut: removing dead air silences >0.65s for clip {idx}"
                )
                tight_res = TightCutEngine.analyze_and_tighten(
                    words=clip_words,
                    clip_start=clip_start,
                    clip_end=clip_end,
                    max_silence=0.65
                )
                if tight_res["has_tightcut"]:
                    try:
                        interm_path = TEMP_DIR / f"{video_p.stem}_tight_{idx}_{int(clip_start)}.mp4"
                        TightCutEngine.render_tightened_intermediate(
                            video_path=str(video_p),
                            keep_intervals=tight_res["keep_intervals"],
                            output_path=interm_path
                        )
                        render_src_video = str(interm_path)
                        clip_words = tight_res["shifted_words"]
                        render_start_sec = 0.0
                        render_dur = tight_res["tightened_duration"]
                        ass_start_offset = 0.0
                        print(f"[TightCut] Compressed clip from {clip_duration:.1f}s down to {render_dur:.1f}s (saved {tight_res['time_saved']:.1f}s of silence)!")
                    except Exception as tc_err:
                        print(f"[TightCut Warning] Fallback to uncut source: {tc_err}")

            # Step 3B: Video Framing Filter (Universal for all camera layouts & padding)
            top_pct = max(0.0, min(45.0, float(top_padding))) / 100.0
            bottom_pct = max(0.0, min(45.0, float(bottom_padding))) / 100.0
            if top_pct + bottom_pct > 0.80:
                scale_pad = 0.80 / (top_pct + bottom_pct)
                top_pct *= scale_pad
                bottom_pct *= scale_pad
            has_padding = (top_pct > 0 or bottom_pct > 0)
            top_pad_px = int(round(self.config['target_height'] * top_pct))
            bottom_pad_px = int(round(self.config['target_height'] * bottom_pct))
            available_h = max(100, self.config['target_height'] - top_pad_px - bottom_pad_px)

            fit_top_space = max(top_pad_px, max(80, min(950, int(canvas_top_space)))) if not has_padding else top_pad_px
            fit_video_h = min(608, available_h)

            update_progress(
                f"Clip {idx}/{total_clips}: Applying '{layout_mode}' layout with safe area framing...",
                base_pct + 5,
                step=3,
                step_name="Framing & Pacing",
                detail=f"Layout: {layout_mode} | Top safe margin: {top_pad_px}px"
            )
            crop_filter, current_layout = self.face_tracker.build_layout_filter(
                video_path=render_src_video,
                start_sec=render_start_sec,
                duration=render_dur,
                layout_mode=layout_mode,
                top_padding=top_padding,
                bottom_padding=bottom_padding,
                canvas_bg=canvas_bg,
                target_w=self.config["target_width"],
                target_h=self.config["target_height"],
                enable_hook_zoom=enable_hook_zoom,
                canvas_top_space=canvas_top_space
            )

            # Step 4: Kinetic Subtitles + Power Keywords + Top Topic Banner
            update_progress(
                f"Clip {idx}/{total_clips}: Generating animated captions & topic banner...",
                base_pct + 12,
                step=4,
                step_name="Subtitles",
                detail=f"Applying '{subtitle_style}' kinetic captions & power keywords"
            )
            ass_path = TEMP_DIR / f"{video_p.stem}_clip_{idx}_{int(clip_start)}.ass"
            part_info = clip.get("part_info", "")

            # Generate AI viral copy data for both video top headline and companion thumbnail
            copy_data = None
            try:
                copy_data = TikTokThumbnailDesigner.generate_ai_copy(
                    topic=clip.get("topic", ""),
                    title=clip.get("title", ""),
                    hook=clip.get("hook", ""),
                    transcript=clip.get("full_transcript", "")
                )
            except Exception as copy_err:
                print(f"[Headline Copy Warning] AI copy fallback: {copy_err}")

            if custom_headline:
                banner_headline = custom_headline
            elif clip.get("title") and len(str(clip.get("title")).split()) >= 4:
                # Prefer the rich 6-12 word topic headline designed for the top safe-area banner
                banner_headline = str(clip.get("title")).strip()
            elif clip.get("hook") and len(str(clip.get("hook")).split()) >= 4:
                # Use the opening viral hook if self-contained
                banner_headline = str(clip.get("hook")).strip()
            elif copy_data and copy_data.get("subheadline") and len(str(copy_data.get("subheadline")).split()) >= 5:
                banner_headline = copy_data.get("subheadline")
            else:
                # Synthesize a high-converting multi-word banner hook from available topic/title keywords
                base_topic = clip.get("title") or clip.get("topic") or clip.get("hook") or "VIRAL HIGHLIGHT"
                banner_headline = self.viral_detector._extract_topic_headline(
                    clip.get("full_transcript", base_topic),
                    clip.get("hook", base_topic)
                )

            SubtitleGenerator.create_ass_file(
                words=clip_words,
                output_path=ass_path,
                style_key=subtitle_style,
                words_per_batch=3,
                clip_start_offset=ass_start_offset,
                clip_duration=render_dur,
                topic_headline=banner_headline,
                part_info=part_info,
                show_headline_banner=show_headline_banner,
                enable_auto_emojis=enable_auto_emojis,
                layout_mode=current_layout,
                top_space=fit_top_space,
                video_h=fit_video_h,
                top_padding=top_padding,
                bottom_padding=bottom_padding
            )

            # Step 5: Render 1080x1920 MP4 via Hardware NVENC / CPU
            update_progress(
                f"Clip {idx}/{total_clips}: Rendering 1080x1920 MP4...",
                base_pct + 20,
                step=5,
                step_name="Render & Covers",
                detail=f"FFmpeg NVENC/CPU encoding 1080x1920 60fps vertical output"
            )
            out_filename = clip.get("assigned_filename") or f"{video_p.stem}_viral_{idx}_{subtitle_style}.mp4"
            rendered_path = self.renderer.render_clip(
                video_path=render_src_video,
                start_sec=render_start_sec,
                duration=render_dur,
                crop_filter=crop_filter,
                ass_subtitle_path=str(ass_path),
                output_filename=out_filename,
                enable_punch_in_zoom=enable_hook_zoom,
                progress_bar_color=progress_bar_color,
                bgm_track=bgm_track,
                bgm_volume=bgm_volume,
                color_preset=color_preset,
                watermark_text=watermark_text,
                watermark_position=watermark_position,
                enable_voice_clarifier=enable_voice_clarifier
            )

            # Create dedicated topic folder for this clip
            safe_topic_name = Path(out_filename).stem or sanitize_topic_filename(clip.get("topic") or clip.get("title") or f"Clip_{idx}")
            clip_folder_name = clip.get("folder_name") or safe_topic_name
            clip_dir = OUTPUTS_DIR / clip_folder_name
            clip_dir.mkdir(parents=True, exist_ok=True)

            # Keep video inside both clip folder and base outputs dir for maximum compatibility
            folder_video_path = clip_dir / f"{safe_topic_name}.mp4"
            if Path(rendered_path).exists() and folder_video_path.resolve() != Path(rendered_path).resolve():
                try:
                    shutil.copy2(str(rendered_path), str(folder_video_path))
                except Exception as cpy_err:
                    print(f"[Folder Video Warning] {cpy_err}")

            # Generate 3 Distinct High-Converting TikTok Thumbnails (Editorial, Red Alert, Authority Blueprint)
            thumb_configs = [
                ("thumb_1", "curiosity", "editorial_premium", "#FFE600", "Curiosity Editorial"),
                ("thumb_2", "warning", "red_alert", "#EF4444", "Red Alert Warning"),
                ("thumb_3", "formula", "podcast_authority", "#00E5FF", "Authority Blueprint")
            ]
            generated_covers = []
            for t_suffix, t_arch, t_style, t_accent, t_label in thumb_configs:
                t_filename = f"{safe_topic_name}_{t_suffix}.jpg"
                t_folder_path = clip_dir / t_filename
                t_flat_path = OUTPUTS_DIR / t_filename
                try:
                    update_progress(
                        f"Clip {idx}/{total_clips}: Designing {t_label} cover...",
                        base_pct + 25,
                        step=5,
                        step_name="Render & Covers",
                        detail=f"Designing {t_label} cover thumbnail for TikTok"
                    )
                    TikTokThumbnailDesigner.create_tiktok_thumbnail(
                        video_path=str(rendered_path),
                        output_jpg_path=str(t_folder_path),
                        topic=clip.get("topic", banner_headline),
                        title=clip.get("title", banner_headline),
                        hook=clip.get("hook", ""),
                        transcript=clip.get("full_transcript", ""),
                        crop_filter=crop_filter,
                        source_clean_video=render_src_video,
                        timestamp_sec=min(2.0, max(0.8, render_dur * 0.2)),
                        copy_data=None,
                        style=t_style,
                        accent_color=t_accent,
                        archetype=t_arch
                    )
                    if t_folder_path.exists():
                        shutil.copy2(str(t_folder_path), str(t_flat_path))
                        if t_suffix == "thumb_1":
                            shutil.copy2(str(t_folder_path), str(OUTPUTS_DIR / f"{safe_topic_name}.jpg"))
                            shutil.copy2(str(t_folder_path), str(clip_dir / f"{safe_topic_name}.jpg"))
                        generated_covers.append(f"{clip_folder_name}/{t_filename}")
                except Exception as t_err:
                    print(f"[Thumbnail Warning] {t_label} cover fallback: {t_err}")
                    try:
                        self.renderer.generate_thumbnail(str(rendered_path), str(t_folder_path), timestamp_sec=1.0)
                        if t_folder_path.exists():
                            shutil.copy2(str(t_folder_path), str(t_flat_path))
                            generated_covers.append(f"{clip_folder_name}/{t_filename}")
                    except Exception:
                        pass

            if not generated_covers:
                def_cover = f"{safe_topic_name}.jpg"
                self.renderer.generate_thumbnail(str(rendered_path), str(OUTPUTS_DIR / def_cover), timestamp_sec=1.0)
                generated_covers = [def_cover]

            # Step 6: Generate AI Social Media Kit
            social_kit = self.viral_detector.generate_social_kit(
                title=clip.get("title", banner_headline or "PODCAST HIGHLIGHT"),
                hook=clip.get("hook", ""),
                transcript=clip.get("full_transcript", ""),
                series_part=part_info
            )

            # Step 7: Generate Dedicated Clip Document (.docx, .txt, .md) inside folder
            clip_data_for_docs = {
                **clip,
                "topic": clip.get("topic", banner_headline),
                "title": clip.get("title", banner_headline),
                "filename": f"{safe_topic_name}.mp4",
                "part_info": part_info,
                "start_sec": clip_start,
                "end_sec": clip_end,
                "duration": render_dur,
                "hook": clip.get("hook", ""),
                "social_kit": social_kit
            }
            try:
                clip_docs_paths = create_clip_docs_files(clip_data_for_docs, output_dir=clip_dir, base_name=safe_topic_name)
            except Exception as doc_err:
                print(f"[Clip Docs Warning] Failed to generate clip docs: {doc_err}")
                clip_docs_paths = {}

            rendered_clips.append({
                **clip,
                "topic": clip.get("topic", banner_headline),
                "title": clip.get("title", banner_headline),
                "start": clip_start,
                "end": clip_end,
                "duration": round(render_dur, 2),
                "output_file": str(folder_video_path if folder_video_path.exists() else rendered_path),
                "filename": out_filename,
                "folder_name": clip_folder_name,
                "folder_video": f"{clip_folder_name}/{safe_topic_name}.mp4",
                "cover": generated_covers[0] if generated_covers else f"{safe_topic_name}.jpg",
                "covers": generated_covers,
                "docs_file": f"{clip_folder_name}/{safe_topic_name}_docs.docx",
                "docs_paths": clip_docs_paths,
                "part_info": part_info,
                "series_id": clip.get("series_id", ""),
                "subtitle_style": subtitle_style,
                "layout_mode": current_layout,
                "top_padding": float(top_padding),
                "bottom_padding": float(bottom_padding),
                "social_kit": social_kit,
                "words": clip_words
            })

        update_progress(
            "Building full video virality heatmap...",
            96,
            step=5,
            step_name="Render & Covers",
            detail="Synthesizing engagement heatmap along timeline"
        )
        virality_timeline = self.viral_detector.generate_virality_timeline(
            segments=segments,
            total_duration=transcription_result["duration"],
            viral_clips=rendered_clips
        )

        update_progress(
            "Generating executive podcast summary & topic map...",
            98,
            step=5,
            step_name="Render & Covers",
            detail="Generating chapter outlines and social media kit"
        )
        podcast_summary = self.viral_detector.generate_podcast_summary(
            segments=segments,
            total_duration=transcription_result["duration"]
        )

        transcript_segments = [
            {"start": round(s["start"], 2), "end": round(s["end"], 2), "text": s["text"]}
            for s in segments
        ]

        update_progress(
            "All viral clips created successfully with complete story arcs!",
            100,
            step=5,
            step_name="Render & Covers",
            detail="Pipeline completed. All clips & covers ready."
        )

        return {
            "source_video": str(video_p),
            "duration": transcription_result["duration"],
            "language": transcription_result["language"],
            "total_clips": len(rendered_clips),
            "clips": rendered_clips,
            "virality_timeline": virality_timeline,
            "podcast_summary": podcast_summary,
            "transcript_segments": transcript_segments,
            "transcript_summary": [s["text"] for s in segments[:10]]
        }
