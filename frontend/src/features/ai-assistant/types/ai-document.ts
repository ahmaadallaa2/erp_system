export type AiDocument = {
  id: string;
  file: string;
  original_filename: string;
  file_type: string;
  file_size: number;
  status: "uploaded" | "processing" | "ready" | "failed";
  notes: string;
  chunks_count: number;
  created_at: string;
  updated_at: string;
};

export type AskCitation = {
  chunk_id: string;
  chunk_index: number;
  page_number: number | null;
  text: string;
  score: number;
};

export type AskResponse = {
  answer: string;
  citations: AskCitation[];
};

export type RetrievalComparisonResult = {
  method: "keyword" | "semantic";
  score: number;
  chunk_id: string;
  chunk_index: number;
  page_number: number | null;
  text: string;
};

export type SemanticSearchResult = {
  score: number;
  chunk: {
    id: string;
    chunk_index: number;
    page_number: number | null;
    text: string;
  };
};
