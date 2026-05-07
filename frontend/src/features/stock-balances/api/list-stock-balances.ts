import { api } from "../../../lib/api/axios";
import { API_ENDPOINTS } from "../../../lib/api/endpoints";
import type { StockBalance } from "../types/stock-balance";

export async function listStockBalances(): Promise<StockBalance[]> {
  const response = await api.get<StockBalance[]>(API_ENDPOINTS.inventory.stockBalances);
  return Array.isArray(response.data) ? response.data : [];
}