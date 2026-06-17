// Вес в кг без лишних нулей: 2.5, 2.55, 3 (максимум 2 знака
// после запятой). Возвращает строку вида "2.5 кг" либо "—".
export function fmtKg(v: number | string | null | undefined): string {
  if (v === null || v === undefined || v === "") return "—";
  const n = typeof v === "string" ? parseFloat(v) : v;
  if (Number.isNaN(n)) return String(v);
  return `${parseFloat(n.toFixed(2))} кг`;
}

// Дата+время в формате "ДД.ММ.ГГГГ, ЧЧ:MM" (ru-RU). Используется в
// табличных колонках "Дата" — вынесено сюда, чтобы не дублировать
// одинаковый toLocaleString-конфиг в ParcelsList/ParcelsChina/ParcelsDushanbe/AuditLog.
export function formatDateTimeRu(v: string | null | undefined): string {
  if (!v) return "—";
  return new Date(v).toLocaleString("ru-RU", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}
