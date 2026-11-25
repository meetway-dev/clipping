import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from core.viral_detector import ViralDetector
from core.ollama_manager import OllamaManager
from fastapi.testclient import TestClient
from app import app

def test_ai_viral_research():
    print("[1/4] Testing AI Viral Research Engine...")
    detector = ViralDetector()

    mock_segments = [
        {"start": 0.0, "end": 15.0, "text": "Welcome to the podcast today we have a very special episode with an incredible guest."},
        {"start": 15.0, "end": 45.0, "text": "Do you know why most people fail to build wealth in their twenties? It is because they rely on motivation instead of discipline."},
        {"start": 45.0, "end": 80.0, "text": "Motivation is a feeling that fades after two days. But when you build daily habits, you never have to think about whether you feel like it or not."},
        {"start": 80.0, "end": 105.0, "text": "That is the brutal truth nobody wants to hear. Most people hate hearing this because it requires taking 100 percent responsibility."},
        {"start": 105.0, "end": 140.0, "text": "Years ago when I lost all my money in my first business, I remember sitting on the floor crying thinking everything was ruined."},
        {"start": 140.0, "end": 175.0, "text": "And in that exact moment, I realized that failure is not the opposite of success, failure is simply the price of entry."},
        {"start": 175.0, "end": 210.0, "text": "Here is the exact 3-step framework to master deep work and get more done in four hours than most do in a week."}
    ]

    # Test research by query
    res_wealth = detector.research_viral_clips(
        segments=mock_segments,
        query="build wealth and daily habits",
        archetype="all",
        min_seconds=30.0,
        max_seconds=90.0,
        top_k=3
    )
    assert len(res_wealth) >= 1, "Expected at least 1 clip matching wealth query"
    top_clip = res_wealth[0]
    print(f"  -> Discovered Query Clip: '{top_clip['title']}' ({top_clip['duration']}s, Score {top_clip['virality_score']})")
    assert "hook" in top_clip
    assert "narrative_breakdown" in top_clip
    assert top_clip["virality_score"] >= 70

    # Test research by archetype (story)
    res_story = detector.research_viral_clips(
        segments=mock_segments,
        query="",
        archetype="story",
        min_seconds=30.0,
        max_seconds=90.0,
        top_k=2
    )
    assert len(res_story) >= 1, "Expected story archetype clips"
    print(f"  -> Discovered Story Clip: '{res_story[0]['title']}' ({res_story[0]['archetype']})")
    print("      -> AI Viral Research Engine PASSED! ✅")

def test_ai_video_copilot():
    print("[2/4] Testing AI Video Edit Copilot...")
    ollama = OllamaManager.get_instance()

    mock_clip = {
        "title": "DAILY HABITS FOR SUCCESS",
        "hook": "Do you know why most people fail to build wealth in their twenties?",
        "full_transcript": "Do you know why most people fail to build wealth in their twenties? It is because they rely on motivation instead of discipline.",
        "subtitle_style": "hormozi",
        "layout_mode": "fit_canvas"
    }

    # Test natural language instructions
    edit1 = ollama.ai_edit_copilot(mock_clip, "Make headline controversial and use MrBeast style")
    assert "updated_title" in edit1
    assert "suggested_subtitle_style" in edit1
    assert edit1["suggested_subtitle_style"] == "hype"
    print(f"  -> Copilot Edit 1: '{edit1['updated_title']}' (Style: {edit1['suggested_subtitle_style']})")

    edit2 = ollama.ai_edit_copilot(mock_clip, "Focus on building wealth and money")
    assert "WEALTH" in edit2["updated_title"] or "MONEY" in edit2["updated_title"] or "INCOME" in edit2["updated_title"]
    print(f"  -> Copilot Edit 2: '{edit2['updated_title']}'")
    print("      -> AI Video Edit Copilot PASSED! ✅")

def test_social_distribution_kit():
    print("[3/4] Testing AI Social Distribution Kit...")
    ollama = OllamaManager.get_instance()

    kit = ollama.generate_social_distribution_kit(
        transcript="Motivation is a feeling that fades after two days. But when you build daily habits, you never have to think about whether you feel like it or not.",
        title="WHY 99% OF PEOPLE FAIL AT BUILDING WEALTH",
        hook="Do you know why most people fail in their twenties?"
    )

    assert "tiktok" in kit
    assert "instagram" in kit
    assert "youtube_shorts" in kit
    assert len(kit["tiktok"]["hashtags"]) >= 3
    print(f"  -> TikTok Caption: '{kit['tiktok']['caption'][:60]}...'")
    print(f"  -> Instagram Call to Action: '{kit['instagram']['call_to_action']}'")
    print(f"  -> YouTube Shorts Title: '{kit['youtube_shorts']['title']}'")
    print("      -> AI Social Distribution Kit PASSED! ✅")

def test_fastapi_endpoints():
    print("[4/4] Testing FastAPI Endpoints...")
    client = TestClient(app)

    # 1. Research clips endpoint
    r1 = client.post("/api/ai/research-clips", json={
        "query": "discipline and habits",
        "archetype": "all",
        "min_duration": 30.0,
        "max_duration": 90.0,
        "top_k": 3
    })
    assert r1.status_code == 200, f"Expected 200, got {r1.status_code}: {r1.text}"
    data1 = r1.json()
    assert data1["status"] == "success"
    print(f"  -> /api/ai/research-clips returned {len(data1['clips'])} candidates")

    # 2. Edit copilot endpoint
    r2 = client.post("/api/ai/edit-copilot", json={
        "instruction": "Sharpen hook and make headline punchy",
        "current_state": {
            "title": "MORNING ROUTINES",
            "hook": "Why you should wake up early"
        }
    })
    assert r2.status_code == 200
    data2 = r2.json()
    assert data2["status"] == "success"
    assert "updated_title" in data2["edits"]
    print(f"  -> /api/ai/edit-copilot returned: '{data2['edits']['updated_title']}'")

    # 3. Social kit endpoint
    r3 = client.post("/api/ai/social-kit", json={
        "title": "THE REAL REASON 99% OF PEOPLE FAIL",
        "hook": "Do you know the real reason?",
        "transcript": "Discipline is what separates the top one percent from the rest."
    })
    assert r3.status_code == 200
    data3 = r3.json()
    assert data3["status"] == "success"
    assert "tiktok" in data3["social_kit"]
    print("  -> /api/ai/social-kit returned valid platform kits")
    print("      -> FastAPI Endpoints PASSED! ✅")

if __name__ == "__main__":
    print("=" * 60)
    print("Running End-to-End Tests for AI Research & Autonomous Editing...")
    print("=" * 60)
    test_ai_viral_research()
    test_ai_video_copilot()
    test_social_distribution_kit()
    test_fastapi_endpoints()
    print("=" * 60)
    print("ALL AI RESEARCH & EDITING TESTS PASSED SUCCESSFULLY! 🚀")
    print("=" * 60)
