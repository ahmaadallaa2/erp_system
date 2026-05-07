import { api } from "../../../lib/api/axios";
import { API_ENDPOINTS } from "../../../lib/api/endpoints";

export type CreateSalesInvoiceItemPayload = {
  invoice: string;
  product: string;
  quantity: string;
  unit_price: string;
  notes?: string;
};

export async function createSalesInvoiceItem(
  payload: CreateSalesInvoiceItemPayload
) {
  const response = await api.post(API_ENDPOINTS.sales.invoiceItems, payload);
  return response.data;
}