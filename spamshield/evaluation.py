"""Model building and evaluation helpers.

- ``build_pipeline(model_type, max_features)``: TF-IDF (unigrams+bigrams,
  English stop words removed) + Logistic Regression (default) or
  Multinomial Naive Bayes (baseline).
- ``evaluate_model``: accuracy, macro/weighted precision/recall/F1,
  per-class report, confusion matrix, and false-positive / false-negative
  examples for error analysis.
"""

from __future__ import annotations

import time

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline

RANDOM_STATE = 42
DEFAULT_MAX_FEATURES = 5000


def build_pipeline(model_type: str = "logreg", max_features: int = DEFAULT_MAX_FEATURES) -> Pipeline:
    """Build the TF-IDF + classifier pipeline."""
    vectorizer = TfidfVectorizer(
        lowercase=True,
        stop_words="english",
        ngram_range=(1, 2),
        max_features=max_features,
        token_pattern=r"(?u)\b\w\w+\b",
    )
    if model_type == "nb":
        clf = MultinomialNB()
    elif model_type == "logreg":
        clf = LogisticRegression(max_iter=1000, random_state=RANDOM_STATE, n_jobs=None)
    else:
        raise ValueError(f"Unknown model_type '{model_type}'. Use 'logreg' or 'nb'.")
    return Pipeline([("tfidf", vectorizer), ("clf", clf)])


def evaluate_model(pipeline: Pipeline, X_test, y_test, X_train=None, y_train=None) -> dict:
    """Evaluate on held-out test data. Returns a JSON-serializable dict."""
    t0 = time.perf_counter()
    y_pred = pipeline.predict(X_test)
    latency_ms = (time.perf_counter() - t0) / max(len(X_test), 1) * 1000

    labels = sorted(set(list(y_test) + list(y_pred)))
    cm = confusion_matrix(y_test, y_pred, labels=labels)
    report = classification_report(y_test, y_pred, labels=labels, output_dict=True, zero_division=0)

    per_class = {
        label: {
            "precision": float(report[label]["precision"]),
            "recall": float(report[label]["recall"]),
            "f1": float(report[label]["f1-score"]),
            "support": int(report[label]["support"]),
        }
        for label in labels
    }

    # Error analysis: up to 10 false positives / false negatives (binary view:
    # ham = negative, anything else = positive).
    fp_examples, fn_examples = [], []
    test_texts = list(X_test)
    for text, true, pred in zip(test_texts, list(y_test), list(y_pred)):
        if pred != true:
            entry = {"text": str(text)[:300], "true": str(true), "predicted": str(pred)}
            if true == "ham":
                if len(fp_examples) < 10:
                    fp_examples.append(entry)
            elif pred == "ham":
                if len(fn_examples) < 10:
                    fn_examples.append(entry)
            elif len(fp_examples) < 10:
                fp_examples.append(entry)

    n_test = len(y_test)
    return {
        "accuracy": float(accuracy_score(y_test, y_pred)),
        "precision_macro": float(precision_score(y_test, y_pred, average="macro", zero_division=0)),
        "recall_macro": float(recall_score(y_test, y_pred, average="macro", zero_division=0)),
        "f1_macro": float(f1_score(y_test, y_pred, average="macro", zero_division=0)),
        "precision_weighted": float(precision_score(y_test, y_pred, average="weighted", zero_division=0)),
        "recall_weighted": float(recall_score(y_test, y_pred, average="weighted", zero_division=0)),
        "f1_weighted": float(f1_score(y_test, y_pred, average="weighted", zero_division=0)),
        "per_class": per_class,
        "labels": labels,
        "confusion_matrix": cm.tolist(),
        "n_test": n_test,
        "n_train": int(len(X_train)) if X_train is not None else None,
        "false_positives": fp_examples,
        "false_negatives": fn_examples,
        "inference_latency_ms_per_message": round(latency_ms, 3),
        "note": (
            "Metrics are computed on the held-out test split only. "
            "With imbalanced or tiny test sets, accuracy alone is misleading — "
            "compare per-class precision/recall/F1."
        ),
    }


def plot_confusion_matrix(cm: list[list[int]], labels: list[str], path: str) -> str:
    """Save a confusion-matrix heatmap with Matplotlib. Returns *path*."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    arr = np.asarray(cm)
    fig, ax = plt.subplots(figsize=(5, 4))
    im = ax.imshow(arr, cmap="Blues")
    ax.set_xticks(range(len(labels)))
    ax.set_yticks(range(len(labels)))
    ax.set_xticklabels(labels)
    ax.set_yticklabels(labels)
    ax.set_xlabel("Predicted")
    ax.set_ylabel("True")
    ax.set_title("Confusion Matrix (held-out test set)")
    for i in range(len(labels)):
        for j in range(len(labels)):
            ax.text(j, i, str(arr[i, j]), ha="center", va="center",
                    color="white" if arr[i, j] > arr.max() / 2 else "black")
    fig.colorbar(im, ax=ax, fraction=0.046)
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)
    return path
