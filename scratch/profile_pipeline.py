import sys
import time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from core.transcriber import AudioTranscriber
from core.face_tracker import SmartFaceTracker
from core.renderer import VideoRenderer
from core.subtitles import SubtitleGenerator

video_path = "storage/uploads/yt_nYrLMyUP4S0.mp4"
start_sec = 10.0
duration = 20.0

print("=== PROFILING PIPELINE STEPS ===")

# 1. Face Tracker Trajectory Profile
print("\n[1] Profiling SmartFaceTracker.compute_crop_trajectory (20s duration)...")
tracker = SmartFaceTracker()
t0 = time.time()
trajectory = tracker.compute_crop_trajectory(video_path, start_sec=start_sec, duration=duration, sample_fps=2.0)
t1 = time.time()
print(f"FaceTracker took: {t1 - t0:.2f} seconds ({len(trajectory)} samples)")

# 2. Subtitle Generator Profile
print("\n[2] Profiling SubtitleGenerator...")
words = [
    {"word": "Hello", "start": 10.5, "end": 11.0},
    {"word": "world", "start": 11.1, "end": 11.5},
    {"word": "this", "start": 11.6, "end": 12.0},
    {"word": "is", "start": 12.1, "end": 12.3},
    {"word": "a", "start": 12.4, "end": 12.5},
    {"word": "speed", "start": 12.6, "end": 13.0},
    {"word": "test", "start": 13.1, "end": 13.5}
]
ass_path = "storage/temp/profile_sub.ass"
t0 = time.time()
SubtitleGenerator.create_ass_file(words, ass_path, style_key="hormozi", clip_start_offset=start_sec, clip_duration=duration)
t1 = time.time()
print(f"SubtitleGenerator took: {t1 - t0:.4f} seconds")

# 3. Crop filter generation
crop_filter = tracker.get_ffmpeg_crop_filter(trajectory)
print(f"Crop filter expression length: {len(crop_filter)}")

# 4. VideoRenderer Profile
print("\n[3] Profiling VideoRenderer (NVENC vs CPU)...")
renderer = VideoRenderer()
t0 = time.time()
out = renderer.render_clip(
    video_path=video_path,
    start_sec=start_sec,
    duration=duration,
    crop_filter=crop_filter,
    ass_subtitle_path=ass_path,
    output_filename="profile_test_out.mp4",
    color_preset="cinematic_pop",
    watermark_text="@clipforge",
    enable_voice_clarifier=True
)
t1 = time.time()
print(f"VideoRenderer took: {t1 - t0:.2f} seconds for 20s clip! Output: {out}")
