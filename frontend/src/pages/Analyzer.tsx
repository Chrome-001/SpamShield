import { useState } from "react";
import { analyzeMessage } from "../api";
import type { AnalyzeResult, HistoryEntry } from "../types";
import { AdvisoryBanner, ProbabilityBars } from "../components/widgets";
import { Icons } from "../components/icons";

const MAX = 5000;
const EXAMPLES: Array<{ label: string; text: string }> = [
  { label: "Friendly check-in", text: "Hey! Are we still on for coffee this Saturday morning?" },
  { label: "Obvious spam", text: "WINNER! You have won a $1000 prize! Call now to claim your reward!" },
  { label: "Phishing-style", text: "URGENT: Your account has been suspended. Verify now at http://bit.ly/xyz123 with your password." },
];

interface Props {
  onAnalyzed: (entry: HistoryEntry) => void;
}

export default function Analyzer({ onAnalyzed }: Props) {
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<AnalyzeResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function run() {
    if (!text.trim() || busy) return;
    setBusy(true);
    setError(null);
    try {
      const r = await analyzeMessage(text);
      setResult(r);
      if (!r.error || r.model_available) {
        onAnalyzed({
          id: `${Date.now()}-${Math.random().toString(36).slice(2)}`,
          prediction: r.prediction,
          advisory_level: r.advisory_level,
          preview: text.length > 90 ? text.slice(0, 90) + "…" : text,
          at: new Date().toLocaleTimeString(),
        });
      }
      if (r.error && r.prediction === "unknown" && r.indicators.length === 0) {
        setError(r.explanation);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Analysis failed. Is the API running (python api.py)?");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="grid cols-2" style={{ alignItems: "start" }}>
      <div className="card">
        <h3>Message input</h3>
        <p className="hint">Paste the full text. Analysis is local — nothing is uploaded.</p>
        <div className="example-row" aria-label="Load an example">
          {EXAMPLES.map((ex) => (
            <button key={ex.label} className="chip" onClick={() => { setText(ex.text); setResult(null); setError(null); }}>
              {ex.label}
            </button>
          ))}
        </div>
        <label htmlFor="msg" className="hint" style={{ display: "block", marginBottom: 6, fontWeight: 600 }}>Message to analyze</label>
        <textarea
          id="msg"
          className="textarea"
          value={text}
          maxLength={MAX}
          onChange={(e) => setText(e.target.value)}
          placeholder="e.g. Hi, your parcel is held — confirm your address at …"
        />
        <div className="toolbar">
          <button className="btn primary" disabled={!text.trim() || busy} onClick={run}>
            {busy ? "Analyzing…" : "Analyze message"}
          </button>
          <button className="btn ghost" onClick={() => { setText(""); setResult(null); setError(null); }}>Clear</button>
          <span className="char-count num">{text.length.toLocaleString()} / {MAX.toLocaleString()}</span>
        </div>
        <div className="callout" style={{ marginTop: 14 }}>
          <strong>Safety reminder:</strong> never share passwords or OTPs, don&apos;t tap suspicious links, and verify
          senders through official channels. This tool is educational and can be wrong.
        </div>
      </div>

      <div className="card" aria-live="polite">
        <h3>Result</h3>
        {error && <div className="alert error" role="alert" style={{ marginTop: 8 }}>{error}</div>}
        {!result && !error && (
          <p className="hint" style={{ marginTop: 8 }}>Run an analysis to see the verdict, confidence, probability breakdown, and rule-based warning signs here.</p>
        )}
        {result && !error && (
          <div style={{ marginTop: 8 }}>
            <AdvisoryBanner result={result} />
            <div className="section-title" style={{ marginTop: 6 }}>Model probabilities</div>
            <ProbabilityBars probs={result.probabilities} />
            <div className="section-title">Risk indicators — rule-based, independent of the model</div>
            {result.indicators.length === 0 ? (
              <div className="alert ok"><span style={{ marginRight: 6 }}>{Icons.check}</span>No common warning patterns found. This does not prove safety.</div>
            ) : (
              <ul className="list">
                {result.indicators.map((i) => (
                  <li key={i}><span style={{ flex: "none" }}>{Icons.alert}</span><span>{i}</span></li>
                ))}
              </ul>
            )}
            <div className="section-title">Why this result</div>
            <details className="explain">
              <summary>Explanation</summary>
              <p style={{ margin: "8px 0 0" }}>{result.explanation}</p>
            </details>
            <p className="footer-note">
              Inference took {result.latency_ms} ms locally · model {result.model_version ?? "unknown"} ·
              advisory level is a heuristic, not a calibrated fraud probability.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
