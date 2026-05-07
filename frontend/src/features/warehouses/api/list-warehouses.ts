import { api } from "../../../lib/api/axios";
import { API_ENDPOINTS } from "../../../lib/api/endpoints";
import type { Warehouse } from "../types/warehouse";

export async function listWarehouses(): Promise<Warehouse[]> {
  const response = await api.get<Warehouse[]>(API_ENDPOINTS.inventory.warehouses);
  return Array.isArray(response.data) ? response.data : [];
}