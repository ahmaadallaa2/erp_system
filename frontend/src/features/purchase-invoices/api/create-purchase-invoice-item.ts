import { api } from "../../../lib/api/axios";
import { API_ENDPOINTS } from "../../../lib/api/endpoints";

export type CreatePurchaseInvoiceItemPayload = {
  invoice: string;
  product: string;
  quantity: string;
  unit_price: string;
  notes?: string;
};

export async function createPurchaseInvoiceItem(
  payload: CreatePurchaseInvoiceItemPayload
) {
  const response = await api.post(API_ENDPOINTS.purchases.invoiceItems, payload);
  return response.data;
}