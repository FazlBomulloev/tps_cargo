import api from "./client";
import type {
  OverviewStats,
  ParcelsByDayPoint,
  RevenuePoint,
  StaffActivityRow,
  StuckParcel,
  TopClient,
} from "../types/api";

export const getOverview = (period = "30d", from_date?: string, to_date?: string) =>
  api.get<OverviewStats>("/stats/overview", { params: { period, from_date, to_date } });

export const getParcelsByDay = (period = "30d", from_date?: string, to_date?: string) =>
  api.get<ParcelsByDayPoint[]>("/stats/parcels-by-day", {
    params: { period, from_date, to_date },
  });

export const getRevenue = (period = "30d", from_date?: string, to_date?: string) =>
  api.get<RevenuePoint[]>("/stats/revenue", { params: { period, from_date, to_date } });

export const getTopClients = (
  period = "30d",
  from_date?: string,
  to_date?: string,
  limit = 10,
  sort_by = "amount",
) =>
  api.get<TopClient[]>("/stats/top-clients", {
    params: { period, from_date, to_date, limit, sort_by },
  });

export const getStuckParcels = (
  period = "30d",
  from_date?: string,
  to_date?: string,
  days = 14,
) =>
  api.get<StuckParcel[]>("/stats/stuck-parcels", {
    params: { period, from_date, to_date, days },
  });

export const getStaffActivity = (period = "30d", from_date?: string, to_date?: string) =>
  api.get<StaffActivityRow[]>("/stats/staff-activity", {
    params: { period, from_date, to_date },
  });
