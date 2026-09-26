import { api } from "../../../lib/api/axios";
import { API_ENDPOINTS } from "../../../lib/api/endpoints";
import type { JournalEntryDetail } from "../types";

export async function getJournalEntry(id: string) {
  const response = await api.get<JournalEntryDetail>(
    API_ENDPOINTS.accounting.journalEntryDetail(id)
  );
  return response.data;
}
