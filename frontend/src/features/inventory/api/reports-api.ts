import { api } from "../../../lib/api/axios";
import { API_ENDPOINTS } from "../../../lib/api/endpoints";

export type ProductMovementFilters = {
  product?: string;
  warehouse?: string;
  start_date?: string;
  end_date?: string;
  transaction_type?: string;
};

export type ProductMovementRow = {
  id?: string;
  date: string;
  transaction: unknown;
  transaction_type: string;
  type?: string;
  product: unknown;
  warehouse: unknown;
  quantity_in: string | number;
  quantity_out: string | number;
  cost: string | number;
};

export type WarehouseBalanceFilters = {
  warehouse?: string;
  product?: string;
  low_stock?: string;
};

export type WarehouseBalanceReportRow = {
  id?: string;
  warehouse: unknown;
  product: unknown;
  quantity: string | number;
  reorder_point: string | number;
  low_stock: boolean;
  average_cost: string | number;
  estimated_value: string | number;
};

export async function getProductMovementHistory(filters: ProductMovementFilters) {
  const response = await api.get<ProductMovementRow[] | { results: ProductMovementRow[] }>(
    API_ENDPOINTS.inventory.reports.productMovements,
    { params: cleanParams(filters) }
  );

  return Array.isArray(response.data) ? response.data : response.data.results || [];
}

export async function getWarehouseBalanceReport(filters: WarehouseBalanceFilters) {
  const response = await api.get<WarehouseBalanceReportRow[] | { results: WarehouseBalanceReportRow[] }>(
    API_ENDPOINTS.inventory.reports.warehouseBalances,
    { params: cleanParams(filters) }
  );

  return Array.isArray(response.data) ? response.data : response.data.results || [];
}

function cleanParams<T extends Record<string, string | undefined>>(params: T) {
  return Object.fromEntries(
    Object.entries(params).filter(([, value]) => value !== undefined && value !== "")
  );
}
