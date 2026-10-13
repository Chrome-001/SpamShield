"""Tests for dataset loading / validation."""
import pandas as pd
import pytest

from spamshield.dataset import DatasetError, load_dataset, split_dataset


def _write_csv(path, rows):
    pd.DataFrame(rows).to_csv(path, index=False)
    return str(path)


def test_missing_columns_raise(tmp_path):
    p = _write_csv(tmp_path / "bad.csv", [{"foo": "x", "bar": "ham"}])
    with pytest.raises(DatasetError, match="missing required column"):
        load_dataset(p)


def test_invalid_labels_raise(tmp_path):
    p = _write_csv(tmp_path / "bad.csv", [{"text": "hello", "label": "maybe"}])
    with pytest.raises(DatasetError, match="invalid label"):
        load_dataset(p)


def test_empty_rows_removed_and_counts_reported(tmp_path):
    p = _write_csv(tmp_path / "d.csv", [
        {"text": "hello there friend", "label": "ham"},
        {"text": "", "label": "ham"},
        {"text": "win prize now", "label": "spam"},
    ])
    df, report = load_dataset(p)
    assert report.empty_rows_removed == 1
    assert report.class_counts == {"ham": 1, "spam": 1}


def test_duplicates_removed(tmp_path):
    p = _write_csv(tmp_path / "d.csv", [
        {"text": "same message here", "label": "ham"},
        {"text": "same message here", "label": "ham"},
        {"text": "another one here", "label": "spam"},
    ])
    df, report = load_dataset(p)
    assert report.duplicates_removed == 1
    assert len(df) == 2


def test_small_dataset_split_still_works(tmp_path):
    p = _write_csv(tmp_path / "d.csv", [
        {"text": f"message number {i} hello", "label": "ham" if i % 2 == 0 else "spam"}
        for i in range(8)
    ])
    df, _ = load_dataset(p)
    Xtr, Xte, ytr, yte = split_dataset(df)
    assert len(Xtr) + len(Xte) == len(df)
    assert len(Xte) >= 1


def test_missing_file_friendly_error(tmp_path):
    with pytest.raises(DatasetError, match="not found"):
        load_dataset(str(tmp_path / "nope.csv"))
