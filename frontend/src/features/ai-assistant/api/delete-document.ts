import { api } from "../../../lib/api/axios";

export async function deleteAiDocument(documentId: string) {
  await api.delete(`/ai-assistant/documents/${documentId}/`);
}
