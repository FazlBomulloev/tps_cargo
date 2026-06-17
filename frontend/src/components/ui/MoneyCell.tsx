import { Tooltip } from "antd";

export interface MoneyCellProps {
  value: number | string;
  currency?: string;
}

export function MoneyCell({ value, currency = "TJS" }: MoneyCellProps) {
  const num = typeof value === "string" ? parseFloat(value) : value;
  const safe = Number.isFinite(num) ? num : 0;
  const text = safe.toLocaleString("ru-RU", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  return (
    <Tooltip title={`${safe} ${currency}`}>
      <span className="num" style={{ fontVariantNumeric: "tabular-nums" }}>
        {text} <span style={{ color: "var(--c-text-muted)", fontSize: "var(--text-xs)" }}>{currency}</span>
      </span>
    </Tooltip>
  );
}
