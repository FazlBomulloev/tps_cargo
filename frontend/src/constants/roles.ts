import type { Role } from "../types/api";

export const ROLE_LABELS: Record<Role, string> = {
  owner: "Владелец",
  admin_china: "Админ Китай",
  admin_dushanbe: "Админ Душанбе",
  staff: "Сотрудник",
};

export const ROLE_COLORS: Record<Role, string> = {
  owner: "var(--c-primary)",
  admin_china: "var(--c-info)",
  admin_dushanbe: "var(--c-warning)",
  staff: "var(--c-text-muted)",
};
