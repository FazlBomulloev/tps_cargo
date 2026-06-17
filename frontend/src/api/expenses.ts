import api from "./client";

export const getExpenses = (params?: Record<string, unknown>) =>
  api.get("/expenses", { params });

export const createExpense = (data: {
  amount: number;
  category: "avia" | "truck";
  comment?: string;
}) => api.post("/expenses", data);

export const deleteExpense = (id: number) =>
  api.delete(`/expenses/${id}`);
