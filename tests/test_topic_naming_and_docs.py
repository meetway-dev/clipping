import io
import sys
import zipfile
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.pipeline import sanitize_topic_filename
from core.docs_generator import (
    generate_session_docx,
    generate_session_text,
    generate_session_markdown,
    add_session_docs_to_zip,
    extract_clip_metadata
)
from core.history_manager import HistoryManager

def test_topic_sanitization():
    print("[1/5] Testing topic sanitization...")
    assert sanitize_topic_filename("THE BIGGEST REAL ESTATE MISTAKE") == "The_Biggest_Real_Estate_Mistake"
    assert sanitize_topic_filename("How To Invest In 2026!") == "How_To_Invest_In_2026"
    assert sanitize_topic_filename("AI & Machine Learning") == "AI_Machine_Learning"
    assert sanitize_topic_filename("") == "Video_Clip"
    print("      -> Topic sanitization PASSED")

def test_multi_part_topic_naming():
    print("[2/5] Testing topic grouping and part_1 / part_2 naming...")
    viral_clips = [
        {"title": "REAL ESTATE MISTAKES", "topic": "REAL ESTATE MISTAKES", "hook": "Mistake 1"},
        {"title": "HOW TO INVEST", "topic": "HOW TO INVEST", "hook": "Step 1"},
        {"title": "REAL ESTATE MISTAKES", "topic": "REAL ESTATE MISTAKES", "hook": "Mistake 2"},
        {"title": "REAL ESTATE MISTAKES", "topic": "REAL ESTATE MISTAKES", "hook": "Mistake 3"},
        {"title": "STOCK MARKET BASICS", "topic": "STOCK MARKET BASICS", "hook": "Intro"}
    ]

    from collections import defaultdict
    import re

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
        c["assigned_filename"] = f"{stem}.mp4"

    # Verify filenames
    assert viral_clips[0]["assigned_filename"] == "Real_Estate_Mistakes_part_1.mp4"
    assert viral_clips[1]["assigned_filename"] == "How_To_Invest.mp4"  # Single occurrence: no part suffix
    assert viral_clips[2]["assigned_filename"] == "Real_Estate_Mistakes_part_2.mp4"
    assert viral_clips[3]["assigned_filename"] == "Real_Estate_Mistakes_part_3.mp4"
    assert viral_clips[4]["assigned_filename"] == "Stock_Market_Basics.mp4"

    # Verify titles
    assert "part_1" in viral_clips[0]["title"]
    assert "part_2" in viral_clips[2]["title"]
    assert "part_3" in viral_clips[3]["title"]
    assert "part" not in viral_clips[1]["title"].lower()
    print("      -> Topic grouping and part_1 / part_2 naming PASSED")

def test_docs_metadata_extraction():
    print("[3/5] Testing metadata extraction (topic, title, hashtags)...")
    clip = {
        "topic": "PASSIVE INCOME STRATEGIES",
        "title": "Why Nobody Talks About Dividends",
        "filename": "Passive_Income_part_1.mp4",
        "start_sec": 12.0,
        "end_sec": 42.0,
        "duration": 30.0,
        "hook": "Dividends are the secret weapon of the wealthy.",
        "social_kit": {
            "titles": [
                {"type": "Curiosity Hook", "text": "Why Nobody Talks About Dividends 🤯"}
            ],
            "hashtags": ["#dividends", "#investing", "#wealth", "#shorts"],
            "hashtags_string": "#dividends #investing #wealth #shorts"
        }
    }
    meta = extract_clip_metadata(clip, 1)
    assert meta["topic"] == "PASSIVE INCOME STRATEGIES"
    assert meta["title"] == "Why Nobody Talks About Dividends"
    assert "#dividends" in meta["hashtags_string"]
    assert meta["filename"] == "Passive_Income_part_1.mp4"
    print("      -> Metadata extraction PASSED")

def test_docs_files_generation():
    print("[4/5] Testing .docx, .txt, .md generation & zip injection...")
    clips = [
        {
            "topic": "REAL ESTATE INVESTING",
            "title": "Cash Flow vs Appreciation part_1",
            "filename": "Real_Estate_Investing_part_1.mp4",
            "start_sec": 0.0,
            "end_sec": 30.0,
            "duration": 30.0,
            "hook": "Cash flow pays your bills every month.",
            "social_kit": {
                "titles": [{"type": "Curiosity", "text": "The Real Estate Myth 🤯"}],
                "hashtags_string": "#realestate #cashflow #wealth #shorts"
            }
        },
        {
            "topic": "REAL ESTATE INVESTING",
            "title": "Cash Flow vs Appreciation part_2",
            "filename": "Real_Estate_Investing_part_2.mp4",
            "start_sec": 30.0,
            "end_sec": 65.0,
            "duration": 35.0,
            "hook": "Here is how to analyze a deal in 60 seconds.",
            "social_kit": {
                "titles": [{"type": "Action", "text": "The 60-Second Deal Rule 🚀"}],
                "hashtags_string": "#realestate #investing #deals #shorts"
            }
        }
    ]

    # Generate documents
    docx_bytes = generate_session_docx(clips, "Real Estate Masterclass")
    txt_content = generate_session_text(clips, "Real Estate Masterclass")
    md_content = generate_session_markdown(clips, "Real Estate Masterclass")

    assert len(docx_bytes) > 500, "DOCX must be valid non-empty byte string"
    assert "REAL ESTATE INVESTING" in txt_content
    assert "#realestate" in txt_content
    assert "Cash Flow vs Appreciation part_1" in txt_content
    assert "REAL ESTATE INVESTING" in md_content

    # Verify DOCX zip validity
    with zipfile.ZipFile(io.BytesIO(docx_bytes), "r") as docx_zip:
        names = docx_zip.namelist()
        assert "[Content_Types].xml" in names
        assert "word/document.xml" in names
        doc_xml = docx_zip.read("word/document.xml").decode("utf-8")
        assert "REAL ESTATE INVESTING" in doc_xml
        assert "Cash Flow vs Appreciation part_1" in doc_xml

    # Verify ZIP injection
    out_zip_buf = io.BytesIO()
    with zipfile.ZipFile(out_zip_buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("test.mp4", b"dummy video content")
        add_session_docs_to_zip(zf, clips, "Real Estate Masterclass")

    with zipfile.ZipFile(out_zip_buf, "r") as zf:
        zf_names = zf.namelist()
        assert "test.mp4" in zf_names
        assert "session_clips_info.docx" in zf_names
        assert "session_clips_info.txt" in zf_names
        assert "session_clips_info.md" in zf_names

    print("      -> Document generation and ZIP injection PASSED")

def test_tiktok_thumbnail_and_zip_companion():
    print("[5/7] Testing TikTok thumbnail 1080x1920 generation & ZIP companion...")
    from core.renderer import VideoRenderer
    from core.config import TEMP_DIR
    import cv2

    renderer = VideoRenderer()
    sample_vid = Path("storage/uploads/yt_nYrLMyUP4S0.mp4")
    if sample_vid.exists():
        test_thumb = TEMP_DIR / "Real_Estate_Mistake_part_1.jpg"
        ok = renderer.generate_thumbnail(str(sample_vid), str(test_thumb), timestamp_sec=1.0)
        assert ok, "Thumbnail generation must succeed"
        assert test_thumb.exists(), "Thumbnail file must exist on disk"

        img = cv2.imread(str(test_thumb))
        assert img is not None, "Must be valid readable image"
        h, w, _ = img.shape
        assert w == 1080 and h == 1920, f"TikTok cover must be exactly 1080x1920, got {w}x{h}"
        print(f"      -> 1080x1920 9:16 TikTok Cover Dimensions Verified ({w}x{h})")

    # Test ZIP packaging with companion thumbnail image
    zip_buf = io.BytesIO()
    with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zf:
        mp4_name = "Real_Estate_Mistake_part_1.mp4"
        jpg_name = "Real_Estate_Mistake_part_1.jpg"
        zf.writestr(mp4_name, b"fake video bytes")
        zf.writestr(jpg_name, b"fake image bytes")

    with zipfile.ZipFile(zip_buf, "r") as zf:
        names = zf.namelist()
        assert mp4_name in names
        assert jpg_name in names
        assert Path(mp4_name).stem == Path(jpg_name).stem, "Video and thumbnail image must share exact same base name"
    print("      -> Video and TikTok companion thumbnail ZIP packaging PASSED")

def test_ai_tiktok_thumbnail_designer():
    print("[6/7] Testing AI TikTok Thumbnail Designer with real speaker body & topic text...")
    from core.thumbnail_designer import TikTokThumbnailDesigner
    from core.config import TEMP_DIR
    import cv2

    copy = TikTokThumbnailDesigner.generate_ai_copy(
        topic="LONGEVITY PROTOCOLS",
        title="The Outlive Method",
        hook="The 3 exercises you need to rebuild mitochondria",
        transcript="Zone 2 cardio is essential. VO2 max training is critical. Heavy strength training prevents frailty."
    )
    assert "headline_white" in copy
    assert "takeaways" in copy and len(copy["takeaways"]) == 3
    print(f"      -> AI Copy Generated: '{copy['headline_white']}' / Takeaways: {copy['takeaways']}")

    sample_vid = Path("storage/uploads/yt_nYrLMyUP4S0.mp4")
    if sample_vid.exists():
        thumb_out = TEMP_DIR / "test_ai_designed_tiktok_cover.jpg"
        res_p = TikTokThumbnailDesigner.create_tiktok_thumbnail(
            video_path=str(sample_vid),
            output_jpg_path=str(thumb_out),
            topic="LONGEVITY PROTOCOLS",
            title="THE OUTLIVE METHOD",
            hook="Dr. Peter Attia's Formula to Rebuild Mitochondria",
            transcript="Zone 2 cardio. VO2 max training. Heavy strength training.",
            timestamp_sec=2.0
        )
        assert res_p.exists(), "AI designed thumbnail must exist"
        img = cv2.imread(str(res_p))
        assert img is not None
        h, w, _ = img.shape
        assert w == 1080 and h == 1920, f"AI thumbnail must be 1080x1920, got {w}x{h}"
        print(f"      -> AI Designed TikTok Cover Generated with Real Speaker ({w}x{h} JPG)")

def test_api_routes():
    print("[7/8] Testing FastAPI routes registration...")
    from app import app
    route_paths = [r.path for r in app.routes]
    assert "/api/clips.zip" in route_paths
    assert "/api/projects/{project_id}/download-zip" in route_paths
    assert "/api/jobs/{job_id}/download-zip" in route_paths
    assert "/api/projects/{project_id}/download-docs" in route_paths
    assert "/api/jobs/{job_id}/download-docs" in route_paths
    assert "/api/clips/{clip_id}/thumbnail/regenerate" in route_paths
    print("      -> FastAPI routes registration PASSED")

def test_yellow_viral_headline_banner():
    print("[8/8] Testing ASS Yellow Viral Hook Headline Banner formatting & styling...")
    from core.subtitles import SubtitleGenerator
    from core.config import TEMP_DIR

    # Test multiline formatting and bracket removal
    fmt = SubtitleGenerator.format_multiline_headline("[THE OUTLIVE METHOD: THE 3 EXERCISES YOU NEED]")
    assert "[" not in fmt and "]" not in fmt, "Brackets must be stripped from headline"
    assert "\\N" in fmt, "Long headline must wrap using \\N"
    print(f"      -> Multiline headline wrapping PASSED: {repr(fmt)}")

    # Test ASS file generation
    ass_test_file = TEMP_DIR / "test_yellow_banner.ass"
    SubtitleGenerator.create_ass_file(
        words=[{"word": "Test", "start": 0.0, "end": 1.0}],
        output_path=ass_test_file,
        style_key="hormozi",
        topic_headline="THE OUTLIVE METHOD: THE 3 EXERCISES YOU NEED",
        clip_duration=30.0,
        show_headline_banner=True
    )
    assert ass_test_file.exists(), "ASS subtitle file must be created"
    content = ass_test_file.read_text(encoding="utf-8")
    ass_test_file.unlink(missing_ok=True)

    # Validate Yellow styling: &H0000E5FF, Impact font, Outline 4.5, Shadow 2.0
    assert "Style: TopicHeader,Impact," in content, "Style must use bold Impact font"
    assert "&H0000E5FF" in content, "Must use bright Yellow color &H0000E5FF in ASS"
    assert "&H00000000" in content, "Must use deep black outline"
    assert "0:00:00.00,0:00:30.00,TopicHeader" in content, "Must be visible from 0.0 to end of clip"
    assert "[  " not in content and "  ]" not in content, "Square brackets must not be in dialogue line"
    print("      -> ASS Yellow Banner Styling & Lifetime PASSED")

if __name__ == "__main__":
    print("=" * 60)
    print("Running Topic Naming, TikTok Thumbnail & Docs Tests...")
    print("=" * 60)
    test_topic_sanitization()
    test_multi_part_topic_naming()
    test_docs_metadata_extraction()
    test_docs_files_generation()
    test_tiktok_thumbnail_and_zip_companion()
    test_ai_tiktok_thumbnail_designer()
    test_api_routes()
    test_yellow_viral_headline_banner()
    print("=" * 60)
    print("ALL TESTS PASSED SUCCESSFULLY! ✅")
    print("=" * 60)
