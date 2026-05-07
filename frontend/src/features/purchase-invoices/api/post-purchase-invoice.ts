import { api } from "../../../lib/api/axios";
import { API_ENDPOINTS } from "../../../lib/api/endpoints";

export async function postPurchaseInvoice(id: string) {
  const response = await api.post(
    `${API_ENDPOINTS.purchases.invoices}${id}/post/`
  );

  return response.data;
}