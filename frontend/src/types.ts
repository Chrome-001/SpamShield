export type PageKey = "overview" | "analyzer" | "evaluation" | "methodology" | "privacy";

export interface ModelStatus {
  available: boolean;
  model_path: string;
  version: string;
  trained_at: string;
  model_type: string;
  labels: string[];
  accuracy: number | null;
}

export interface AnalyzeResult {
  prediction: string;
  confidence: number | null;
  probabilities: Record<string, number>;
  indicators: string[];
  explanation: string;
  advisory_level: string;
  advisory_message: string;
  model_version: string | null;
  model_available: boolean;
  latency_ms: number;
  error?: string;
}

export interface HistoryEntry {
  id: string;
  prediction: string;
  advisory_level: string;
  preview: string;
  at: string;
}

export interface EvaluationPayload {
  evaluation: {
    accuracy: number;
    precision_macro: number;
    recall_macro: number;
    f1_macro: number;
    n_test: number;
    n_train?: number;
    inference_latency_ms_per_message?: number;
    per_class?: Record<string, { precision: number; recall: number; f1: number; support: number }>;
    confusion_matrix?: number[][];
    false_positives?: Array<string | { text: string; true?: string }>;
    false_negatives?: Array<string | { text: string; predicted?: string }>;
  } | null;
  comparison: Record<string, { accuracy?: number; precision_macro?: number; recall_macro?: number; f1_macro?: number; f1_weighted?: number }> | null;
  has_confusion_matrix: boolean;
}

export const VERDICT_LABEL: Record<string, string> = {
  ham: "Legitimate",
  spam: "Spam",
  scam: "Likely scam",
  unknown: "Unknown",
};

export function formatDateTime(raw: string | undefined): string {
  if (!raw || raw === "unknown") return "—";
  const d = new Date(raw);
  if (Number.isNaN(d.getTime())) return raw.slice(0, 16).replace("T", " ");
  return d.toLocaleString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function pct(v: number | null | undefined): string {
  if (v === null || v === undefined || Number.isNaN(v)) return "—";
  return `${(v * 100).toFixed(v < 1 && v > 0 ? 1 : 0)}%`;
}
