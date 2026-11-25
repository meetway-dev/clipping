import ctypes
import json
import logging
import math
import os
import shutil
import subprocess
import threading
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple
from urllib.parse import urlparse

import requests

from .config import STORAGE_DIR

logger = logging.getLogger("ClipForge.AIEngine")

DEFAULT_ASSIGNMENTS = {
    "primary": "qwen3.5:4b",
    "reviewer": "qwen2.5:7b",
    "fallback": "llama3.2:latest",
    "embedding": "nomic-embed-text:latest",
}
PROCESSING_MODES = {"fast", "balanced", "maximum_quality"}


class AIEngineError(RuntimeError):
    """An Ollama request or AI-engine configuration failed."""


class OllamaClient:
    """Small Ollama HTTP client. All production inference goes through AIEngine."""

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()

    def set_base_url(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")

    def _request(self, method: str, endpoint: str, timeout: float, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            response = self.session.request(
                method,
                f"{self.base_url}{endpoint}",
                json=payload,
                timeout=timeout,
            )
            response.raise_for_status()
            body = response.json()
            if not isinstance(body, dict):
                raise AIEngineError(f"Ollama returned an invalid response from {endpoint}.")
            return body
        except AIEngineError:
            raise
        except requests.RequestException as exc:
            raise AIEngineError(f"Ollama request to {endpoint} failed: {exc}") from exc
        except ValueError as exc:
            raise AIEngineError(f"Ollama returned invalid JSON from {endpoint}.") from exc

    def list_models(self, timeout: float = 5.0) -> List[Dict[str, Any]]:
        body = self._request("GET", "/api/tags", timeout)
        models = body.get("models", [])
        if not isinstance(models, list):
            raise AIEngineError("Ollama /api/tags returned an invalid models list.")
        return [model for model in models if isinstance(model, dict) and model.get("name")]

    def running_models(self, timeout: float = 5.0) -> List[Dict[str, Any]]:
        body = self._request("GET", "/api/ps", timeout)
        models = body.get("models", [])
        if not isinstance(models, list):
            raise AIEngineError("Ollama /api/ps returned an invalid models list.")
        return [model for model in models if isinstance(model, dict)]

    def chat(
        self,
        model: str,
        prompt: str,
        system_prompt: str = "",
        timeout: float = 120.0,
        keep_alive: str = "45s",
        json_mode: bool = False,
    ) -> Dict[str, Any]:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        payload: Dict[str, Any] = {
            "model": model,
            "messages": messages,
            "stream": False,
            "keep_alive": keep_alive,
            "options": {"num_ctx": 4096},
        }
        if json_mode:
            payload["format"] = "json"
            payload["think"] = False
        return self._request("POST", "/api/chat", timeout, payload)

    def embed(self, model: str, texts: Sequence[str], timeout: float = 90.0) -> List[List[float]]:
        body = self._request(
            "POST",
            "/api/embed",
            timeout,
            {"model": model, "input": list(texts), "keep_alive": "45s"},
        )
        embeddings = body.get("embeddings")
        if not isinstance(embeddings, list) or len(embeddings) != len(texts):
            raise AIEngineError("Ollama /api/embed returned an incomplete embedding batch.")
        vectors: List[List[float]] = []
        for vector in embeddings:
            if not isinstance(vector, list) or not vector:
                raise AIEngineError("Ollama /api/embed returned an invalid vector.")
            try:
                vectors.append([float(value) for value in vector])
            except (TypeError, ValueError) as exc:
                raise AIEngineError("Ollama /api/embed returned non-numeric vector values.") from exc
        return vectors

    def unload(self, model: str, timeout: float = 30.0) -> None:
        self._request(
            "POST",
            "/api/generate",
            timeout,
            {"model": model, "prompt": "", "stream": False, "keep_alive": 0},
        )


class MultiModelAIEngine:
    """Hardware-conscious model registry, inference scheduler, and clip-analysis orchestrator."""

    _instance: Optional["MultiModelAIEngine"] = None
    _instance_lock = threading.Lock()

    def __init__(
        self,
        config_path: Optional[Path] = None,
        client: Optional[OllamaClient] = None,
    ):
        self.config_path = config_path or STORAGE_DIR / "ai_engine_config.json"
        self._settings_lock = threading.RLock()
        self._inference_lock = threading.Lock()
        self._last_discovery_at = 0.0
        self._installed_models: List[Dict[str, Any]] = []
        self._running_models: List[Dict[str, Any]] = []
        self._last_discovery_error: Optional[str] = None
        self._loaded_model: Optional[str] = None
        self._settings = self._load_settings()
        self.client = client or OllamaClient(self._settings["base_url"])
        self.client.set_base_url(self._settings["base_url"])

    @classmethod
    def get_instance(cls) -> "MultiModelAIEngine":
        with cls._instance_lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    @staticmethod
    def _defaults() -> Dict[str, Any]:
        return {
            "base_url": os.environ.get("CLIPFORGE_OLLAMA_URL", "http://127.0.0.1:11434"),
            "processing_mode": "balanced",
            "model_assignments": dict(DEFAULT_ASSIGNMENTS),
        }

    def _load_settings(self) -> Dict[str, Any]:
        settings = self._defaults()
        if not self.config_path.exists():
            return settings
        try:
            stored = json.loads(self.config_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise AIEngineError(f"Could not read AI settings at {self.config_path}: {exc}") from exc
        if not isinstance(stored, dict):
            raise AIEngineError(f"AI settings at {self.config_path} must contain a JSON object.")
        settings.update({key: value for key, value in stored.items() if key != "model_assignments"})
        assignments = stored.get("model_assignments", {})
        if isinstance(assignments, dict):
            settings["model_assignments"].update(
                {key: value for key, value in assignments.items() if key in DEFAULT_ASSIGNMENTS}
            )
        self._validate_settings(settings)
        return settings

    @staticmethod
    def _validate_settings(settings: Dict[str, Any]) -> None:
        parsed_url = urlparse(str(settings.get("base_url", "")))
        if parsed_url.scheme not in {"http", "https"} or not parsed_url.netloc:
            raise AIEngineError("Ollama host must be a valid HTTP or HTTPS URL.")
        if settings.get("processing_mode") not in PROCESSING_MODES:
            raise AIEngineError("Processing mode must be fast, balanced, or maximum_quality.")
        assignments = settings.get("model_assignments")
        if not isinstance(assignments, dict):
            raise AIEngineError("Model assignments must be a JSON object.")
        for role in DEFAULT_ASSIGNMENTS:
            model = assignments.get(role)
            if not isinstance(model, str) or not model.strip():
                raise AIEngineError(f"An installed model must be assigned to the {role} role.")

    def get_settings(self) -> Dict[str, Any]:
        with self._settings_lock:
            return json.loads(json.dumps(self._settings))

    def update_settings(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        with self._settings_lock:
            updated = self.get_settings()
            host = payload.get("base_url", payload.get("host"))
            if host is not None:
                updated["base_url"] = str(host).strip().rstrip("/")
            mode = payload.get("processing_mode", payload.get("mode"))
            if mode is not None:
                updated["processing_mode"] = str(mode).strip().lower()
            assignments = dict(updated["model_assignments"])
            supplied = payload.get("model_assignments")
            if isinstance(supplied, dict):
                assignments.update(supplied)
            if payload.get("model") is not None:
                assignments["primary"] = payload["model"]
            updated["model_assignments"] = assignments
            self._validate_settings(updated)

            try:
                self.config_path.parent.mkdir(parents=True, exist_ok=True)
                temporary_path = self.config_path.with_suffix(self.config_path.suffix + ".tmp")
                temporary_path.write_text(json.dumps(updated, indent=2), encoding="utf-8")
                os.replace(temporary_path, self.config_path)
            except OSError as exc:
                raise AIEngineError(f"Could not persist AI settings: {exc}") from exc

            self._settings = updated
            self.client.set_base_url(updated["base_url"])
            self._last_discovery_at = 0.0
            return self.get_settings()

    def discover_models(self, force: bool = False) -> List[Dict[str, Any]]:
        if not force and time.monotonic() - self._last_discovery_at < 5.0 and self._installed_models:
            return list(self._installed_models)
        try:
            self._installed_models = self.client.list_models()
            self._running_models = self.client.running_models()
            self._last_discovery_error = None
            self._last_discovery_at = time.monotonic()
            return list(self._installed_models)
        except AIEngineError as exc:
            self._installed_models = []
            self._running_models = []
            self._last_discovery_error = str(exc)
            self._last_discovery_at = time.monotonic()
            raise

    def get_status(self, refresh: bool = False) -> Dict[str, Any]:
        settings = self.get_settings()
        try:
            models = self.discover_models(force=refresh)
            connected = True
            error = None
        except AIEngineError as exc:
            models = []
            connected = False
            error = str(exc)
        installed_names = [model["name"] for model in models]
        assignments = settings["model_assignments"]
        missing = {
            role: model for role, model in assignments.items()
            if model not in installed_names
        }
        running_names = [model.get("name") for model in self._running_models if model.get("name")]
        return {
            "connected": connected,
            "url": settings["base_url"],
            "processing_mode": settings["processing_mode"],
            "model_assignments": assignments,
            "configured_primary": assignments["primary"],
            "models": models,
            "available_models": installed_names,
            "running_models": list(self._running_models),
            "missing_assignments": missing,
            "active_model": assignments["primary"] if assignments["primary"] in running_names else None,
            "configured_primary_available": assignments["primary"] in installed_names,
            "error": error,
            "hardware": self.hardware_info(),
        }

    def _resolve_model(self, role: str, requested_model: Optional[str]) -> Tuple[str, bool, Optional[str]]:
        try:
            installed = [model["name"] for model in self.discover_models()]
        except AIEngineError:
            raise
        if requested_model:
            if requested_model not in installed:
                raise AIEngineError(f"Requested model '{requested_model}' is not installed. Use Find Models to refresh.")
            return requested_model, False, None

        assignments = self.get_settings()["model_assignments"]
        model = assignments.get(role)
        if model in installed:
            return model, False, None

        fallback = assignments.get("fallback")
        if role != "fallback" and fallback in installed:
            return fallback, True, f"Assigned {role} model '{model}' is not installed; using configured fallback '{fallback}'."
        raise AIEngineError(
            f"Assigned {role} model '{model}' is not installed, and the configured fallback is unavailable."
        )

    def _switch_model(self, model: str) -> None:
        if self._loaded_model and self._loaded_model != model:
            self.client.unload(self._loaded_model)
            self._loaded_model = None

    @staticmethod
    def _read_chat_content(body: Dict[str, Any], model: str) -> str:
        message = body.get("message", {})
        content = message.get("content") if isinstance(message, dict) else None
        if not isinstance(content, str) or not content.strip():
            raise AIEngineError(f"Model '{model}' returned an empty chat response.")
        return content.strip()

    def generate_text(
        self,
        prompt: str,
        system_prompt: str = "",
        role: str = "primary",
        model: Optional[str] = None,
        timeout: float = 120.0,
        json_mode: bool = False,
        allow_fallback: bool = True,
    ) -> Dict[str, Any]:
        if not isinstance(prompt, str) or not prompt.strip():
            raise AIEngineError("Cannot run an empty AI prompt.")
        if role not in DEFAULT_ASSIGNMENTS:
            raise AIEngineError(f"Unknown model role: {role}.")

        selected, used_fallback, warning = self._resolve_model(role, model)
        settings = self.get_settings()
        primary_model = selected
        started = time.monotonic()
        with self._inference_lock:
            try:
                self._switch_model(selected)
                body = self.client.chat(
                    selected,
                    prompt,
                    system_prompt=system_prompt,
                    timeout=timeout,
                    json_mode=json_mode,
                )
                content = self._read_chat_content(body, selected)
                self._loaded_model = selected
            except AIEngineError as primary_error:
                fallback = settings["model_assignments"]["fallback"]
                if not allow_fallback or model or role == "fallback" or fallback == selected:
                    raise
                installed = [item["name"] for item in self.discover_models(force=True)]
                if fallback not in installed:
                    raise AIEngineError(
                        f"Model '{selected}' failed ({primary_error}); configured fallback '{fallback}' is not installed."
                    ) from primary_error
                self._switch_model(fallback)
                selected = fallback
                warning = f"Model '{primary_model}' failed; retried with configured fallback '{fallback}'."
                try:
                    body = self.client.chat(
                        selected,
                        prompt,
                        system_prompt=system_prompt,
                        timeout=timeout,
                        json_mode=json_mode,
                    )
                    content = self._read_chat_content(body, selected)
                    self._loaded_model = selected
                    used_fallback = True
                except AIEngineError as fallback_error:
                    raise AIEngineError(
                        f"Primary model '{primary_model}' failed ({primary_error}); fallback '{fallback}' failed ({fallback_error})."
                    ) from fallback_error

        return {
            "text": content,
            "model": selected,
            "role": role,
            "source": "ollama",
            "used_fallback": used_fallback,
            "warning": warning,
            "elapsed_seconds": round(time.monotonic() - started, 2),
            "metrics": {
                "prompt_tokens": body.get("prompt_eval_count"),
                "response_tokens": body.get("eval_count"),
            },
        }

    @staticmethod
    def parse_json_response(text: str) -> Any:
        cleaned = text.strip()
        if cleaned.startswith("```"):
            lines = cleaned.splitlines()
            if lines and lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            cleaned = "\n".join(lines).strip()
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as exc:
            raise AIEngineError(f"Model returned invalid JSON: {exc}") from exc

    def generate_json(self, prompt: str, **kwargs: Any) -> Tuple[Any, Dict[str, Any]]:
        result = self.generate_text(prompt, json_mode=True, **kwargs)
        return self.parse_json_response(result["text"]), result

    def embed_texts(self, texts: Sequence[str], timeout: float = 90.0) -> Tuple[List[List[float]], str]:
        if not texts:
            return [], ""
        try:
            installed = [model["name"] for model in self.discover_models()]
        except AIEngineError:
            raise
        model = self.get_settings()["model_assignments"]["embedding"]
        if model not in installed:
            raise AIEngineError(f"Assigned embedding model '{model}' is not installed.")
        with self._inference_lock:
            self._switch_model(model)
            vectors = self.client.embed(model, texts, timeout=timeout)
            self._loaded_model = model
        return vectors, model

    def select_clip_candidates(
        self,
        sentences: List[Dict[str, Any]],
        min_seconds: float,
        max_seconds: float,
        top_k: int,
        processing_mode: Optional[str] = None,
        progress_cb: Optional[Callable[[str, float], None]] = None,
    ) -> Dict[str, Any]:
        mode = processing_mode or self.get_settings()["processing_mode"]
        if mode not in PROCESSING_MODES:
            raise AIEngineError(f"Unsupported AI processing mode: {mode}.")
        chunks = self._chunk_sentences(sentences)
        candidates: List[Dict[str, Any]] = []
        used_models: List[str] = []
        warnings: List[str] = []

        for index, chunk in enumerate(chunks):
            if progress_cb:
                progress_cb(
                    f"Analyzing transcript chunk {index + 1}/{len(chunks)} with the assigned primary model...",
                    33.0 + 5.0 * (index + 1) / max(1, len(chunks)),
                )
            prompt = self._candidate_prompt(chunk, min_seconds, max_seconds, min(3, max(1, top_k)))
            parsed, result = self.generate_json(
                prompt,
                system_prompt="You identify self-contained podcast clips and return only valid JSON.",
                role="primary",
                timeout=180.0,
            )
            used_models.append(result["model"])
            if result.get("warning"):
                warnings.append(result["warning"])
            if progress_cb:
                status = result.get("warning") or f"Chunk {index + 1} completed with {result['model']}."
                progress_cb(status, 33.0 + 5.0 * (index + 1) / max(1, len(chunks)))
            entries = parsed.get("clips", []) if isinstance(parsed, dict) else parsed
            if not isinstance(entries, list):
                warnings.append(f"Primary model returned no clip list for transcript chunk {index + 1}.")
                continue
            for entry in entries:
                candidate = self._validate_candidate(entry, chunk, min_seconds, max_seconds)
                if candidate:
                    candidate["selection_model"] = result["model"]
                    candidates.append(candidate)

        candidates = self._dedupe_by_overlap(candidates)
        if not candidates:
            return {
                "candidates": [],
                "provenance": {
                    "source": "ollama",
                    "processing_mode": mode,
                    "models": list(dict.fromkeys(used_models)),
                    "warnings": warnings,
                },
            }

        if mode in {"balanced", "maximum_quality"}:
            if progress_cb:
                progress_cb(
                    f"Reviewing {len(candidates)} candidates with the assigned reviewer model...",
                    38.5,
                )
            candidates, reviewer_models, review_warning = self._review_candidates(
                candidates, sentences, top_k, mode, progress_cb=progress_cb
            )
            used_models.extend(reviewer_models)
            if review_warning:
                warnings.append(review_warning)

        if mode == "maximum_quality":
            if progress_cb:
                progress_cb("Embedding candidate context with the assigned semantic model...", 39.5)
            try:
                candidates, embedding_model = self._semantic_dedupe(candidates, sentences)
                if embedding_model:
                    used_models.append(embedding_model)
                    if progress_cb:
                        progress_cb(f"Semantic duplicate check completed with {embedding_model}.", 40.0)
            except AIEngineError as exc:
                warnings.append(f"Semantic duplicate check unavailable: {exc}")
                if progress_cb:
                    progress_cb(f"Semantic deduplication skipped: {exc}", 40.0)

        candidates.sort(key=lambda item: item.get("virality_score", 0), reverse=True)
        candidates = candidates[:top_k]
        for candidate in candidates:
            candidate["model_provenance"] = {
                "source": "ollama",
                "processing_mode": mode,
                "models": list(dict.fromkeys(used_models)),
                "warnings": warnings,
            }
        return {
            "candidates": candidates,
            "provenance": {
                "source": "ollama",
                "processing_mode": mode,
                "models": list(dict.fromkeys(used_models)),
                "warnings": warnings,
            },
        }

    @staticmethod
    def _chunk_sentences(sentences: List[Dict[str, Any]], max_chars: int = 3000) -> List[List[Dict[str, Any]]]:
        chunks: List[List[Dict[str, Any]]] = []
        current: List[Dict[str, Any]] = []
        char_count = 0
        for sentence in sentences:
            text = str(sentence.get("text", "")).strip()
            if not text:
                continue
            line_size = len(text) + 32
            if current and char_count + line_size > max_chars:
                chunks.append(current)
                overlap = current[-2:] if len(current) > 2 else current[-1:]
                current = list(overlap)
                char_count = sum(len(str(item.get("text", ""))) + 32 for item in current)
            current.append(sentence)
            char_count += line_size
        if current:
            chunks.append(current)
        return chunks

    @staticmethod
    def _candidate_prompt(
        sentences: List[Dict[str, Any]],
        min_seconds: float,
        max_seconds: float,
        count: int,
    ) -> str:
        lines = [
            f"[{float(item.get('start', 0)):.2f}-{float(item.get('end', 0)):.2f}] {item.get('text', '').strip()}"
            for item in sentences
        ]
        return (
            f"Find up to {count} distinct, complete podcast clips in this transcript. "
            f"Each clip must last {min_seconds:.1f} to {max_seconds:.1f} seconds, start and end on the "
            "provided sentence boundaries, contain a clear hook and a complete thought, and avoid invented claims. "
            "Timestamps must be absolute seconds from the transcript. Return JSON only in this shape: "
            '{"clips":[{"start":12.0,"end":48.5,"title":"ALL CAPS TITLE","hook":"Opening sentence",'
            '"virality_score":80,"reason":"Why it is a complete story"}]}\n\n'
            "Transcript:\n" + "\n".join(lines)
        )

    @staticmethod
    def _validate_candidate(
        entry: Any,
        chunk: List[Dict[str, Any]],
        min_seconds: float,
        max_seconds: float,
    ) -> Optional[Dict[str, Any]]:
        if not isinstance(entry, dict):
            return None
        try:
            start = float(entry.get("start"))
            end = float(entry.get("end"))
        except (TypeError, ValueError):
            return None
        chunk_start = float(chunk[0].get("start", 0))
        chunk_end = float(chunk[-1].get("end", 0))
        duration = end - start
        if start < chunk_start - 0.25 or end > chunk_end + 0.25:
            return None
        if duration < min_seconds or duration > max_seconds:
            return None
        title = str(entry.get("title", "")).strip()
        hook = str(entry.get("hook", "")).strip()
        if not title or not hook:
            return None
        try:
            score = max(0, min(100, int(float(entry.get("virality_score", entry.get("score", 50))))))
        except (TypeError, ValueError):
            score = 50
        return {
            "start": round(start, 2),
            "end": round(end, 2),
            "duration": round(duration, 2),
            "title": title.upper(),
            "hook": hook,
            "virality_score": score,
            "reason": str(entry.get("reason", "Selected by the assigned AI model.")),
        }

    @staticmethod
    def _dedupe_by_overlap(candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        kept: List[Dict[str, Any]] = []
        for candidate in sorted(candidates, key=lambda item: item["virality_score"], reverse=True):
            duplicate = False
            for existing in kept:
                overlap = max(
                    0.0,
                    min(candidate["end"], existing["end"]) - max(candidate["start"], existing["start"]),
                )
                ratio = overlap / max(1.0, min(candidate["duration"], existing["duration"]))
                if ratio >= 0.55:
                    duplicate = True
                    break
            if not duplicate:
                kept.append(candidate)
        return kept

    def _review_candidates(
        self,
        candidates: List[Dict[str, Any]],
        sentences: List[Dict[str, Any]],
        top_k: int,
        mode: str,
        progress_cb: Optional[Callable[[str, float], None]] = None,
    ) -> Tuple[List[Dict[str, Any]], List[str], Optional[str]]:
        shortlist_size = max(top_k * (4 if mode == "maximum_quality" else 2), 8 if mode == "maximum_quality" else 5)
        shortlist = candidates[: min(len(candidates), shortlist_size)]
        reviewed: List[Dict[str, Any]] = []
        models_used: List[str] = []
        warnings: List[str] = []
        batch_size = 8
        batches = [shortlist[index:index + batch_size] for index in range(0, len(shortlist), batch_size)]

        for batch_index, batch in enumerate(batches):
            candidates_text = []
            for index, candidate in enumerate(batch):
                context = " ".join(
                    item.get("text", "")
                    for item in sentences
                    if float(item.get("end", 0)) > candidate["start"]
                    and float(item.get("start", 0)) < candidate["end"]
                )
                candidates_text.append(
                    f"{index}: {candidate['title']} | {candidate['start']:.1f}-{candidate['end']:.1f}s | "
                    f"Hook: {candidate['hook']} | Draft reason: {candidate['reason']} | Transcript: {context[:500]}"
                )
            prompt = (
                f"Review candidate clips for completeness, context, factual support, and distinctiveness. "
                f"Mode: {mode}. Rank each of the {len(batch)} candidates from strongest to weakest. "
                "Do not change timestamps or invent information. Return JSON only: "
                '{"ranking":[{"index":0,"score":90,"reason":"Short reason"}]}\n\n'
                + "\n".join(candidates_text)
            )
            try:
                parsed, result = self.generate_json(
                    prompt,
                    system_prompt="You are a strict short-form video quality reviewer.",
                    role="reviewer",
                    timeout=120.0,
                )
                models_used.append(result["model"])
                if result.get("warning"):
                    warnings.append(result["warning"])
                ranking = parsed.get("ranking", []) if isinstance(parsed, dict) else []
                if not isinstance(ranking, list):
                    raise AIEngineError("Reviewer returned an invalid ranking list.")
                for item in ranking:
                    if not isinstance(item, dict):
                        continue
                    try:
                        index = int(item.get("index"))
                        if index < 0 or index >= len(batch):
                            continue
                        candidate = batch[index]
                        reviewed_candidate = dict(candidate)
                        reviewed_candidate["virality_score"] = max(
                            0, min(100, int(float(item.get("score", candidate["virality_score"]))))
                        )
                        reviewed_candidate["review_reason"] = str(item.get("reason", "")).strip()
                        reviewed_candidate["review_model"] = result["model"]
                        reviewed.append(reviewed_candidate)
                    except (IndexError, TypeError, ValueError):
                        continue
                if progress_cb:
                    progress_cb(
                        f"Review batch {batch_index + 1}/{len(batches)} completed with {result['model']}.",
                        39.0,
                    )
            except AIEngineError as exc:
                warnings.append(f"Reviewer batch {batch_index + 1} failed: {exc}")

        if not reviewed:
            warnings.insert(0, "Reviewer stage failed; primary model ranking retained.")
            return shortlist, [], " ".join(warnings)

        # Candidates omitted from a partial reviewer response keep their primary-model scores.
        reviewed_indices = {
            (item["start"], item["end"]) for item in reviewed
        }
        reviewed.extend(
            candidate for candidate in shortlist
            if (candidate["start"], candidate["end"]) not in reviewed_indices
        )
        reviewed.sort(key=lambda item: item["virality_score"], reverse=True)
        return reviewed, list(dict.fromkeys(models_used)), (" ".join(warnings) if warnings else None)

    def _semantic_dedupe(
        self,
        candidates: List[Dict[str, Any]],
        sentences: List[Dict[str, Any]],
    ) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        texts = []
        for candidate in candidates:
            context = " ".join(
                item.get("text", "")
                for item in sentences
                if float(item.get("end", 0)) > candidate["start"]
                and float(item.get("start", 0)) < candidate["end"]
            )
            texts.append(f"{candidate['title']}. {candidate['hook']}. {context[:500]}")
        vectors, model = self.embed_texts(texts)
        kept: List[Dict[str, Any]] = []
        kept_vectors: List[List[float]] = []
        for candidate, vector in zip(candidates, vectors):
            if any(self._cosine_similarity(vector, previous) >= 0.91 for previous in kept_vectors):
                continue
            kept.append(candidate)
            kept_vectors.append(vector)
        return kept, model

    @staticmethod
    def _cosine_similarity(left: Sequence[float], right: Sequence[float]) -> float:
        if len(left) != len(right):
            return 0.0
        left_norm = math.sqrt(sum(value * value for value in left))
        right_norm = math.sqrt(sum(value * value for value in right))
        if not left_norm or not right_norm:
            return 0.0
        return sum(a * b for a, b in zip(left, right)) / (left_norm * right_norm)

    @staticmethod
    def hardware_info() -> Dict[str, Any]:
        info: Dict[str, Any] = {
            "cpu_count": os.cpu_count(),
            "ram_total_gb": None,
            "ram_available_gb": None,
            "gpu_name": None,
            "gpu_vram_total_mb": None,
            "gpu_vram_free_mb": None,
        }
        try:
            if os.name == "nt":
                class MemoryStatus(ctypes.Structure):
                    _fields_ = [
                        ("dwLength", ctypes.c_ulong),
                        ("dwMemoryLoad", ctypes.c_ulong),
                        ("ullTotalPhys", ctypes.c_ulonglong),
                        ("ullAvailPhys", ctypes.c_ulonglong),
                        ("ullTotalPageFile", ctypes.c_ulonglong),
                        ("ullAvailPageFile", ctypes.c_ulonglong),
                        ("ullTotalVirtual", ctypes.c_ulonglong),
                        ("ullAvailVirtual", ctypes.c_ulonglong),
                        ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
                    ]
                memory = MemoryStatus()
                memory.dwLength = ctypes.sizeof(MemoryStatus)
                if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(memory)):
                    info["ram_total_gb"] = round(memory.ullTotalPhys / (1024 ** 3), 1)
                    info["ram_available_gb"] = round(memory.ullAvailPhys / (1024 ** 3), 1)
            else:
                page_size = os.sysconf("SC_PAGE_SIZE")
                total_pages = os.sysconf("SC_PHYS_PAGES")
                available_pages = os.sysconf("SC_AVPHYS_PAGES")
                info["ram_total_gb"] = round(page_size * total_pages / (1024 ** 3), 1)
                info["ram_available_gb"] = round(page_size * available_pages / (1024 ** 3), 1)
        except (AttributeError, OSError, ValueError):
            logger.debug("System RAM telemetry is unavailable.")

        executable = shutil.which("nvidia-smi")
        if executable:
            try:
                result = subprocess.run(
                    [
                        executable,
                        "--query-gpu=name,memory.total,memory.free",
                        "--format=csv,noheader,nounits",
                    ],
                    capture_output=True,
                    text=True,
                    timeout=3.0,
                    check=True,
                )
                first_line = result.stdout.strip().splitlines()[0]
                name, total, free = [part.strip() for part in first_line.split(",", 2)]
                info.update({
                    "gpu_name": name,
                    "gpu_vram_total_mb": int(total),
                    "gpu_vram_free_mb": int(free),
                })
            except (OSError, subprocess.SubprocessError, IndexError, ValueError) as exc:
                logger.debug("GPU telemetry unavailable: %s", exc)
        return info
