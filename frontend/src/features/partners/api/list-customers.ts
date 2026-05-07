import { api } from "../../../lib/api/axios";
import { API_ENDPOINTS } from "../../../lib/api/endpoints";
import type { Partner } from "../types/partner";

export async function listCustomers(): Promise<Partner[]> {
  const response = await api.get<Partner[]>(API_ENDPOINTS.partners.customers);
  return Array.isArray(response.data) ? response.data : [];
}