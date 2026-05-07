import { api } from "../../../lib/api/axios";
import { API_ENDPOINTS } from "../../../lib/api/endpoints";
import type { PurchaseInvoice } from "../types/purchase-invoice";

export async function listPurchaseInvoices(): Promise<PurchaseInvoice[]> {
  const response = await api.get<PurchaseInvoice[]>(
    API_ENDPOINTS.purchases.invoices
  );

  return Array.isArray(response.data) ? response.data : [];
}