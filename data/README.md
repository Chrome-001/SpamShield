# Data directory

## Bundled sample (`sample_messages.csv`)

A small **synthetic** dataset (25 ham + 20 spam = 45 messages) written for this
project so training and tests run offline with zero downloads. Columns:

- `text` — the message
- `label` — `ham` (legitimate) or `spam` (unsolicited/unwanted)

> These synthetic examples are **not** a substitute for a representative
> real-world dataset. A model trained only on them is illustrative — expect
> modest, honest metrics (see `reports/evaluation.json` after training).

## Using a real public SMS spam dataset (manual download)

A widely used option is the **SMS Spam Collection** (Almeida & Hidalgo, 2011 —
UCI Machine Learning Repository). Because redistribution terms apply, we do
**not** bundle or auto-download it. To use it manually:

1. Visit the UCI ML Repository page for the "SMS Spam Collection" dataset and
   review its license / attribution requirements.
2. Download the data file (typically `SMSSpamCollection`, tab-separated with
   `ham`/`spam` labels and no header).
3. Convert it to our CSV format with headers `text,label`, e.g. with Python:
   ```python
   import csv
   with open("SMSSpamCollection", encoding="utf-8") as src, \
        open("data/sms_spam.csv", "w", newline="", encoding="utf-8") as dst:
       w = csv.writer(dst)
       w.writerow(["text", "label"])
       for line in src:
           label, msg = line.strip().split("\t", 1)
           w.writerow([msg, label])
   ```
4. Train: `python train.py --data data/sms_spam.csv`
5. Cite the dataset in any published work (see `docs/MODEL_CARD.md`).

Approx. size of the SMS Spam Collection: ~5,574 messages (~13% spam) — small
enough for CPU training on low-memory machines.

## Adding your own data

Any CSV with `text,label` columns works. Keep labels to `ham` / `spam`
(`scam` only if separately verified — never relabel spam as scam silently).
