import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
from .config import TEMP_DIR, OUTPUTS_DIR, DEFAULT_CONFIG
from .transcriber import AudioTranscriber
from .viral_detector import ViralDetector
from .face_tracker import SmartFaceTracker
from .subtitles import SubtitleGenerator
from .renderer import VideoRenderer
from .tight_cut import TightCutEngine

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
        def update_progress(msg: str, percent: float):
            print(f"[{percent:.0f}%] {msg}")
            if progress_cb:
                progress_cb(msg, percent)

        video_p = Path(video_path)
        if not video_p.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")

        # Step 1: Transcription
        update_progress("Extracting audio and transcribing speech with word timestamps...", 10)
        transcribe_lang = None if (not language or language.lower() in ["auto", "none"]) else language
        transcription_result = self.transcriber.transcribe(str(video_p), language=transcribe_lang)
        segments = transcription_result["segments"]
        words = transcription_result["words"]

        # Step 2: Semantic Narrative Arc & Viral Clip Detection
        update_progress(f"Analyzing topics in '{clip_mode}' mode for complete conversational context...", 35)
        viral_clips = self.viral_detector.find_viral_clips(
            segments=segments,
            min_seconds=min_clip_seconds,
            max_seconds=max_clip_seconds,
            top_k=max_clips,
            clip_mode=clip_mode
        )

        if not viral_clips:
            dur = min(45.0, transcription_result["duration"])
            viral_clips = [{
                "start": 0.0,
                "end": dur,
                "duration": dur,
                "title": "PODCAST HIGHLIGHT",
                "hook": "Opening statement...",
                "virality_score": 85,
                "narrative_breakdown": {"hook_score": 85, "story_score": 85, "conclusion_score": 85},
                "full_transcript": "Default highlight selection.",
                "part_info": "",
                "series_id": "",
                "reason": "Default highlight selection."
            }]

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
                update_progress(f"Clip {idx}/{total_clips}: Tightening pacing (cutting dead air)...", base_pct)
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

            update_progress(f"Clip {idx}/{total_clips}: Applying '{layout_mode}' layout with safe area framing...", base_pct + 5)
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
            update_progress(f"Clip {idx}/{total_clips}: Generating animated captions & topic banner...", base_pct + 12)
            ass_path = TEMP_DIR / f"{video_p.stem}_clip_{idx}_{int(clip_start)}.ass"
            part_info = clip.get("part_info", "")
            banner_headline = custom_headline if custom_headline else clip.get("title", "")
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
            update_progress(f"Clip {idx}/{total_clips}: Rendering 1080x1920 MP4...", base_pct + 20)
            part_suffix = f"_{part_info.lower().replace('/', '_').replace(' ', '_')}" if part_info else ""
            out_filename = f"{video_p.stem}_viral_{idx}{part_suffix}_{subtitle_style}.mp4"
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

            # Step 6: Generate AI Social Media Kit
            social_kit = self.viral_detector.generate_social_kit(
                title=clip.get("title", "PODCAST HIGHLIGHT"),
                hook=clip.get("hook", ""),
                transcript=clip.get("full_transcript", ""),
                series_part=part_info
            )

            rendered_clips.append({
                **clip,
                "start": clip_start,
                "end": clip_end,
                "duration": round(render_dur, 2),
                "output_file": str(rendered_path),
                "filename": out_filename,
                "cover": f"{Path(out_filename).stem}.jpg",
                "part_info": part_info,
                "series_id": clip.get("series_id", ""),
                "subtitle_style": subtitle_style,
                "layout_mode": current_layout,
                "top_padding": float(top_padding),
                "bottom_padding": float(bottom_padding),
                "social_kit": social_kit,
                "words": clip_words
            })

        update_progress("Building full video virality heatmap...", 96)
        virality_timeline = self.viral_detector.generate_virality_timeline(
            segments=segments,
            total_duration=transcription_result["duration"],
            viral_clips=rendered_clips
        )

        update_progress("Generating executive podcast summary & topic map...", 98)
        podcast_summary = self.viral_detector.generate_podcast_summary(
            segments=segments,
            total_duration=transcription_result["duration"]
        )

        transcript_segments = [
            {"start": round(s["start"], 2), "end": round(s["end"], 2), "text": s["text"]}
            for s in segments
        ]

        update_progress("All viral clips created successfully with complete story arcs!", 100)

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
