import { useEffect, useMemo, useState } from "react";
import axios from "axios";
import { askAiDocument } from "../api/ask-document";
import { listAiDocuments } from "../api/list-documents";
import { processAiDocument } from "../api/process-document";
import { uploadAiDocument } from "../api/upload-document";
import type { AiDocument, AskResponse } from "../types/ai-document";

function AiAssistantPage() {
  const [documents, setDocuments] = useState<AiDocument[]>([]);
  const [selectedDocumentId, setSelectedDocumentId] = useState("");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState<AskResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [busyDocumentId, setBusyDocumentId] = useState("");
  const [error, setError] = useState("");

  const selectedDocument = useMemo(
    () => documents.find((document) => document.id === selectedDocumentId),
    [documents, selectedDocumentId]
  );

  useEffect(() => {
    loadDocuments();
  }, []);

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

export default AiAssistantPage;
