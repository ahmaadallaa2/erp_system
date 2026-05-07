import { api } from "../../../lib/api/axios";
import type { AiDocument } from "../types/ai-document";

export async function listAiDocuments() {
  const response = await api.get<AiDocument[]>("/ai-assistant/documents/");
  return response.data;
}
