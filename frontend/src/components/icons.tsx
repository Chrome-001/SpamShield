import type { ReactNode } from "react";
import type { PageKey } from "../types";

export function ShieldIcon({ size = 22 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path
        d="M12 2.5 4.5 5.5v6c0 4.6 3.2 8.4 7.5 10 4.3-1.6 7.5-5.4 7.5-10v-6L12 2.5Z"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinejoin="round"
      />
      <path d="m9 11.5 2.2 2.2L15.5 9.5" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function icon(path: ReactNode, size = 17) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" aria-hidden="true">
      {path}
    </svg>
  );
}

const S = { stroke: "currentColor", strokeWidth: 1.8, strokeLinecap: "round", strokeLinejoin: "round" } as const;

export const Icons = {
  overview: icon(<path d="M4 4h7v7H4zM13 4h7v4h-7zM13 11h7v9h-7zM4 14h7v6H4z" {...S} />),
  analyzer: icon(<path d="M4 5h16v11H8l-4 4V5Z" {...S} />),
  evaluation: icon(<path d="M4 20V10M10 20V4M16 20v-7M22 20H2" {...S} />),
  methodology: icon(<path d="M5 4h14v16H5zM9 9h6M9 13h6M9 17h4" {...S} />),
  privacy: icon(<path d="M12 3 5 6v5c0 5 3 8.5 7 10 4-1.5 7-5 7-10V6l-7-3ZM12 8v4" {...S} />),
  alert: icon(<path d="M12 4 2.5 20h19L12 4Zm0 6v4m0 3v.5" {...S} />),
  check: icon(<path d="m4.5 12.5 5 5L19.5 7" {...S} />),
  info: icon(<path d="M12 8v.5M12 11v6M12 22a10 10 0 1 0 0-20 10 10 0 0 0 0 20Z" {...S} />),
};

export const NAV: Array<{ key: PageKey; label: string; blurb: string; icon: ReactNode }> = [
  { key: "overview", label: "Overview", blurb: "Model status & recent activity", icon: Icons.overview },
  { key: "analyzer", label: "Analyzer", blurb: "Inspect a suspicious message", icon: Icons.analyzer },
  { key: "evaluation", label: "Evaluation", blurb: "Held-out metrics & errors", icon: Icons.evaluation },
  { key: "methodology", label: "Methodology", blurb: "How the model works", icon: Icons.methodology },
  { key: "privacy", label: "Privacy", blurb: "Local-only guarantees", icon: Icons.privacy },
];
