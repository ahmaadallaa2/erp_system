import { useEffect, useMemo, useState } from "react";
import axios from "axios";
import { askAiDocument } from "../api/ask-document";
import {
  keywordSearchDocument,
  semanticSearchDocument,
} from "../api/compare-retrieval";
import { deleteAiDocument } from "../api/delete-document";
import { listAiDocuments } from "../api/list-documents";
import { processAiDocument } from "../api/process-document";
import { uploadAiDocument } from "../api/upload-document";
import type {
  AiDocument,
  AskResponse,
  RetrievalComparisonResult,
} from "../types/ai-document";

const EXAMPLE_QUESTIONS = [
  "What is this contract about?",
  "What are the payment terms?",
  "Who are the parties involved?",
  "What happens if one party breaches the agreement?",
  "Summarize this contract in simple terms.",
  "List the important clauses in this agreement.",
];

function AiAssistantPage() {
  const [documents, setDocuments] = useState<AiDocument[]>([]);
  const [selectedDocumentId, setSelectedDocumentId] = useState("");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState<AskResponse | null>(null);
  const [comparisonDocumentId, setComparisonDocumentId] = useState("");
  const [comparisonQuery, setComparisonQuery] = useState("");
  const [keywordResults, setKeywordResults] = useState<RetrievalComparisonResult[]>([]);
  const [semanticResults, setSemanticResults] = useState<RetrievalComparisonResult[]>([]);
  const [comparisonLoading, setComparisonLoading] = useState(false);
  const [loading, setLoading] = useState(false);
  const [busyDocumentId, setBusyDocumentId] = useState("");
  const [error, setError] = useState("");

  const selectedDocument = useMemo(
    () => documents.find((document) => document.id === selectedDocumentId),
    [documents, selectedDocumentId]
  );

  const processedDocuments = useMemo(
    () => documents.filter((document) => document.status === "ready"),
    [documents]
  );

  useEffect(() => {
    loadDocuments();
  }, []);

  useEffect(() => {
    if (
      processedDocuments.length > 0 &&
      !processedDocuments.some((document) => document.id === comparisonDocumentId)
    ) {
      setComparisonDocumentId(processedDocuments[0].id);
    }
  }, [comparisonDocumentId, processedDocuments]);

  async function loadDocuments() {
    try {
      setLoading(true);
      setError("");
      const result = await listAiDocuments();
      setDocuments(Array.isArray(result) ? result : []);
      if (!selectedDocumentId && result.length > 0) {
        setSelectedDocumentId(result[0].id);
      }
    } catch (err) {
      console.error("AI documents load error:", err);
      setError("Failed to load documents.");
    } finally {
      setLoading(false);
    }
  }

  async function handleUpload() {
    if (!selectedFile) {
      setError("Choose a PDF or DOCX file first.");
      return;
    }

    try {
      setLoading(true);
      setError("");
      const document = await uploadAiDocument(selectedFile);
      setDocuments((current) => [document, ...current]);
      setSelectedDocumentId(document.id);
      setSelectedFile(null);
    } catch (err) {
      const backendError = getBackendErrorMessage(err);
      console.error("AI document upload error:", {
        error: err,
        backendResponse: axios.isAxiosError(err) ? err.response?.data : null,
      });
      setError(backendError || "Failed to upload document.");
    } finally {
      setLoading(false);
    }
  }

  async function handleProcess(documentId: string) {
    try {
      setBusyDocumentId(documentId);
      setError("");
      const updated = await processAiDocument(documentId);
      setDocuments((current) =>
        current.map((document) => (document.id === documentId ? updated : document))
      );
    } catch (err) {
      const backendError = getBackendErrorMessage(err);
      console.error("AI document process error:", {
        error: err,
        backendResponse: axios.isAxiosError(err) ? err.response?.data : null,
      });
      setError(backendError || "Failed to process document.");
    } finally {
      setBusyDocumentId("");
    }
  }

  async function handleDelete(document: AiDocument) {
    const displayName = document.original_filename || "this document";
    const confirmed = window.confirm(`Delete ${displayName}?`);

    if (!confirmed) {
      return;
    }

    try {
      setBusyDocumentId(document.id);
      setError("");
      await deleteAiDocument(document.id);
      setDocuments((current) => current.filter((item) => item.id !== document.id));

      if (selectedDocumentId === document.id) {
        setSelectedDocumentId("");
        setAnswer(null);
      }

      if (comparisonDocumentId === document.id) {
        setComparisonDocumentId("");
        setKeywordResults([]);
        setSemanticResults([]);
      }
    } catch (err) {
      const backendError = getBackendErrorMessage(err);
      console.error("AI document delete error:", {
        error: err,
        backendResponse: axios.isAxiosError(err) ? err.response?.data : null,
      });
      setError(backendError || "Failed to delete document.");
    } finally {
      setBusyDocumentId("");
    }
  }

  async function handleCompareRetrieval() {
    if (!comparisonDocumentId) {
      setError("Select a processed document first.");
      return;
    }

    if (!comparisonQuery.trim()) {
      setError("Type a comparison query first.");
      return;
    }

    try {
      setComparisonLoading(true);
      setError("");
      setKeywordResults([]);
      setSemanticResults([]);

      const [keyword, semantic] = await Promise.all([
        keywordSearchDocument(comparisonDocumentId, comparisonQuery.trim(), 5),
        semanticSearchDocument(comparisonDocumentId, comparisonQuery.trim(), 5),
      ]);

      setKeywordResults(keyword);
      setSemanticResults(semantic);
    } catch (err) {
      const backendError = getBackendErrorMessage(err);
      console.error("AI retrieval comparison error:", {
        error: err,
        backendResponse: axios.isAxiosError(err) ? err.response?.data : null,
      });
      setError(backendError || "Failed to compare retrieval results.");
    } finally {
      setComparisonLoading(false);
    }
  }

  async function handleAsk() {
    if (!selectedDocumentId) {
      setError("Select a document first.");
      return;
    }

    if (!question.trim()) {
      setError("Type a question first.");
      return;
    }

    try {
      setLoading(true);
      setError("");
      setAnswer(null);
      const result = await askAiDocument(selectedDocumentId, question.trim(), 5);
      setAnswer(result);
    } catch (err) {
      const backendError = getBackendErrorMessage(err);
      console.error("AI document ask error:", {
        error: err,
        backendResponse: axios.isAxiosError(err) ? err.response?.data : null,
      });
      setError(backendError || "Failed to get an answer.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main>
      <div style={{ marginBottom: "20px" }}>
        <h1 style={{ margin: 0 }}>AI Document Assistant</h1>
        <p style={{ marginTop: "8px", color: "#666" }}>
          Upload documents, process text, and ask questions with citations.
        </p>
      </div>

      {error && <div style={errorStyle}>{error}</div>}

      <section style={panelStyle}>
        <h2 style={sectionTitleStyle}>Upload Document</h2>
        <div style={uploadRowStyle}>
          <input
            accept=".pdf,.docx"
            type="file"
            onChange={(event) => setSelectedFile(event.target.files?.[0] ?? null)}
          />
          <button disabled={loading} onClick={handleUpload} style={primaryButtonStyle}>
            Upload
          </button>
        </div>
      </section>

      <section style={panelStyle}>
        <h2 style={sectionTitleStyle}>Documents</h2>
        {loading && documents.length === 0 && <p>Loading documents...</p>}
        {!loading && documents.length === 0 && <p>No documents uploaded yet.</p>}

        {documents.length > 0 && (
          <div style={{ overflowX: "auto" }}>
            <table style={tableStyle}>
              <thead>
                <tr>
                  <th style={thStyle}>File</th>
                  <th style={thStyle}>Type</th>
                  <th style={thStyle}>Status</th>
                  <th style={thStyle}>Chunks</th>
                  <th style={thStyle}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {documents.map((document) => (
                  <tr key={document.id}>
                    <td style={tdStyle}>
                      <label style={radioLabelStyle}>
                        <input
                          checked={selectedDocumentId === document.id}
                          name="selected-document"
                          onChange={() => {
                            setSelectedDocumentId(document.id);
                            setAnswer(null);
                          }}
                          type="radio"
                        />
                        {document.original_filename || "Untitled document"}
                      </label>
                    </td>
                    <td style={tdStyle}>{document.file_type || "-"}</td>
                    <td style={tdStyle}>{document.status}</td>
                    <td style={tdStyle}>{document.chunks_count}</td>
                    <td style={tdStyle}>
                      <button
                        disabled={busyDocumentId === document.id}
                        onClick={() => handleProcess(document.id)}
                        style={secondaryButtonStyle}
                      >
                        {busyDocumentId === document.id ? "Processing..." : "Process"}
                      </button>
                      <button
                        disabled={busyDocumentId === document.id}
                        onClick={() => handleDelete(document)}
                        style={dangerButtonStyle}
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <section style={panelStyle}>
        <h2 style={sectionTitleStyle}>Ask</h2>
        <div style={{ marginBottom: "12px", color: "#555" }}>
          Selected: {selectedDocument?.original_filename || "No document selected"}
        </div>

        <div style={examplesContainerStyle}>
          <div style={examplesTitleStyle}>Example Questions</div>
          <div style={chipsStyle}>
            {EXAMPLE_QUESTIONS.map((example) => (
              <button
                key={example}
                onClick={() => setQuestion(example)}
                style={chipButtonStyle}
                type="button"
              >
                {example}
              </button>
            ))}
          </div>
        </div>

        <textarea
          onChange={(event) => setQuestion(event.target.value)}
          placeholder="Ask a question about the selected document"
          rows={3}
          style={textareaStyle}
          value={question}
        />
        <button disabled={loading} onClick={handleAsk} style={primaryButtonStyle}>
          Ask
        </button>
      </section>

      <section style={panelStyle}>
        <h2 style={sectionTitleStyle}>Retrieval Comparison</h2>
        <div style={comparisonControlsStyle}>
          <select
            disabled={processedDocuments.length === 0 || comparisonLoading}
            onChange={(event) => {
              setComparisonDocumentId(event.target.value);
              setKeywordResults([]);
              setSemanticResults([]);
            }}
            style={selectStyle}
            value={comparisonDocumentId}
          >
            {processedDocuments.length === 0 && (
              <option value="">No processed documents</option>
            )}
            {processedDocuments.map((document) => (
              <option key={document.id} value={document.id}>
                {document.original_filename || "Untitled document"}
              </option>
            ))}
          </select>
          <input
            disabled={comparisonLoading}
            onChange={(event) => setComparisonQuery(event.target.value)}
            placeholder="Search query"
            style={comparisonInputStyle}
            type="text"
            value={comparisonQuery}
          />
          <button
            disabled={comparisonLoading || processedDocuments.length === 0}
            onClick={handleCompareRetrieval}
            style={primaryButtonStyle}
            type="button"
          >
            {comparisonLoading ? "Comparing..." : "Compare Retrieval"}
          </button>
        </div>

        <div style={comparisonGridStyle}>
          <RetrievalResultsColumn title="Keyword Search Results" results={keywordResults} />
          <RetrievalResultsColumn title="Semantic Search Results" results={semanticResults} />
        </div>
      </section>

      {answer && (
        <section style={panelStyle}>
          <h2 style={sectionTitleStyle}>Answer</h2>
          <p style={answerStyle}>{answer.answer}</p>

          <h3 style={citationTitleStyle}>Citations</h3>
          {answer.citations.length === 0 && <p>No citations returned.</p>}
          {answer.citations.map((citation) => (
            <article key={citation.chunk_id} style={citationStyle}>
              <div style={citationMetaStyle}>
                Chunk {citation.chunk_index}
                {citation.page_number ? ` | Page ${citation.page_number}` : ""}
                {" | "}
                Score {citation.score.toFixed(3)}
              </div>
              <p style={{ margin: 0 }}>{citation.text}</p>
            </article>
          ))}
        </section>
      )}
    </main>
  );
}

type RetrievalResultsColumnProps = {
  title: string;
  results: RetrievalComparisonResult[];
};

function RetrievalResultsColumn({ title, results }: RetrievalResultsColumnProps) {
  return (
    <div style={comparisonColumnStyle}>
      <h3 style={comparisonTitleStyle}>{title}</h3>
      {results.length === 0 && <p style={emptyResultStyle}>No results yet.</p>}
      {results.map((result) => (
        <article key={`${result.method}-${result.chunk_id}`} style={citationStyle}>
          <div style={citationMetaStyle}>
            {result.method} | Score {result.score.toFixed(3)} | Chunk{" "}
            {result.chunk_index}
            {result.page_number ? ` | Page ${result.page_number}` : ""}
          </div>
          <p style={previewTextStyle}>{getTextPreview(result.text)}</p>
        </article>
      ))}
    </div>
  );
}

function getTextPreview(text: string) {
  const normalized = text.replace(/\s+/g, " ").trim();
  return normalized.length > 280 ? `${normalized.slice(0, 280)}...` : normalized;
}

function getBackendErrorMessage(error: unknown) {
  if (!axios.isAxiosError(error)) {
    return "";
  }

  const data = error.response?.data;

  if (!data) {
    return error.message;
  }

  if (typeof data === "string") {
    return data;
  }

  if (typeof data.detail === "string") {
    return data.detail;
  }

  if (Array.isArray(data.detail)) {
    return data.detail.join(" ");
  }

  if (typeof data === "object") {
    return JSON.stringify(data);
  }

  return error.message;
}

const panelStyle: React.CSSProperties = {
  background: "#fff",
  border: "1px solid #ddd",
  borderRadius: "8px",
  marginBottom: "16px",
  padding: "16px",
};

const sectionTitleStyle: React.CSSProperties = {
  fontSize: "18px",
  margin: "0 0 12px",
};

const uploadRowStyle: React.CSSProperties = {
  alignItems: "center",
  display: "flex",
  flexWrap: "wrap",
  gap: "12px",
};

const primaryButtonStyle: React.CSSProperties = {
  background: "#2563eb",
  border: "none",
  borderRadius: "8px",
  color: "#fff",
  cursor: "pointer",
  fontWeight: 700,
  padding: "10px 16px",
};

const secondaryButtonStyle: React.CSSProperties = {
  background: "#f8fafc",
  border: "1px solid #cbd5e1",
  borderRadius: "8px",
  cursor: "pointer",
  padding: "8px 12px",
};

const dangerButtonStyle: React.CSSProperties = {
  background: "#fff1f2",
  border: "1px solid #fecdd3",
  borderRadius: "8px",
  color: "#be123c",
  cursor: "pointer",
  marginLeft: "8px",
  padding: "8px 12px",
};

const errorStyle: React.CSSProperties = {
  background: "#fef2f2",
  border: "1px solid #fecaca",
  borderRadius: "8px",
  color: "#991b1b",
  marginBottom: "16px",
  padding: "12px",
};

const tableStyle: React.CSSProperties = {
  borderCollapse: "collapse",
  width: "100%",
};

const thStyle: React.CSSProperties = {
  background: "#f8fafc",
  borderBottom: "1px solid #ddd",
  fontSize: "14px",
  padding: "10px",
  textAlign: "left",
};

const tdStyle: React.CSSProperties = {
  borderBottom: "1px solid #eee",
  fontSize: "14px",
  padding: "10px",
};

const radioLabelStyle: React.CSSProperties = {
  alignItems: "center",
  display: "flex",
  gap: "8px",
};

const textareaStyle: React.CSSProperties = {
  border: "1px solid #cbd5e1",
  borderRadius: "8px",
  boxSizing: "border-box",
  display: "block",
  marginBottom: "12px",
  padding: "10px",
  resize: "vertical",
  width: "100%",
};

const selectStyle: React.CSSProperties = {
  border: "1px solid #cbd5e1",
  borderRadius: "8px",
  minWidth: "220px",
  padding: "10px",
};

const comparisonControlsStyle: React.CSSProperties = {
  alignItems: "center",
  display: "flex",
  flexWrap: "wrap",
  gap: "10px",
  marginBottom: "14px",
};

const comparisonInputStyle: React.CSSProperties = {
  border: "1px solid #cbd5e1",
  borderRadius: "8px",
  flex: "1 1 260px",
  padding: "10px",
};

const comparisonGridStyle: React.CSSProperties = {
  display: "grid",
  gap: "12px",
  gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))",
};

const comparisonColumnStyle: React.CSSProperties = {
  border: "1px solid #e2e8f0",
  borderRadius: "8px",
  padding: "12px",
};

const comparisonTitleStyle: React.CSSProperties = {
  fontSize: "15px",
  margin: "0 0 10px",
};

const emptyResultStyle: React.CSSProperties = {
  color: "#64748b",
  fontSize: "14px",
  margin: 0,
};

const examplesContainerStyle: React.CSSProperties = {
  background: "#f8fafc",
  border: "1px solid #e2e8f0",
  borderRadius: "8px",
  marginBottom: "12px",
  padding: "12px",
};

const examplesTitleStyle: React.CSSProperties = {
  color: "#475569",
  fontSize: "13px",
  fontWeight: 700,
  marginBottom: "8px",
};

const chipsStyle: React.CSSProperties = {
  display: "flex",
  flexWrap: "wrap",
  gap: "8px",
};

const chipButtonStyle: React.CSSProperties = {
  background: "#fff",
  border: "1px solid #cbd5e1",
  borderRadius: "999px",
  color: "#0f172a",
  cursor: "pointer",
  fontSize: "13px",
  padding: "7px 10px",
};

const answerStyle: React.CSSProperties = {
  lineHeight: 1.6,
  marginTop: 0,
  whiteSpace: "pre-wrap",
};

const citationTitleStyle: React.CSSProperties = {
  fontSize: "16px",
  margin: "16px 0 8px",
};

const citationStyle: React.CSSProperties = {
  background: "#f8fafc",
  border: "1px solid #e2e8f0",
  borderRadius: "8px",
  marginTop: "8px",
  padding: "12px",
};

const citationMetaStyle: React.CSSProperties = {
  color: "#475569",
  fontSize: "13px",
  fontWeight: 700,
  marginBottom: "8px",
};

const previewTextStyle: React.CSSProperties = {
  lineHeight: 1.5,
  margin: 0,
};

export default AiAssistantPage;
