"""Dataset loading, validation, and splitting for SpamShield.

Expected CSV columns: ``text`` and ``label``.

Labels (normalized to lowercase):
- ``ham``: legitimate message
- ``spam``: unsolicited / unwanted message
- ``scam`` (optional): only used when the dataset was *separately verified*
  as scam. We never silently relabel spam as scam.

Steps:
1. Check required columns exist.
2. Drop rows with empty / non-string text or missing labels.
3. Normalize labels; reject unknown labels with a clear error.
4. Drop exact-duplicate texts (keep first) and report how many were removed,
   to reduce train/test leakage from duplicates.
5. Report per-class counts, warn on severe imbalance (<10% minority share
   or any class with < 10 samples).
6. Stratified train/test split when every class has >= 2 samples;
   otherwise fall back to a non-stratified split with a warning.
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass, field

import pandas as pd
from sklearn.model_selection import train_test_split

REQUIRED_COLUMNS = ("text", "label")
VALID_LABELS = ("ham", "spam")
VALID_LABELS_WITH_SCAM = ("ham", "spam", "scam")

RANDOM_STATE = 42
TEST_SIZE = 0.2
MIN_STRATIFY_PER_CLASS = 2
MIN_SAMPLES_WARN = 10


@dataclass
class DatasetReport:
    total_rows_raw: int = 0
    rows_after_cleaning: int = 0
    duplicates_removed: int = 0
    empty_rows_removed: int = 0
    class_counts: dict = field(default_factory=dict)
    warnings: list = field(default_factory=list)
    labels: list = field(default_factory=list)
    has_scam_label: bool = False


class DatasetError(ValueError):
    """Raised when a dataset file is invalid."""


def normalize_label(label: object) -> str:
    return str(label).strip().lower()


def load_dataset(path: str, allow_scam: bool = True) -> tuple[pd.DataFrame, DatasetReport]:
    """Load and validate a CSV dataset. Returns (clean DataFrame, report)."""
    report = DatasetReport()
    try:
        df = pd.read_csv(path)
    except FileNotFoundError:
        raise DatasetError(
            f"Dataset not found: '{path}'. Tip: try 'data/sample_messages.csv' "
            "for the bundled synthetic sample, or see data/README.md to "
            "obtain a public SMS spam dataset manually."
        )
    except pd.errors.EmptyDataError:
        raise DatasetError(f"Dataset file '{path}' is empty.")
    except Exception as exc:  # noqa: BLE001 - surface any parse problem clearly
        raise DatasetError(f"Could not read dataset '{path}': {exc}") from exc

    report.total_rows_raw = len(df)

    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise DatasetError(
            f"Dataset '{path}' is missing required column(s): {missing}. "
            f"Found columns: {list(df.columns)}. Expected at least: {list(REQUIRED_COLUMNS)}."
        )

    df = df[["text", "label"]].copy()

    # Drop rows with empty / non-string text.
    def _text_ok(v: object) -> bool:
        return isinstance(v, str) and v.strip() != ""

    empty_mask = ~df["text"].map(_text_ok) | df["label"].isna()
    report.empty_rows_removed = int(empty_mask.sum())
    df = df.loc[~empty_mask].copy()
    df["text"] = df["text"].map(lambda s: s.strip())
    df["label"] = df["label"].map(normalize_label)

    if df.empty:
        raise DatasetError(
            f"Dataset '{path}' has no usable rows after removing "
            f"{report.empty_rows_removed} empty/invalid row(s)."
        )

    valid = VALID_LABELS_WITH_SCAM if allow_scam else VALID_LABELS
    unknown = sorted(set(df["label"].unique()) - set(valid))
    if unknown:
        raise DatasetError(
            f"Dataset '{path}' contains invalid label(s): {unknown}. "
            f"Allowed labels: {list(valid)}."
        )

    # Exact-duplicate removal (keep first) to reduce train/test leakage.
    before = len(df)
    df = df.drop_duplicates(subset=["text"], keep="first").reset_index(drop=True)
    report.duplicates_removed = before - len(df)

    counts = df["label"].value_counts().to_dict()
    report.class_counts = {str(k): int(v) for k, v in counts.items()}
    report.rows_after_cleaning = len(df)
    report.labels = sorted(report.class_counts)
    report.has_scam_label = "scam" in report.class_counts

    # Imbalance / small-sample warnings.
    total = len(df)
    for label, count in report.class_counts.items():
        if count < MIN_SAMPLES_WARN:
            report.warnings.append(
                f"Class '{label}' has only {count} sample(s) "
                f"(fewer than {MIN_SAMPLES_WARN}); metrics for this class will be unreliable."
            )
    if len(report.class_counts) > 1:
        minority_share = min(report.class_counts.values()) / total
        if minority_share < 0.10:
            report.warnings.append(
                f"Severe class imbalance: minority class is only "
                f"{minority_share:.1%} of {total} samples. Accuracy alone is "
                "misleading here — check precision/recall/F1 per class."
            )
    if total < 50:
        report.warnings.append(
            f"Dataset is very small ({total} rows). Results are illustrative only; "
            "use a larger representative dataset for meaningful evaluation."
        )

    for w in report.warnings:
        warnings.warn(w, UserWarning, stacklevel=2)
    return df, report


def split_dataset(
    df: pd.DataFrame,
    test_size: float = TEST_SIZE,
    random_state: int = RANDOM_STATE,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    """Split into train/test. Stratified when every class has >= 2 samples."""
    counts = df["label"].value_counts()
    can_stratify = bool((counts >= MIN_STRATIFY_PER_CLASS).all()) and len(df) >= 4
    stratify = df["label"] if can_stratify else None
    if not can_stratify:
        warnings.warn(
            "Not enough samples per class for a stratified split "
            f"(counts: {counts.to_dict()}); using a plain random split. "
            "Evaluation on tiny test sets is unreliable.",
            UserWarning,
            stacklevel=2,
        )
    X_train, X_test, y_train, y_test = train_test_split(
        df["text"],
        df["label"],
        test_size=test_size,
        random_state=random_state,
        stratify=stratify,
    )
    return X_train, X_test, y_train, y_test
