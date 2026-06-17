import api from "./client";
import type { PermissionKey, Role, StaffUser } from "../types/api";

export interface CreateStaffData {
  full_name: string;
  login: string;
  password: string;
  role: Role;
  warehouse_id?: number | null;
}

export interface UpdateStaffData {
  full_name?: string;
  role?: Role;
  warehouse_id?: number | null;
  is_active?: boolean;
}

export const getStaff = () => api.get<StaffUser[]>("/staff");

export const createStaff = (data: CreateStaffData) =>
  api.post<StaffUser>("/staff", data);

export const updateStaff = (id: number, data: UpdateStaffData) =>
  api.patch<StaffUser>(`/staff/${id}`, data);

export const deleteStaff = (id: number) => api.delete(`/staff/${id}`);

export const resetPassword = (id: number, new_password: string) =>
  api.post(`/staff/${id}/reset-password`, { new_password });

export const updatePermissions = (id: number, permissions: PermissionKey[]) =>
  api.patch<StaffUser>(`/staff/${id}/permissions`, { permissions });

export interface PermissionRegistryEntry {
  key: PermissionKey;
  label: string;
}

export const getPermissionsRegistry = () =>
  api.get<{ permissions: PermissionRegistryEntry[] }>("/staff/permissions/registry");
