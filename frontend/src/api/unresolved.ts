import api from "./client";
import type { UnresolvedParcel } from "../types/api";

export const getUnresolved = () => api.get<UnresolvedParcel[]>("/unresolved");

export const resolveParcel = (id: number, tps_code: string) =>
  api.post<UnresolvedParcel>(`/unresolved/${id}/resolve`, { tps_code });

export const deleteUnresolved = (id: number) =>
  api.delete(`/unresolved/${id}`);
