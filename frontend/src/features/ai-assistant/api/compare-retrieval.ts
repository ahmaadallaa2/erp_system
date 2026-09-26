import { api } from "../../../lib/api/axios";
import type {
  RetrievalComparisonResult,
  SemanticSearchResult,
} from "../types/ai-document";

export async function keywordSearchDocument(
  documentId: string,
  query: string,
  topK = 5
) {
  const response = await api.post<RetrievalComparisonResult[]>(
    `/ai-assistant/documents/${documentId}/keyword-search/`,
    {
      query,
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

export async function semanticSearchDocument(
  documentId: string,
  query: string,
  topK = 5
) {
  const response = await api.post<SemanticSearchResult[]>(
    `/ai-assistant/documents/${documentId}/search/`,
    {
      query,
      top_k: topK,
    },
    {
      headers: {
        "Content-Type": "application/json",
      },
    }
  );

  return response.data.map((result) => ({
    method: "semantic" as const,
    score: result.score,
    chunk_id: result.chunk.id,
    chunk_index: result.chunk.chunk_index,
    page_number: result.chunk.page_number,
    text: result.chunk.text,
  }));
}
