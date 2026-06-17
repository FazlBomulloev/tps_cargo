import api from "./client";
import type { StaffUser } from "../types/api";

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: StaffUser;
}

export interface UpdateProfileParams {
  full_name?: string;
  password?: string;
}

export const login = (login: string, password: string) =>
  api.post<LoginResponse>("/auth/login", { login, password });

export const getMe = () => api.get<StaffUser>("/auth/me");

export const updateProfile = (data: UpdateProfileParams) =>
  api.patch<StaffUser>("/auth/profile", data);

export const uploadAvatar = (file: File) => {
  const fd = new FormData();
  fd.append("file", file);
  return api.post<StaffUser>("/auth/profile/avatar", fd, {
    headers: { "Content-Type": "multipart/form-data" },
  });
};
