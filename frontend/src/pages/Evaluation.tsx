import { useEffect, useState } from "react";
import { confusionMatrixUrl, fetchEvaluation } from "../api";
import type { EvaluationPayload } from "../types";

function fmt(v: number | undefined): string {
  return typeof v === "number" ? v.toFixed(3) : "—";
}

export default function Evaluation() {
  const [data, setData] = useState<EvaluationPayload | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const ctl = new AbortController();
    fetchEvaluation(ctl.signal)
      .then(setData)
      .catch((e: unknown) => {
        if (e instanceof DOMException && e.name === "AbortError") return;
        setError(e instanceof Error ? e.message : "Failed to load evaluation");
      })
      .finally(() => setLoading(false));
    return () => ctl.abort();
  }, []);

  if (loading) return <div className="skeleton" />;
  if (error) return <div className="alert error">Could not load evaluation: {error}</div>;

  const ev = data?.evaluation;
  if (!ev) {
    return (
      <div className="alert">
        No evaluation report found. Generate one by running <span className="mono">python train.py --data data/sample_messages.csv</span>, then refresh.
      </div>
    );
  }

  const perClass = Object.entries(ev.per_class ?? {});
  const comparison = data?.comparison ? Object.entries(data.comparison) : [];

  return (
    <div>
      <div className="grid cols-4">
        <div className="card"><div className="stat-top"><span style={{ fontSize: 13, fontWeight: 700, color: "var(--muted)" }}>Accuracy</span></div><div className="stat-value num">{fmt(ev.accuracy)}</div><p className="stat-sub">Held-out test set</p></div>
        <div className="card"><div className="stat-top"><span style={{ fontSize: 13, fontWeight: 700, color: "var(--muted)" }}>Precision (macro)</span></div><div className="stat-value num">{fmt(ev.precision_macro)}</div><p className="stat-sub">Mean over classes</p></div>
        <div className="card"><div className="stat-top"><span style={{ fontSize: 13, fontWeight: 700, color: "var(--muted)" }}>Recall (macro)</span></div><div className="stat-value num">{fmt(ev.recall_macro)}</div><p className="stat-sub">Mean over classes</p></div>
        <div className="card"><div className="stat-top"><span style={{ fontSize: 13, fontWeight: 700, color: "var(--muted)" }}>F1 (macro)</span></div><div className="stat-value num">{fmt(ev.f1_macro)}</div><p className="stat-sub">Mean over classes</p></div>
      </div>

      <p className="footer-note">
        Evaluated on {ev.n_test} held-out messages{ev.n_train ? ` (train: ${ev.n_train})` : ""}
        {ev.inference_latency_ms_per_message ? ` · ~${ev.inference_latency_ms_per_message} ms/message` : ""}.
        Accuracy alone misleads under class imbalance — compare per-class precision / recall / F1 below.
      </p>

      <div className="section-title">Per-class metrics</div>
      <div className="card tight">
        <div className="table-wrap">
          <table className="data">
            <thead><tr><th>Class</th><th>Precision</th><th>Recall</th><th>F1</th><th>Support</th></tr></thead>
            <tbody>
              {perClass.map(([cls, m]) => (
                <tr key={cls}>
                  <td style={{ textTransform: "capitalize", fontWeight: 650 }}>{cls}</td>
                  <td className="num">{fmt(m.precision)}</td>
                  <td className="num">{fmt(m.recall)}</td>
                  <td className="num">{fmt(m.f1)}</td>
                  <td className="num">{m.support}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="section-title">Confusion matrix</div>
      <div className="card">
        {data?.has_confusion_matrix ? (
          <img className="cm-img" src={confusionMatrixUrl()} alt="Confusion matrix of predicted versus true labels" />
        ) : (
          <p className="hint mono">Raw counts: {JSON.stringify(ev.confusion_matrix)}</p>
        )}
      </div>

      <div className="grid cols-2" style={{ marginTop: 14 }}>
        <div className="card">
          <h3>False positives</h3>
          <p className="hint">Legitimate messages flagged as spam / scam.</p>
          <ul className="list">
            {(ev.false_positives?.length ? ev.false_positives : ["None in test set."]).map((e, i) => (
              <li key={i}>{typeof e === "string" ? <code className="mono">{e}</code> : <span><em>{e.text}</em> (true: {e.true})</span>}</li>
            ))}
          </ul>
        </div>
        <div className="card">
          <h3>False negatives</h3>
          <p className="hint">Spam or scam messages missed as legitimate.</p>
          <ul className="list">
            {(ev.false_negatives?.length ? ev.false_negatives : ["None in test set."]).map((e, i) => (
              <li key={i}>{typeof e === "string" ? <code className="mono">{e}</code> : <span><em>{e.text}</em> (predicted: {e.predicted})</span>}</li>
            ))}
          </ul>
        </div>
      </div>

      {comparison.length > 0 && (
        <>
          <div className="section-title">Model comparison — Logistic Regression vs Naive Bayes</div>
          <div className="card tight">
            <div className="table-wrap">
              <table className="data">
                <thead><tr><th>Model</th><th>Accuracy</th><th>Precision</th><th>Recall</th><th>F1 (macro)</th><th>F1 (weighted)</th></tr></thead>
                <tbody>
                  {comparison.map(([name, v]) => (
                    <tr key={name}>
                      <td style={{ fontWeight: 650 }}>{name}</td>
                      <td className="num">{fmt(v.accuracy)}</td>
                      <td className="num">{fmt(v.precision_macro)}</td>
                      <td className="num">{fmt(v.recall_macro)}</td>
                      <td className="num">{fmt(v.f1_macro)}</td>
                      <td className="num">{fmt(v.f1_weighted)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {comparison.map(([name, v]) => (
              <div className="prob-row" key={name}>
                <span style={{ fontWeight: 600 }}>{name}</span>
                <div className="meter"><span style={{ width: `${Math.min(100, (v.f1_macro ?? 0) * 100)}%` }} /></div>
                <span className="v num">F1 {fmt(v.f1_macro)}</span>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
