import json

import pytest

from core.ai_engine import AIEngineError, MultiModelAIEngine
from fastapi.testclient import TestClient


class FakeOllamaClient:
    def __init__(self, names=None, offline=False):
        names = names or [
            "qwen3.5:4b",
            "qwen2.5:7b",
            "llama3.2:latest",
            "nomic-embed-text:latest",
        ]
        self.models = [{"name": name, "size": 1} for name in names]
        self.offline = offline
        self.calls = []
        self.unloaded = []
        self.embedded = []

    def set_base_url(self, _base_url):
        return None

    def list_models(self):
        if self.offline:
            raise AIEngineError("Ollama is offline.")
        return self.models

    def running_models(self):
        if self.offline:
            raise AIEngineError("Ollama is offline.")
        return []

    def chat(self, model, prompt, system_prompt="", **_kwargs):
        self.calls.append((model, system_prompt, prompt))
        if "strict short-form video quality reviewer" in system_prompt:
            content = json.dumps({"ranking": [{"index": 0, "score": 93, "reason": "Complete arc"}]})
        elif "Find up to" in prompt:
            content = json.dumps({
                "clips": [{
                    "start": 0,
                    "end": 20,
                    "title": "A COMPLETE STORY ARC",
                    "hook": "Here is the surprising opening.",
                    "virality_score": 82,
                    "reason": "It includes context and a conclusion.",
                }]
            })
        else:
            content = "ClipForge AI connection verified."
        return {
            "message": {"content": content},
            "prompt_eval_count": 12,
            "eval_count": 8,
        }

    def embed(self, model, texts, **_kwargs):
        self.embedded.append((model, list(texts)))
        return [[1.0, float(index), 0.0] for index, _ in enumerate(texts)]

    def unload(self, model):
        self.unloaded.append(model)


class EmptyPrimaryOllamaClient(FakeOllamaClient):
    def chat(self, model, prompt, system_prompt="", **kwargs):
        if model == "qwen3.5:4b":
            self.calls.append((model, system_prompt, prompt))
            return {"message": {"content": ""}}
        return super().chat(model, prompt, system_prompt, **kwargs)


def make_engine(tmp_path, client=None):
    return MultiModelAIEngine(
        config_path=tmp_path / "ai_engine_config.json",
        client=client or FakeOllamaClient(),
    )


def test_registry_uses_only_exact_installed_model_tags(tmp_path):
    client = FakeOllamaClient(names=["qwen3.5:4b", "nomic-embed-text:latest"])
    engine = make_engine(tmp_path, client)

    status = engine.get_status(refresh=True)

    assert status["available_models"] == ["qwen3.5:4b", "nomic-embed-text:latest"]
    assert status["missing_assignments"]["reviewer"] == "qwen2.5:7b"
    assert status["active_model"] is None


def test_settings_are_persisted_and_loaded(tmp_path):
    client = FakeOllamaClient()
    engine = make_engine(tmp_path, client)
    assignments = {
        "primary": "qwen3.5:4b",
        "reviewer": "qwen2.5:7b",
        "fallback": "llama3.2:latest",
        "embedding": "nomic-embed-text:latest",
    }

    engine.update_settings({
        "base_url": "http://127.0.0.1:11434",
        "processing_mode": "maximum_quality",
        "model_assignments": assignments,
    })
    restored = make_engine(tmp_path, FakeOllamaClient())

    assert restored.get_settings()["processing_mode"] == "maximum_quality"
    assert restored.get_settings()["model_assignments"] == assignments


def test_unknown_explicit_model_fails_instead_of_substituting(tmp_path):
    client = FakeOllamaClient()
    engine = make_engine(tmp_path, client)

    with pytest.raises(AIEngineError, match="not installed"):
        engine.generate_text("test prompt", model="not-installed:latest")

    assert client.calls == []


def test_balanced_mode_reviews_candidates_with_assigned_models(tmp_path):
    client = FakeOllamaClient()
    engine = make_engine(tmp_path, client)
    sentences = [
        {"start": 0.0, "end": 10.0, "text": "The opening context is clear."},
        {"start": 10.0, "end": 20.0, "text": "The speaker explains the key idea."},
    ]

    result = engine.select_clip_candidates(sentences, 10, 30, 1, "balanced")

    assert result["candidates"][0]["virality_score"] == 93
    assert result["provenance"]["models"] == ["qwen3.5:4b", "qwen2.5:7b"]
    assert [call[0] for call in client.calls] == ["qwen3.5:4b", "qwen2.5:7b"]
    assert client.unloaded == ["qwen3.5:4b"]


def test_fast_mode_uses_primary_only_and_max_quality_embeds(tmp_path):
    sentences = [
        {"start": 0.0, "end": 10.0, "text": "The opening context is clear."},
        {"start": 10.0, "end": 20.0, "text": "The speaker explains the key idea."},
    ]
    fast_client = FakeOllamaClient()
    fast_engine = make_engine(tmp_path / "fast", fast_client)
    fast_result = fast_engine.select_clip_candidates(sentences, 10, 30, 1, "fast")

    assert fast_result["provenance"]["models"] == ["qwen3.5:4b"]
    assert len(fast_client.calls) == 1
    assert fast_client.embedded == []

    quality_client = FakeOllamaClient()
    quality_engine = make_engine(tmp_path / "quality", quality_client)
    quality_result = quality_engine.select_clip_candidates(sentences, 10, 30, 1, "maximum_quality")

    assert quality_result["provenance"]["models"] == [
        "qwen3.5:4b",
        "qwen2.5:7b",
        "nomic-embed-text:latest",
    ]
    assert quality_client.embedded[0][0] == "nomic-embed-text:latest"


def test_unavailable_primary_uses_only_configured_fallback_with_warning(tmp_path):
    client = FakeOllamaClient()
    engine = make_engine(tmp_path, client)
    assignments = engine.get_settings()["model_assignments"]
    assignments["primary"] = "missing-primary:latest"
    engine.update_settings({"model_assignments": assignments})

    result = engine.generate_text("test prompt")

    assert result["model"] == "llama3.2:latest"
    assert result["used_fallback"] is True
    assert "not installed" in result["warning"]


def test_empty_primary_response_retries_configured_fallback(tmp_path):
    client = EmptyPrimaryOllamaClient()
    engine = make_engine(tmp_path, client)
    engine._loaded_model = "qwen3.5:4b"

    result = engine.generate_text("test prompt")

    assert result["model"] == "llama3.2:latest"
    assert result["used_fallback"] is True
    assert "qwen3.5:4b" in result["warning"]
    assert [call[0] for call in client.calls] == ["qwen3.5:4b", "llama3.2:latest"]
    assert client.unloaded == ["qwen3.5:4b"]


def test_offline_registry_reports_error_without_inventing_models(tmp_path):
    engine = make_engine(tmp_path, FakeOllamaClient(offline=True))

    status = engine.get_status(refresh=True)

    assert status["connected"] is False
    assert status["available_models"] == []
    assert status["error"] == "Ollama is offline."


def test_ai_settings_and_test_endpoints_use_the_registry(monkeypatch, tmp_path):
    from app import app

    engine = make_engine(tmp_path, FakeOllamaClient())
    monkeypatch.setattr(
        MultiModelAIEngine,
        "get_instance",
        classmethod(lambda _cls: engine),
    )

    with TestClient(app) as client:
        status = client.get("/api/ai")
        models = client.post("/api/ai/models", json={})
        tested = client.post("/api/ai/test", json={"model": "qwen3.5:4b"})
        invalid = client.post("/api/ai/test", json={"model": "not-installed:latest"})

    assert status.status_code == 200
    assert status.json()["models"] == [
        "qwen3.5:4b",
        "qwen2.5:7b",
        "llama3.2:latest",
        "nomic-embed-text:latest",
    ]
    assert models.status_code == 200
    assert tested.status_code == 200
    assert tested.json()["model"] == "qwen3.5:4b"
    assert invalid.status_code == 503
