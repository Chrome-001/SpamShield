import type { ReactNode } from "react";
import type { PageKey } from "../types";
import { NAV, ShieldIcon } from "./icons";

interface Props {
  page: PageKey;
  onNavigate: (p: PageKey) => void;
  title: string;
  subtitle: string;
  modelBadge: string;
  theme: "light" | "dark";
  onToggleTheme: () => void;
  children: ReactNode;
}

export default function Layout({ page, onNavigate, title, subtitle, modelBadge, theme, onToggleTheme, children }: Props) {
  return (
    <div className="app-shell">
      <aside className="sidebar" aria-label="Primary">
        <div className="brand">
          <span className="brand-mark">
            <ShieldIcon size={22} />
          </span>
          <div>
            <h1>SpamShield</h1>
            <p>Local spam &amp; scam analyzer</p>
          </div>
        </div>

        <nav className="nav">
          <div className="nav-label">Workspace</div>
          {NAV.map((item) => (
            <button
              key={item.key}
              className={`nav-btn${page === item.key ? " active" : ""}`}
              onClick={() => onNavigate(item.key)}
              aria-current={page === item.key ? "page" : undefined}
            >
              {item.icon}
              {item.label}
            </button>
          ))}
        </nav>

        <div className="sidebar-card">
          <div>
            <span className={`status-dot ${modelBadge.startsWith("Ready") ? "ok" : "warn"}`} />
            <strong style={{ color: "#fff" }}>{modelBadge}</strong>
          </div>
          <div style={{ marginTop: 6 }}>Inference runs on this machine. No message is uploaded or stored.</div>
        </div>
      </aside>

      <div className="main">
        <header className="topbar">
          <div>
            <h2>{title}</h2>
            <p className="sub">{subtitle}</p>
          </div>
          <div className="topbar-spacer" />
          <span className="pill" title="All analysis happens locally">
            <span className="lock-dot" /> 100% local
          </span>
          <button className="icon-btn" onClick={onToggleTheme} aria-label="Toggle color theme">
            {theme === "dark" ? "Light mode" : "Dark mode"}
          </button>
        </header>
        <main className="content">{children}</main>
      </div>
    </div>
  );
}
