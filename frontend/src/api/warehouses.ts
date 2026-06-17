import api from "./client";
import type { Warehouse } from "../types/api";

export interface CreateWarehouseData {
  name: string;
  type: string;
  country?: string | null;
  city?: string | null;
  phone: string;
  region: string;
  address: string;
}

export interface UpdateWarehouseData {
  name?: string;
  type?: string;
  country?: string | null;
  city?: string | null;
  phone?: string;
  region?: string;
  address?: string;
  is_active?: boolean;
}

export const getWarehouses = () => api.get<Warehouse[]>("/warehouses");

export const getWarehouse = (id: number) => api.get<Warehouse>(`/warehouses/${id}`);

export const createWarehouse = (data: CreateWarehouseData) =>
  api.post<Warehouse>("/warehouses", data);

export const updateWarehouse = (id: number, data: UpdateWarehouseData) =>
  api.patch<Warehouse>(`/warehouses/${id}`, data);

export const deleteWarehouse = (id: number) =>
  api.delete(`/warehouses/${id}`);
