import { api } from "../../../lib/api/axios";
import { API_ENDPOINTS } from "../../../lib/api/endpoints";
import type { Partner } from "../types/partner";

export async function listPartners(): Promise<Partner[]> {
  const response = await api.get<Partner[]>(API_ENDPOINTS.partners.list);
  return Array.isArray(response.data) ? response.data : [];
}