# Smart Contract Summary & Q&A Assistant

## Overview

This project is an ERP system with an isolated AI Document Assistant module. The
assistant is designed for a simple end-to-end demo: upload a contract or report,
process it into searchable chunks, ask questions, and receive an answer with
citations from the uploaded document.

The AI Assistant is intentionally isolated from the ERP core apps. It does not
modify accounting, inventory, sales, purchases, users, or core business logic.

## Features

- Upload PDF and DOCX files.
- List uploaded documents.
- Delete uploaded documents safely.
- Extract text from PDF files with `pypdf`.
- Extract text from DOCX files with `python-docx`.
- Chunk extracted text into smaller sections.
- Generate local embeddings with `sentence-transformers`.
- Build and search a local FAISS vector index.
- Ask questions using LangChain + Ollama `llama3`.
- Return clear answers with chunk citations.
- Guardrail response when the answer is not in the document:
  `I could not find this information in the uploaded document.`
- Simple React UI for demo usage.

## Tech Stack

- Backend: Django, Django REST Framework, drf-spectacular.
- Frontend: React, TypeScript, Vite.
- Document parsing: pypdf, python-docx.
- Vector search: sentence-transformers, FAISS.
- LLM: LangChain + Ollama llama3.
- Database: PostgreSQL.

## Architecture / Flow

1. User uploads PDF/DOCX from the frontend.
2. Backend stores a `Document` record and file.
3. User clicks `Process`.
4. Backend extracts text, creates `DocumentChunk` rows, generates embeddings,
   and builds a FAISS index under `MEDIA_ROOT`.
5. User asks a question.
6. Backend performs semantic search over the document chunks.
7. Retrieved chunks are passed as context to Ollama `llama3`.
8. Backend returns answer + citations.
9. User can delete the document, which also cleans chunks and FAISS index storage.

## How To Run Backend

```powershell
cd backend
pip install -r requirements.txt
python manage.py check
python manage.py runserver 9000
```

If `ai_assistant` migrations are not applied yet, run manually:

```powershell
python manage.py makemigrations ai_assistant
python manage.py migrate ai_assistant
```

## How To Run Frontend

```powershell
cd frontend
npm install
npm run dev
```

Open the app and use the sidebar link:

```text
AI Assistant
```

## How To Run Ollama llama3

```powershell
ollama pull llama3
ollama serve
```

Ollama must be running before using the Ask feature.

## API Endpoints

- `POST /api/ai-assistant/documents/`
  - Upload PDF/DOCX.
  - Content type: `multipart/form-data`.
  - Required field: `file`.

- `GET /api/ai-assistant/documents/`
  - List uploaded documents.

- `DELETE /api/ai-assistant/documents/{id}/`
  - Delete document.
  - Cleans related chunks and local FAISS index when present.

- `POST /api/ai-assistant/documents/{id}/process/`
  - No request body.
  - Extracts text, chunks text, generates embeddings, and builds FAISS index.

- `GET /api/ai-assistant/documents/{id}/chunks/`
  - Lists extracted chunks.

- `POST /api/ai-assistant/documents/{id}/search/`
  - Content type: `application/json`.
  - Body:
    ```json
    {
      "query": "termination clause",
      "top_k": 5
    }
    ```

- `POST /api/ai-assistant/documents/{id}/ask/`
  - Content type: `application/json`.
  - Body:
    ```json
    {
      "question": "What are the payment terms?",
      "top_k": 5
    }
    ```

## Demo Steps

1. Start PostgreSQL.
2. Start backend on port `9000`.
3. Start Ollama and pull `llama3`.
4. Start frontend.
5. Log in to the ERP frontend.
6. Open `AI Assistant`.
7. Upload `sample_smart_contract_agreement.pdf` or `.docx`.
8. Click `Process`.
9. Ask: `What are the payment terms?`
10. Review answer and citations.
11. Ask a missing-information question, such as:
    `What is the CEO's phone number?`
12. Confirm the guardrail answer.
13. Delete the document and confirm the list updates.

## Test Cases

Demo files and manual API test references are stored under:

```text
backend/apps/ai_assistant/test_assets/
```

Run automated AI Assistant tests:

```powershell
cd backend
python manage.py test apps.ai_assistant.tests
```

The tests cover:

- PDF/DOCX upload validation.
- Uppercase `.PDF` and `.DOCX` extensions.
- Rejection of unsupported extensions.
- Presence of demo fixtures.
- PDF/DOCX extraction when parsing dependencies are installed.

## Limitations

- Scanned/image-only PDFs may not produce extractable text.
- First processing run may download the sentence-transformers model.
- Ollama must be installed and running locally.
- `llama3` must be pulled before using Ask.
- Answer quality depends on extracted text and retrieved chunks.
- This is a demo-oriented assistant, not a full production document management system.

## Notes For Instructor

- The AI Assistant is implemented as an isolated Django app: `apps.ai_assistant`.
- No ERP core business apps were modified for AI logic.
- Frontend integration is intentionally simple and demo-focused.
- The delete operation cleans document chunks and removes the local FAISS index directory when available.
- The app supports both Swagger testing and end-to-end frontend testing.
