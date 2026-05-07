# Demo Files for AI Document Assistant

These files are ready to use in the final project demo.

## Files

- `sample_smart_contract_agreement.docx` - DOCX contract demo file.
- `sample_smart_contract_agreement.pdf` - PDF contract demo file.
- `demo_sales_report.docx` - ERP-style sales report demo file.
- `demo_sales_report.pdf` - PDF sales report demo file.
- `test_cases/AI_Document_Assistant_Test_Cases.md` - Manual test cases.
- `test_cases/api_test_cases.json` - API test cases reference.

## Recommended live demo flow

1. Upload `sample_smart_contract_agreement.docx`.
2. Click Process.
3. Ask: `What are the payment terms?`
4. Show answer and citations.
5. Upload `demo_sales_report.pdf`.
6. Click Process.
7. Ask: `Summarize the monthly sales performance.`

## Guardrail demo

Ask:

```text
What is the CEO's phone number?
```

Expected answer:

```text
I could not find this information in the uploaded document.
```
