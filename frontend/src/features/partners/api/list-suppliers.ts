import { api } from "../../../lib/api/axios";
import { API_ENDPOINTS } from "../../../lib/api/endpoints";
import type { Partner } from "../types/partner";

export async function listSuppliers(): Promise<Partner[]> {
  const response = await api.get<Partner[]>(API_ENDPOINTS.partners.suppliers);
  return Array.isArray(response.data) ? response.data : [];
}