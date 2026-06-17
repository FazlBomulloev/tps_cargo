import { Link } from "react-router-dom";

export interface BrandLogoProps {
  collapsed?: boolean;
}

export function BrandLogo({ collapsed = false }: BrandLogoProps) {
  return (
    <Link
      to="/"
      style={{
        display: "flex",
        alignItems: "center",
        gap: 12,
        padding: "20px 16px",
        textDecoration: "none",
        borderBottom: "1px solid rgba(255, 255, 255, 0.06)",
      }}
    >
      <div
        style={{
          width: 36,
          height: 36,
          borderRadius: 10,
          background: "var(--c-primary)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          color: "#fff",
          fontFamily: "var(--font-mono)",
          fontWeight: 700,
          fontSize: 16,
          letterSpacing: "-0.02em",
          flexShrink: 0,
        }}
      >
        Cg
      </div>
      {!collapsed && (
        <div style={{ overflow: "hidden", whiteSpace: "nowrap" }}>
          <div style={{ color: "#fff", fontSize: 16, fontWeight: 700, letterSpacing: "-0.02em" }}>
            Cargo TPS
          </div>
          <div style={{ color: "var(--c-sidebar-text-muted)", fontSize: 11, marginTop: 2 }}>
            CN → TJ logistics
          </div>
        </div>
      )}
    </Link>
  );
}
