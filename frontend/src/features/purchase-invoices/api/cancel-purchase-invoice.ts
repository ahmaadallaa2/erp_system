import { api } from "../../../lib/api/axios";
import { API_ENDPOINTS } from "../../../lib/api/endpoints";

export async function cancelPurchaseInvoice(id: string) {
  const response = await api.post(`${API_ENDPOINTS.purchases.invoices}${id}/cancel/`);
  return response.data;
}
