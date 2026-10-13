import { Icons } from "../components/icons";

const ITEMS = [
  ["All analysis is local", "The model, rules, and UI run on your machine. Inference makes zero network calls."],
  ["No message leaves the tab", "Session history lives in React state only — nothing is written to disk by the app."],
  ["Clearing removes it", "Use “Clear session history” on the Overview page, or simply close the tab."],
  ["Logs never contain message contents", "Only counts, timings, and errors are ever logged."],
  ["Model files are pickle-based", "joblib artifacts can execute code on load — only use models you trained yourself or trust."],
];

export default function Privacy() {
  return (
    <div className="grid cols-2" style={{ alignItems: "start" }}>
      <div className="card">
        <h3>Privacy guarantees</h3>
        <p className="hint">Concrete, verifiable properties — not marketing copy.</p>
        <ul className="list">
          {ITEMS.map(([title, body]) => (
            <li key={title}>
              <span style={{ flex: "none" }}>{Icons.check}</span>
              <span><strong>{title}.</strong> {body}</span>
            </li>
          ))}
        </ul>
      </div>
      <div className="card">
        <h3>What to verify yourself</h3>
        <div className="callout warn">
          You don&apos;t have to take our word for it: open DevTools → Network, run an analysis, and confirm
          the only request is <span className="mono">POST /api/analyze</span> to your own machine (localhost).
        </div>
        <dl className="kv" style={{ marginTop: 14 }}>
          <dt>Input cap</dt><dd className="mono">5,000 characters</dd>
          <dt>Storage</dt><dd>in-memory only (this tab)</dd>
          <dt>Telemetry</dt><dd>none — Streamlit stats disabled; no analytics in this UI</dd>
          <dt>Uploads</dt><dd>none — file upload is not offered</dd>
        </dl>
      </div>
    </div>
  );
}
