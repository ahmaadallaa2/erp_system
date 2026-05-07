# AI Document Assistant - Test Cases

Use these test cases during the demo or include them in the repository under `test_cases/`.

## Prerequisites

- Backend is running on `http://127.0.0.1:9000`
- Frontend is running with `npm run dev`
- Ollama is running and `llama3` is installed
- User is logged in to the ERP frontend

## Test Case 1 - Upload DOCX Contract

**File:** `sample_smart_contract_agreement.docx`

**Steps:**
1. Open AI Assistant page.
2. Select `sample_smart_contract_agreement.docx`.
3. Click Upload.

**Expected Result:**
- Document appears in the documents list.
- Status is `uploaded`.
- File type is `docx`.

## Test Case 2 - Process DOCX Contract

**Steps:**
1. Click Process on the uploaded contract.
2. Wait until processing finishes.

**Expected Result:**
- Status becomes `ready`.
- Chunks are created.
- FAISS index is built.

## Test Case 3 - Ask Contract Summary Question

**Question:**
```text
What is this contract about?
```

**Expected Result:**
- The assistant summarizes the agreement.
- The answer mentions Alpha Client LLC and Beta Development Studio.
- Citations are displayed.

## Test Case 4 - Ask Payment Terms Question

**Question:**
```text
What are the payment terms?
```

**Expected Result:**
- The assistant mentions the fixed fee of 5,000 USD.
- The assistant mentions two milestones: 50% upon signing and 50% upon final delivery.
- Citations are displayed.

## Test Case 5 - Ask Breach/Termination Question

**Question:**
```text
What happens if one party breaches the agreement?
```

**Expected Result:**
- The assistant mentions seven days written notice and failure to cure the breach.
- Citations are displayed.

## Test Case 6 - Guardrail Test

**Question:**
```text
What is the CEO's phone number?
```

**Expected Result:**
- The assistant should not invent an answer.
- It should return: `I could not find this information in the uploaded document.`

## Test Case 7 - Upload PDF Contract

**File:** `sample_smart_contract_agreement.pdf`

**Steps:**
1. Upload the PDF version.
2. Process it.
3. Ask: `List the important clauses in this agreement.`

**Expected Result:**
- PDF upload succeeds.
- Process succeeds.
- The answer includes clauses like Parties, Scope of Work, Payment Terms, Confidentiality, Termination, and Governing Law.

## Test Case 8 - Sales Report Demo

**File:** `demo_sales_report.pdf` or `demo_sales_report.docx`

**Question:**
```text
Summarize the monthly sales performance.
```

**Expected Result:**
- The assistant mentions total sales of 185,000 EGP.
- The assistant mentions 42 invoices.
- The assistant mentions the top product and top customer.
- Citations are displayed.

## Suggested Demo Questions

```text
What is this contract about?
```

```text
What are the payment terms?
```

```text
Who are the parties involved in this agreement?
```

```text
What happens if one party breaches the agreement?
```

```text
Summarize the monthly sales performance.
```

```text
What is the main risk in the sales report?
```
