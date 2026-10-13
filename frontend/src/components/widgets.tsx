import { pct, VERDICT_LABEL } from "../types";
import type { AnalyzeResult } from "../types";
import { Icons } from "./icons";

export function VerdictBadge({ value }: { value: string }) {
  const key = (value || "unknown").toLowerCase();
  const label = VERDICT_LABEL[key] ?? "Unknown";
  return (
    <span className={`badge ${key}`}>
      {label} · {key}
    </span>
  );
}

export function AdvisoryBanner({ result }: { result: AnalyzeResult }) {
  const level = (result.advisory_level || "unknown").toLowerCase();
  const icon = level === "low" ? Icons.check : level === "unknown" ? Icons.info : Icons.alert;
  return (
    <div className={`verdict ${level}`}>
      <span className="verdict-ic">{icon}</span>
      <div>
        <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
          <VerdictBadge value={result.prediction} />
          <span className={`badge ${level}`}>{level === "low" ? "Low risk" : level === "unknown" ? "No verdict" : `${level} advisory`}</span>
          {result.confidence !== null && result.confidence !== undefined && (
            <span className="mono" style={{ fontSize: 12.5 }}>confidence {pct(result.confidence)}</span>
          )}
        </div>
        <p style={{ margin: "8px 0 0", fontSize: 14 }}>
          <strong>Advisory — {level}:</strong> {result.advisory_message}
        </p>
      </div>
    </div>
  );
}

export function ProbabilityBars({ probs }: { probs: Record<string, number> }) {
  const entries = Object.entries(probs).sort((a, b) => b[1] - a[1]);
  if (entries.length === 0) return <p className="hint">Probability breakdown unavailable for this classifier.</p>;
  return (
    <div>
      {entries.map(([label, p]) => (
        <div className="prob-row" key={label}>
          <span style={{ textTransform: "capitalize", fontWeight: 600 }}>{VERDICT_LABEL[label.toLowerCase()] ?? label}</span>
          <div className="meter" role="progressbar" aria-valuenow={Math.round(p * 100)} aria-valuemin={0} aria-valuemax={100} aria-label={`${label} probability`}>
            <span style={{ width: `${Math.min(100, Math.max(0, p * 100))}%` }} />
          </div>
          <span className="v num">{pct(p)}</span>
        </div>
      ))}
    </div>
  );
}

export function StatCard({ icon, label, value, sub }: { icon: React.ReactNode; label: string; value: string; sub?: string }) {
  return (
    <div className="card">
      <div className="stat-top">
        <span style={{ fontSize: 13, fontWeight: 700, color: "var(--muted)" }}>{label}</span>
        <span className="stat-ic">{icon}</span>
      </div>
      <div className="stat-value">{value}</div>
      {sub && <p className="stat-sub">{sub}</p>}
    </div>
  );
}
