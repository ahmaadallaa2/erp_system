import { api } from "../../../lib/api/axios";
import type { AiDocument } from "../types/ai-document";

export async function uploadAiDocument(file: File) {
  const formData = new FormData();
  formData.append("file", file);

  const response = await api.post<AiDocument>(
    "/ai-assistant/documents/",
    formData
  );

  return response.data;
}
