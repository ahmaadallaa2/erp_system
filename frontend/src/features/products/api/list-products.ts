import { api } from "../../../lib/api/axios";
import { API_ENDPOINTS } from "../../../lib/api/endpoints";
import type { Product } from "../types/product";

export async function listProducts(): Promise<Product[]> {
  const response = await api.get<Product[]>(API_ENDPOINTS.inventory.products);
  return Array.isArray(response.data) ? response.data : [];
}