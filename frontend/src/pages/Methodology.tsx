export default function Methodology() {
  return (
    <div className="card prose">
      <h3>Methodology — how SpamShield learns</h3>
      <p>
        SpamShield pairs a transparent text representation (<strong>TF-IDF</strong> with unigrams + bigrams,
        English stop-words removed, vocabulary capped for low-memory machines) with a
        <strong> Logistic Regression</strong> classifier. A <strong>Multinomial Naive Bayes</strong> baseline
        is available for comparison via <code className="mono">train.py --compare</code>.
      </p>
      <h4>Training vs inference</h4>
      <ul>
        <li><strong>Training</strong> learns feature weights once from labeled examples (<code className="mono">train.py</code>) with a stratified 80/20 split (seed 42).</li>
        <li><strong>Inference</strong> applies the frozen weights to new messages locally (<code className="mono">analyze_message</code>) — no internet, no data leaves your machine.</li>
      </ul>
      <h4>Evaluation</h4>
      <p>
        Metrics are computed on the held-out test set only: accuracy, macro / weighted precision, recall, F1,
        per-class report, confusion matrix, false-positive / false-negative examples, and inference latency.
        Accuracy alone is insufficient under class imbalance — always read per-class recall and F1.
      </p>
      <h4>Limitations</h4>
      <ul>
        <li>Synthetic sample data is illustrative only; short texts and novel scam phrasing confuse the model.</li>
        <li>A spam probability is not a real-world fraud probability; rule hits are heuristics, not verdicts.</li>
        <li>English short-text only in the bundled sample; no verified scam labels bundled.</li>
      </ul>
      <p className="footer-note">Full model card: <code className="mono">docs/MODEL_CARD.md</code>. Reports regenerate locally via <code className="mono">train.py</code>.</p>
    </div>
  );
}
