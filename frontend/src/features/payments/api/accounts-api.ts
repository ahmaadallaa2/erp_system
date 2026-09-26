import { api } from "../../../lib/api/axios";
import { API_ENDPOINTS } from "../../../lib/api/endpoints";

export type AccountLookup = {
  id: string;
  code: string;
  name: string;
  account_type: string;
  normal_balance: string;
  is_postable: boolean;
  is_active: boolean;
};

export async function getAccounts() {
  const response = await api.get<AccountLookup[]>(
    API_ENDPOINTS.accounting.accounts
  );
  return Array.isArray(response.data) ? response.data : [];
}
