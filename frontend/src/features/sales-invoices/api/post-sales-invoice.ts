import { api } from "../../../lib/api/axios";
import { API_ENDPOINTS } from "../../../lib/api/endpoints";

export async function postSalesInvoice(id: string) {
  const response = await api.post(`${API_ENDPOINTS.sales.invoices}${id}/post/`);
  return response.data;
}