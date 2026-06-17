import api from "./client";
import type {
  DeliveryMethod,
  ParcelChina,
  ParcelDushanbe,
  ParcelStatus,
  Paginated,
} from "../types/api";

export interface GetChinaParcelsParams {
  page?: number;
  per_page?: number;
  q?: string;
  warehouse_id?: number;
  [key: string]: unknown;
}

export interface GetAllParcelsParams {
  page?: number;
  per_page?: number;
  q?: string;
  status?: ParcelStatus;
  delivery_method?: DeliveryMethod;
  [key: string]: unknown;
}

export interface GetParcelsParams {
  page?: number;
  per_page?: number;
  q?: string;
  status?: ParcelStatus;
  [key: string]: unknown;
}

export interface AddDushanbeParcelData {
  track_id: string;
  tps_code?: string;
  weight_kg: number;
  volume_m3?: number;
  delivery_method: DeliveryMethod;
  comment?: string;
  shelf?: string;
}

export interface AddDushanbeBulkData {
  tps_code?: string;
  track_ids: string[];
  weight_kg: number;
  delivery_method: DeliveryMethod;
  volume_m3?: number;
  comment?: string;
  shelf?: string;
}

export interface UpdateParcelData {
  weight_kg?: number;
  volume_m3?: number;
  delivery_method?: DeliveryMethod;
  comment?: string;
  status?: ParcelStatus;
}

export const getChinaParcels = (params?: GetChinaParcelsParams) =>
  api.get<Paginated<ParcelChina>>("/parcels/china", { params });

export const addChinaParcel = (track_id: string) =>
  api.post<ParcelChina>("/parcels/china", { track_id });

export interface ChinaBulkResult {
  added: number;
  total: number;
  duplicates?: number;
  items?: ParcelChina[];
}

export const addChinaBulk = (track_ids: string[]) =>
  api.post<ChinaBulkResult>("/parcels/china/bulk", { track_ids });

export const getAllParcels = (params?: GetAllParcelsParams) =>
  api.get<Paginated<ParcelDushanbe>>("/parcels/all", { params });

export const addDushanbeParcel = (data: AddDushanbeParcelData) =>
  api.post<ParcelDushanbe>("/parcels/dushanbe", data);

export interface DushanbeBulkResult {
  added: number;
  unresolved: number;
  duplicates: number;
  items?: ParcelDushanbe[];
}

export const addDushanbeBulk = (data: AddDushanbeBulkData) =>
  api.post<DushanbeBulkResult>("/parcels/dushanbe/bulk", data);

export const getParcels = (params?: GetParcelsParams) =>
  api.get<Paginated<ParcelDushanbe>>("/parcels", { params });

export const getParcel = (id: number) => api.get<ParcelDushanbe>(`/parcels/${id}`);

export const searchTrack = (track_id: string) =>
  api.get<ParcelDushanbe>(`/parcels/track/${track_id}`);

export const updateParcelStatus = (id: number, status: ParcelStatus) =>
  api.patch<ParcelDushanbe>(`/parcels/${id}/status`, { status });

export const updateParcel = (id: number, data: UpdateParcelData) =>
  api.patch<ParcelDushanbe>(`/parcels/${id}`, data);

export const deleteDushanbeParcel = (id: number) =>
  api.delete(`/parcels/dushanbe/${id}`);

export const deleteChinaParcel = (id: number) =>
  api.delete(`/parcels/china/${id}`);
