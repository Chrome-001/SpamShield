"""Tests for the prediction engine (structure, validation, privacy)."""
import json

from spamshield import predictor
from spamshield.predictor import analyze_message, model_status


def test_empty_and_whitespace_input_return_error_dict():
    for bad in ("", "   "):
        r = analyze_message(bad)
        assert r["prediction"] == "unknown"
        assert "error" in r
        assert r["confidence"] is None


def test_overlong_input_rejected():
    r = analyze_message("x" * 6000)
    assert r["prediction"] == "unknown"
    assert "too long" in r["explanation"].lower()


def test_output_structure_keys():
    r = analyze_message("Hello, see you tomorrow!")
    for key in ("prediction", "confidence", "probabilities", "indicators",
                "explanation", "advisory_level", "advisory_message",
                "model_available", "latency_ms"):
        assert key in r, f"missing key: {key}"


def test_probabilities_sum_to_one_when_model_available():
    r = analyze_message("WINNER claim your free prize now!!!")
    if r["model_available"] and r["probabilities"]:
        assert abs(sum(r["probabilities"].values()) - 1.0) < 1e-6
        assert 0.0 <= r["confidence"] <= 1.0


def test_indicators_independent_of_model(monkeypatch):
    # Even with the model file "missing", rule indicators must still appear.
    monkeypatch.setattr(predictor, "MODEL_PATH", predictor.BASE_DIR / "models" / "nonexistent.joblib")
    predictor._model = None
    r = analyze_message("Send your password and OTP to http://bit.ly/x now, urgent!")
    assert isinstance(r["indicators"], list) and len(r["indicators"]) >= 1
    predictor._model = None  # reset cache


def test_model_status_shape():
    s = model_status()
    assert "available" in s and "version" in s


def test_missing_model_handled_with_message(tmp_path, monkeypatch):
    monkeypatch.setattr(predictor, "MODEL_PATH", tmp_path / "missing.joblib")
    predictor._model = None
    r = analyze_message("Hello there")
    assert r["prediction"] == "unknown"
    assert r["model_available"] is False
    predictor._model = None


def test_no_message_contents_in_logs(caplog):
    import logging
    secret = "super-secret-token-xyz-123"
    with caplog.at_level(logging.WARNING, logger="spamshield.predictor"):
        analyze_message(secret)
    for record in caplog.records:
        assert secret not in record.getMessage()
        assert secret not in str(getattr(record, "args", ""))


def test_evaluation_report_is_real_if_present():
    from pathlib import Path
    p = Path(__file__).resolve().parent.parent / "reports" / "evaluation.json"
    if p.exists():
        ev = json.loads(p.read_text(encoding="utf-8"))
        assert 0.0 <= ev["accuracy"] <= 1.0
        assert ev["n_test"] >= 1
