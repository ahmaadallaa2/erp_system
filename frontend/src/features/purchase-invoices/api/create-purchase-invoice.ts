import { api } from "../../../lib/api/axios";
import { API_ENDPOINTS } from "../../../lib/api/endpoints";

export type CreatePurchaseInvoicePayload = {
  branch: string;
  supplier: string;
  warehouse: string;
  invoice_date: string;
  vendor_bill_number?: string;
  shipping_cost?: string;
  clearance_cost?: string;
  commission_percentage?: string;
  notes?: string;
};

export async function createPurchaseInvoice(
  payload: CreatePurchaseInvoicePayload
) {
  const response = await api.post(API_ENDPOINTS.purchases.invoices, payload);
  return response.data;
}