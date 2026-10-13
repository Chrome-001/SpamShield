"""SpamShield training pipeline.

Usage:
    python train.py --data data/sample_messages.csv
    python train.py --data data/sample_messages.csv --model-type nb --compare
    python train.py --data data/sms_spam.csv --max-features 5000 --test-size 0.2

Steps: load + validate -> show distribution -> stratified split -> train
TF-IDF + Logistic Regression (and optionally Naive Bayes) -> evaluate on the
HELD-OUT test set only -> save model, metadata, evaluation JSON, confusion
matrix PNG, and a model-comparison report.
"""

from __future__ import annotations

import argparse
import datetime
import json
import sys
import time
import tracemalloc
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
MODELS_DIR = BASE_DIR / "models"
REPORTS_DIR = BASE_DIR / "reports"

sys.path.insert(0, str(BASE_DIR))

from spamshield.dataset import RANDOM_STATE, load_dataset, split_dataset  # noqa: E402
from spamshield.evaluation import build_pipeline, evaluate_model, plot_confusion_matrix  # noqa: E402


def parse_args(argv=None):
    p = argparse.ArgumentParser(description="Train the SpamShield text classifier.")
    p.add_argument("--data", required=True, help="Path to CSV dataset with text,label columns.")
    p.add_argument("--model-type", choices=["logreg", "nb"], default="logreg",
                   help="Classifier to save as the app model (default: logreg).")
    p.add_argument("--compare", action="store_true",
                   help="Also train the other classifier and write reports/model_comparison.json.")
    p.add_argument("--max-features", type=int, default=5000, help="TF-IDF vocabulary cap (default: 5000).")
    p.add_argument("--test-size", type=float, default=0.2, help="Held-out fraction (default: 0.2).")
    p.add_argument("--no-scantest", action="store_true", help=argparse.SUPPRESS)  # ignored compat flag
    return p.parse_args(argv)


def train_and_eval(model_type, X_train, y_train, X_test, y_test, max_features):
    pipe = build_pipeline(model_type=model_type, max_features=max_features)
    t0 = time.perf_counter()
    pipe.fit(X_train, y_train)
    train_s = time.perf_counter() - t0
    results = evaluate_model(pipe, X_test, y_test, X_train, y_train)
    results["train_seconds"] = round(train_s, 2)
    return pipe, results


def main(argv=None) -> int:
    args = parse_args(argv)
    MODELS_DIR.mkdir(exist_ok=True)
    REPORTS_DIR.mkdir(exist_ok=True)
    overall_t0 = time.perf_counter()
    tracemalloc.start()

    print(f"Loading dataset: {args.data}")
    try:
        df, report = load_dataset(args.data)
    except Exception as exc:  # DatasetError with friendly message
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(f"Rows: raw={report.total_rows_raw}, usable={report.rows_after_cleaning} "
          f"(removed {report.empty_rows_removed} empty, {report.duplicates_removed} duplicates)")
    print(f"Label distribution: {report.class_counts}")
    for w in report.warnings:
        print(f"WARNING: {w}")

    X_train, X_test, y_train, y_test = split_dataset(df, test_size=args.test_size)
    print(f"Split: train={len(X_train)}, test={len(X_test)} (random_state={RANDOM_STATE})")

    pipe, results = train_and_eval(args.model_type, X_train, y_train, X_test, y_test, args.max_features)
    kind = "Logistic Regression" if args.model_type == "logreg" else "Multinomial Naive Bayes"
    print(f"\n[{kind}] accuracy={results['accuracy']:.3f} "
          f"precision(macro)={results['precision_macro']:.3f} recall(macro)={results['recall_macro']:.3f} "
          f"F1(macro)={results['f1_macro']:.3f}  (train {results['train_seconds']}s, "
          f"~{results['inference_latency_ms_per_message']} ms/message)")

    comparison = None
    if args.compare:
        other = "nb" if args.model_type == "logreg" else "logreg"
        _, other_res = train_and_eval(other, X_train, y_train, X_test, y_test, args.max_features)
        comparison = {
            args.model_type: {k: results[k] for k in ("accuracy", "precision_macro", "recall_macro", "f1_macro", "f1_weighted")},
            other: {k: other_res[k] for k in ("accuracy", "precision_macro", "recall_macro", "f1_macro", "f1_weighted")},
            "note": ("Why accuracy alone is insufficient: with imbalanced classes a model can score "
                     "high accuracy by mostly predicting the majority class while missing most spam "
                     "(low spam recall). Compare per-class precision/recall/F1 and the confusion matrix."),
        }
        (REPORTS_DIR / "model_comparison.json").write_text(json.dumps(comparison, indent=2), encoding="utf-8")
        print(f"Model comparison written to {REPORTS_DIR / 'model_comparison.json'}")

    # Save artifacts.
    import joblib

    joblib.dump(pipe, MODELS_DIR / "spamshield_model.joblib")
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    metadata = {
        "version": "1.0.0",
        "trained_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "model_type": kind,
        "model_type_key": args.model_type,
        "max_features": args.max_features,
        "test_size": args.test_size,
        "random_state": RANDOM_STATE,
        "labels": results["labels"],
        "n_train": results["n_train"],
        "n_test": results["n_test"],
        "class_counts": report.class_counts,
        "eval": {k: results[k] for k in ("accuracy", "precision_macro", "recall_macro",
                                         "f1_macro", "precision_weighted", "recall_weighted",
                                         "f1_weighted", "per_class")},
        "train_seconds": results["train_seconds"],
        "total_seconds": round(time.perf_counter() - overall_t0, 2),
        "peak_memory_mb": round(peak / 1e6, 2),
        "current_memory_mb": round(current / 1e6, 2),
    }
    (MODELS_DIR / "model_metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    full = dict(results)
    full["metadata"] = {k: v for k, v in metadata.items() if k != "eval"}
    (REPORTS_DIR / "evaluation.json").write_text(json.dumps(full, indent=2), encoding="utf-8")
    plot_confusion_matrix(results["confusion_matrix"], results["labels"],
                          str(REPORTS_DIR / "confusion_matrix.png"))

    print(f"\nSaved model -> {MODELS_DIR / 'spamshield_model.joblib'}")
    print(f"Saved metadata -> {MODELS_DIR / 'model_metadata.json'}")
    print(f"Saved evaluation -> {REPORTS_DIR / 'evaluation.json'}")
    print(f"Saved confusion matrix -> {REPORTS_DIR / 'confusion_matrix.png'}")
    print(f"Done in {metadata['total_seconds']}s (peak ~{metadata['peak_memory_mb']} MB). "
          "Metrics above are from the HELD-OUT test set only.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
