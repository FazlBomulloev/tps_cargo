import api from "./client";
import type { AuditLog, Paginated } from "../types/api";

export interface GetAuditLogsParams {
  page?: number;
  per_page?: number;
  staff_id?: number;
  action?: string;
  entity_type?: string;
  from_date?: string;
  to_date?: string;
  [key: string]: unknown;
}

export const getAuditLogs = (params?: GetAuditLogsParams) =>
  api.get<Paginated<AuditLog>>("/audit-logs", { params });
