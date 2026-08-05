"""
SemanticClassifier — standalone FastEmbed anchor-phrase classifier.

Copied from $PROJECT_ROOT/intent_classifier.py with two minimal changes:
  - stdlib `logging` (a `logging_util` import was removed) removed; stdlib logging used instead.
  - `constants.MODE_CHARACTER` replaced by configurable `default_label` constructor arg.
  - `ANCHOR_PHRASES` is now a constructor arg instead of a module-level dict.

Usage:
    from semantic_classifier import SemanticClassifier

    clf = SemanticClassifier(
        anchor_phrases={"approval": ["do you want to proceed?", ...]},
        default_label="SKIP",
    )
    clf.initialize_async()          # warm up in background thread
    label, score = clf.predict("do you want to create this file?")
"""
from __future__ import annotations

import atexit
import inspect
import logging
import os
import shutil
import threading
import time
from pathlib import Path

_logger = logging.getLogger(__name__)

# NumPy is an optional accelerator.
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except Exception as e:
    np = None  # type: ignore[assignment]
    NUMPY_AVAILABLE = False
    _logger.warning("CLASSIFIER: numpy not available (%s) - semantic routing disabled", e)

try:
    from fastembed import TextEmbedding
    FASTEMBED_AVAILABLE = True
except Exception as e:
    TextEmbedding = None  # type: ignore[assignment]
    FASTEMBED_AVAILABLE = False
    _logger.warning("CLASSIFIER: fastembed not available (%s) - semantic routing disabled", e)

try:
    import onnxruntime  # noqa: F401
    ONNXRUNTIME_AVAILABLE = True
except Exception as e:
    ONNXRUNTIME_AVAILABLE = False
    _logger.warning("CLASSIFIER: onnxruntime not available (%s) - semantic routing disabled", e)

MODEL_NAME = "BAAI/bge-small-en-v1.5"


def _resolve_fastembed_cache_dir() -> str:
    explicit = os.environ.get("FASTEMBED_CACHE_PATH")
    if explicit:
        return explicit
    home_cache = os.path.join(os.path.expanduser("~"), ".cache", "fastembed")
    try:
        os.makedirs(home_cache, exist_ok=True)
        if os.access(home_cache, os.W_OK):
            return home_cache
    except OSError:
        pass
    return "/tmp/fastembed"


_FASTEMBED_CACHE_DIR: str | None = _resolve_fastembed_cache_dir()


def _is_hf_offline_mode() -> bool:
    return os.environ.get("HF_HUB_OFFLINE", "").strip().lower() in {"1", "true", "yes"}


def _text_embedding_supports_local_files_only() -> bool:
    if TextEmbedding is None:
        return False
    try:
        sig = inspect.signature(TextEmbedding.__init__)
    except (TypeError, ValueError):
        return False
    return "local_files_only" in sig.parameters


class SemanticClassifier:
    """Anchor-phrase cosine-similarity classifier backed by FastEmbed."""

    _instances: dict[str, "SemanticClassifier"] = {}
    _registry_lock = threading.Lock()

    @classmethod
    def get_instance(cls, key: str, **kwargs) -> "SemanticClassifier":
        """Return a named singleton, creating it with kwargs on first call."""
        if key not in cls._instances:
            with cls._registry_lock:
                if key not in cls._instances:
                    cls._instances[key] = cls(**kwargs)
        return cls._instances[key]

    def __init__(
        self,
        anchor_phrases: dict[str, list[str]],
        default_label: str = "SKIP",
        similarity_threshold: float = 0.65,
        max_retries: int = 3,
    ):
        self._anchor_phrases = anchor_phrases
        self._default_label = default_label
        self._similarity_threshold = similarity_threshold
        self._max_retries = max_retries

        self.model = None
        self.anchor_embeddings: dict[str, "np.ndarray"] = {}
        self.ready = False
        self._load_error: str | None = None
        self._initializing = False
        self._cleaned_up = False
        self._retry_count = 0

        self._lock = threading.Lock()
        self._init_lock = threading.Lock()
        self._ready_event = threading.Event()

        atexit.register(self._cleanup)

    # ------------------------------------------------------------------ cache

    @staticmethod
    def _cache_candidates() -> list[Path]:
        model_cache_name = f"models--{MODEL_NAME.replace('/', '--')}"
        candidates = []
        if _FASTEMBED_CACHE_DIR:
            candidates.append(Path(_FASTEMBED_CACHE_DIR) / model_cache_name)
            candidates.append(Path(_FASTEMBED_CACHE_DIR) / f"{model_cache_name}-onnx")
        return candidates

    _MIN_BLOBS_TOTAL_SIZE_BYTES = 60_000_000

    @staticmethod
    def _is_corrupted_cache_dir(cache_dir: Path) -> bool:
        try:
            for onnx_file in cache_dir.rglob("*.onnx"):
                try:
                    if onnx_file.is_symlink() and not onnx_file.exists():
                        return True
                except OSError:
                    return True
        except OSError as e:
            _logger.debug("CLASSIFIER: Filesystem error checking ONNX files in %s: %s", cache_dir, e)
            return True

        blobs_dir = cache_dir / "blobs"
        if not blobs_dir.exists():
            try:
                has_content = any(cache_dir.iterdir())
            except OSError:
                return True
            return has_content  # empty = not corrupted; has content but no blobs = corrupted

        total_bytes = 0
        try:
            for blob_file in blobs_dir.rglob("*"):
                try:
                    if blob_file.is_file():
                        total_bytes += blob_file.stat().st_size
                except OSError:
                    pass
        except OSError:
            return True
        return total_bytes < SemanticClassifier._MIN_BLOBS_TOTAL_SIZE_BYTES

    @staticmethod
    def _has_active_download_lock(cache_dir: Path) -> bool:
        lock_patterns = ["*.lock", "*.tmp", "*.incomplete"]
        for pattern in lock_patterns:
            try:
                if any(cache_dir.rglob(pattern)):
                    return True
            except OSError:
                return True
        return False

    def _validate_and_repair_cache(self) -> None:
        for cache_dir in self._cache_candidates():
            if not cache_dir.exists() and not cache_dir.is_symlink():
                continue
            if not self._is_corrupted_cache_dir(cache_dir):
                continue
            if self._has_active_download_lock(cache_dir):
                _logger.warning(
                    "CLASSIFIER: Corrupted cache at %s but active download lock present; skipping purge.",
                    cache_dir,
                )
                continue
            _logger.warning("CLASSIFIER: Corrupted cache at %s. Rebuilding.", cache_dir)
            try:
                if cache_dir.is_symlink() or cache_dir.is_file():
                    cache_dir.unlink()
                else:
                    shutil.rmtree(cache_dir)
            except FileNotFoundError:
                pass
            except (PermissionError, OSError) as e:
                _logger.error("CLASSIFIER: Failed to remove corrupted cache %s: %s. Proceeding.", cache_dir, e)

    # ------------------------------------------------------------------ init

    def initialize_async(self) -> None:
        if not NUMPY_AVAILABLE or not FASTEMBED_AVAILABLE or not ONNXRUNTIME_AVAILABLE:
            self._load_error = "Dependencies not available"
            return
        with self._init_lock:
            if self.ready or self._initializing:
                return
            self._initializing = True
        threading.Thread(target=self._initialize_model, daemon=False).start()

    def initialize(self, timeout_seconds: float = 60) -> bool:
        """Warm the model once and wait up to timeout_seconds for readiness."""
        self.initialize_async()
        self._ready_event.wait(timeout=max(0, timeout_seconds))
        return self.ready

    def _initialize_model(self) -> None:
        retry_delay = 2.0
        try:
            try:
                self._validate_and_repair_cache()
            except Exception as e:
                self._load_error = str(e)
                _logger.error("CLASSIFIER: Cache preflight failed: %s", e)
                return

            for attempt in range(self._max_retries):
                try:
                    if attempt > 0:
                        _logger.info("CLASSIFIER: Retry %d/%d after %.1fs...", attempt, self._max_retries - 1, retry_delay)
                        time.sleep(retry_delay)
                        retry_delay *= 2

                    _logger.info("CLASSIFIER: Loading %s...", MODEL_NAME)
                    self._validate_and_repair_cache()
                    model_kwargs: dict = {
                        "model_name": MODEL_NAME,
                        "threads": 1,
                        "cache_dir": _FASTEMBED_CACHE_DIR,
                    }
                    if _is_hf_offline_mode() and _text_embedding_supports_local_files_only():
                        model_kwargs["local_files_only"] = True
                    self.model = TextEmbedding(**model_kwargs)

                    _logger.info("CLASSIFIER: Computing anchor embeddings (%d groups)...", len(self._anchor_phrases))
                    for label, phrases in self._anchor_phrases.items():
                        matrix = np.array(list(self.model.embed(phrases)))
                        norms = np.linalg.norm(matrix, axis=1, keepdims=True)
                        norms[norms == 0] = 1.0
                        self.anchor_embeddings[label] = matrix / norms

                    self.ready = True
                    self._retry_count = attempt
                    _logger.info("CLASSIFIER: Ready (attempt %d).", attempt + 1)
                    return

                except Exception as e:
                    self.model = None
                    self._load_error = str(e)
                    if _is_hf_offline_mode() and ("local file" in str(e).lower() or "offline" in str(e).lower()):
                        _logger.warning("CLASSIFIER: Offline cache load failed; giving up.")
                        self._retry_count = attempt
                        return
                    if attempt < self._max_retries - 1:
                        _logger.warning("CLASSIFIER: Attempt %d failed: %s. Retrying.", attempt + 1, e)
                    else:
                        _logger.error("CLASSIFIER: Failed after %d attempts: %s.", self._max_retries, e)
                        self._retry_count = attempt
        finally:
            with self._init_lock:
                self._initializing = False
            self._ready_event.set()

    # ------------------------------------------------------------------ predict

    def predict(self, text: str, context: str | None = None) -> tuple[str, float]:
        """Return (label, score). Falls back to (default_label, 0.0) on any failure."""
        if not NUMPY_AVAILABLE:
            return self._default_label, 0.0
        if not text or not text.strip() or len(text.strip()) < 2:
            return self._default_label, 0.0

        classification_input = text
        if context and context.strip():
            classification_input = f"{context.strip()[-500:]}\n\nUSER ACTION: {text}"

        retry_needed = False
        with self._lock:
            if not self.ready:
                if self._load_error and self.model is None:
                    retry_needed = True

        if retry_needed:
            self.initialize_async()
            return self._default_label, 0.0

        if not self.ready:
            return self._default_label, 0.0

        with self._lock:
            if self.model is None:
                return self._default_label, 0.0
            model = self.model
            anchor_embeddings = self.anchor_embeddings.copy()

        try:
            vec = list(model.embed([classification_input]))[0]
            norm = np.linalg.norm(vec)
            if norm > 0:
                vec = vec / norm

            best_label = self._default_label
            best_score = -1.0
            for label, anchors in anchor_embeddings.items():
                score = float(np.max(np.dot(anchors, vec)))
                if score > best_score:
                    best_score = score
                    best_label = label

            if best_score >= self._similarity_threshold:
                return best_label, best_score
            return self._default_label, best_score

        except Exception as e:
            _logger.error("CLASSIFIER: Prediction error: %s", e)
            return self._default_label, 0.0

    def is_match(self, text: str, label: str) -> bool:
        """Return True if predict returns the given label."""
        result_label, _ = self.predict(text)
        return result_label == label

    def _cleanup(self) -> None:
        if self._cleaned_up:
            return
        self._cleaned_up = True
        try:
            self.model = None
            self.anchor_embeddings.clear()
            self.ready = False
            self._ready_event.clear()
        except Exception:
            pass
