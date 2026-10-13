"""SpamShield Streamlit app — local-only suspicious-message analyzer.

Run:  streamlit run app.py
No network calls, no tracking, no persistent message storage.
"""

from __future__ import annotations

import html
import json
from pathlib import Path

import streamlit as st

BASE_DIR = Path(__file__).resolve().parent
EVAL_PATH = BASE_DIR / "reports" / "evaluation.json"
CM_PATH = BASE_DIR / "reports" / "confusion_matrix.png"

st.set_page_config(page_title="SpamShield", page_icon="🛡️", layout="wide")

CUSTOM_CSS = """
<style>
/* Structural polish only. No global background/text colors are set here, so
   both dark and light modes stay readable. Accent components below carry
   their OWN background AND text colors, rendering identically either way. */
.stButton > button { border-radius: 10px; font-weight: 600; }
.badge { display:inline-block; padding:6px 14px; border-radius:999px; font-weight:700; }
.badge-ham { background:#123d2b; color:#4ade80; border:1px solid #22c55e; }
.badge-spam { background:#40260f; color:#fbbf24; border:1px solid #f59e0b; }
.badge-scam { background:#421418; color:#f87171; border:1px solid #ef4444; }
.badge-unknown { background:#2a3350; color:#cbd5e1; border:1px solid #64748b; }
.card { background:#16203a; border:1px solid #2b3a5f; color:#e8edf5;
        border-radius:12px; padding:16px 18px; margin:10px 0; }
.risk-low { border-left:6px solid #22c55e; }
.risk-caution { border-left:6px solid #f59e0b; }
.risk-elevated { border-left:6px solid #ef4444; }
.prob-row { margin: 2px 0 10px 0; }
.prob-label { font-size: 0.9em; margin-bottom: 2px; }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

EXAMPLES = {
    "Friendly check-in (likely legitimate)": "Hey! Are we still on for coffee this Saturday morning?",
    "Obvious spam": "WINNER! You have won a $1000 prize! Call now to claim your reward!",
    "Phishing-style": "URGENT: Your account has been suspended. Verify now at http://bit.ly/xyz123 with your password.",
}


def load_evaluation() -> dict | None:
    if EVAL_PATH.exists():
        try:
            return json.loads(EVAL_PATH.read_text(encoding="utf-8"))
        except Exception:
            return None
    return None


def prediction_badge(pred: str) -> str:
    p = (pred or "unknown").lower()
    cls = {"ham": "badge-ham", "spam": "badge-spam", "scam": "badge-scam"}.get(p, "badge-unknown")
    label = {"ham": "Legitimate", "spam": "Spam", "scam": "Potential scam"}.get(p, "Unknown")
    return f'<span class="badge {cls}">{html.escape(label)} · model: {html.escape(p)}</span>'


def show_result(result: dict):
    st.markdown(prediction_badge(result.get("prediction", "unknown")), unsafe_allow_html=True)
    conf = result.get("confidence")
    st.write(f"**Confidence:** {conf:.0%}" if conf is not None else "**Confidence:** unavailable for this classifier")
    probs = result.get("probabilities") or {}
    if probs:
        st.write("**Probability breakdown:**")
        for label, p in sorted(probs.items(), key=lambda kv: kv[1], reverse=True):
            st.markdown(
                f"<div class='prob-label'>{html.escape(label)} — {p:.0%}</div>",
                unsafe_allow_html=True,
            )
            st.progress(min(max(float(p), 0.0), 1.0))
    st.markdown(
        f"<div class='card risk-{html.escape(str(result.get('advisory_level', 'unknown')))}'>"
        f"<b>Advisory: {html.escape(str(result.get('advisory_level', 'unknown')).title())}</b><br>"
        f"{html.escape(str(result.get('advisory_message', '')))}"
        f"</div>",
        unsafe_allow_html=True,
    )
    inds = result.get("indicators") or []
    if inds:
        st.write("**Risk indicators (rule-based, independent of the model):**")
        for i in inds:
            st.warning(f"⚠️ {i}")
    else:
        st.success("No common rule-based warning patterns found (this does not prove safety).")
    with st.expander("Why this result? (explanation)"):
        st.write(result.get("explanation", ""))
    st.caption(f"Inference took {result.get('latency_ms', '?')} ms locally. "
               "Advisory level is a heuristic, not a calibrated fraud probability.")
    st.warning("🛡️ Safety reminder: never share passwords or OTPs, don't tap suspicious links, "
               "and verify senders through official channels. This tool is educational and can be wrong.")


# ---- Sidebar nav ----
st.sidebar.title("🛡️ SpamShield")
st.sidebar.caption("Detect suspicious messages. Understand the warning signs.")
page = st.sidebar.radio("Navigate", ["Dashboard", "Message Analyzer", "Model Evaluation", "About", "Privacy"])

# Session history (in-memory only, cleared with session / button).
if "history" not in st.session_state:
    st.session_state.history = []

if page == "Dashboard":
    st.title("🛡️ SpamShield Dashboard")
    st.caption("Detect suspicious messages. Understand the warning signs.")
    from spamshield.predictor import model_status
    status = model_status()
    trained_raw = str(status.get("trained_at", "?"))
    trained_short = trained_raw[:16].replace("T", " ") + " UTC" if "T" in trained_raw else trained_raw
    c1, c2, c3 = st.columns(3)
    c1.metric("Model status", "Ready ✅" if status["available"] else "Not trained ⚠️")
    c2.metric("Model version", status.get("version", "unknown"))
    c3.metric("Held-out accuracy", f"{status['accuracy']:.1%}" if status.get("accuracy") is not None else "—")
    if not status["available"]:
        st.info("No trained model found. Train one with: `python train.py --data data/sample_messages.csv`")
    else:
        st.write(f"**Classifier:** {status.get('model_type', '?')} · **Labels:** {', '.join(status.get('labels', [])) or '?'} "
                 f"· **Trained:** {trained_short}")
    st.subheader("Latest analyses this session")
    if st.session_state.history:
        import pandas as pd

        st.dataframe(
            pd.DataFrame(reversed(st.session_state.history[-5:]))[
                ["prediction", "advisory_level", "preview"]
            ],
            width="stretch",
            hide_index=True,
        )
    else:
        st.write("No messages analyzed yet this session. Go to **Message Analyzer** to start.")
    st.info("🔒 Privacy: all analysis runs locally in this app. Messages are never uploaded, "
            "and history exists only in memory until you clear it or close the session.")
    if st.button("Clear session history"):
        st.session_state.history = []
        st.rerun()

elif page == "Message Analyzer":
    st.title("✉️ Message Analyzer")
    if "msg" not in st.session_state:
        st.session_state.msg = ""
    col_ex = st.columns(len(EXAMPLES))
    for (name, txt), col in zip(EXAMPLES.items(), col_ex):
        if col.button(name, width="stretch"):
            st.session_state.msg = txt
            st.rerun()
    text = st.text_area("Paste a message to analyze", key="msg", height=160, max_chars=5000)
    b1, b2 = st.columns([1, 1])
    analyze = b1.button("🔍 Analyze", type="primary", width="stretch")
    if b2.button("🧹 Clear", width="stretch"):
        st.session_state.msg = ""
        st.rerun()
    if analyze:
        from spamshield.predictor import analyze_message
        result = analyze_message(text)
        if result.get("error") and result.get("prediction") == "unknown" and not result.get("indicators"):
            st.error(result["explanation"])
        else:
            show_result(result)
            if not result.get("error") or result.get("model_available"):
                st.session_state.history.append({
                    "prediction": result.get("prediction"),
                    "advisory_level": result.get("advisory_level"),
                    "preview": (text[:80] + "…") if len(text) > 80 else text,
                })

elif page == "Model Evaluation":
    st.title("📊 Model Evaluation")
    ev = load_evaluation()
    if ev is None:
        st.warning("No evaluation report found. Generate one by running:\n\n`python train.py --data data/sample_messages.csv`")
    else:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Accuracy", f"{ev['accuracy']:.3f}")
        c2.metric("Precision (macro)", f"{ev['precision_macro']:.3f}")
        c3.metric("Recall (macro)", f"{ev['recall_macro']:.3f}")
        c4.metric("F1 (macro)", f"{ev['f1_macro']:.3f}")
        st.caption(f"Evaluated on {ev['n_test']} held-out test messages "
                   f"(train: {ev.get('n_train', '?')}) · ~{ev.get('inference_latency_ms_per_message', '?')} ms/message. "
                   "Accuracy alone is insufficient with imbalanced classes — compare per-class precision/recall/F1 below.")
        st.subheader("Per-class metrics")
        import pandas as pd

        per_class = ev.get("per_class", {})
        df_metrics = pd.DataFrame(per_class).T.reset_index(names="class")
        if "support" in df_metrics.columns:
            df_metrics["support"] = df_metrics["support"].astype(int)
        st.dataframe(
            df_metrics.style.format({c: "{:.3f}" for c in ("precision", "recall", "f1")}),
            width="stretch",
            hide_index=True,
        )
        st.subheader("Confusion matrix")
        if CM_PATH.exists():
            st.image(str(CM_PATH), width=520)
        else:
            st.write(f"Raw counts: {ev.get('confusion_matrix')}")
        with st.expander("Error analysis (false positives / false negatives)"):
            st.write("**False positives** (legitimate flagged as spam/scam):")
            for e in ev.get("false_positives", []) or ["None in test set."]:
                st.write(f"- `{e}`" if isinstance(e, str) else f"- _{e['text']}_ (true: {e['true']})")
            st.write("**False negatives** (spam missed as legitimate):")
            for e in ev.get("false_negatives", []) or ["None in test set."]:
                st.write(f"- `{e}`" if isinstance(e, str) else f"- _{e['text']}_ (predicted: {e['predicted']})")
        cmp_path = BASE_DIR / "reports" / "model_comparison.json"
        if cmp_path.exists():
            st.subheader("Logistic Regression vs Naive Bayes")
            cmp = json.loads(cmp_path.read_text(encoding="utf-8"))
            rows = {k: v for k, v in cmp.items() if isinstance(v, dict)}
            st.dataframe(
                pd.DataFrame(rows).T.reset_index(names="model").style.format(
                    {c: "{:.3f}" for c in ("accuracy", "precision_macro", "recall_macro", "f1_macro", "f1_weighted")},
                    na_rep="—",
                ),
                width="stretch",
                hide_index=True,
            )
            for model_name, vals in rows.items():
                f1 = vals.get("f1_macro")
                if isinstance(f1, (int, float)):
                    st.markdown(
                        f"<div class='prob-label'>{html.escape(model_name)} — F1 {f1:.3f}</div>",
                        unsafe_allow_html=True,
                    )
                    st.progress(min(max(float(f1), 0.0), 1.0))
            st.caption(cmp.get("note", ""))

elif page == "About":
    st.title("📘 About SpamShield")
    st.markdown("""
**TF-IDF** turns each message into numbers by weighting words that are frequent in
the message but rare across all messages (with unigrams + bigrams, English stop
words removed, vocabulary capped for low-memory machines).

**Logistic Regression** learns a weighted score over those TF-IDF features to
separate classes (ham vs spam). A **Multinomial Naive Bayes** baseline is
available for comparison (`--compare`).

**Training vs inference:** training learns weights from labeled examples once
(`train.py`); inference applies the frozen weights to new messages locally
(`analyze_message`), with no internet and no data leaving your machine.

**Limitations:** synthetic sample data is illustrative only; short texts and
new scam wordings confuse the model; a spam probability is *not* a real-world
fraud probability; rule hits are heuristics, not verdicts. See `docs/MODEL_CARD.md`.
""")

else:  # Privacy
    st.title("🔒 Privacy")
    st.markdown("""
- **All analysis is local.** The model, rules, and UI run on your machine.
- **No message is sent to any remote AI API** — inference makes zero network calls.
- **History is in-memory only** (this browser session); nothing is written to disk by the app.
- **Clearing the session** (Dashboard → *Clear session history*, or closing the tab) removes it.
- **Logs never contain message contents** — only counts, timings, and errors.
- ⚠️ Model files use `joblib` (pickle-based): only load model files you trained yourself or trust.
""")
