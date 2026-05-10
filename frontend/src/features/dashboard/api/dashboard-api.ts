import { api } from "../../../lib/api/axios";
import { API_ENDPOINTS } from "../../../lib/api/endpoints";

export type DashboardSummary = {
  total_sales: number | string;
  total_purchases: number | string;
  inventory_items: number;
  inventory_quantity: number | string;
  customers_receivable: number | string;
  suppliers_payable: number | string;
  low_stock_products: number;
};

export async function getDashboardSummary() {
  const response = await api.get<DashboardSummary>(API_ENDPOINTS.dashboard.summary);
  return response.data;
}
