import dayjs from "dayjs";

export const TZ_DUSHANBE = "Asia/Dushanbe";

export function fmtKg(v: number | string | null | undefined): string {
  if (v === null || v === undefined || v === "") return "—";
  const n = typeof v === "string" ? parseFloat(v) : v;
  if (Number.isNaN(n)) return String(v);
  return `${parseFloat(n.toFixed(2))} кг`;
}

// Бэк хранит naive UTC: трактуем строку как UTC, выводим в Душанбе.
function toLocal(v: string) {
  return dayjs.utc(v).tz(TZ_DUSHANBE);
}

export function formatDateTimeRu(v: string | null | undefined): string {
  if (!v) return "—";
  return toLocal(v).format("DD.MM.YYYY HH:mm");
}

export function formatDateRu(v: string | null | undefined): string {
  if (!v) return "—";
  return toLocal(v).format("DD.MM.YYYY");
}
