import os
import sys
from pathlib import Path
from PIL import Image

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from core.thumbnail_designer import TikTokThumbnailDesigner
from core.config import OUTPUTS_DIR
from fastapi.testclient import TestClient
from app import app

def test_styles_and_archetypes():
    print("Testing TikTok Thumbnail Designer styles & archetypes...")
    vid_candidates = list(OUTPUTS_DIR.glob("*.mp4"))
    if not vid_candidates:
        # Fallback to temp dir
        from core.config import TEMP_DIR
        vid_candidates = list(TEMP_DIR.glob("*.mp4"))
    assert vid_candidates, "At least one sample MP4 must exist for testing"
    vid_path = vid_candidates[0]

    styles = ["hormozi", "tiktok_native", "podcast_authority", "red_alert"]
    archetypes = ["curiosity", "warning", "formula", "callout"]

    for st in styles:
        out_jpg = OUTPUTS_DIR / f"test_verify_{st}.jpg"
        p = TikTokThumbnailDesigner.create_tiktok_thumbnail(
            video_path=str(vid_path),
            output_jpg_path=str(out_jpg),
            topic="MENTAL HEALTH BREAKDOWN",
            title="The Real Struggle",
            hook="What nobody tells you about healing",
            style=st,
            accent_color="#22C55E" if st == "tiktok_native" else "#FFE600",
            archetype="warning" if st == "red_alert" else "curiosity",
            timestamp_sec=1.5
        )
        assert p.exists(), f"Thumbnail for style {st} must exist"
        with Image.open(p) as img:
            w, h = img.size
            assert w == 1080 and h == 1920, f"Expected 1080x1920, got {w}x{h}"
        print(f"  -> Style '{st}' generated cleanly (1080x1920)")

    # Test copy generator with all 4 archetypes
    for arch in archetypes:
        copy = TikTokThumbnailDesigner.generate_ai_copy(
            topic="PRODUCTIVITY SECRETS",
            title="How Top 1% Work",
            hook="The 3 rules of deep work",
            archetype=arch
        )
        assert "headline_1" in copy and "headline_2" in copy
        assert len(copy["headline_1"]) > 0 and len(copy["headline_2"]) > 0
        print(f"  -> Archetype '{arch}' produced: '{copy['headline_1']} {copy['headline_2']}'")

def test_api_endpoints():
    print("Testing FastAPI Thumbnail endpoints...")
    client = TestClient(app)
    from core.history_manager import HistoryManager
    projects = HistoryManager.get_all_projects()
    clip_id = projects[0]['clips'][0]['id'] if (projects and projects[0].get('clips')) else "test_clip_1"

    # 1. Generate viral hook options
    r1 = client.post(f"/api/clips/{clip_id}/thumbnail/generate-hooks", json={
        "topic": "PRODUCTIVITY HACKS",
        "hook": "Stop wasting hours"
    })
    assert r1.status_code == 200
    d1 = r1.json()
    assert d1.get("status") == "success"
    assert len(d1.get("hooks", [])) == 4
    print("  -> /api/clips/{id}/thumbnail/generate-hooks: PASSED (returned 4 archetypes)")

    # 2. Regenerate thumbnail with custom style & copy
    r2 = client.post(f"/api/clips/{clip_id}/thumbnail/regenerate", json={
        "topic": "DEEP WORK",
        "category": "FOCUS PROTOCOL",
        "headline_1": "HOW THE TOP 1%",
        "headline_2": "ACTUALLY WORK",
        "subheadline": "The daily focus routine",
        "style": "editorial_premium",
        "accent_color": "#FFE600",
        "timestamp_sec": 2.0
    })
    assert r2.status_code == 200
    d2 = r2.json()
    assert d2.get("status") == "success"
    assert "thumbnail_url" in d2
    assert d2.get("style") == "editorial_premium"
    print("  -> /api/clips/{id}/thumbnail/regenerate: PASSED")

if __name__ == "__main__":
    test_styles_and_archetypes()
    test_api_endpoints()
    print("\nALL TIKTOK THUMBNAIL UI & ENGINE TESTS PASSED! 🚀")
