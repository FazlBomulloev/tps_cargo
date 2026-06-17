import api from "./client";
import type { Client, Paginated } from "../types/api";

export interface GetClientsParams {
  page?: number;
  per_page?: number;
  q?: string;
  status?: string;
  [key: string]: unknown;
}

export interface UpdateClientData {
  full_name?: string;
  phone?: string;
  address?: string;
  lang?: string;
}

export const getClients = (params?: GetClientsParams) =>
  api.get<Paginated<Client>>("/clients", { params });

export const searchClients = (q: string) =>
  api.get<Client[]>("/clients/search", { params: { q } });

export const getClient = (id: number) => api.get<Client>(`/clients/${id}`);

export const updateClient = (id: number, data: UpdateClientData) =>
  api.patch<Client>(`/clients/${id}`, data);

export const blockClient = (id: number) =>
  api.patch<Client>(`/clients/${id}/block`);
