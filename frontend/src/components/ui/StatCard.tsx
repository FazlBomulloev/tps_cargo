import type { ReactNode } from "react";
import { Card } from "antd";

export interface StatCardProps {
  title: string;
  value: ReactNode;
  caption?: string;
  icon?: ReactNode;
  accent?: "primary" | "warning" | "error" | "info" | "neutral";
  href?: string;
  onClick?: () => void;
}

export function StatCard({ title, value, caption, icon, accent = "neutral", href, onClick }: StatCardProps) {
  const accentColor = {
    primary: "var(--c-primary)",
    warning: "var(--c-warning)",
    error: "var(--c-error)",
    info: "var(--c-info)",
    neutral: "var(--c-text-muted)",
  }[accent];
  const interactive = !!(href || onClick);
  return (
    <Card
      hoverable={interactive}
      onClick={onClick}
      style={{
        cursor: interactive ? "pointer" : "default",
        height: "100%",
      }}
      styles={{ body: { padding: "var(--s-5)" } }}
    >
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          marginBottom: "var(--s-3)",
        }}
      >
        <span
          style={{
            fontSize: "var(--text-xs)",
            color: "var(--c-text-secondary)",
            textTransform: "uppercase",
            letterSpacing: "0.04em",
          }}
        >
          {title}
        </span>
        {icon && <span style={{ color: accentColor, fontSize: 18 }}>{icon}</span>}
      </div>
      <div
        className="num"
        style={{
          fontSize: "var(--text-xl)",
          fontWeight: 700,
          color: "var(--c-text)",
          lineHeight: "var(--lh-tight)",
        }}
      >
        {value}
      </div>
      {caption && (
        <div style={{ fontSize: "var(--text-xs)", color: "var(--c-text-muted)", marginTop: "var(--s-2)" }}>
          {caption}
        </div>
      )}
    </Card>
  );
}
