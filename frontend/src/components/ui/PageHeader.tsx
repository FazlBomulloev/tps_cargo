import type { ReactNode } from "react";
import { Typography } from "antd";

export interface PageHeaderProps {
  title: string;
  subtitle?: ReactNode;
  actions?: ReactNode;
}

export function PageHeader({ title, subtitle, actions }: PageHeaderProps) {
  return (
    <div
      className="page-header"
      style={{
        display: "flex",
        justifyContent: "space-between",
        alignItems: "flex-start",
        flexWrap: "wrap",
        gap: "var(--s-3)",
        rowGap: "var(--s-4)",
        marginBottom: "var(--s-5)",
      }}
    >
      <div>
        <Typography.Title level={3} style={{ margin: 0, fontWeight: 700, letterSpacing: "-0.02em" }}>
          {title}
        </Typography.Title>
        {subtitle && (
          <Typography.Text type="secondary" style={{ fontSize: "var(--text-sm)" }}>
            {subtitle}
          </Typography.Text>
        )}
      </div>
      {actions && (
        <div style={{ display: "flex", alignItems: "center", gap: "var(--s-3)", flexWrap: "wrap" }}>{actions}</div>
      )}
    </div>
  );
}
