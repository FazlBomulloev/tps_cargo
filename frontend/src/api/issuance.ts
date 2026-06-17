import api from "./client";
import type { IssuanceOrder, Paginated } from "../types/api";

export interface CreateIssuanceData {
  client_id: number;
  parcel_ids: number[];
  payment_method: string | null;
  payment_status: string;
  comment?: string;
  custom_prices?: Record<number, number>;
}

export interface GetIssuancesParams {
  page?: number;
  per_page?: number;
  client_id?: number;
  from_date?: string;
  to_date?: string;
  [key: string]: unknown;
}

export const createIssuance = (data: CreateIssuanceData) =>
  api.post<IssuanceOrder>("/issuance", data);

export const getIssuances = (params?: GetIssuancesParams) =>
  api.get<Paginated<IssuanceOrder>>("/issuance", { params });

export const getIssuance = (id: number) => api.get<IssuanceOrder>(`/issuance/${id}`);
