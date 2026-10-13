"""Prediction engine: loads the trained model and analyzes messages.

``analyze_message(text)`` returns a dict with:
- prediction: predicted class label (or "unknown" if no model is loaded)
- confidence: max class probability (None when unavailable)
- probabilities: {label: probability} (empty when unavailable)
- indicators: rule-based warning strings (independent of the model)
- explanation: human-readable summary
- advisory_level / advisory_message: heuristic risk guidance (NOT a
  calibrated fraud probability)
- model_version / model_trained_at / model_available
- latency_ms: inference time for this call

Privacy: this module performs NO network calls, NO persistent storage of
messages, and NEVER logs message contents. Callers must not log them either.

Security note: model files are loaded with joblib (pickle-based). Only load
model files you trained yourself or from trusted sources.
"""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path

logger = logging.getLogger(__name__)  # never log message contents

BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_PATH = BASE_DIR / "models" / "spamshield_model.joblib"
METADATA_PATH = BASE_DIR / "models" / "model_metadata.json"

_model = None
_metadata: dict = {}


def _load_metadata() -> dict:
    if METADATA_PATH.exists():
        try:
            return json.loads(METADATA_PATH.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001 - corrupt metadata is non-fatal
            logger.warning("Could not read model metadata.")
    return {}


def get_model():
    """Load (and cache) the trained pipeline. Raises FileNotFoundError if missing."""
    global _model, _metadata
    if _model is not None:
        return _model
    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"No trained model found at '{MODEL_PATH}'. "
            "Train one with: python train.py --data data/sample_messages.csv"
        )
    import joblib  # local import: keeps module importable without sklearn

    try:
        _model = joblib.load(MODEL_PATH)
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(
            f"Could not load model file '{MODEL_PATH}': {exc}. "
            "The file may be corrupt or from an incompatible version. "
            "Re-run training to regenerate it."
        ) from exc
    _metadata = _load_metadata()
    return _model


def model_status() -> dict:
    """Return model availability + metadata without requiring a prediction."""
    available = MODEL_PATH.exists()
    meta = _load_metadata() if not _metadata else dict(_metadata)
    return {
        "available": available,
        "model_path": str(MODEL_PATH),
        "version": meta.get("version", "unknown"),
        "trained_at": meta.get("trained_at", "unknown"),
        "model_type": meta.get("model_type", "unknown"),
        "labels": meta.get("labels", []),
        "accuracy": meta.get("eval", {}).get("accuracy"),
    }


def analyze_message(text: str) -> dict:
    """Analyze a single message. Never raises on bad input — returns an error dict."""
    from .preprocessing import MAX_INPUT_CHARS, validate_input
    from .rules import advisory_level, detect_indicators

    t0 = time.perf_counter()
    ok, err = validate_input(text, MAX_INPUT_CHARS)
    if not ok:
        return {
            "prediction": "unknown",
            "confidence": None,
            "probabilities": {},
            "indicators": [],
            "explanation": err,
            "advisory_level": "unknown",
            "advisory_message": "No analysis performed due to invalid input.",
            "model_version": (_metadata.get("version") if _metadata else None),
            "model_available": MODEL_PATH.exists(),
            "latency_ms": round((time.perf_counter() - t0) * 1000, 2),
            "error": err,
        }

    indicators = detect_indicators(text)

    try:
        model = get_model()
    except (FileNotFoundError, RuntimeError) as exc:
        level, msg = advisory_level("unknown", len(indicators), None)
        return {
            "prediction": "unknown",
            "confidence": None,
            "probabilities": {},
            "indicators": indicators,
            "explanation": (
                f"{exc} Showing rule-based indicators only; "
                "no model prediction is available."
            ),
            "advisory_level": level,
            "advisory_message": msg + " (Heuristic guidance only — not a fraud probability.)",
            "model_version": None,
            "model_available": False,
            "latency_ms": round((time.perf_counter() - t0) * 1000, 2),
            "error": str(exc),
        }

    classes = list(getattr(model, "classes_", []))
    try:
        proba = model.predict_proba([text])[0]
        probabilities = {str(c): float(p) for c, p in zip(classes, proba)}
        best_idx = int(proba.argmax())
        prediction = str(classes[best_idx])
        confidence = float(proba[best_idx])
    except Exception:  # noqa: BLE001 - some classifiers lack predict_proba
        prediction = str(model.predict([text])[0])
        probabilities = {}
        confidence = None

    level, msg = advisory_level(prediction, len(indicators), confidence)

    if confidence is None:
        conf_txt = "estimated confidence is unavailable for this classifier"
    elif confidence >= 0.85:
        conf_txt = f"the model is fairly confident ({confidence:.0%})"
    elif confidence >= 0.6:
        conf_txt = f"the model is only moderately confident ({confidence:.0%}) — treat this cautiously"
    else:
        conf_txt = f"the model is uncertain ({confidence:.0%}) — this message may be ambiguous or unlike the training data"

    parts = [f"Model prediction: {prediction} ({conf_txt})."]
    if indicators:
        parts.append(f"Rule check found {len(indicators)} warning pattern(s): " + "; ".join(indicators) + ".")
    else:
        parts.append("Rule check found no common warning patterns (absence of patterns does not prove safety).")
    parts.append("Advisory level is a heuristic combining the model output and rule hits — not a calibrated fraud probability.")
    explanation = " ".join(parts)

    return {
        "prediction": prediction,
        "confidence": confidence,
        "probabilities": probabilities,
        "indicators": indicators,
        "explanation": explanation,
        "advisory_level": level,
        "advisory_message": msg + " (Heuristic guidance only — not a fraud probability.)",
        "model_version": _metadata.get("version", "unknown") if _metadata else "unknown",
        "model_available": True,
        "latency_ms": round((time.perf_counter() - t0) * 1000, 2),
    }
