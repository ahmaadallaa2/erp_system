import { api } from "../../../lib/api/axios";
import { API_ENDPOINTS } from "../../../lib/api/endpoints";
import type { StockMovement } from "../types/stock-movement";

export async function listStockMovements(): Promise<StockMovement[]> {
  const response = await api.get<StockMovement[]>(
    API_ENDPOINTS.inventory.stockMovements
  );

  return Array.isArray(response.data) ? response.data : [];
}