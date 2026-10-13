import { formatDateTime, pct } from "../types";
import type { HistoryEntry, ModelStatus } from "../types";
import { Icons } from "../components/icons";
import { StatCard } from "../components/widgets";
import type { PageKey } from "../types";

interface Props {
  status: ModelStatus | null;
  loading: boolean;
  error: string | null;
  history: HistoryEntry[];
  onClearHistory: () => void;
  onGo: (p: PageKey) => void;
}

export default function Overview({ status, loading, error, history, onClearHistory, onGo }: Props) {
  return (
    <div>
      {error && <div className="alert error" role="alert">Could not reach the API ({error}). Start it with <span className="mono">python api.py</span>.</div>}

      {loading || !status ? (
        <div className="grid cols-4"><div className="skeleton" /><div className="skeleton" /><div className="skeleton" /><div className="skeleton" /></div>
      ) : (
        <div className="grid cols-4">
          <StatCard icon={Icons.privacy} label="Model status" value={status.available ? "Ready" : "Not trained"} sub={status.available ? `v${status.version} · ${status.model_type}` : "Run python train.py"} />
          <StatCard icon={Icons.evaluation} label="Held-out accuracy" value={status.accuracy !== null ? pct(status.accuracy) : "—"} sub="Stratified 80/20 split, seed 42" />
          <StatCard icon={Icons.methodology} label="Labels" value={status.labels.length ? status.labels.join(" / ") : "—"} sub={`${status.labels.length || 0} classes`} />
          <StatCard icon={Icons.info} label="Trained" value={formatDateTime(status.trained_at).split(",")[0]} sub={formatDateTime(status.trained_at)} />
        </div>
      )}

      {!status?.available && !loading && (
        <div className="alert" style={{ marginTop: 14 }}>
          No trained model found. Train one with <span className="mono">python train.py --data data/sample_messages.csv</span>, then refresh.
        </div>
      )}

      <div className="grid cols-2" style={{ marginTop: 14 }}>
        <div className="card">
          <h3>How an analysis works</h3>
          <p className="hint">Three independent signals, presented separately so you can judge for yourself.</p>
          <div className="steps" style={{ marginTop: 12 }}>
            <div><div className="step-num">1</div><strong>Model score</strong><p className="hint">TF-IDF + Logistic Regression estimates ham / spam likelihood.</p></div>
            <div><div className="step-num">2</div><strong>Rule check</strong><p className="hint">Transparent patterns: links, OTP requests, prize lures, urgency.</p></div>
            <div><div className="step-num">3</div><strong>Advisory</strong><p className="hint">Heuristic guidance — not a fraud probability. You decide.</p></div>
          </div>
          <div className="toolbar">
            <button className="btn primary" onClick={() => onGo("analyzer")}>Analyze a message</button>
            <button className="btn ghost" onClick={() => onGo("evaluation")}>View evaluation</button>
          </div>
        </div>
        <div className="card">
          <h3>Privacy by design</h3>
          <p className="hint">Everything runs on this machine — the model, the rules, and this interface.</p>
          <ul className="list">
            <li><span>{Icons.check}</span> Zero network calls during inference; no uploads, no tracking.</li>
            <li><span>{Icons.check}</span> History below lives only in this browser tab — clearing it removes it.</li>
            <li><span>{Icons.check}</span> Logs never contain message contents, only counts and timings.</li>
          </ul>
        </div>
      </div>

      <div className="section-title">Recent analyses — this session only</div>
      <div className="card tight">
        {history.length === 0 ? (
          <p className="hint" style={{ margin: 4 }}>Nothing analyzed yet. Open the Analyzer to inspect your first message.</p>
        ) : (
          <>
            <div className="table-wrap">
              <table className="data">
                <thead><tr><th>Time</th><th>Verdict</th><th>Advisory</th><th>Preview</th></tr></thead>
                <tbody>
                  {[...history].reverse().slice(0, 8).map((h) => (
                    <tr key={h.id}>
                      <td className="mono" style={{ whiteSpace: "nowrap" }}>{h.at}</td>
                      <td style={{ textTransform: "capitalize" }}>{h.prediction}</td>
                      <td style={{ textTransform: "capitalize" }}>{h.advisory_level}</td>
                      <td>{h.preview}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="toolbar">
              <button className="btn ghost sm" onClick={onClearHistory}>Clear session history</button>
              <span className="char-count">{history.length} entr{history.length === 1 ? "y" : "ies"} · never leaves this browser</span>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
