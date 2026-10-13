import type { AnalyzeResult, EvaluationPayload, ModelStatus } from "./types";

async function readJson<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(text || `Request failed (${res.status})`);
  }
  return (await res.json()) as T;
}

export async function fetchStatus(signal?: AbortSignal): Promise<ModelStatus> {
  const res = await fetch("/api/status", { signal });
  return readJson<ModelStatus>(res);
}

export async function analyzeMessage(text: string): Promise<AnalyzeResult> {
  const res = await fetch("/api/analyze", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });
  return readJson<AnalyzeResult>(res);
}

export async function fetchEvaluation(signal?: AbortSignal): Promise<EvaluationPayload> {
  const res = await fetch("/api/evaluation", { signal });
  return readJson<EvaluationPayload>(res);
}

export function confusionMatrixUrl(): string {
  return "/api/confusion-matrix";
}
