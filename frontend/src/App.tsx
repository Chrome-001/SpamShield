import { useCallback, useEffect, useState } from "react";
import Layout from "./components/Layout";
import Overview from "./pages/Overview";
import Analyzer from "./pages/Analyzer";
import Evaluation from "./pages/Evaluation";
import Methodology from "./pages/Methodology";
import Privacy from "./pages/Privacy";
import { fetchStatus } from "./api";
import type { HistoryEntry, ModelStatus, PageKey } from "./types";
import "./styles.css";

const META: Record<PageKey, { title: string; subtitle: string }> = {
  overview: { title: "Overview", subtitle: "Model status, how it works, and this session's activity." },
  analyzer: { title: "Message Analyzer", subtitle: "Inspect a message — verdict, confidence, and warning signs." },
  evaluation: { title: "Model Evaluation", subtitle: "Real held-out metrics, errors, and model comparison." },
  methodology: { title: "Methodology", subtitle: "How the model learns, and where it falls short." },
  privacy: { title: "Privacy", subtitle: "Local-only guarantees you can verify." },
};

function initialTheme(): "light" | "dark" {
  const saved = localStorage.getItem("spamshield-theme");
  if (saved === "light" || saved === "dark") return saved;
  return window.matchMedia?.("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

export default function App() {
  const [page, setPage] = useState<PageKey>("overview");
  const [theme, setTheme] = useState<"light" | "dark">(initialTheme);
  const [status, setStatus] = useState<ModelStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [history, setHistory] = useState<HistoryEntry[]>([]);

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    localStorage.setItem("spamshield-theme", theme);
  }, [theme]);

  useEffect(() => {
    const ctl = new AbortController();
    fetchStatus(ctl.signal)
      .then((s) => { setStatus(s); setError(null); })
      .catch((e: unknown) => {
        if (e instanceof DOMException && e.name === "AbortError") return;
        setError(e instanceof Error ? e.message : "API unreachable");
      })
      .finally(() => setLoading(false));
    return () => ctl.abort();
  }, []);

  const addHistory = useCallback((entry: HistoryEntry) => {
    setHistory((h) => [...h.slice(-49), entry]);
  }, []);

  const meta = META[page];
  const modelBadge = loading ? "Checking model…" : status?.available ? `Ready · v${status.version}` : "Not trained";

  return (
    <Layout
      page={page}
      onNavigate={setPage}
      title={meta.title}
      subtitle={meta.subtitle}
      modelBadge={modelBadge}
      theme={theme}
      onToggleTheme={() => setTheme((t) => (t === "dark" ? "light" : "dark"))}
    >
      {page === "overview" && (
        <Overview
          status={status}
          loading={loading}
          error={error}
          history={history}
          onClearHistory={() => setHistory([])}
          onGo={setPage}
        />
      )}
      {page === "analyzer" && <Analyzer onAnalyzed={addHistory} />}
      {page === "evaluation" && <Evaluation />}
      {page === "methodology" && <Methodology />}
      {page === "privacy" && <Privacy />}
    </Layout>
  );
}
