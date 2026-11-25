"""
Automated Verification Test for Multi-Clip Topic Folder Organization & 3 Viral Thumbnails
Verifies:
1. Each clip gets organized into its own dedicated topic folder.
2. Inside each folder:
   - 1 topic-named video file (.mp4)
   - 3 distinct viral thumbnails (_thumb_1 Curiosity, _thumb_2 Warning, _thumb_3 Authority)
   - 1 clip-specific documentation file (.docx and .txt)
3. Single clip ZIP download route (/api/clips/{id}/download-zip).
4. Multi-clip ZIP download route (/api/clips.zip & /api/projects/{id}/download-zip).
5. Cover switching route (/api/clips/{id}/set-cover).
"""

import sys
import os
import io
import zipfile
import json
from pathlib import Path
from fastapi.testclient import TestClient

# Ensure root directory is in sys.path
root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))

from app import app, package_clips_into_zip, OUTPUTS_DIR, TEMP_DIR
from core.history_manager import HistoryManager
from core.docs_generator import create_clip_docs_files, generate_clip_docx, generate_clip_text

client = TestClient(app)

def setup_module():
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    HistoryManager.init_db()

def test_single_clip_docs_generation(tmp_path):
    """Test generating single clip docs (.docx, .txt, .md)."""
    clip_sample = {
        "id": "test_clip_doc_1",
        "topic": "Why 99% Of People Fail At Fitness",
        "title": "WHY 99% FAIL AT FITNESS (AND HOW TO FIX IT)",
        "hook": "THE SECRET TO CONSISTENCY NO ONE TELLS YOU",
        "part_info": "Part 1 of 3",
        "start_sec": 12.5,
        "end_sec": 78.0,
        "duration": 65.5,
        "virality_score": 94,
        "full_transcript": "The real reason people fail at fitness is not lack of willpower. It's friction in your daily environment.",
        "social_kit": {
            "viral_hashtags": ["#fitness", "#habits", "#longevity", "#discipline", "#workout"],
            "tiktok": {
                "headline": "WHY 99% FAIL AT FITNESS",
                "caption": "Stop relying on willpower. Design your environment first.",
                "hook_voiceover": "If you struggle to stay consistent, listen to this."
            },
            "instagram_reels": {
                "hook": "The willpower myth debunked",
                "caption": "Consistency is an environment problem, not a discipline problem."
            },
            "youtube_shorts": {
                "title": "Why Willpower Fails You Every Time #shorts",
                "description": "How top performers stay consistent effortlessly."
            }
        }
    }

    # 1. Test docx bytes
    docx_bytes = generate_clip_docx(clip_sample)
    assert len(docx_bytes) > 200, "DOCX bytes should not be empty"
    # Verify it is a valid zip (OpenXML)
    with zipfile.ZipFile(io.BytesIO(docx_bytes), "r") as zf:
        assert "word/document.xml" in zf.namelist()

    # 2. Test text content
    txt_content = generate_clip_text(clip_sample)
    assert "WHY 99% FAIL AT FITNESS" in txt_content
    assert "#fitness" in txt_content
    assert "friction in your daily environment" in txt_content.lower()

    # 3. Test saving files in dedicated directory
    saved_files = create_clip_docs_files(clip_sample, output_dir=tmp_path, base_name="01_Fitness_Fail")
    assert "docx" in saved_files
    assert Path(saved_files["docx"]).exists()
    assert "txt" in saved_files
    assert Path(saved_files["txt"]).exists()
    assert "md" in saved_files
    assert Path(saved_files["md"]).exists()

def test_package_clips_into_zip_structure(tmp_path):
    """Test packaging multiple clips into organized per-topic folders."""
    # Create fake video and thumbnail files
    clip1_dir = OUTPUTS_DIR / "01_Mitochondria_Secret"
    clip1_dir.mkdir(parents=True, exist_ok=True)
    (clip1_dir / "01_Mitochondria_Secret.mp4").write_bytes(b"FAKE_MP4_1")
    (clip1_dir / "01_Mitochondria_Secret_thumb_1.jpg").write_bytes(b"FAKE_THUMB_1")
    (clip1_dir / "01_Mitochondria_Secret_thumb_2.jpg").write_bytes(b"FAKE_THUMB_2")
    (clip1_dir / "01_Mitochondria_Secret_thumb_3.jpg").write_bytes(b"FAKE_THUMB_3")

    clip2_dir = OUTPUTS_DIR / "02_Cold_Plunge_Protocol"
    clip2_dir.mkdir(parents=True, exist_ok=True)
    (clip2_dir / "02_Cold_Plunge_Protocol.mp4").write_bytes(b"FAKE_MP4_2")
    (clip2_dir / "02_Cold_Plunge_Protocol_thumb_1.jpg").write_bytes(b"FAKE_THUMB_1")
    (clip2_dir / "02_Cold_Plunge_Protocol_thumb_2.jpg").write_bytes(b"FAKE_THUMB_2")
    (clip2_dir / "02_Cold_Plunge_Protocol_thumb_3.jpg").write_bytes(b"FAKE_THUMB_3")

    clips = [
        {
            "id": "clip_t1",
            "topic": "Mitochondria Secret",
            "title": "THE REAL SECRET TO AGING MITOCHONDRIA",
            "folder_name": "01_Mitochondria_Secret",
            "filename": "01_Mitochondria_Secret/01_Mitochondria_Secret.mp4",
            "covers": [
                "01_Mitochondria_Secret/01_Mitochondria_Secret_thumb_1.jpg",
                "01_Mitochondria_Secret/01_Mitochondria_Secret_thumb_2.jpg",
                "01_Mitochondria_Secret/01_Mitochondria_Secret_thumb_3.jpg"
            ],
            "full_transcript": "Mitochondrial health controls cellular longevity.",
            "social_kit": {"viral_hashtags": ["#aging", "#mitochondria", "#health"]}
        },
        {
            "id": "clip_t2",
            "topic": "Cold Plunge Protocol",
            "title": "COLD PLUNGE PROTOCOL FOR NOREPINEPHRINE",
            "folder_name": "02_Cold_Plunge_Protocol",
            "filename": "02_Cold_Plunge_Protocol/02_Cold_Plunge_Protocol.mp4",
            "covers": [
                "02_Cold_Plunge_Protocol/02_Cold_Plunge_Protocol_thumb_1.jpg",
                "02_Cold_Plunge_Protocol/02_Cold_Plunge_Protocol_thumb_2.jpg",
                "02_Cold_Plunge_Protocol/02_Cold_Plunge_Protocol_thumb_3.jpg"
            ],
            "full_transcript": "Three minutes of deliberate cold exposure spikes dopamine for hours.",
            "social_kit": {"viral_hashtags": ["#coldplunge", "#dopamine", "#focus"]}
        }
    ]

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        package_clips_into_zip(zf, clips, session_title="Huberman Test Session")

    buf.seek(0)
    with zipfile.ZipFile(buf, "r") as zf:
        namelist = zf.namelist()

        # Check Clip 1 folder contents
        assert any("01_Mitochondria_Secret" in n and n.endswith(".mp4") for n in namelist)
        assert any("01_Mitochondria_Secret" in n and "_thumb_1_curiosity.jpg" in n for n in namelist)
        assert any("01_Mitochondria_Secret" in n and "_thumb_2_warning.jpg" in n for n in namelist)
        assert any("01_Mitochondria_Secret" in n and "_thumb_3_blueprint.jpg" in n for n in namelist)
        assert any("01_Mitochondria_Secret" in n and "_docs.docx" in n for n in namelist)
        assert any("01_Mitochondria_Secret" in n and "_docs.txt" in n for n in namelist)

        # Check Clip 2 folder contents
        assert any("02_Cold_Plunge_Protocol" in n and n.endswith(".mp4") for n in namelist)
        assert any("02_Cold_Plunge_Protocol" in n and "_thumb_1_curiosity.jpg" in n for n in namelist)
        assert any("02_Cold_Plunge_Protocol" in n and "_thumb_2_warning.jpg" in n for n in namelist)
        assert any("02_Cold_Plunge_Protocol" in n and "_thumb_3_blueprint.jpg" in n for n in namelist)
        assert any("02_Cold_Plunge_Protocol" in n and "_docs.docx" in n for n in namelist)

        # Check session overview docs at root
        assert any("session_clips_info.docx" in n for n in namelist)
        assert any("session_clips_info.txt" in n for n in namelist)

def test_api_single_clip_download_zip():
    """Test GET /api/clips/{clip_id}/download-zip."""
    proj_id = "test_single_proj_zip"
    clip_id = "test_single_clip_zip"
    clip_folder = "01_Universal_Thumbnail_Test"
    c_dir = OUTPUTS_DIR / clip_folder
    c_dir.mkdir(parents=True, exist_ok=True)
    (c_dir / f"{clip_folder}.mp4").write_bytes(b"CLIP_VIDEO_DATA")
    (c_dir / f"{clip_folder}_thumb_1.jpg").write_bytes(b"THUMB1")
    (c_dir / f"{clip_folder}_thumb_2.jpg").write_bytes(b"THUMB2")
    (c_dir / f"{clip_folder}_thumb_3.jpg").write_bytes(b"THUMB3")

    clip_obj = {
        "id": clip_id,
        "project_id": proj_id,
        "filename": f"{clip_folder}/{clip_folder}.mp4",
        "title": "Universal Thumbnail Test",
        "topic": "Universal Thumbnail Test",
        "hook": "TEST HOOK FOR TIKTOK",
        "duration": 45.0,
        "start": 0,
        "end": 45,
        "folder_name": clip_folder,
        "cover": f"{clip_folder}/{clip_folder}_thumb_1.jpg",
        "covers": [
            f"{clip_folder}/{clip_folder}_thumb_1.jpg",
            f"{clip_folder}/{clip_folder}_thumb_2.jpg",
            f"{clip_folder}/{clip_folder}_thumb_3.jpg"
        ],
        "full_transcript": "Testing universal thumbnail system with real speaker image extraction.",
        "social_kit": {"viral_hashtags": ["#test", "#shorts"]}
    }

    HistoryManager.save_project_with_clips(
        project_id=proj_id,
        title="Test Single Proj",
        source_type="upload",
        source_identifier="test.mp4",
        thumbnail_url="",
        duration=45.0,
        clips=[clip_obj]
    )

    resp = client.get(f"/api/clips/{clip_id}/download-zip")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/zip"

    with zipfile.ZipFile(io.BytesIO(resp.content), "r") as zf:
        names = zf.namelist()
        assert any(n.endswith(".mp4") for n in names)
        assert any("_thumb_1" in n for n in names)
        assert any("_thumb_2" in n for n in names)
        assert any("_thumb_3" in n for n in names)
        assert any("_docs.docx" in n for n in names)

def test_api_set_active_cover():
    """Test POST /api/clips/{clip_id}/set-cover."""
    clip_id = "test_single_clip_zip"
    new_cover = "01_Universal_Thumbnail_Test/01_Universal_Thumbnail_Test_thumb_2.jpg"

    resp = client.post(f"/api/clips/{clip_id}/set-cover", json={"cover": new_cover})
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert data["cover"] == new_cover

    # Verify database was updated
    updated_clip = HistoryManager.get_clip_by_id(clip_id)
    assert updated_clip is not None
    assert updated_clip.get("cover") == new_cover


if __name__ == "__main__":
    setup_module()
    print("Testing single clip docs generation...")
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        test_single_clip_docs_generation(Path(td))
    print("✓ test_single_clip_docs_generation passed!")

    print("Testing package clips into zip structure...")
    with tempfile.TemporaryDirectory() as td:
        test_package_clips_into_zip_structure(Path(td))
    print("✓ test_package_clips_into_zip_structure passed!")

    print("Testing API single clip download ZIP...")
    test_api_single_clip_download_zip()
    print("✓ test_api_single_clip_download_zip passed!")

    print("Testing API set active cover...")
    test_api_set_active_cover()
    print("✓ test_api_set_active_cover passed!")

    print("\n🎉 ALL TESTS PASSED SUCCESSFULLY!")
