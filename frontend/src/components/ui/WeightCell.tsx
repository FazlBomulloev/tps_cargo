import { Tooltip } from "antd";

export interface WeightCellProps {
  value: number | string;
  unit?: "kg" | "t";
}

export function WeightCell({ value, unit = "kg" }: WeightCellProps) {
  const num = typeof value === "string" ? parseFloat(value) : value;
  const safe = Number.isFinite(num) ? num : 0;
  const display = unit === "t" ? safe / 1000 : safe;
  const label = unit === "t" ? "т" : "кг";
  const text = display.toLocaleString("ru-RU", {
    minimumFractionDigits: unit === "t" ? 3 : 2,
    maximumFractionDigits: unit === "t" ? 3 : 2,
  });
  return (
    <Tooltip title={`${safe} кг`}>
      <span className="num" style={{ fontVariantNumeric: "tabular-nums" }}>
        {text} <span style={{ color: "var(--c-text-muted)", fontSize: "var(--text-xs)" }}>{label}</span>
      </span>
    </Tooltip>
  );
}
