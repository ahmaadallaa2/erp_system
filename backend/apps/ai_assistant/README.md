# AI Document Assistant

## Project Overview

AI Document Assistant is an isolated module inside the ERP system. It allows a
user to upload PDF/DOCX documents, process them into searchable chunks, ask
questions, and receive answers with citations from the uploaded document.

The module is intentionally scoped to `apps.ai_assistant` and does not modify ERP
core business modules such as accounting, inventory, sales, purchases, users, or
core.

## Features

- Upload PDF and DOCX files.
- List uploaded documents.
- Delete uploaded documents safely.
- Extract text from PDF/DOCX files.
- Chunk extracted text.
- Generate embeddings for chunks.
- Build and search a local FAISS index.
- Ask questions using LangChain + Ollama `llama3`.
- Return answers with citations from retrieved chunks.
- Simple React UI for demo usage.

## RAG Pipeline

1. Upload document.
2. Extract text:
   - PDF via `pypdf`.
   - DOCX via `python-docx`.
3. Split text into chunks.
4. Generate chunk embeddings using `sentence-transformers`.
5. Store/search vectors with FAISS.
6. Retrieve top matching chunks for the question.
7. Send only retrieved context to Ollama `llama3`.
8. Return answer plus citations.

## Tech Stack

- Django REST Framework
- drf-spectacular / Swagger
- pypdf
- python-docx
- sentence-transformers
- FAISS
- LangChain
- Ollama llama3
- React UI integration

## API Endpoints

- `POST /api/ai-assistant/documents/`
  - Upload PDF/DOCX.
  - Content type: `multipart/form-data`.
  - Field: `file`.

- `GET /api/ai-assistant/documents/`
  - List uploaded documents.

- `DELETE /api/ai-assistant/documents/{id}/`
  - Delete a document.
  - Cleans related chunks and local FAISS index when possible.

- `POST /api/ai-assistant/documents/{id}/process/`
  - No request body.
  - Extracts text, chunks it, generates embeddings, and builds the FAISS index.

- `GET /api/ai-assistant/documents/{id}/chunks/`
  - Lists extracted chunks.

- `POST /api/ai-assistant/documents/{id}/search/`
  - Content type: `application/json`.
  - Example:
    ```json
    {
      "query": "termination clause",
      "top_k": 5
    }
    ```

- `POST /api/ai-assistant/documents/{id}/ask/`
  - Content type: `application/json`.
  - Example:
    ```json
    {
      "question": "What are the payment terms?",
      "top_k": 5
    }
    ```

## Setup Instructions

Install backend dependencies:

```powershell
cd backend
pip install -r requirements.txt
python manage.py check
python manage.py runserver 9000
```

If migrations for this module are not applied yet:

```powershell
python manage.py makemigrations ai_assistant
python manage.py migrate ai_assistant
```

Run frontend:

```powershell
cd frontend
npm install
npm run dev
```

Open the frontend and select `AI Assistant` from the sidebar.

## Ollama Setup

```powershell
ollama pull llama3
ollama serve
```

Ollama must be running before using the Ask endpoint.

## Demo Steps

1. Start backend on port `9000`.
2. Start Ollama and ensure `llama3` is available.
3. Start frontend.
4. Log in to the ERP frontend.
5. Open `AI Assistant`.
6. Upload a PDF or DOCX.
7. Click `Process`.
8. Select the processed document.
9. Click one example question or type your own.
10. Click `Ask`.
11. Review answer and citations.
12. Delete the document to confirm cleanup.

## Example Questions

- What is this contract about?
- What are the payment terms?
- Who are the parties involved?
- What happens if one party breaches the agreement?
- Summarize this contract in simple terms.
- List the important clauses in this agreement.

## Guardrails

The model is instructed to answer only from retrieved document context. If the
answer is not available in the uploaded document, it should return:

```text
I could not find this information in the uploaded document.
```

## Test Cases

Demo files and manual API test references are stored under:

```text
backend/apps/ai_assistant/test_assets/
```

Run automated tests:

```powershell
cd backend
python manage.py test apps.ai_assistant.tests
```

The tests cover:

- PDF/DOCX upload validation.
- Uppercase `.PDF` and `.DOCX` extensions.
- Unsupported extension rejection.
- Demo fixture availability.
- PDF/DOCX extraction when parsing dependencies are installed.

## Limitations

- Scanned/image-only PDFs may not produce extractable text.
- First processing run may download the sentence-transformers model.
- Ollama must be installed and running locally.
- `llama3` must be pulled before Ask works.
- Answer quality depends on extraction quality and retrieved chunks.
- This is a demo-focused assistant, not a full production DMS.
