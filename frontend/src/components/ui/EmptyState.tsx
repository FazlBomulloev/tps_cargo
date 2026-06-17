import type { ReactNode } from "react";
import { Empty } from "antd";

export interface EmptyStateProps {
  title?: string;
  description?: string;
  action?: ReactNode;
  image?: ReactNode;
}

export function EmptyState({ title = "Пусто", description, action, image }: EmptyStateProps) {
  return (
    <Empty
      image={image ?? Empty.PRESENTED_IMAGE_SIMPLE}
      description={
        <div>
          <div style={{ fontSize: "var(--text-base)", fontWeight: 600, color: "var(--c-text)" }}>{title}</div>
          {description && (
            <div style={{ fontSize: "var(--text-sm)", color: "var(--c-text-muted)", marginTop: 4 }}>
              {description}
            </div>
          )}
        </div>
      }
    >
      {action}
    </Empty>
  );
}
