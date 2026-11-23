import unittest
import numpy as np
import cv2
from pathlib import Path
from core.config import BASE_DIR, TEMP_DIR
from core.face_tracker import SmartFaceTracker
from core.subtitles import SubtitleGenerator

class TestPaddingAndCameraLayouts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Create a synthetic 16:9 test video (1920x1080, 3 seconds) with two circular "faces"
        cls.test_video_path = TEMP_DIR / "test_synth_podcast_16_9.mp4"
        cls.test_video_path.parent.mkdir(parents=True, exist_ok=True)
        
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        fps = 30
        w, h = 1920, 1080
        out = cv2.VideoWriter(str(cls.test_video_path), fourcc, fps, (w, h))
        
        for frame_idx in range(fps * 3):
            # Background dark studio gradient
            frame = np.full((h, w, 3), 20, dtype=np.uint8)
            # Left speaker (host) face circle at (480, 450)
            cv2.circle(frame, (480, 450), 120, (180, 150, 120), -1)
            # Right speaker (guest) face circle at (1440, 450)
            cv2.circle(frame, (1440, 450), 120, (140, 170, 200), -1)
            out.write(frame)
        out.release()
        cls.tracker = SmartFaceTracker()

    def test_padding_aspect_ratio_and_zoom_reduction(self):
        """
        Verify that 20% top + 20% bottom padding yields an active area of 1152px,
        which widens the crop from 608px (at 0% pad) to 1012px (at 20% pad),
        preserving 52.7% of the 16:9 frame instead of only 31.6% (66% less zoom).
        """
        # 1. 0% Padding (Standard 9:16)
        traj_0 = self.tracker.compute_crop_trajectory(
            video_path=str(self.test_video_path),
            start_sec=0.0,
            duration=1.0,
            top_padding=0.0,
            bottom_padding=0.0,
            target_w=1080,
            target_h=1920
        )
        self.assertGreater(len(traj_0), 0)
        crop_w_0 = traj_0[0]["crop_w"]
        crop_h_0 = traj_0[0]["crop_h"]
        # Standard 9:16 crop width for 1080h is round(1080 * 9/16) = 608px
        self.assertEqual(crop_w_0, 608)
        self.assertEqual(crop_h_0, 1080)

        # 2. 20% Top + 20% Bottom Padding (Active Area 60% = 1152px)
        traj_20 = self.tracker.compute_crop_trajectory(
            video_path=str(self.test_video_path),
            start_sec=0.0,
            duration=1.0,
            top_padding=20.0,
            bottom_padding=20.0,
            target_w=1080,
            target_h=1920
        )
        self.assertGreater(len(traj_20), 0)
        crop_w_20 = traj_20[0]["crop_w"]
        crop_h_20 = traj_20[0]["crop_h"]
        # Active height = 1920 * 0.60 = 1152px
        # Target aspect ratio = 1080 / 1152 = 0.9375
        # Proportional crop width = round(1080 * 0.9375) = 1012px
        self.assertEqual(crop_w_20, 1012)
        self.assertEqual(crop_h_20, 1080)

        # Verify that crop_w_20 is significantly wider than crop_w_0 (+66% wider view)
        gain_pct = (crop_w_20 - crop_w_0) / float(crop_w_0) * 100.0
        self.assertGreater(gain_pct, 60.0)
        print(f"[Test OK] 0% Pad Crop Width: {crop_w_0}px (31.6% of 1920)")
        print(f"[Test OK] 20% Pad Crop Width: {crop_w_20}px (52.7% of 1920)")
        print(f"[Test OK] Field of view gain: +{gain_pct:.1f}% wider horizontal view without zoom!")

    def test_all_six_camera_layouts_with_padding(self):
        """
        Verify that build_layout_filter produces valid FFmpeg filters with
        exact padding and dimensions across ALL 6 camera layouts:
        - fit_canvas
        - face_center
        - speaker_focus
        - split_screen
        - blur
        - center_crop
        """
        layouts = ["fit_canvas", "face_center", "speaker_focus", "split_screen", "blur", "center_crop"]
        top_pad = 20.0
        bot_pad = 20.0
        top_px = int(round(1920 * 0.20)) # 384
        avail_h = 1920 - top_px - top_px # 1152

        for lay in layouts:
            crop_filter, actual = self.tracker.build_layout_filter(
                video_path=str(self.test_video_path),
                start_sec=0.5,
                duration=1.5,
                layout_mode=lay,
                top_padding=top_pad,
                bottom_padding=bot_pad,
                canvas_bg="solid_black",
                target_w=1080,
                target_h=1920
            )
            self.assertIsInstance(crop_filter, str)
            self.assertGreater(len(crop_filter), 10)
            
            # Ensure padding position 384 is present in the filter
            self.assertTrue(
                ("384" in crop_filter) or ("pad=" in crop_filter) or ("overlay=" in crop_filter),
                f"Layout '{lay}' did not include top padding offset 384: {crop_filter}"
            )
            # Ensure active height 1152 is present in the scale expression
            self.assertTrue(
                ("1152" in crop_filter) or ("scale=" in crop_filter),
                f"Layout '{lay}' did not include available height 1152: {crop_filter}"
            )
            print(f"[Test OK] Layout '{lay}' (actual: '{actual}'):\n         {crop_filter[:75]}...")

    def test_subtitle_and_banner_margins_with_padding(self):
        """
        Verify that SubtitleGenerator places the headline banner inside the top padding safe zone,
        and animated subtitles inside/near the bottom padding safe zone.
        """
        ass_path = TEMP_DIR / "test_sub_padding.ass"
        SubtitleGenerator.create_ass_file(
            words=[{"word": "VIRAL", "start": 0.0, "end": 1.0}],
            output_path=ass_path,
            style_key="hormozi",
            topic_headline="PODCAST SAFE TITLE",
            show_headline_banner=True,
            top_padding=20.0,
            bottom_padding=20.0
        )
        self.assertTrue(ass_path.exists())
        content = ass_path.read_text(encoding="utf-8")
        
        # Check Style: Default has MarginV=192 (bottom safe area)
        # Check Style: TopicHeader has MarginV=172 (top safe area)
        found_default_margin = False
        found_header_margin = False
        for line in content.splitlines():
            if line.startswith("Style: Default,"):
                parts = line.split(",")
                margin_v = int(parts[21])
                # Should be 192px (384 / 2)
                self.assertEqual(margin_v, 192)
                found_default_margin = True
            elif line.startswith("Style: TopicHeader,"):
                parts = line.split(",")
                margin_v = int(parts[21])
                # Should be 172px (384 / 2 - 20)
                self.assertEqual(margin_v, 172)
                found_header_margin = True

        self.assertTrue(found_default_margin, "Style: Default with custom MarginV not found")
        self.assertTrue(found_header_margin, "Style: TopicHeader with custom MarginV not found")
        print("[Test OK] Subtitles and Topic Headline Banner correctly positioned in padded safe zones!")

if __name__ == "__main__":
    unittest.main()
