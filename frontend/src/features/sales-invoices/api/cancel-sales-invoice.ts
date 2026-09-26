import { api } from "../../../lib/api/axios";
import { API_ENDPOINTS } from "../../../lib/api/endpoints";

export async function cancelSalesInvoice(id: string) {
  const response = await api.post(`${API_ENDPOINTS.sales.invoices}${id}/cancel/`);
  return response.data;
}
