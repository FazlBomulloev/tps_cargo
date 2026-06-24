import api from "./client";
import type { UnresolvedParcel } from "../types/api";

export const getUnresolved = (search?: string) =>
  api.get<UnresolvedParcel[]>("/unresolved", { params: search ? { search } : undefined });

export const resolveParcel = (id: number, tps_code: string) =>
  api.post<UnresolvedParcel>(`/unresolved/${id}/resolve`, { tps_code });

export const deleteUnresolved = (id: number) =>
  api.delete(`/unresolved/${id}`);
