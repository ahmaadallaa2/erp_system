import { api } from "../../../lib/api/axios";
import { API_ENDPOINTS } from "../../../lib/api/endpoints";
import type { PurchaseInvoice } from "../types/purchase-invoice";

export async function getPurchaseInvoice(id: string): Promise<PurchaseInvoice> {
  const response = await api.get<PurchaseInvoice>(
    `${API_ENDPOINTS.purchases.invoices}${id}/`
  );

  return response.data;
}