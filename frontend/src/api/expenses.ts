import api from "./client";
import type { DeliveryMethod, Expense, Money } from "../types/api";

export interface GetExpensesParams {
  page?: number;
  per_page?: number;
  category?: DeliveryMethod;
  from_date?: string;
  to_date?: string;
  [key: string]: unknown;
}

export interface ExpensesListResponse {
  items: Expense[];
  total: number;
  total_sum: Money;
}

export const getExpenses = (params?: GetExpensesParams) =>
  api.get<ExpensesListResponse>("/expenses", { params });

export const createExpense = (data: {
  amount: number;
  category: DeliveryMethod;
  comment?: string;
}) => api.post<Expense>("/expenses", data);

export const deleteExpense = (id: number) =>
  api.delete(`/expenses/${id}`);
