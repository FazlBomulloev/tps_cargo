// Вес в кг без лишних нулей: 2.5, 2.55, 3 (максимум 2 знака
// после запятой). Возвращает строку вида "2.5 кг" либо "—".
export function fmtKg(v: number | string | null | undefined): string {
  if (v === null || v === undefined || v === "") return "—";
  const n = typeof v === "string" ? parseFloat(v) : v;
  if (Number.isNaN(n)) return String(v);
  return `${parseFloat(n.toFixed(2))} кг`;
}
