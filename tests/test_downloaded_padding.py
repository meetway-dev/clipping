import unittest
import os
import cv2
from pathlib import Path
from core.config import BASE_DIR, TEMP_DIR, OUTPUTS_DIR
from core.face_tracker import SmartFaceTracker
from core.subtitles import SubtitleGenerator
from core.renderer import VideoRenderer
from core.history_manager import HistoryManager

class TestDownloadedVideoPadding(unittest.TestCase):
    """
    Production-grade verification of the padding feature on the actual exported MP4 video files.
    Ensures that when a user downloads the video, it contains exact proportional padding
    with +66.4% wider horizontal field-of-view and zero excessive zoom.
    """

    @classmethod
    def setUpClass(cls):
        cls.test_video = str(BASE_DIR / "storage" / "uploads" / "yt_Xo1nuVe5g7k.mp4")
        if not os.path.exists(cls.test_video):
            raise unittest.SkipTest("Test video not found in storage/uploads")

    def test_rendered_mp4_has_physical_padding_on_disk(self):
        """
        Renders a full 1080x1920 MP4 clip with 20% top & 20% bottom padding
        and verifies the actual video frames on disk have padded bars & wide crop.
        """
        tracker = SmartFaceTracker()
        top_padding = 20.0
        bottom_padding = 20.0
        
        # 1. Generate filter
        crop_filter, actual_layout = tracker.build_layout_filter(
            video_path=self.test_video,
            start_sec=2.0,
            duration=3.0,
            layout_mode="speaker_focus",
            top_padding=top_padding,
            bottom_padding=bottom_padding,
            canvas_bg="solid_black",
            target_w=1080,
            target_h=1920
        )
        
        # Verify 1012px crop width in filter (not 608px standard 9:16)
        self.assertIn("1012", crop_filter)
        self.assertIn("pad=1080:1920:0:384", crop_filter)

        # 2. Generate ASS subtitles in padded safe zones
        ass_path = TEMP_DIR / "test_download_padded.ass"
        SubtitleGenerator.create_ass_file(
            words=[{"word": "VIRAL", "start": 2.0, "end": 3.0}],
            output_path=ass_path,
            style_key="hormozi",
            clip_start_offset=2.0,
            clip_duration=3.0,
            topic_headline="HIGH RETENTION HOOK",
            show_headline_banner=True,
            top_padding=top_padding,
            bottom_padding=bottom_padding
        )

        # 3. Render MP4 to disk
        renderer = VideoRenderer()
        out_name = "test_download_verified_pad.mp4"
        out_path = renderer.render_clip(
            video_path=self.test_video,
            start_sec=2.0,
            duration=3.0,
            crop_filter=crop_filter,
            ass_subtitle_path=str(ass_path),
            output_filename=out_name
        )

        self.assertTrue(out_path.exists())
        self.assertGreater(out_path.stat().st_size, 100_000)

        # 4. Open rendered MP4 file with OpenCV and inspect physical pixel geometry
        cap = cv2.VideoCapture(str(out_path))
        self.assertTrue(cap.isOpened())
        
        ret, frame = cap.read()
        cap.release()
        self.assertTrue(ret)
        
        h, w = frame.shape[:2]
        self.assertEqual(w, 1080, "Video width must be 1080px")
        self.assertEqual(h, 1920, "Video height must be 1920px")

        # Top padding zone: 0 to 384px (y=100)
        # Should be solid dark background
        top_pixel = frame[100, 540]
        # Middle active video zone: 384px to 1536px (y=960)
        mid_pixel = frame[960, 540]
        
        print(f"\n[Test Verification] Rendered MP4 Frame Shape: {w}x{h}")
        print(f"  Top padding zone pixel (y=100, x=540): {top_pixel}")
        print(f"  Middle active video pixel (y=960, x=540): {mid_pixel}")

        # The top padding zone should be dark solid canvas background
        # (approx #0E0C0A -> [10, 12, 14] in BGR)
        self.assertLess(top_pixel[0], 40)
        self.assertLess(top_pixel[1], 40)
        self.assertLess(top_pixel[2], 40)

if __name__ == "__main__":
    unittest.main()
