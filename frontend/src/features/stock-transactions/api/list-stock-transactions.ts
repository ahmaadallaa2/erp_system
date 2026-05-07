import { api } from "../../../lib/api/axios";
import { API_ENDPOINTS } from "../../../lib/api/endpoints";
import type { StockTransaction } from "../types/stock-transaction";

export async function listStockTransactions(): Promise<StockTransaction[]> {
  const response = await api.get<StockTransaction[]>(
    API_ENDPOINTS.inventory.stockTransactions
  );

  return Array.isArray(response.data) ? response.data : [];
}