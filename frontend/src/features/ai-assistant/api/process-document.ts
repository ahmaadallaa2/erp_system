import { api } from "../../../lib/api/axios";
import type { AiDocument } from "../types/ai-document";

export async function processAiDocument(documentId: string) {
  const response = await api.post<AiDocument>(
    `/ai-assistant/documents/${documentId}/process/`
  );
  return response.data;
}
