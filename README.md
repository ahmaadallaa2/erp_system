# ERP System

This repository contains a Django-based ERP system with a React frontend.

## Overview

The project provides core ERP modules for users, partners, inventory, purchases,
sales, and accounting. The backend exposes REST APIs with Django REST Framework,
and the frontend provides a simple operational UI built with React and Vite.

## Main Modules

- Users and authentication
- Companies and branches
- Partners, customers, and suppliers
- Inventory products, warehouses, stock balances, and stock movements
- Purchase invoices
- Sales invoices
- Accounting accounts, journals, entries, and payments

## Tech Stack

- Backend: Django, Django REST Framework, PostgreSQL
- Frontend: React, TypeScript, Vite
- API docs: drf-spectacular / Swagger

## AI Assistant Module

The project also includes an isolated AI Document Assistant module for uploading
PDF/DOCX files, processing them with a RAG pipeline, and asking questions with
citations.

See the dedicated documentation:

```text
backend/apps/ai_assistant/README.md
```

## Run Backend

```powershell
cd backend
pip install -r requirements.txt
python manage.py check
python manage.py runserver 9000
```

## Run Frontend

```powershell
cd frontend
npm install
npm run dev
```
