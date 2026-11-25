import asyncio

import numpy as np
from PIL import Image

from core.ai_engine import AIEngineError, MultiModelAIEngine
from core.thumbnail_designer import TikTokThumbnailDesigner


class FakeThumbnailAI:
    def __init__(self, fail=False):
        self.fail = fail
        self.prompt = ""

    def generate_json(self, prompt, **_kwargs):
        self.prompt = prompt
        if self.fail:
            raise AIEngineError("Ollama is offline.")
        return {
            arch: {
                    "topic_phrase": "Marathon training",
                    "badge": "RUNNING",
                    "headline_white": "Why consistency matters",
                    "headline_yellow_1": "Marathon training",
                    "headline_yellow_2": "Easy days feel easy",
                }
                for arch in ("curiosity", "warning", "formula", "callout")
        }, {"model": "qwen3.5:4b", "warning": None}


class UnsupportedThumbnailAI:
    def generate_json(self, _prompt, **_kwargs):
        return {
            "curiosity": {
                "topic_phrase": "Breakthrough potential",
                "badge": "Unlock progress",
                "headline_white": "Unlock your future",
                "headline_yellow_1": "Transform everything",
                "headline_yellow_2": "Guaranteed results",
            }
        }, {"model": "qwen3.5:4b", "warning": None}


def install_fake_engine(monkeypatch, engine):
    monkeypatch.setattr(
        MultiModelAIEngine,
        "get_instance",
        classmethod(lambda _cls: engine),
    )


def test_thumbnail_copy_uses_local_ai_and_caps_copy_length(monkeypatch):
    engine = FakeThumbnailAI()
    install_fake_engine(monkeypatch, engine)

    variations = TikTokThumbnailDesigner.generate_ai_copy_variations(
        topic="Running",
        title="Ryan Hall's marathon training",
        transcript="Consistency matters more than speed. Easy days should feel easy.",
    )

    assert set(variations) == {"curiosity", "warning", "formula", "callout"}
    assert variations["curiosity"]["generation_source"] == "ollama"
    assert variations["curiosity"]["model"] == "qwen3.5:4b"
    assert variations["curiosity"]["headline_yellow_1"] == "MARATHON TRAINING"
    assert "Easy days should feel easy" in engine.prompt
    assert "fake statistics" in engine.prompt


def test_offline_thumbnail_copy_is_explicit_and_avoids_fake_claims(monkeypatch):
    install_fake_engine(monkeypatch, FakeThumbnailAI(fail=True))

    copy = TikTokThumbnailDesigner.generate_ai_copy(
        topic="Marathon training",
        transcript="Consistency matters more than speed.",
        archetype="warning",
    )

    assert copy["generation_source"] == "heuristic_fallback"
    assert "Ollama is offline" in copy["generation_warning"]
    assert "99%" not in " ".join(copy["takeaways"])
    assert copy["headline_yellow_1"] == "MARATHON TRAINING"


def test_grounding_keeps_explicit_topic_and_rejects_reversed_phrasing():
    topic = TikTokThumbnailDesigner.extract_clean_topic(
        topic="Marathon training",
        title="Ryan Hall's 2010 marathon training regimen",
        transcript="Easy days should feel easy before a hard workout.",
    )

    assert topic == "MARATHON TRAINING"
    assert not TikTokThumbnailDesigner._copy_is_grounded(
        "Easy days feel hard",
        "Easy days should feel easy before a hard workout.",
    )


def test_unsupported_model_copy_uses_grounded_local_fallback(monkeypatch):
    install_fake_engine(monkeypatch, UnsupportedThumbnailAI())

    copy = TikTokThumbnailDesigner.generate_ai_copy(
        topic="Marathon training",
        title="Marathon training basics",
        transcript="Consistency matters more than speed.",
    )

    assert copy["generation_source"] == "heuristic_fallback"
    assert copy["exact_topic"] == "MARATHON TRAINING"
    assert copy["headline_yellow_1"] == "MARATHON TRAINING"
    assert "not grounded" in copy["generation_warning"]


def test_cover_layout_spreads_large_copy_across_safe_vertical_space(tmp_path):
    base_path = tmp_path / "base.jpg"
    output_path = tmp_path / "cover.jpg"
    Image.new("RGB", (1080, 1920), (18, 20, 24)).save(base_path)

    TikTokThumbnailDesigner._render_editorial_master_composition(
        base_frame_path=str(base_path),
        output_path=str(output_path),
        copy_data={
            "headline_white": "THE REAL STORY",
            "headline_yellow_1": "MARATHON TRAINING",
            "headline_yellow_2": "CONSISTENCY BEATS SPEED",
            "speaker_name": "PODCAST GUEST",
            "speaker_tag": "PODCAST CLIP",
            "exact_topic": "MARATHON TRAINING",
            "pill_badge": "RUNNING",
        },
        genre="general",
        frame_meta={"is_dual": False},
    )

    image = np.asarray(Image.open(output_path).convert("RGB"))
    assert image.shape == (1920, 1080, 3)
    opening = image[430:700, 60:760]
    highlight = image[700:980, 60:760]
    support = image[980:1300, 60:760]
    assert np.count_nonzero(np.all(opening > 180, axis=2)) > 100
    assert np.count_nonzero((highlight[:, :, 0] > 200) & (highlight[:, :, 1] > 150) & (highlight[:, :, 2] < 100)) > 1000
    assert np.count_nonzero(np.all(support > 180, axis=2)) > 100


def test_thumbnail_hooks_api_returns_ai_source_and_four_archetypes(monkeypatch):
    import app as app_module

    engine = FakeThumbnailAI()
    install_fake_engine(monkeypatch, engine)
    monkeypatch.setattr(app_module.HistoryManager, "get_clip_by_id", lambda _clip_id: None)

    result = asyncio.run(app_module.generate_clip_thumbnail_hooks(
        "missing",
        {
            "topic": "Marathon training",
            "transcript": "Consistency matters more than speed.",
        },
    ))

    assert result["source"] == "ollama"
    assert result["model"] == "qwen3.5:4b"
    assert len(result["hooks"]) == 4
    assert all(item["generation_source"] == "ollama" for item in result["hooks"])


def test_regenerate_endpoint_passes_selected_copy_to_renderer(monkeypatch, tmp_path):
    import app as app_module

    video_path = tmp_path / "clip.mp4"
    video_path.write_bytes(b"video")
    clip = {
        "id": "clip-id",
        "project_id": "project-id",
        "filename": video_path.name,
        "title": "Marathon training",
        "hook": "Consistency matters more than speed.",
        "full_transcript": "Easy days should feel easy.",
    }
    captured = {}
    monkeypatch.setattr(app_module, "OUTPUTS_DIR", tmp_path)
    monkeypatch.setattr(app_module.HistoryManager, "get_clip_by_id", lambda _clip_id: clip)

    def capture_thumbnail(_cls, **kwargs):
        captured.update(kwargs)
        return tmp_path / "cover.jpg"

    monkeypatch.setattr(
        TikTokThumbnailDesigner,
        "create_tiktok_thumbnail",
        classmethod(capture_thumbnail),
    )
    result = asyncio.run(app_module.regenerate_clip_thumbnail(
        "clip-id",
        {
            "topic": "Marathon training",
            "category": "Running",
            "headline_1": "Consistency wins",
            "headline_2": "Train for the long run",
            "subheadline": "Easy days matter",
            "copy_source": "ollama",
            "copy_model": "qwen3.5:4b",
            "archetype": "formula",
        },
    ))

    assert result["status"] == "success"
    assert captured["copy_data"]["headline_white"] == "CONSISTENCY WINS"
    assert captured["copy_data"]["headline_yellow_1"] == "TRAIN FOR THE LONG RUN"
    assert captured["copy_data"]["headline_yellow_2"] == "EASY DAYS MATTER"
    assert captured["copy_data"]["archetype"] == "formula"
    assert captured["copy_data"]["generation_source"] == "ollama"
    assert result["copy_data"]["model"] == "qwen3.5:4b"


def test_regenerate_endpoint_generates_local_ai_copy_when_fields_are_empty(monkeypatch, tmp_path):
    import app as app_module

    video_path = tmp_path / "clip.mp4"
    video_path.write_bytes(b"video")
    clip = {
        "id": "clip-id",
        "project_id": "project-id",
        "filename": video_path.name,
        "title": "Marathon training",
        "hook": "Consistency matters more than speed.",
        "full_transcript": "Easy days should feel easy.",
    }
    captured = {}
    monkeypatch.setattr(app_module, "OUTPUTS_DIR", tmp_path)
    monkeypatch.setattr(app_module.HistoryManager, "get_clip_by_id", lambda _clip_id: clip)
    install_fake_engine(monkeypatch, FakeThumbnailAI())

    def capture_thumbnail(_cls, **kwargs):
        captured.update(kwargs)
        return tmp_path / "cover.jpg"

    monkeypatch.setattr(
        TikTokThumbnailDesigner,
        "create_tiktok_thumbnail",
        classmethod(capture_thumbnail),
    )
    result = asyncio.run(app_module.regenerate_clip_thumbnail(
        "clip-id",
        {"topic": "Marathon training", "archetype": "curiosity"},
    ))

    assert result["status"] == "success"
    assert captured["copy_data"]["generation_source"] == "ollama"
    assert captured["copy_data"]["model"] == "qwen3.5:4b"
    assert captured["copy_data"]["headline_white"] == "WHY CONSISTENCY MATTERS"
    assert captured["copy_data"]["headline_yellow_1"] == "MARATHON TRAINING"
