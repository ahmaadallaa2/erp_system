import { api } from "../../../lib/api/axios";
import { API_ENDPOINTS } from "../../../lib/api/endpoints";
import type { SalesInvoice } from "../types/sales-invoice";

export async function getSalesInvoice(id: string): Promise<SalesInvoice> {
  const response = await api.get<SalesInvoice>(
    `${API_ENDPOINTS.sales.invoices}${id}/`
  );

  return response.data;
}