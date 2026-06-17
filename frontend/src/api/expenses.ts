import api from "./client";
import type { DeliveryMethod, Expense } from "../types/api";

export interface GetExpensesParams {
  page?: number;
  per_page?: number;
  category?: DeliveryMethod;
  from_date?: string;
  to_date?: string;
  [key: string]: unknown;
}

export const getExpenses = (params?: GetExpensesParams) =>
  api.get<Expense[]>("/expenses", { params });

export const createExpense = (data: {
  amount: number;
  category: DeliveryMethod;
  comment?: string;
}) => api.post<Expense>("/expenses", data);

export const deleteExpense = (id: number) =>
  api.delete(`/expenses/${id}`);
