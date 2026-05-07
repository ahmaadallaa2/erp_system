import { api } from "../../../lib/api/axios";
import type { AskResponse } from "../types/ai-document";

export async function askAiDocument(documentId: string, question: string, topK = 5) {
  const response = await api.post<AskResponse>(
    `/ai-assistant/documents/${documentId}/ask/`,
    {
      question,
      top_k: topK,
    },
    {
      headers: {
        "Content-Type": "application/json",
      },
    }
  );

  return response.data;
}
