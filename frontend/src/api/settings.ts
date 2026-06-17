import api from "./client";
import type { Setting } from "../types/api";

export const getSettings = () => api.get<Setting[]>("/settings");

export const getSetting = (key: string) => api.get<Setting>(`/settings/${key}`);

export const updateSetting = (key: string, value: string) =>
  api.put<Setting>(`/settings/${key}`, { value });
