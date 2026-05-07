import { api } from "../../../lib/api/axios";
import { API_ENDPOINTS } from "../../../lib/api/endpoints";

export type CreateSalesInvoicePayload = {
  branch: string;
  customer: string;
  warehouse: string;
  date: string;
  notes?: string;
};

export async function createSalesInvoice(
  payload: CreateSalesInvoicePayload
) {
  const response = await api.post(API_ENDPOINTS.sales.invoices, payload);
  return response.data;
}