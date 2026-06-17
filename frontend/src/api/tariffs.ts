import api from "./client";
import type { DeliveryMethod, Tariff } from "../types/api";

export interface CreateTariffData {
  method: DeliveryMethod;
  price_per_kg: number;
  price_per_m3?: number;
  currency?: string;
  is_active?: boolean;
}

export interface UpdateTariffData {
  method?: DeliveryMethod;
  price_per_kg?: number;
  price_per_m3?: number;
  currency?: string;
  is_active?: boolean;
}

export const getTariffs = () => api.get<Tariff[]>("/tariffs");

export const getActiveTariffs = () => api.get<Tariff[]>("/tariffs/active");

export const createTariff = (data: CreateTariffData) =>
  api.post<Tariff>("/tariffs", data);

export const updateTariff = (id: number, data: UpdateTariffData) =>
  api.patch<Tariff>(`/tariffs/${id}`, data);
