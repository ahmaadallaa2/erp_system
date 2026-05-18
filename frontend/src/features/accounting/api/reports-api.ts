import { api } from "../../../lib/api/axios";
import { API_ENDPOINTS } from "../../../lib/api/endpoints";

export type GeneralLedgerFilters = {
  start_date?: string;
  end_date?: string;
  account?: string;
  partner?: string;
};

export type GeneralLedgerRow = {
  id?: string;
  date: string;
  entry_number: string;
  reference: string | null;
  account: unknown;
  partner: unknown;
  debit: string | number;
  credit: string | number;
  running_balance: string | number;
};

export async function getGeneralLedger(filters: GeneralLedgerFilters) {
  const response = await api.get<GeneralLedgerRow[] | { results: GeneralLedgerRow[] }>(
    API_ENDPOINTS.accounting.reports.generalLedger,
    { params: cleanParams(filters) }
  );

  return Array.isArray(response.data) ? response.data : response.data.results || [];
}

function cleanParams(params: GeneralLedgerFilters) {
  return Object.fromEntries(
    Object.entries(params).filter(([, value]) => value !== undefined && value !== "")
  );
}
