import type { PermissionKey, Role } from "../types/api";

export interface PermissionEntry {
  key: PermissionKey;
  label: string;
}

// Единый источник правды для UI. Backend дублирует эти ключи в
// VALID_PERMISSIONS (backend/app/api/staff.py) и отдаёт совпадающий
// список через GET /api/staff/permissions/registry.
export const ALL_PERMISSIONS: readonly PermissionEntry[] = [
  { key: "dashboard", label: "Дашборд" },
  { key: "parcels_china", label: "Склад Китай" },
  { key: "parcels_dushanbe", label: "Склад Душанбе" },
  { key: "parcels_list", label: "Все посылки" },
  { key: "parcels_delete", label: "Удаление посылок" },
  { key: "issuance", label: "Выдача" },
  { key: "issuance_history", label: "История выдач" },
  { key: "clients", label: "Клиенты" },
  { key: "unresolved", label: "Неопознанные" },
  { key: "warehouses", label: "Склады" },
  { key: "tariffs", label: "Тарифы" },
  { key: "expenses", label: "Расходы" },
  { key: "staff", label: "Сотрудники" },
  { key: "settings", label: "Настройки" },
  { key: "audit", label: "Журнал" },
];

export function hasAccess(
  page: string,
  role: Role | null,
  permissions?: readonly string[],
): boolean {
  if (!role) return false;
  if (role === "owner") return true;
  if (!permissions || permissions.length === 0) return false;
  return permissions.includes(page);
}
