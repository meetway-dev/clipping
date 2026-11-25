"""
Test Suite for Episode Multi-Clip Timeline Studio Editor
Verifies:
1. GET /api/projects/{id}: Retrieves project details, clips, and transcript segments.
2. GET /api/projects/{id}/source-video: Streams source video with byte-range support.
3. POST /api/projects/{id}/apply-timeline-edits: Re-renders vertical clips from source video,
   generates 3 viral thumbnails & docs per clip, replaces old clips in DB.
4. GET /api/projects/{id}/download-zip: Packages newly edited clips in topic folders with thumbnails & docs.
"""

import sys
import os
import io
import json
import zipfile
import unittest
import sqlite3
from pathlib import Path
from fastapi.testclient import TestClient

root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))

from app import app, OUTPUTS_DIR, TEMP_DIR, UPLOADS_DIR
from core.history_manager import HistoryManager

client = TestClient(app)

class TestTimelineEditor(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        HistoryManager.init_db()
        OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
        TEMP_DIR.mkdir(parents=True, exist_ok=True)

        cls.test_vid = root_dir / "storage" / "uploads" / "yt_uslV_dz6APY.mp4"
        assert cls.test_vid.exists(), f"Source test video not found at {cls.test_vid}"

        cls.project_id = "test_timeline_project_1"
        HistoryManager.delete_project(cls.project_id)
        # Seed test project with 1 initial clip
        HistoryManager.save_project_with_clips(
            project_id=cls.project_id,
            title="Podcast on Health & Statins",
            source_type="upload",
            source_identifier="yt_uslV_dz6APY.mp4",
            thumbnail_url="/media/test.jpg",
            duration=666.85,
            source_video=str(cls.test_vid),
            clips=[
                {
                    "id": "old_clip_1",
                    "filename": "old_clip.mp4",
                    "title": "Old Clip 1",
                    "hook": "OLD HOOK",
                    "start": 0.0,
                    "end": 30.0,
                    "duration": 30.0
                }
            ],
            transcript_segments=[
                {"start": 0.0, "end": 15.0, "text": "Statins are widely prescribed for cholesterol."},
                {"start": 15.0, "end": 35.0, "text": "However there is controversy around diabetes risk."},
                {"start": 35.0, "end": 60.0, "text": "Let us examine the clinical trials."}
            ]
        )

    def test_01_get_project_details(self):
        """Verify GET /api/projects/{id} returns project with clips and segments."""
        resp = client.get(f"/api/projects/{self.project_id}")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["id"], self.project_id)
        self.assertEqual(data["title"], "Podcast on Health & Statins")
        self.assertEqual(len(data["clips"]), 1)
        self.assertTrue(len(data.get("transcript_segments", [])) >= 3)
        self.assertTrue(data.get("source_video"))

    def test_02_stream_source_video(self):
        """Verify GET /api/projects/{id}/source-video serves video with Range support."""
        resp = client.get(
            f"/api/projects/{self.project_id}/source-video",
            headers={"Range": "bytes=0-1024"}
        )
        self.assertIn(resp.status_code, [200, 206])
        self.assertEqual(resp.headers.get("content-type"), "video/mp4")
        self.assertTrue(len(resp.content) > 0)

    def test_03_source_directory_falls_back_to_real_file(self):
        """A directory stored as source_video must not be passed to FileResponse."""
        db_path = root_dir / "storage" / "clipforge.db"
        with sqlite3.connect(db_path) as conn:
            conn.execute(
                "UPDATE projects SET source_video = ? WHERE id = ?",
                (str(OUTPUTS_DIR), self.project_id)
            )

        try:
            resp = client.get(
                f"/api/projects/{self.project_id}/source-video",
                headers={"Range": "bytes=0-1024"}
            )
            self.assertIn(resp.status_code, [200, 206])
            self.assertEqual(resp.headers.get("content-type"), "video/mp4")
            self.assertTrue(len(resp.content) > 0)
        finally:
            with sqlite3.connect(db_path) as conn:
                conn.execute(
                    "UPDATE projects SET source_video = ? WHERE id = ?",
                    (str(self.test_vid), self.project_id)
                )

    def test_04_apply_timeline_edits(self):
        """
        Verify POST /api/projects/{id}/apply-timeline-edits renders 2 adjusted clips,
        produces 3 viral thumbnails & docs each, and updates the database.
        """
        payload = {
            "clips": [
                {
                    "id": "edited_clip_1",
                    "start": 5.0,
                    "end": 10.0,
                    "title": "Statin Myths Debunked",
                    "hook": "THE STATIN TRUTH",
                    "subtitle_style": "hormozi",
                    "layout_mode": "speaker_focus"
                },
                {
                    "id": "edited_clip_2",
                    "start": 18.0,
                    "end": 23.0,
                    "title": "Diabetes and Cholesterol",
                    "hook": "DO NOT IGNORE THIS",
                    "subtitle_style": "hype",
                    "layout_mode": "fit_canvas"
                }
            ]
        }

        resp = client.post(f"/api/projects/{self.project_id}/apply-timeline-edits", json=payload)
        self.assertEqual(resp.status_code, 200, f"Error: {resp.text}")
        data = resp.json()
        self.assertEqual(data["status"], "success")

        updated_project = data["project"]
        self.assertEqual(updated_project["clip_count"], 2)
        self.assertEqual(len(updated_project["clips"]), 2)

        # Verify both clips exist in DB and on disk
        for c in updated_project["clips"]:
            self.assertIn(c["title"], ["Statin Myths Debunked", "Diabetes and Cholesterol"])
            folder_name = c.get("folder_name")
            self.assertTrue(folder_name)
            clip_folder = OUTPUTS_DIR / folder_name
            self.assertTrue(clip_folder.exists(), f"Folder {clip_folder} not found")

            # Check 3 distinct viral thumbnails inside clip folder
            curiosity_thumb = list(clip_folder.glob("*_thumb_1.jpg"))
            warning_thumb = list(clip_folder.glob("*_thumb_2.jpg"))
            authority_thumb = list(clip_folder.glob("*_thumb_3.jpg"))
            self.assertTrue(len(curiosity_thumb) > 0, "Curiosity thumbnail missing")
            self.assertTrue(len(warning_thumb) > 0, "Warning thumbnail missing")
            self.assertTrue(len(authority_thumb) > 0, "Authority thumbnail missing")

            # Check docs files
            docx_files = list(clip_folder.glob("*_docs.docx"))
            self.assertTrue(len(docx_files) > 0, "Docx file missing")

    def test_05_save_and_restore_editor_state(self):
        """Verify normalized editor state is persisted and returned unchanged."""
        payload = {
            "editor_project": {
                "projectId": self.project_id,
                "title": "Podcast on Health & Statins",
                "fps": 29.97,
                "width": 1080,
                "height": 1920,
                "durationFrames": 19974,
                "tracks": [
                    {"id": "video-main", "type": "video", "name": "Main Video", "clips": []},
                    {"id": "text-main", "type": "text", "name": "Text", "clips": []}
                ],
                "clips": [{"id": "clip-a", "start": 5.0, "end": 10.0}],
                "settings": {"aspectRatio": "9:16", "resolution": "1080x1920"}
            }
        }
        resp = client.post(f"/api/projects/{self.project_id}/editor-state", json=payload)
        self.assertEqual(resp.status_code, 200, f"Error: {resp.text}")
        data = resp.json()
        self.assertEqual(data["status"], "success")

        restored = client.get(f"/api/projects/{self.project_id}")
        self.assertEqual(restored.status_code, 200)
        editor = restored.json()["editor_project"]
        self.assertEqual(editor["fps"], 29.97)
        self.assertEqual(editor["width"], 1080)
        self.assertEqual(len(editor["tracks"]), 2)
        self.assertEqual(editor["clips"][0]["id"], "clip-a")

    def test_06_download_project_zip_with_edited_clips(self):
        """Verify ZIP download organizes newly edited clips in topic folders."""
        resp = client.get(f"/api/projects/{self.project_id}/download-zip")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.headers.get("content-type"), "application/zip")

        # Inspect ZIP archive contents
        with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
            namelist = zf.namelist()
            self.assertTrue(any("Statin_Myths" in name for name in namelist))
            self.assertTrue(any("Diabetes_and_Cholesterol" in name for name in namelist))
            self.assertTrue(any("docs" in name.lower() for name in namelist))
            self.assertTrue(any("_thumb_1" in name for name in namelist))

if __name__ == "__main__":
    unittest.main()
